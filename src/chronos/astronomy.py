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


def _solar_term_index(lon_degrees: float) -> int:
    """
    Table index of the term in force at a longitude.

    Term k begins at (315 + 15k) degrees, so the index is
    int(((lon - 315) % 360) / 15). Shared by the name and type lookups
    so both stay consistent by construction.
    """
    if not 0.0 <= lon_degrees < 360.0:
        raise ValueError(
            f"longitude must be in [0, 360), got {lon_degrees}"
        )
    return int(((lon_degrees - 315.0) % 360.0) / 15.0)


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
    return SOLAR_TERMS[_solar_term_index(lon_degrees)]

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
    return "Jie" if _solar_term_index(lon_degrees) % 2 == 0 else "Qi"

def next_solar_term(dt: datetime) -> tuple[datetime, str, str]:
    """
    Finds the next solar term boundary after a moment.

    Solar longitude grows monotonically at roughly 0.99 degrees per
    day, so the next 15 degree boundary (315 + 15k) is at most about
    15.2 days away; bisection over a 17 day bracket locates it to
    well under a second. The simplified longitude kernel carries
    about 0.006 degrees of error, so the returned moment is good
    to roughly a minute.

    :param dt: Datetime to search forward from; naive inputs are
        assumed to be UTC. A moment exactly on a boundary returns
        the following term, not the current one.
    :return: (moment, english_name, chinese_name) of the term that
        begins at that boundary; moment is timezone aware UTC.
    """
    dt_utc = _to_utc(dt)
    start_lon = calculate_solar_longitude(dt_utc)
    # Distance to the next boundary, in (0, 15]: the modulo wraps to
    # 0 both exactly on a boundary and exactly 15 degrees before one,
    # and in both cases the next boundary is 15 degrees ahead.
    delta = (315.0 - start_lon) % 15.0
    if delta == 0.0:
        delta = 15.0
    current_idx = _solar_term_index(start_lon)
    next_term = SOLAR_TERMS[(current_idx + 1) % 24]

    def progress(t: datetime) -> float:
        return (calculate_solar_longitude(t) - start_lon) % 360.0

    lo = dt_utc
    hi = dt_utc + timedelta(days=17)
    for _ in range(50):
        mid = lo + (hi - lo) / 2
        if progress(mid) < delta:
            lo = mid
        else:
            hi = mid
    return hi, next_term[0], next_term[1]

def _validate_term_count(count: int) -> None:
    """Rejects non-integer or non-positive term counts."""
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError("count must be an integer")
    if count < 1:
        raise ValueError(f"count must be at least 1, got {count}")


def next_solar_terms(dt: datetime, count: int = 1) -> list[tuple[datetime, str, str]]:
    """
    Lists the next count solar term boundaries after a moment.

    Chains next_solar_term: each returned moment sits just after the
    boundary it names, so the next call steps to the following term,
    including the wrap from DaHan back to LiChun.

    :param dt: Datetime to search forward from; naive inputs are
        assumed to be UTC.
    :param count: How many upcoming terms to list.
    :return: List of (moment, english_name, chinese_name), earliest first.
    :raises TypeError: If count is not an integer.
    :raises ValueError: If count is less than 1.
    """
    _validate_term_count(count)
    cursor = _to_utc(dt)
    terms = []
    for _ in range(count):
        moment, en, cn = next_solar_term(cursor)
        terms.append((moment, en, cn))
        cursor = moment
    return terms


def previous_solar_term(dt: datetime) -> tuple[datetime, str, str]:
    """
    Finds the solar term boundary at or before a moment.

    Mirror of next_solar_term, searching backward: solar longitude
    grows monotonically at roughly 0.99 degrees per day, so the
    previous 15 degree boundary (315 + 15k) is at most about
    15.2 days behind; bisection over a 17 day bracket locates it to
    well under a second. The simplified longitude kernel carries
    about 0.006 degrees of error, so the returned moment is good
    to roughly a minute.

    The returned moment sits just before the boundary, so chaining
    calls walks the term table backward one term at a time.

    :param dt: Datetime to search backward from; naive inputs are
        assumed to be UTC. A moment exactly on a boundary returns
        that boundary's term, not the one before it.
    :return: (moment, english_name, chinese_name) of the term that
        began at that boundary; moment is timezone aware UTC.
    """
    dt_utc = _to_utc(dt)
    start_lon = calculate_solar_longitude(dt_utc)
    # Distance back to the most recent boundary, in [0, 15): the
    # modulo wraps to 0 exactly on a boundary, and that boundary is
    # the term in force, so return it directly.
    delta = (start_lon - 315.0) % 15.0
    current_idx = _solar_term_index(start_lon)
    term = SOLAR_TERMS[current_idx]
    if delta == 0.0:
        return dt_utc, term[0], term[1]

    def progress(t: datetime) -> float:
        return (start_lon - calculate_solar_longitude(t)) % 360.0

    lo = dt_utc - timedelta(days=17)
    hi = dt_utc
    for _ in range(50):
        mid = lo + (hi - lo) / 2
        if progress(mid) < delta:
            hi = mid
        else:
            lo = mid
    return lo, term[0], term[1]

