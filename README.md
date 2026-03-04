# Chronos-Core: High-Precision Temporal Feature Extraction Engine

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![Coverage](https://img.shields.io/badge/coverage-95%25-success)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

**Chronos-Core** is a high-performance Python library designed for temporal feature extraction and complex periodic time-series modeling. 

It maps linear Gregorian timestamps (UTC) into a 4-dimensional cyclic coordinate system (the Sexagenary or Base-60 cycle). Unlike standard `datetime` libraries, Chronos-Core utilizes **astronomical physics algorithms** to achieve sub-hour precision, making it ideal for detecting non-linear periodic patterns in historical data.

## 🚀 Core Architecture & Engineering Highlights

### 1. Astronomical Physics Kernel
Standard calendars are approximations. Chronos-Core calculates absolute orbital positions to define strict temporal boundaries:
* **Equation of Time (EoT):** Corrects the discrepancy between Mean Solar Time and Apparent Solar Time caused by Earth's orbital eccentricity, critical for exact hour-boundary transitions.
* **Solar Ecliptic Longitude ($\lambda$):** Computes the exact solar position relative to the J2000.0 epoch. The annual cycle strictly resets at $\lambda = 315^\circ$ (Vernal Equinox indicator), eliminating the inaccuracies of the Gregorian Jan 1st boundary.

### 2. $\mathbb{Z}_{60}$ Modular Arithmetic Engine
Temporal coordinates are modeled within a finite cyclic group $\mathbb{Z}_{60}$.
* **Memory Optimization:** Core objects utilize Python's `__slots__` to eliminate dictionary overhead, enabling the generation of millions of temporal data points with a minimal RAM footprint.
* **O(1) Pattern Matching:** Relationships between time points are computed via modular arithmetic rather than heavy lookup tables. For example, a "Clash" (a 180-degree phase shift in the 12-base sub-cycle) is computed in O(1) time via: 
  $$(a - b) \pmod{12} = 6$$
* **Hashable States:** Objects implement `__hash__` and `__eq__`, allowing temporal states to be directly used as keys in Hash Maps for high-speed frequency counting.

### 3. Algorithmic Temporal Routing
Implements traditional temporal hash functions (historically known as the "Five Tigers" and "Five Rats" algorithms) to derive orthogonal coordinates:
* Resolves the Month vector by mapping the Year vector and Solar Longitude offset.
* Resolves the Hour vector by hashing the Day vector against the Local Apparent Solar Time.

## 📦 Installation

```bash
git clone [https://github.com/your-username/chronos-core.git](https://github.com/your-username/chronos-core.git)
cd chronos-core
pip install -r requirements.txt
