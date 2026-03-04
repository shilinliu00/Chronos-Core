# Chronos-Core: High-Precision Temporal Feature Extraction Engine

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![Coverage](https://img.shields.io/badge/coverage-95%25-success)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

**TL;DR:** A high-performance Python library that converts linear Gregorian timestamps (UTC) into 4-dimensional cyclic coordinates (Base-60) using strict astronomical physics. Built for feature engineering in non-linear periodic time-series modeling.

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
git clone [https://github.com/shilinliu00/chronos-core.git](https://github.com/shilinliu00/chronos-core.git)
cd chronos-core
pip install -e .