def previous_solar_terms(dt: datetime, count: int = 1) -> list[tuple[datetime, str, str]]:
    """
    Lists the count solar term boundaries at or before a moment,
    most recent first.

    Chains previous_solar_term: each returned moment sits just before
    the boundary it names, so the next call steps to the term before
    it, including the wrap from LiChun back to DaHan. The cursor is
    nudged one second back between calls so a moment landing exactly
    on a boundary can never return the same term twice.

    :param dt: Datetime to search backward from; naive inputs are
        assumed to be UTC.
    :param count: How many preceding terms to list.
    :return: List of (moment, english_name, chinese_name), most recent first.
    :raises TypeError: If count is not an integer.
    :raises ValueError: If count is less than 1.
    """
    _validate_term_count(count)
    cursor = _to_utc(dt)
    terms = []
    for _ in range(count):
        moment, en, cn = previous_solar_term(cursor)
        terms.append((moment, en, cn))
        cursor = moment - timedelta(seconds=1)
    return terms


def _resolve_term_name(term: str) -> tuple[str, str]:
    """
    Validates a solar term name and returns its canonical pair.

    English names match case insensitively ("dongzhi", "DongZhi"),
    Chinese names match exactly ("冬至"); surrounding whitespace is
    ignored.
    """
    if not isinstance(term, str):
        raise TypeError("term name must be a string")
    cleaned = term.strip()
    for en, cn in SOLAR_TERMS:
        if cleaned.lower() == en.lower() or cleaned == cn:
            return en, cn
    raise ValueError(f"unknown solar term {term!r}")


def next_solar_term_named(dt: datetime, term: str) -> tuple[datetime, str, str]:
    """
    Finds the next occurrence of one named solar term after a moment.

    Scans at most one full year of boundaries: the named term occurs
    exactly once in any 24 consecutive terms, so the first match in
    next_solar_terms(dt, 24) is the answer. A moment exactly on the
    named term's boundary returns next year's occurrence, matching
    next_solar_term.

    :param dt: Datetime to search forward from; naive inputs are
        assumed to be UTC.
    :param term: English name (case insensitive, e.g. "DongZhi") or
        Chinese name (e.g. "冬至").
    :return: (moment, english_name, chinese_name) of the next
        occurrence; moment is timezone aware UTC.
    :raises TypeError: If term is not a string.
    :raises ValueError: If term names no solar term.
    """
    en, _ = _resolve_term_name(term)
    for moment, term_en, term_cn in next_solar_terms(dt, 24):
        if term_en == en:
            return moment, term_en, term_cn
    raise RuntimeError(f"term {en} not found in a full year of terms")


def previous_solar_term_named(dt: datetime, term: str) -> tuple[datetime, str, str]:
    """
    Finds the most recent occurrence of one named solar term at or
    before a moment.

    Mirror of next_solar_term_named, scanning backward: the first
    match in previous_solar_terms(dt, 24) is the answer. A moment
    exactly on the named term's boundary returns that boundary,
    matching previous_solar_term.

    :param dt: Datetime to search backward from; naive inputs are
        assumed to be UTC.
    :param term: English name (case insensitive, e.g. "DongZhi") or
        Chinese name (e.g. "冬至").
    :return: (moment, english_name, chinese_name) of the most recent
        occurrence; moment is timezone aware UTC.
    :raises TypeError: If term is not a string.
    :raises ValueError: If term names no solar term.
    """
    en, _ = _resolve_term_name(term)
    for moment, term_en, term_cn in previous_solar_terms(dt, 24):
        if term_en == en:
            return moment, term_en, term_cn
    raise RuntimeError(f"term {en} not found in a full year of terms")


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
