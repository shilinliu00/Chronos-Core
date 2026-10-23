"""
Module: astronomy.py
Description: Astronomical physics kernel for Chronos-Core.
Computes the Equation of Time, geometric solar ecliptic longitude
(lambda), and solar declination (delta) used to define strict
temporal boundaries (solar terms) for the cyclic coordinates.
"""

import math
from datetime import datetime, timedelta, timezone

# Astronomical Constants
J2000_EPOCH = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
MINUTES_PER_DEGREE_LONGITUDE = 4.0  # Earth rotates 1 degree every 4 minutes
SECONDS_PER_DAY = 86400.0
J2000_OBLIQUITY = 23.4393  # Mean obliquity of the ecliptic at J2000.0 (degrees)

# The 24 Solar Terms (二十四节气), ordered from the engine's annual reset
# point: LiChun (Start of Spring) at 315 degrees ecliptic longitude. Each
# term spans a 15 degree segment; the 12 "Jie" (节) terms spaced 30 degrees
# apart are exactly the month pillar boundaries in converter.py.
SOLAR_TERMS = [
    ("LiChun", "立春"), ("YuShui", "雨水"), ("JingZhe", "惊蛰"),
    ("ChunFen", "春分"), ("QingMing", "清明"), ("GuYu", "谷雨"),
    ("LiXia", "立夏"), ("XiaoMan", "小满"), ("MangZhong", "芒种"),
    ("XiaZhi", "夏至"), ("XiaoShu", "小暑"), ("DaShu", "大暑"),
    ("LiQiu", "立秋"), ("ChuShu", "处暑"), ("BaiLu", "白露"),
    ("QiuFen", "秋分"), ("HanLu", "寒露"), ("ShuangJiang", "霜降"),
    ("LiDong", "立冬"), ("XiaoXue", "小雪"), ("DaXue", "大雪"),
    ("DongZhi", "冬至"), ("XiaoHan", "小寒"), ("DaHan", "大寒"),
]


def solar_term_for_longitude(lon_degrees: float) -> tuple[str, str]:
    """
    Names the solar term (节气) in force at a given ecliptic longitude.

    Term k begins at (315 + 15k) degrees, so the index is
    int(((lon - 315) % 360) / 15). The 12 Jie terms (even spacing of
    30 degrees) line up with the month branch boundaries computed in
    converter.py, which counts month offsets from LiChun the same way.

    :param lon_degrees: Solar ecliptic longitude in [0, 360).
    :return: (english_name, chinese_name) of the current term.
    :raises ValueError: If longitude is outside [0, 360).
    """
    if not 0.0 <= lon_degrees < 360.0:
        raise ValueError(
            f"longitude must be in [0, 360), got {lon_degrees}"
        )
    idx = int(((lon_degrees - 315.0) % 360.0) / 15.0)
    return SOLAR_TERMS[idx]

def solar_term_type(lon_degrees: float) -> str:
    """
    Classifies the solar term in force as "Jie" (节) or "Qi" (气).

    The term table starts at LiChun and alternates Jie, Qi, so even
    table indices are Jie terms and odd ones are Qi terms. The 12 Jie
    terms are the month pillar boundaries in converter.py; the Qi
    terms sit mid month and never change a pillar.

    :param lon_degrees: Solar ecliptic longitude in [0, 360).
    :return: "Jie" or "Qi".
    :raises ValueError: If longitude is outside [0, 360).
    """
    term_en, _ = solar_term_for_longitude(lon_degrees)
    idx = next(i for i, (en, _) in enumerate(SOLAR_TERMS) if en == term_en)
    return "Jie" if idx % 2 == 0 else "Qi"

def _to_utc(dt: datetime) -> datetime:
    """Helper to enforce UTC timezone on inputs to prevent localization bugs."""
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
    :raises ValueError: If day_of_year is outside [1, 366].
    """
    if not 1 <= day_of_year <= 366:
        raise ValueError(
            f"day_of_year must be in [1, 366], got {day_of_year}"
        )
    # B parameter approximation (Smart, 1977)
    # B represents the mean anomaly of the Earth relative to the perihelion.
    B = 2.0 * math.pi * (day_of_year - 81) / 365.0
    
    # EoT Formula: E = 9.87sin(2B) - 7.53cos(B) - 1.5sin(B)
    eot_minutes = (9.87 * math.sin(2.0 * B)) - (7.53 * math.cos(B)) - (1.5 * math.sin(B))
    
    return eot_minutes

def calculate_solar_longitude(dt: datetime) -> float:
    """
    Calculates the geometric Solar Ecliptic Longitude (Lambda).
    Crucial for determining Solar Terms (JieQi) for Month Pillar switching.

    Simplified from VSOP87 for moderate precision. Nutation and aberration
    are not applied, so this is geometric longitude rather than apparent.
    
    :param dt: UTC Datetime.
    :return: Degrees (0.0 - 360.0), where 0 is Vernal Equinox.
    """
    dt_utc = _to_utc(dt)
    
    # Calculate Julian Days (n) since J2000.0
    # Using total_seconds() preserves microsecond precision
    delta = dt_utc - J2000_EPOCH
    n = delta.total_seconds() / SECONDS_PER_DAY
    
    # Mean Longitude of the Sun (L)
    L = (280.460 + 0.9856474 * n) % 360.0
    
    # Mean Anomaly of the Sun (g)
    g_degrees = (357.528 + 0.9856003 * n) % 360.0
    g_radians = math.radians(g_degrees)
    
    # Ecliptic Longitude (Lambda)
    lambda_degrees = L + 1.915 * math.sin(g_radians) + 0.020 * math.sin(2.0 * g_radians)
    
    return lambda_degrees % 360.0

def calculate_solar_declination(dt: datetime) -> float:
    """
    Calculates the Sun's declination (celestial latitude).

    Standard formula (as used by the NOAA solar calculator):
    δ = asin(sin ε · sin λ), where ε is the mean obliquity of the ecliptic
    and λ is the geometric ecliptic longitude from calculate_solar_longitude.

    :param dt: UTC Datetime.
    :return: Declination in degrees, within [-23.44, 23.44].
    """
    lambda_degrees = calculate_solar_longitude(dt)
    sin_delta = (
        math.sin(math.radians(J2000_OBLIQUITY))
        * math.sin(math.radians(lambda_degrees))
    )
    # Clamp guards against |sin_delta| > 1 from floating point noise.
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_delta))))

def get_true_solar_time(dt: datetime, longitude: float) -> datetime:
    """
    Converts a standard UTC timestamp to Local Apparent Solar Time (LAST).
    
    This function applies two physics corrections:
    1. Geographic Offset: Longitude difference from UTC (Greenwich).
    2. Equation of Time: Orbital eccentricity correction.
    
    :param dt: Input datetime (UTC).
    :param longitude: Observer's longitude (East positive, West negative).
    :return: Naive datetime representing Local Apparent Solar Time at that
        location (tzinfo is stripped because the value is no longer UTC).
    :raises ValueError: If longitude is outside [-180, 180] degrees.
    """
    if not -180.0 <= longitude <= 180.0:
        raise ValueError(
            f"longitude must be within [-180, 180], got {longitude}"
        )
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
    return solar_time.replace(tzinfo=None)
