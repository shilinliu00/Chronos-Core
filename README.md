# Chronos-Core: High-Precision Temporal Coordinate Engine

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

**Chronos-Core** is a Python library designed for high-precision conversion between the Gregorian Calendar and the Sexagenary (Base-60) Cyclic Time System. 

Unlike standard datetime libraries, Chronos-Core integrates **astronomical corrections** (Equation of Time, True Solar Time) to map temporal data into a cyclic coordinate system commonly used in East Asian temporal pattern analysis.

## 🚀 Key Features

* **Astronomical Precision**: Implements the **Equation of Time (EoT)** to correct Mean Solar Time to **Local Apparent Solar Time**, ensuring sub-hour accuracy for temporal boundary delimitation.
* **Base-60 Cyclic Arithmetic**: A dedicated math kernel (`CyclicVariable`) for handling non-decimal, modulo-60 operations required by the Sexagenary cycle (Stem-Branch system).
* **Coordinate Normalization**: Converts linear time (Unix Timestamp) into a 4-dimensional cyclic vector (Year, Month, Day, Hour).
* **Extensible Architecture**: Designed to interface with NASA JPL's **DE421/VSOP87** ephemeris data for precise solar term (season) transitions.

## 🛠 Domain Reframing (Concepts)

This engine treats traditional temporal concepts as data engineering problems:

| Traditional Term | System Concept | Implementation |
| :--- | :--- | :--- |
| **BaZi (Eight Characters)** | `Temporal Coordinate Set` | A vector of 4 `CyclicVariable` objects. |
| **True Solar Time** | `Apparent Solar Time` | $T_{apparent} = T_{mean} + \Delta T_{geo} + E_{qt}$ |
| **Solar Terms (JieQi)** | `Solar Longitude Nodes` | Calculated points where solar longitude $\lambda = 15^\circ \times n$. |
| **GanZhi Cycle** | `Base-60 Modulo Arithmetic` | Custom Class `CyclicVariable(0..59)`. |

## 📦 Installation

```bash
git clone [https://github.com/your-username/chronos-core.git](https://github.com/your-username/chronos-core.git)
cd chronos-core
pip install -r requirements.txt
