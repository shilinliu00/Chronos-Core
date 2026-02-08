"""
Module: astronomy.py
Description: Provides high-precision astronomical calculations including 
Equation of Time (EoT) corrections and Solar Longitude analysis.
"""

import math
from datetime import datetime, timedelta

def calculate_equation_of_time(day_of_year: int) -> float:
    """
    Approximates the Equation of Time (EoT) correction factor.
    The EoT creates the difference between Apparent Solar Time and Mean Solar Time
    due to the obliquity of the ecliptic and the eccentricity of Earth's orbit.
    
    :param day_of_year: The nth day of the year (1-366).
    :return: Correction in minutes.
    """
    # Approximation formula (Smart, 1977)
    # B is in radians
    B = 2 * math.pi * (day_of_year - 81) / 365
    eot = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)
    return eot

def get_true_solar_time(dt: datetime, longitude: float) -> datetime:
    """
    Converts a standard UTC-based datetime to Local Apparent Solar Time (LAST).
    
    Formula: LAST = Local Standard Time + (Long - StandardMeridian)*4min + EoT
    
    :param dt: Datetime object (assumed naive is Local Standard Time or aware is UTC).
    :param longitude: Observer's longitude (East is positive).
    :return: Adjusted Datetime object representing True Solar Time.
    """
    # 1. Calculate offset from UTC (assume input is UTC for simplicity in this demo)
    # In production, this handles timezone localization via `pytz`
    
    # 2. Solar noon offset: Earth rotates 1 degree every 4 minutes.
    # UTC is at 0 degrees.
    geo_offset_minutes = longitude * 4
    
    # 3. Equation of Time correction
    day_of_year = dt.timetuple().tm_yday
    eot_minutes = calculate_equation_of_time(day_of_year)
    
    total_offset = timedelta(minutes=geo_offset_minutes + eot_minutes)
    
    return dt + total_offset
