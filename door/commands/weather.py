"""
commands:
wx (blank) or forecast
wx alerts
wx obs

Future (or another module)? Watch for new alerts and automatically broadcast
"""

import os
import datetime
from loguru import logger as log
import requests

import pytz
from pydantic import BaseModel, HttpUrl

from .base_command import BaseCommand, CommandLoadError, CommandRunError

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
        p = feat["properties"]
        observations.insert(
            0,
            Observation(
                timestamp=p["timestamp"],
                temperature=p["temperature"]["value"],
                humidity=p["relativeHumidity"]["value"],
            ),
        )
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

    latitude: float
    longitude: float

    # which weather station to use for current observations
    station_info: StationInfo

    def load(self):
        # TODO move these to configuration or ask the Meshtastic node
        self.latitude = float(os.getenv("DEFAULT_LATITUDE", 33.548786))
        self.longitude = float(os.getenv("DEFAULT_LONGITUDE", -101.905093))

        # loading fails if we can't reach the weather API
        try:
            self.point_info = get_point_info(self.latitude, self.longitude)
            self.station_info = get_station_info(self.point_info.observationStations)
        except:
            # log.exception()
            raise CommandLoadError("Failed to reach api.weather.gov")

    def invoke(self, msg: str, node: str) -> str:
        if "alerts" in msg.lower():
            return self.alerts()
        if "obs" in msg.lower():
            return self.observations()
        else:
            return self.forecast()

    def forecast(self):
        try:
            forecast_periods: list[ForecastItem] = get_forecast(
                self.point_info.forecast
            )
        except:
            raise CommandRunError(f"Failed to request weather forecast.")

        if len(forecast_periods) == 0:
            return "No forecast returned."

        reply = ""
        for p in forecast_periods:
            proposed_addition = f"{p.name.upper()}: {p.detailedForecast}\n"
            if len(reply + proposed_addition) > 210:
                break
            else:
                reply += proposed_addition

        return reply.strip()

    def alerts(self) -> str:
        try:
            alerts: list[Alert] = get_alerts(self.latitude, self.longitude)
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

    def observations(self) -> str:
        try:
            observations = get_observations(self.station_info.stationIdentifier)
        except:
            log.exception("Failed to get observations")
            raise CommandLoadError()

        if len(observations) == 0:
            return "No weather observations"

        timezone = pytz.timezone(self.station_info.timeZone)

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
