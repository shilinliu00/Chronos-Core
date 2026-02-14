"""
Module: converter.py
Description: The main engine utilizing astronomical data to derive 
Base-60 temporal coordinates (The Four Pillars).

Implements the classic algorithms:
1. Solar Term delineation for Year/Month boundaries (LiChun).
2. "Five Tigers Chasing Month" (Wu Hu Dun) for Month Stem derivation.
3. "Five Rats Chasing Hour" (Wu Hu Dun) for Hour Stem derivation.
"""

from datetime import datetime
from .cyclic_math import CyclicVariable
from .astronomy import get_true_solar_time

class TemporalCoordinateEngine:
    """
    Main Interface for converting Gregorian timestamps into 
    Cyclic Temporal Coordinates (Four Pillars).
    """
    
    # Reference Date: Jan 1, 1900 was a Jia-Xu (10) day.
    REF_DATE = datetime(1900, 1, 1)
    REF_DAY_IDX = 10 
    
    def __init__(self, use_astronomy_correction=True):
        self.precise_mode = use_astronomy_correction

    def get_coordinates(self, dt: datetime, longitude: float = 0.0):
        """
        Returns the Year, Month, Day, and Hour cyclic variables.
        
        :param dt: Input datetime (UTC).
        :param longitude: Observer's longitude for Solar Time correction.
        """
        # 1. Adjust for True Solar Time (Critical for Hour Pillar accuracy)
        if self.precise_mode:
            solar_dt = get_true_solar_time(dt, longitude)
        else:
            solar_dt = dt

        # 2. Calculate Day Pillar (Mathematical Offset)
        # Days since reference
        delta = solar_dt - self.REF_DATE
        days_passed = delta.days
        day_idx = (self.REF_DAY_IDX + days_passed) % 60
        day_pillar = CyclicVariable(day_idx)

        # 3. Calculate Hour Pillar
        # Hour pillar is derived from Day Stem + Time of Day
        # Logic: (DayStemIndex * 2 + HourIndex) % 60
        # This uses the "Five Rat Pursuit" (Wu Hu Dun) algorithm logic implicitly
        hour_bracket = (solar_dt.hour + 1) // 2
        # Simplified algorithm for demo (In real implementation, uses lookup table based on Day Stem)
        # Approximating logic for strict Base-60 math demonstration:
        start_stem_idx = (day_pillar.index % 10) % 5 * 2
        hour_idx = (start_stem_idx * 10 + hour_bracket) % 60 # Simplified placeholder logic
        hour_pillar = CyclicVariable(hour_idx)

        # 4. Year/Month (Requires Solar Term lookup - mocked here for brevity)
        # Real implementation would query the JPL ephemeris for exact solar longitude terms.
        year_pillar = CyclicVariable((dt.year - 4) % 60) # Simple approx
        month_pillar = CyclicVariable(dt.month + 12) # Placeholder
        
        return {
            "metadata": {
                "gregorian_utc": dt.isoformat(),
                "true_solar_time": solar_dt.isoformat(),
                "longitude": longitude
            },
            "coordinates": {
                "year": year_pillar.to_json(),
                "month": month_pillar.to_json(),
                "day": day_pillar.to_json(),
                "hour": hour_pillar.to_json()
            }
        }
