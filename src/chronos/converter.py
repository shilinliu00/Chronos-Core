"""
Module: converter.py
Description: The main engine utilizing astronomical data to derive 
Base-60 temporal coordinates (The Four Pillars).

Implements the classic algorithms:
1. Solar Term delineation for Year/Month boundaries (LiChun).
2. "Five Tigers Chasing Month" (Wu Hu Dun) for Month Stem derivation.
3. "Five Rats Chasing Hour" (Wu Zi Dun) for Hour Stem derivation.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Any

from .cyclic_math import CyclicVariable
from .astronomy import get_true_solar_time, calculate_solar_longitude

class TemporalCoordinateEngine:
    """
    Main Interface for converting Gregorian timestamps into 
    Cyclic Temporal Coordinates (Four Pillars).
    
    Architecture:
    - Input: UTC Datetime + Geo-coordinates.
    - Process: Physics Correction (EoT) -> Solar Longitude Analysis -> Pattern Mapping.
    - Output: 4-Dimensional Cyclic Vector.
    """
    
    # Reference Date for DAY pillar: Jan 1, 1900 was a Jia-Xu (Index 10) day.
    # This is a continuous count independent of solar terms.
    REF_DATE = datetime(1900, 1, 1)
    REF_DAY_IDX = 10 
    
    def __init__(self, use_astronomy_correction: bool = True):
        self.precise_mode = use_astronomy_correction

    def _get_year_index(self, dt: datetime, solar_lon: float) -> int:
        """
        Determines the Year Pillar Index.
        Critical Logic: The year does NOT change on Jan 1st. 
        It changes at 'LiChun' (Start of Spring), approx Feb 4th, 
        when Solar Longitude reaches 315 degrees.
        """
        # 1984 was the start of a new cycle (Jia-Zi, 0)
        base_year = 1984
        diff = dt.year - base_year
        
        # If before LiChun (315 deg), it belongs to the previous year conceptually
        # Note: 315 degrees is the exact astronomical definition of Start of Spring
        if solar_lon < 315 and dt.month <= 2: 
            # Case: Jan/Feb before Feb 4th
            diff -= 1
            
        # Handle wrap-around for negative differences
        return diff % 60

    def _get_month_index(self, year_stem_idx: int, solar_lon: float) -> int:
        """
        Determines the Month Pillar Index using 'Five Tigers Chasing Month'.
        
        Algorithm:
        1. Determine the Lunar Month Branch based on Solar Longitude.
           (e.g., 315-345 deg = Tiger/Yin).
        2. Calculate Month Stem based on Year Stem.
           Formula: (YearStem % 5) * 2 + 2 + (MonthBranchOffset)
        """
        # Map Solar Longitude to Month Branch (Yin=2, Mao=3, ..., Chou=1)
        # LiChun (315) -> Yin (2). 
        # (SolarLon - 315) / 30 gives the offset from Tiger.
        # We handle the circular degree wrap-around (360 -> 0)
        
        effective_lon = solar_lon if solar_lon >= 315 else solar_lon + 360
        branch_offset_from_tiger = int((effective_lon - 315) / 30)
        
        # The Branch Index for the month (Tiger is index 2)
        month_branch_idx = (2 + branch_offset_from_tiger) % 12
        
        # Calculate Stem using "Five Tigers" formula
        # Base stem for Tiger month depends on Year Stem
        base_stem_idx = (year_stem_idx % 5) * 2 + 2
        
        # Current month stem
        month_stem_idx = (base_stem_idx + branch_offset_from_tiger) % 10
        
        # Combine into Base-60 index (Stem-Branch) via closed-form CRT lookup.
        return CyclicVariable.from_stem_branch(
            month_stem_idx, month_branch_idx
        ).index

    def _get_day_index(self, solar_dt: datetime) -> int:
        """
        Calculates Day Pillar based on mathematical offset from epoch.
        Independent of astronomical position, purely continuous count.
        """
        # Strip time for pure date math
        current_date = solar_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        # Handle timezone naive/aware diff
        ref_date = self.REF_DATE.replace(tzinfo=current_date.tzinfo)
        
        delta = current_date - ref_date
        days_passed = delta.days
        return (self.REF_DAY_IDX + days_passed) % 60


    def _get_hour_index(self, day_stem_idx: int, hour_of_day: int) -> int:
        """
        Calculates Hour Pillar using 'Five Rats Chasing Hour'.

        Logic:
        1. Branch is determined by 2-hour blocks (Zi = 23:00-01:00).
        2. Stem is determined by Day Stem.
        """
        # 1. Determine Branch (0 = Zi/Rat = 23:00-01:00)
        # (Hour + 1) // 2 handles the wrap around (23+1)//2 = 12 -> 0
        hour_branch_idx = ((hour_of_day + 1) // 2) % 12

        # 2. Determine Stem using "Five Rats" formula
        # Formula: (DayStem % 5) * 2 + HourBranch
        hour_stem_idx = ((day_stem_idx % 5) * 2 + hour_branch_idx) % 10

        # 3. Resolve the Z_60 index via closed-form CRT lookup.
        return CyclicVariable.from_stem_branch(
            hour_stem_idx, hour_branch_idx
        ).index

    def get_coordinates(self, dt: datetime, longitude: float = 0.0) -> Dict[str, Any]:
            """
            Executes the conversion pipeline.
        
            :param dt: Input datetime (UTC).
            :param longitude: Observer's longitude for Solar Time correction.
            :raises ValueError: If longitude is outside [-180, 180] degrees.
            """
            if not -180.0 <= longitude <= 180.0:
                raise ValueError(
                    f"longitude must be within [-180, 180], got {longitude}"
                )
            # 1. Physics Layer: Adjust for True Solar Time (Critical for Hour Boundary)
            # Solar longitude is geocentric (location-independent), so it is always
            # computed exactly. The precise_mode flag only toggles the EoT/longitude
            # correction applied to the clock time itself (which drives Day/Hour).
            solar_lambda = calculate_solar_longitude(dt)
            if self.precise_mode:
                solar_dt = get_true_solar_time(dt, longitude)
            else:
                solar_dt = dt

            # 2. Mathematical Layer: Calculate Indices
            # A. Day (Base for Hour)
            day_idx = self._get_day_index(solar_dt)
            day_pillar = CyclicVariable(day_idx)

            # B. Year (Base for Month)
            year_idx = self._get_year_index(solar_dt, solar_lambda)
            year_pillar = CyclicVariable(year_idx)

            # C. Month (Derived from Year + Solar Term)
            month_idx = self._get_month_index(year_pillar.stem_index, solar_lambda)
            month_pillar = CyclicVariable(month_idx)

            # D. Hour (Derived from Day + Solar Time)
            hour_idx = self._get_hour_index(day_pillar.stem_index, solar_dt.hour)
            hour_pillar = CyclicVariable(hour_idx)
        
            return {
                "metadata": {
                    "gregorian_utc": dt.isoformat(),
                    "true_solar_time": solar_dt.isoformat(),
                    "solar_longitude_deg": round(solar_lambda, 4),
                    "longitude": longitude
                },
                "coordinates": {
                    "year": year_pillar.to_json(),
                    "month": month_pillar.to_json(),
                    "day": day_pillar.to_json(),
                    "hour": hour_pillar.to_json()
                }
            }
