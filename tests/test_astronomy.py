"""Tests for the astronomical physics kernel (astronomy.py)."""
from datetime import datetime, timedelta, timezone

import pytest

from chronos.astronomy import (
    calculate_equation_of_time,
    calculate_solar_longitude,
    get_true_solar_time,
    _to_utc,
)


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


class TestSolarLongitude:
    # True moments of the 2024 solar terms; the simplified VSOP87-based
    # formula should land within half a degree (~2 days is way too coarse,
    # we expect arc-minute level agreement).
    def test_at_known_solar_terms(self):
        cases = [
            (utc(2024, 2, 4, 8, 27), 315),    # LiChun
            (utc(2024, 3, 20, 3, 6), 0),      # Vernal equinox
            (utc(2024, 6, 20, 20, 51), 90),   # Summer solstice
            (utc(2024, 9, 22, 12, 44), 180),  # Autumnal equinox
            (utc(2024, 12, 21, 9, 20), 270),  # Winter solstice
        ]
        for dt, expected in cases:
            lam = calculate_solar_longitude(dt)
            err = min(abs(lam - expected), 360 - abs(lam - expected))
            assert err < 0.5, (dt, lam, expected)

    def test_output_range(self):
        lam = calculate_solar_longitude(utc(2024, 7, 4, 12, 0))
        assert 0.0 <= lam < 360.0

    def test_monotonic_increase_over_a_day(self):
        a = calculate_solar_longitude(utc(2024, 6, 1, 0, 0))
        b = calculate_solar_longitude(utc(2024, 6, 2, 0, 0))
        assert 0.9 < (b - a) < 1.1  # ~0.986 deg/day


class TestEquationOfTime:
    def test_known_extrema(self):
        # Mid-February minimum ~ -14.2 min, early-November maximum ~ +16.4 min.
        assert calculate_equation_of_time(32) == pytest.approx(-13.7, abs=1.0)
        assert calculate_equation_of_time(306) == pytest.approx(16.4, abs=1.0)

    def test_zero_crossing(self):
        # Mid-April the sundial and the clock agree.
        assert abs(calculate_equation_of_time(105)) < 1.0

    def test_bounded_all_year(self):
        for doy in range(1, 367):
            assert -17.0 < calculate_equation_of_time(doy) < 17.0

    def test_out_of_range_day_rejected(self):
        for bad in (0, -3, 367, 400):
            with pytest.raises(ValueError):
                calculate_equation_of_time(bad)

    def test_year_endpoints_accepted(self):
        assert calculate_equation_of_time(1) == pytest.approx(-3.7, abs=1.0)
        assert calculate_equation_of_time(366) == pytest.approx(-3.7, abs=1.0)


class TestTrueSolarTime:
    def test_greenwich_gets_eot_only(self):
        dt = utc(2024, 1, 1, 12, 0)
        solar = get_true_solar_time(dt, 0.0)
        expected = dt.replace(tzinfo=None) + timedelta(
            minutes=calculate_equation_of_time(1)
        )
        assert solar == expected

    def test_longitude_offset_is_4min_per_degree(self):
        dt = utc(2024, 6, 1, 12, 0)
        east = get_true_solar_time(dt, 15.0)
        west = get_true_solar_time(dt, -15.0)
        assert (east - west) == timedelta(minutes=120)

    def test_result_is_naive_solar_time(self):
        solar = get_true_solar_time(utc(2024, 6, 1, 12, 0), 120.0)
        assert solar.tzinfo is None
        # 120E -> +8h plus a few minutes of EoT: mid-morning becomes evening.
        assert solar.hour == 20

    def test_naive_input_assumed_utc(self):
        naive = datetime(2024, 6, 1, 12, 0)
        assert get_true_solar_time(naive, 0.0) == get_true_solar_time(
            utc(2024, 6, 1, 12, 0), 0.0
        )


class TestToUtc:
    def test_naive_assumed_utc(self):
        out = _to_utc(datetime(2024, 1, 1, 0, 0))
        assert out.tzinfo is timezone.utc

    def test_aware_converted(self):
        from datetime import timezone as tz

        beijing = timezone(timedelta(hours=8))
        out = _to_utc(datetime(2024, 1, 1, 8, 0, tzinfo=beijing))
        assert out == datetime(2024, 1, 1, 0, 0, tzinfo=tz.utc)
