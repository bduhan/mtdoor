"""
commands:
wx (blank) or forecast
wx alerts
wx obs

Future (or another module)? Watch for new alerts and automatically broadcast
"""

import datetime
from loguru import logger as log
import requests

import pytz
from pydantic import BaseModel, HttpUrl

from . import BaseCommand, CommandLoadError, CommandRunError

NWS_API = "https://api.weather.gov"


class PointInfo(BaseModel):
    """
    Response from api.weather.gov/points/{lat},{lon}
    Gives information needed for forecast and
    """

    # Three-letter identifier for responsible NWS office
    gridId: str  # also "cwa"
    gridX: int
    gridY: int

    # forecast with ~2 periods per day
    forecast: HttpUrl

    # forecase hourly
    forecastHourly: HttpUrl

    # current observations
    forecastGridData: HttpUrl

    # which weather stations are used for observations here?
    observationStations: HttpUrl

    # information about the forecast zone so we can look up alerts
    forecastZone: HttpUrl


def get_point_info(latitude, longitude) -> PointInfo:
    response = requests.get(f"{NWS_API}/points/{latitude},{longitude}")
    response.raise_for_status()
    data = response.json()
    return PointInfo(**data["properties"])


class StationInfo(BaseModel):
    """
    Item from response to url provided by PointInfo.observationStations
    This is how we get current observations for a single weather station.
    """

    stationIdentifier: str  # used to get current observations
    name: str
    timeZone: str
    forecast: HttpUrl
    county: HttpUrl
    fireWeatherZone: HttpUrl


def get_station_info(station_url: HttpUrl) -> StationInfo:
    response = requests.get(station_url)
    data = response.json()
    if "features" in data and len(data["features"]) > 0:
        # blindly take the first one
        if "properties" in data["features"][0]:
            return StationInfo(**data["features"][0]["properties"])


class ForecastItem(BaseModel):
    """
    Single forecast item from response to PointInfo.forecast
    """

    name: str
    detailedForecast: str


def get_forecast(forecast_url: HttpUrl) -> list[ForecastItem]:
    response = requests.get(forecast_url)
    response.raise_for_status()
    data = response.json()
    return [ForecastItem(**period) for period in data["properties"]["periods"]]


class Observation(BaseModel):
    """
    Single observation
    """

    timestamp: datetime.datetime
    temperature: float
    humidity: float


def get_observations(station_id: str) -> list[Observation]:
    response = requests.get(
        f"{NWS_API}/stations/{station_id}/observations", params={"limit": 10}
    )
    response.raise_for_status()
    data = response.json()

    observations: list[Observation] = []

    for feat in data["features"]:
        if "properties" not in feat:
            continue

        p = feat["properties"]
        try:
            # sometimes observations don't have temperature or relativeHumidity.. we skip them
            obs = Observation(
                timestamp=p["timestamp"],
                temperature=p["temperature"]["value"],
                humidity=p["relativeHumidity"]["value"],
            )
        except:
            continue
        observations.insert(0, obs)
    return observations


class Alert(BaseModel):
    """
    Single alert item. Alerts can be requested by latitude/longitude.
    """

    headline: str
    description: str
    effective: datetime.datetime
    severity: str


def get_alerts(latitude, longitude) -> list[Alert]:
    response = requests.get(
        f"{NWS_API}/alerts",
        params=dict(
            status="actual",
            severity="Extreme,Severe,Moderate,Minor",
            limit=5,
            point=f"{latitude},{longitude}",
        ),
    )

    response.raise_for_status()
    data = response.json()
    return [Alert(**feats["properties"]) for feats in data["features"]]


class Weather(BaseCommand):
    command = "wx"
    description = "read api.weather.gov"
    help = """'wx' - forecast
'wx obs' - current observations
'wx alerts' - alerts"""

    # where to get weather information about the point provided
    point_info: PointInfo

    default_latitude: float
    default_longitude: float

    def load(self):
        self.default_latitude = self.settings.getfloat(
            "global", "default_latitude", fallback=33.548786
        )
        self.default_longitude = self.settings.getfloat(
            "global", "default_longitude", fallback=-101.905093
        )

        # try the API
        try:
            requests.get(NWS_API, timeout=5).raise_for_status()
        except:
            raise CommandLoadError("Failed to reach NWS API")

    def invoke(self, msg: str, node: str) -> str:
        self.run_in_thread(self.run, msg, node)

    def run(self, msg: str, node: str):
        # if we have location for a user, use it
        latitude = self.default_latitude
        longitude = self.default_longitude
        user = self.get_node(node)

        if (
            user
            and user.position
            and user.position.latitude
            and user.position.longitude
        ):
            latitude = user.position.latitude
            longitude = user.position.longitude
            log.debug(f"user position: {round(latitude, 5)}, {round(longitude, 5)}")

        reply = ""
        if "alerts" in msg.lower():
            reply = self.alerts(latitude, longitude)
        elif "obs" in msg.lower():
            reply = self.observations(latitude, longitude)
        else:
            reply = self.forecast(latitude, longitude)

        self.send_dm(reply, node)

    def alerts(self, latitude: float, longitude: float) -> str:
        try:
            alerts: list[Alert] = get_alerts(latitude, longitude)
        except:
            log.exception("Failed to get alerts")
            raise CommandRunError()

        if len(alerts) == 0:
            return "No weather alerts"

        reply = ""
        for alert in alerts:
            proposed_addition = (
                f"({alert.severity}) {alert.headline}: {alert.description}\n"
            )
            if len(reply + proposed_addition) > 210:
                break
            else:
                reply += proposed_addition
        return reply.strip()

    def observations(self, latitude, longitude) -> str:
        try:
            point_info = get_point_info(latitude, longitude)
        except:
            log.exception("Failed to get point info.")
            return "Error getting point info."

        try:
            station_info = get_station_info(point_info.observationStations)
        except:
            log.exception("Failed to get observation stations.")
            return "Error getting observation stations."

        try:
            observations = get_observations(station_info.stationIdentifier)
        except:
            log.exception("Failed to get observations")
            return "Error getting observations."

        if len(observations) == 0:
            return "No weather observations"

        timezone = pytz.timezone(station_info.timeZone)

        reply = ""
        for obs in observations:
            local_time = obs.timestamp.astimezone(timezone).strftime("%H:%M:%S")
            proposed_addition = (
                f"{local_time} {obs.temperature:.1f}° C, {obs.humidity:.1f}% RH\n"
            )

            if len(reply + proposed_addition) > 210:
                break
            else:
                reply += proposed_addition
        return reply.strip()

    def forecast(self, latitude, longitude):
        try:
            point_info = get_point_info(latitude, longitude)
        except:
            log.exception("Failed to get point info.")
            return "Error getting point info."

        try:
            forecast_periods: list[ForecastItem] = get_forecast(point_info.forecast)
        except:
            raise CommandRunError(f"Failed to request weather forecast.")

        if len(forecast_periods) == 0:
            return "No forecast returned."

        reply = ""
        for p in forecast_periods:
            proposed_addition = f"{p.name.upper()}: {p.detailedForecast}\n"
            if len(reply + proposed_addition) > 200:
                break
            else:
                reply += proposed_addition

        if reply.strip() == "":
            return "Forecast was too long 😤"
        return reply.strip()
