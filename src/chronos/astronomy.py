"""
Module: astronomy.py
Description: Provides high-precision astronomical calculations including 
Equation of Time (EoT) corrections and Solar Ecliptic Longitude analysis.

References:
- Smart, W.M. (1977). Textbook on Spherical Astronomy.
- Meeus, J. (1998). Astronomical Algorithms.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Tuple

# Astronomical Constants
J2000_EPOCH = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
DEGREES_PER_RADIAN = 180 / math.pi
RADIANS_PER_DEGREE = math.pi / 180
MINUTES_PER_DEGREE_LONGITUDE = 4.0  # Earth rotates 1 degree every 4 minutes

def _to_utc(dt: datetime) -> datetime:
    """Helper to enforce UTC timezone on inputs."""
    if dt.tzinfo is None:
        # Assume naive datetime is UTC to avoid ambiguity
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def calculate_equation_of_time(day_of_year: int) -> float:
    """
    Calculates the Equation of Time (EoT) correction factor.
    
    The EoT accounts for the discrepancy between Apparent Solar Time (Sundial)
    and Mean Solar Time (Clock) caused by:
    1. The obliquity of the ecliptic (approx 23.44 degrees).
    2. The eccentricity of Earth's orbit (approx 0.0167).

    :param day_of_year: The nth day of the year (1-366).
    :return: Time correction in minutes (positive means Sun is fast).
    """
    # B parameter approximation (Smart, 1977)
    # B represents the mean anomaly of the Earth relative to the perihelion.
    B = 2 * math.pi * (day_of_year - 81) / 365
    
    # EoT Formula: E = 9.87sin(2B) - 7.53cos(B) - 1.5sin(B)
    eot_minutes = (9.87 * math.sin(2 * B)) - (7.53 * math.cos(B)) - (1.5 * math.sin(B))
    
    return eot_minutes

def calculate_solar_longitude(dt: datetime) -> float:
    """
    Calculates the Apparent Solar Ecliptic Longitude (Lambda).
    Crucial for determining Solar Terms (JieQi) for Month Pillar switching.
    
    Algorithm simplified from VSOP87 for moderate precision.
    
    :param dt: UTC Datetime.
    :return: Degrees (0.0 - 360.0), where 0 is Vernal Equinox.
    """
    dt_utc = _to_utc(dt)
    
    # Calculate Julian Days (n) since J2000.0
    delta = dt_utc - J2000_EPOCH
    n = delta.days + (delta.seconds / 86400.0)
    
    # Mean Longitude of the Sun (L)
    # L = 280.460 + 0.9856474 * n
    L = (280.460 + 0.9856474 * n) % 360
    
    # Mean Anomaly of the Sun (g)
    # g = 357.528 + 0.9856003 * n
    g_degrees = (357.528 + 0.9856003 * n) % 360
    g_radians = g_degrees * RADIANS_PER_DEGREE
    
    # Ecliptic Longitude (Lambda)
    # Lambda = L + 1.915 * sin(g) + 0.020 * sin(2g)
    lambda_degrees = L + 1.915 * math.sin(g_radians) + 0.020 * math.sin(2 * g_radians)
    
    return lambda_degrees % 360
    
def get_true_solar_time(dt: datetime, longitude: float) -> datetime:
    """
    Converts a standard UTC timestamp to Local Apparent Solar Time (LAST).
    
    This function applies two physics corrections:
    1. Geographic Offset: Longitude difference from UTC (Greenwich).
    2. Equation of Time: Orbital eccentricity correction.
    
    :param dt: Input datetime (UTC).
    :param longitude: Observer's longitude (East positive, West negative).
    :return: Adjusted Datetime object representing True Solar Time.
    """
    dt_utc = _to_utc(dt)
    
    # 1. Geographic Offset Calculation
    # Earth rotates 15 degrees per hour -> 4 minutes per degree.
    geo_offset_minutes = longitude * MINUTES_PER_DEGREE_LONGITUDE
    
    # 2. Equation of Time Calculation
    day_of_year = dt_utc.timetuple().tm_yday
    eot_minutes = calculate_equation_of_time(day_of_year)
    
    # 3. Apply Total Offset
    total_offset = timedelta(minutes=geo_offset_minutes + eot_minutes)
    solar_time = dt_utc + total_offset
    
    # Note: The result is conceptually "Solar Time" at that location.
    # We strip tzinfo in the final step or keep it as reference depending on downstream needs.
    # Here we return a naive datetime implied to be local solar time.
    return solar_time.replace(tzinfo=None)
