"""
Module: converter.py
Description: The main engine utilizing astronomical data to derive 
Base-60 temporal coordinates (The Four Pillars).

Implements the classic algorithms:
1. Solar Term delineation for Year/Month boundaries (LiChun).
2. "Five Tigers Chasing Month" (Wu Hu Dun) for Month Stem derivation.
3. "Five Rats Chasing Hour" (Wu Hu Dun) for Hour Stem derivation.
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
        
        # Combine into Base-60 index (Stem-Branch)
        # We need to find the index X where X%10==stem and X%12==branch
        # Optimized lookup or simple search in 60-cycle
        # Since stem/branch move together, index = (StemIndex - BranchIndex)/2 * 10 + Branch? 
        # Easier robust way: find matching pair in Z_60
        # (This is O(1) in concept, O(60) in brute implementation, but fast)
        for i in range(60):
            if i % 10 == month_stem_idx and i % 12 == month_branch_idx:
                return i
        return 0 # Should not reach here
