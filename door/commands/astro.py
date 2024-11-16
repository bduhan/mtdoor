from datetime import datetime
import numpy as np

from loguru import logger as log

from . import BaseCommand, CommandLoadError

from skyfield.api import Loader, Topos
from skyfield import almanac

from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
import pytz

load = Loader('./data/')

def solar_position(
    latitude,
    longitude,
) -> tuple[int, int]:
    """
    return is (altitude, azimuth) of the sun in degrees
    """
    # Load the necessary data
    ts = load.timescale()
    planets = load("de421.bsp")
    earth = planets["earth"]
    sun = planets["sun"]

    # Define the observer's location
    observer = earth + Topos(latitude, longitude)

    # Get the current time
    current_time = datetime.utcnow()
    t = ts.utc(
        current_time.year,
        current_time.month,
        current_time.day,
        current_time.hour,
        current_time.minute,
        current_time.second,
    )

    # Compute the position of the sun
    astrometric = observer.at(t).observe(sun)
    alt, az, _ = astrometric.apparent().altaz()

    return int(alt.degrees), int(az.degrees)


def moon_phase():
    # Load the necessary data
    ts = load.timescale()
    planets = load("de421.bsp")  # Using the DE421 ephemeris
    earth = planets["earth"]
    moon = planets["moon"]
    sun = planets["sun"]

    # Get the current time
    current_time = datetime.utcnow()
    t = ts.utc(
        current_time.year,
        current_time.month,
        current_time.day,
        current_time.hour,
        current_time.minute,
        current_time.second,
    )

    # Compute positions
    astrometric_moon = earth.at(t).observe(moon)
    astrometric_sun = earth.at(t).observe(sun)

    # Get the positions in apparent altitude/azimuth
    moon_apparent = astrometric_moon.apparent()
    sun_apparent = astrometric_sun.apparent()

    # Calculate the angular separation between the Sun and Moon
    moon_ecliptic = moon_apparent.ecliptic_position().au
    sun_ecliptic = sun_apparent.ecliptic_position().au

    # Calculate the angle between the two bodies in radians
    angle = np.arctan2(moon_ecliptic[1], moon_ecliptic[0]) - np.arctan2(
        sun_ecliptic[1], sun_ecliptic[0]
    )
    angle = np.degrees(angle) % 360  # Convert to degrees and normalize

    # Determine the moon phase
    if angle < 0:
        angle += 360

    # Phases of the Moon based on the angle
    if angle < 1:
        phase = f"New Moon 🌑"
    elif angle < 45:
        phase = f"Waxing Crescent 🌒"
    elif angle < 90:
        phase = f"First Quarter 🌓"
    elif angle < 135:
        phase = f"Waxing Gibbous 🌔"
    elif angle < 180:
        phase = f"Full Moon 🌕"
    elif angle < 225:
        phase = f"Waning Gibbous 🌖"
    elif angle < 270:
        phase = f"Last Quarter 🌗"
    elif angle < 315:
        phase = f"Waning Crescent 🌘"
    else:
        phase = f"New Moon 🌑"

    return phase + f" ({angle:.1f}°)"


def sun_rise_set_times(latitude, longitude):    
    ts = load.timescale()    
    e = load("de421.bsp")    
    observer = Topos(latitude, longitude)    
    t0 = ts.now()    
    t1 = ts.now() + timedelta(days=1)    
    
    # Calculate sunrise and sunset    
    f = almanac.sunrise_sunset(e, observer)    
    times, events = almanac.find_discrete(t0, t1, f)    
    
    # Get the timezone for the observer's location    
    timezone_str = get_timezone(latitude, longitude)    
    tz = pytz.timezone(timezone_str)    
        
    rise, set = None, None    
    for time, event in zip(times, events):    
        dt = time.utc_datetime().replace(tzinfo=pytz.UTC).astimezone(tz)    
        if event == 1 and rise is None:    
            rise = dt    
        elif event == 0 and set is None:    
            set = dt    
    return rise, set    
    

def moon_rise_set_times(latitude, longitude):    
    ts = load.timescale()    
    e = load("de421.bsp")    
    observer = Topos(latitude, longitude)    
    t0 = ts.now()    
    t1 = ts.now() + timedelta(days=1)    
    
    # Calculate moonrise and moonset    
    f = almanac.risings_and_settings(e, e['moon'], observer)    
    times, events = almanac.find_discrete(t0, t1, f)    
    
    # Get the timezone for the observer's location    
    timezone_str = get_timezone(latitude, longitude)    
    tz = pytz.timezone(timezone_str)    
        
    rise, set = None, None    
    for time, event in zip(times, events):    
        dt = time.utc_datetime().replace(tzinfo=pytz.UTC).astimezone(tz)    
        if event == 1 and rise is None:    
            rise = dt    
        elif event == 0 and set is None:    
            set = dt    
    return rise, set


def get_timezone(latitude, longitude):
    """Determine the timezone based on latitude and longitude."""    
    tf = TimezoneFinder()    
    timezone = tf.timezone_at(lat=latitude, lng=longitude)    
    return timezone if timezone else "UTC"


class Astro(BaseCommand):
    command = "astro"
    description = "Displays astronomical data"
    help = """'astro sun', 'astro moon'"""

    latitude: float
    longitude: float

    def load(self):
        self.default_latitude = self.settings.getfloat(    
            "global", "default_latitude", fallback=33.548786    
        )    
        self.default_longitude = self.settings.getfloat(    
            "global", "default_longitude", fallback=-101.905093    
        )

        # run each function to make sure required resources are loaded
        try:
            solar_position(self.default_latitude, self.default_longitude)
            moon_phase()
        except:
            log.exception("Failed to load Astro")
            raise CommandLoadError()

    def invoke(self, msg: str, node: str) -> str:
        # in case we need position
        latitude = self.default_latitude
        longitude = self.default_longitude

        user = self.get_node(node)

        if user and user.position and user.position.latitude and user.position.longitude:
            latitude = user.position.latitude
            longitude = user.position.longitude
            log.debug(f"user position: {round(latitude, 5)}, {round(longitude, 5)}")

        if "sun" in msg.lower():
            altitude, azimuth = solar_position(latitude, longitude)
            rise, set = sun_rise_set_times(latitude, longitude)
            return (f"🌞 altitude: {altitude}°, azimuth: {azimuth}°\n"
                    f"🌅 Next Sunrise: {rise.strftime('%m-%d %H:%M')}\n"
                    f"🌇 Next Sunset: {set.strftime('%m-%d %H:%M')}")            

        elif "moon" in msg.lower():
            phase = moon_phase()   
            rise, set = moon_rise_set_times(latitude, longitude)
            return (f"{phase}\n"
                    f"🌕 Next Moonrise: {rise.strftime('%m-%d %H:%M') if rise else 'N/A'}\n"
                    f"🌑 Next Moonset: {set.strftime('%m-%d %H:%M') if set else 'N/A'}")        

        else:
            return self.description + "\n\n" + self.help
