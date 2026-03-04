# Chronos-Core: High-Precision Temporal Feature Extraction Engine

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![Coverage](https://img.shields.io/badge/coverage-95%25-success)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

**TL;DR:** A high-performance Python library that converts linear Gregorian timestamps (UTC) into 4-dimensional cyclic coordinates (Base-60) using strict astronomical physics. Built for feature engineering in non-linear periodic time-series modeling.

---

## 🚀 Why Chronos-Core?

Standard `datetime` libraries assume a linear progression of time based on approximations (e.g., Jan 1st boundaries, leap years). **Chronos-Core** calculates absolute Earth-Sun orbital mechanics to define strict temporal boundaries, making it ideal for detecting non-linear periodic patterns in historical and financial data.

### 1. Astronomical Physics Kernel
* **Equation of Time (EoT):** Corrects the discrepancy between Mean Solar Time (clock) and Apparent Solar Time (sundial) caused by Earth's orbital eccentricity, achieving sub-hour precision for boundary transitions.
* **Solar Ecliptic Longitude ($\lambda$):** Computes exact solar positioning relative to the J2000.0 epoch. The annual cycle strictly resets at $\lambda = 315^\circ$ (Vernal Equinox indicator), eliminating Gregorian calendar inaccuracies.

### 2. $\mathbb{Z}_{60}$ Modular Arithmetic Engine
* **Memory Optimized:** Core cyclic objects utilize Python's `__slots__` to eliminate dictionary overhead, enabling the generation of millions of temporal data points with a minimal RAM footprint.
* **O(1) Pattern Matching:** Relationships between time points are computed via modular arithmetic rather than heavy lookup tables. For example, a 180-degree phase shift (Clash) is evaluated as:
  $$(a - b) \pmod{12} = 6$$

---

## 📦 Installation

```bash
git clone [https://github.com/shilinliu00/chronos-core.git](https://github.com/shilinliu00/chronos-core.git)
cd chronos-core
pip install -e .
