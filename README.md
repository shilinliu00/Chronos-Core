# Chronos-Core: High-Precision Temporal Feature Extraction Engine

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![Coverage](https://img.shields.io/badge/coverage-99%25-success)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

A high-performance Python library that converts linear Gregorian timestamps (UTC) into 4-dimensional cyclic coordinates (Base-60) using strict astronomical physics. Built for feature engineering in non-linear periodic time-series modeling.

---

## 🛑 The Problem: Why not just use `datetime`?

Standard `datetime` libraries assume a linear progression of time and rely on administrative approximations (e.g., Jan 1st boundaries, 28/30/31-day months, leap years). However, natural phenomena, human behavioral cycles, and certain financial market rhythms (like agricultural futures or seasonal macro-trends) do not adhere to administrative calendars. They adhere to **solar and orbital mechanics**.

**Chronos-Core** solves this by bridging astronomical ephemeris algorithms with abstract algebra, mapping raw UTC timestamps into a continuous, physics-corrected cyclic group ($\mathbb{Z}_{60}$).

---

## 🚀 Core Architecture & Engineering Highlights

### 1. Astronomical Physics Kernel
Chronos-Core calculates absolute Earth-Sun orbital mechanics to define strict temporal boundaries:
* **Equation of Time (EoT):** Corrects the discrepancy between Mean Solar Time (clock) and Apparent Solar Time (sundial) caused by Earth's orbital eccentricity. Essential for sub-hour precision during temporal boundary transitions.
* **Solar Ecliptic Longitude ($\lambda$):** Computes exact solar positioning relative to the J2000.0 epoch. The annual cycle strictly resets at $\lambda = 315^\circ$ (Vernal Equinox indicator), dynamically resolving the "Year Boundary" edge cases.

### 2. $\mathbb{Z}_{60}$ Modular Arithmetic Engine
Temporal coordinates are modeled within a finite cyclic group $\mathbb{Z}_{60}$.
* **Memory Optimized:** Core objects utilize Python's `__slots__` to eliminate dictionary overhead, enabling the generation of millions of temporal data points with a minimal RAM footprint.
* **O(1) Pattern Matching:** Relationships between time points are computed via modular arithmetic rather than heavy lookup tables. For example, a 180-degree phase shift (Clash) is evaluated as:
  $$(a - b) \pmod{12} = 6$$
* **Hashable States:** Objects implement `__hash__` and `__eq__`, allowing temporal states to be directly used as keys in Hash Maps for high-speed frequency counting.

---

## 📂 Module Architecture

The library is designed with strict Separation of Concerns (SoC):

| Module | Description | Design Pattern / Focus |
| :--- | :--- | :--- |
| `astronomy.py` | Physics engine. Calculates EoT and solar longitude $\lambda$. | Pure functions, stateless scientific computing. |
| `cyclic_math.py` | Mathematical kernel. Defines the `CyclicVariable` class. | Memory optimization (`__slots__`), Operator Overloading. |
| `converter.py` | The main integration layer. Maps physics to cyclic vectors. | Factory Pattern, Dependency Injection ready. |

---

## 📦 Installation

```bash
git clone https://github.com/shilinliu00/Chronos-Core.git
cd Chronos-Core
pip install -e .
```

Requires Python 3.9+. No runtime dependencies.

## ⚡ Quick Start

```python
from datetime import datetime, timezone
from chronos.converter import TemporalCoordinateEngine
from chronos.cyclic_math import CyclicVariable

# 1. Initialize engine with strict astronomical physics corrections
engine = TemporalCoordinateEngine(use_astronomy_correction=True)

# 2. Input: UTC time and observer longitude (e.g. Wall Street, NYC)
event_time = datetime(2024, 2, 4, 14, 30, tzinfo=timezone.utc)
nyc_longitude = -74.0060

# 3. Extract 4-dimensional cyclic coordinates
result = engine.get_coordinates(event_time, longitude=nyc_longitude)

print(result["metadata"]["solar_longitude_deg"])          # 315.26...
print(result["coordinates"]["day"]["label_cn"])           # 戊戌
print(result["coordinates"]["hour"]["stem"])              # Xin

# 4. O(1) relational computation on the cycle
day = CyclicVariable(result["coordinates"]["day"]["index"])
if day.is_clashing(CyclicVariable(4)):
    print("Phase shift (clash) detected")
```

See `examples/quick_start.py` for the full runnable example.

### `use_astronomy_correction`

- `True` (default): input UTC is converted to true solar time (longitude
  offset + Equation of Time) before deriving Day/Hour pillars. Year/Month
  pillars always use the exact solar longitude, which is
  location-independent.
- `False`: pillars follow the UTC clock directly (no EoT correction).
  Useful for testing and for hand-verifiable expectations.

## 🧪 Testing

```bash
pip install -r requirements.txt
PYTHONPATH=src pytest tests/ -q
```

49 tests, 99% coverage. Day-pillar anchors are cross-checked against
published perpetual calendars (万年历): `2024-01-01 = 甲子日`; the solar
longitude kernel is validated against the true moments of the 2024 solar
terms (max error 0.006°, ≈ 25 seconds of time); Equation-of-Time extrema
match the known February minimum (≈ −14 min) and November maximum
(≈ +16 min).

## ⚠️ Known Limitations

- **Solar-term boundary precision.** The simplified VSOP87 longitude is
  accurate to ~0.006°, so a Year/Month pillar can flip within roughly
  ±1 minute of the true solar-term moment. Expectations near boundaries
  (e.g. the exact minute of 立春) should allow for this.
- **Late Zi hour convention.** 23:00–24:00 is treated as Zi hour of the
  *current* day. Some BaZi schools roll it into the next day; this engine
  deliberately does not.
- **Equation of Time** uses the Smart (1977) approximation (±0.5 min),
  adequate for pillar boundaries but not for arc-second work.

## 📄 License

MIT
