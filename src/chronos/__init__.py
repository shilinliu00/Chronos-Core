"""
Chronos-Core: high-precision temporal coordinate engine.

Converts linear Gregorian timestamps (UTC) into 4-dimensional cyclic
coordinates (Base-60 / sexagenary), corrected with astronomical physics
(Equation of Time, solar ecliptic longitude).
"""

from .cyclic_math import CyclicVariable
from .astronomy import (
    calculate_equation_of_time,
    calculate_solar_longitude,
    calculate_solar_declination,
    get_true_solar_time,
)
from .converter import TemporalCoordinateEngine

__version__ = "0.1.0"

__all__ = [
    "CyclicVariable",
    "TemporalCoordinateEngine",
    "calculate_equation_of_time",
    "calculate_solar_longitude",
    "calculate_solar_declination",
    "get_true_solar_time",
]
