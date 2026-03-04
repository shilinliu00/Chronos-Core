from chronos.converter import TemporalCoordinateEngine
from datetime import datetime, timezone

# 1. Initialize engine with strict astronomical physics corrections
engine = TemporalCoordinateEngine(use_astronomy_correction=True)

# 2. Input: UTC time and Observer Longitude (e.g., Wall Street, NYC)
event_time = datetime(2024, 2, 4, 14, 30, tzinfo=timezone.utc) 
nyc_longitude = -74.0060

# 3. Extract 4-Dimensional Cyclic Coordinates
result = engine.get_coordinates(event_time, longitude=nyc_longitude)

print(f"Solar Longitude: {result['metadata']['solar_longitude_deg']}°")
print(f"True Solar Time: {result['metadata']['true_solar_time']}")
print(f"Base-60 Day Coordinate: {result['coordinates']['day']['stem']}-{result['coordinates']['day']['branch']}")

# 4. O(1) Relational Computation Example
from chronos.cyclic_math import CyclicVariable
day_var = CyclicVariable(result['coordinates']['day']['index'])
target_var = CyclicVariable(4) # Arbitrary point in the cyclic group

if day_var.is_clashing(target_var):
    print("Phase Shift (Clash) Detected!")
