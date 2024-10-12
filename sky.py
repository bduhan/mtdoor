"""
https://rhodesmill.org/skyfield/toc.html

ChatGPT wrote these functions
"""

from skyfield.api import load
from skyfield.api import Topos
from datetime import datetime
import numpy as np


LUBBOCK_COUNTY_CENTER = (33.5661, -101.9164)


def solar_position(
    latitude: float = LUBBOCK_COUNTY_CENTER[0],
    longitude: float = LUBBOCK_COUNTY_CENTER[1],
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
        phase = f"New Moon 🌑 ({angle:.1f}°)"
    elif angle < 45:
        phase = f"Waxing Crescent 🌒 ({angle:.1f}°)"
    elif angle < 90:
        phase = f"First Quarter 🌓 ({angle:.1f}°)"
    elif angle < 135:
        phase = f"Waxing Gibbous 🌔 ({angle:.1f}°)"
    elif angle < 180:
        phase = f"Full Moon 🌕 ({angle:.1f}°)"
    elif angle < 225:
        phase = f"Waning Gibbous 🌖 ({angle:.1f}°)"
    elif angle < 270:
        phase = f"Last Quarter 🌗 ({angle:.1f}°)"
    elif angle < 315:
        phase = f"Waning Crescent 🌘 ({angle:.1f}°)"
    else:
        phase = f"New Moon 🌑 ({angle:.1f}°)"

    return phase
