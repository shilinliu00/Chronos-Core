"""Tests for the astronomical physics kernel (astronomy.py)."""
from datetime import datetime, timedelta, timezone

import pytest

from chronos.astronomy import (
    calculate_equation_of_time,
    calculate_solar_longitude,
    calculate_solar_declination,
    get_true_solar_time,
    solar_term_for_longitude,
    solar_term_type,
    next_solar_term,
    next_solar_terms,
    previous_solar_term,
    previous_solar_terms,
    SOLAR_TERMS,
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

    def test_naive_and_aware_inputs_agree(self):
        # 2024-06-01 20:00 in Beijing (+08:00) is 12:00 UTC; the pure
        # astronomy functions must not care which spelling was passed.
        beijing = timezone(timedelta(hours=8))
        aware = datetime(2024, 6, 1, 20, 0, tzinfo=beijing)
        naive = datetime(2024, 6, 1, 12, 0)
        assert calculate_solar_longitude(aware) == pytest.approx(
            calculate_solar_longitude(naive)
        )
        assert calculate_solar_declination(aware) == pytest.approx(
            calculate_solar_declination(naive)
        )


class TestSolarDeclination:
    def test_solstice_extrema(self):
        # Sun at its highest/lowest celestial latitude on the solstices.
        assert calculate_solar_declination(utc(2024, 6, 20, 20, 51)) == pytest.approx(
            23.4393, abs=0.1
        )
        assert calculate_solar_declination(utc(2024, 12, 21, 9, 20)) == pytest.approx(
            -23.4393, abs=0.1
        )

    def test_equinox_crosses_equator(self):
        # On the equinox the Sun crosses the celestial equator: δ ≈ 0.
        assert calculate_solar_declination(utc(2024, 3, 20, 3, 6)) == pytest.approx(
            0.0, abs=0.1
        )
        assert calculate_solar_declination(utc(2024, 9, 22, 12, 44)) == pytest.approx(
            0.0, abs=0.1
        )

    def test_bounded_all_year(self):
        for month in range(1, 13):
            delta = calculate_solar_declination(utc(2024, month, 15, 12, 0))
            assert -23.45 <= delta <= 23.45

    def test_sign_changes_across_both_equinoxes(self):
        # Declination is negative before the vernal equinox and
        # positive just after it; the autumnal equinox flips it back.
        assert calculate_solar_declination(utc(2024, 3, 19, 12, 0)) < 0
        assert calculate_solar_declination(utc(2024, 3, 21, 12, 0)) > 0
        assert calculate_solar_declination(utc(2024, 9, 21, 12, 0)) > 0
        assert calculate_solar_declination(utc(2024, 9, 23, 12, 0)) < 0

    def test_monotonic_increase_over_a_day(self):
        a = calculate_solar_longitude(utc(2024, 6, 1, 0, 0))
        b = calculate_solar_longitude(utc(2024, 6, 2, 0, 0))
        assert 0.9 < (b - a) < 1.1  # ~0.986 deg/day

    def test_continuous_across_longitude_wrap(self):
        # Longitude wraps 360 -> 0 at the vernal equinox, inside the
        # Mao month, so the raw value drops; unwrapped, it must keep
        # increasing by ~0.986 deg/day with no jump, or term lookups
        # near the equinox would see a spurious boundary.
        start = utc(2024, 3, 18, 0, 0)
        prev = calculate_solar_longitude(start)
        for day in range(1, 6):
            raw = calculate_solar_longitude(start + timedelta(days=day))
            unwrapped = raw + 360.0 if raw < prev else raw
            assert 0.9 < (unwrapped - prev) < 1.1, day
            prev = raw

    def test_microsecond_inputs_give_distinct_longitudes(self):
        # The kernel claims microsecond precision via total_seconds();
        # shifting by one microsecond must move the longitude forward.
        t = utc(2024, 6, 1, 12, 0, 0, 123456)
        a = calculate_solar_longitude(t)
        b = calculate_solar_longitude(t + timedelta(microseconds=1))
        assert b > a


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

    def test_out_of_range_longitude_rejected(self):
        dt = utc(2024, 6, 1, 12, 0)
        for bad in (180.1, -180.1, 360.0):
            with pytest.raises(ValueError):
                get_true_solar_time(dt, bad)

    def test_longitude_endpoints_shift_exactly_12_hours(self):
        # +/-180 degrees is the farthest a location can be from Greenwich.
        dt = utc(2024, 6, 1, 12, 0)
        east = get_true_solar_time(dt, 180.0)
        west = get_true_solar_time(dt, -180.0)
        greenwich = get_true_solar_time(dt, 0.0)
        assert (east - greenwich) == timedelta(minutes=720)
        assert (greenwich - west) == timedelta(minutes=720)


class TestSolarTerms:
    def test_table_has_twenty_four_entries(self):
        assert len(SOLAR_TERMS) == 24
        assert SOLAR_TERMS[0] == ("LiChun", "立春")
        assert SOLAR_TERMS[3] == ("ChunFen", "春分")
        assert SOLAR_TERMS[23] == ("DaHan", "大寒")

    def test_each_term_begins_at_315_plus_15k(self):
        # Term k owns the 15 degree segment starting at 315 + 15k.
        for k, expected in enumerate(SOLAR_TERMS):
            lon = (315.0 + 15.0 * k) % 360.0
            assert solar_term_for_longitude(lon) == expected

    def test_term_holds_until_next_boundary(self):
        # A hair below 330 it is still LiChun; at 330 it flips to YuShui.
        assert solar_term_for_longitude(329.999) == SOLAR_TERMS[0]
        assert solar_term_for_longitude(330.0) == SOLAR_TERMS[1]
        # Wrap around the 360/0 discontinuity: just below 315 is DaHan.
        assert solar_term_for_longitude(314.999) == SOLAR_TERMS[23]

    def test_matches_known_2024_solar_terms(self):
        # Dates sit a few days inside each term, clear of the ~0.006 deg
        # model error at the exact boundary moments.
        cases = [
            (utc(2024, 2, 9, 12, 0), "LiChun"),
            (utc(2024, 3, 25, 12, 0), "ChunFen"),
            (utc(2024, 6, 25, 12, 0), "XiaZhi"),
            (utc(2024, 9, 27, 12, 0), "QiuFen"),
            (utc(2024, 12, 26, 12, 0), "DongZhi"),
        ]
        for dt, expected_en in cases:
            en, _ = solar_term_for_longitude(calculate_solar_longitude(dt))
            assert en == expected_en, (dt, en)

    def test_out_of_range_longitude_rejected(self):
        for bad in (-0.1, 360.0, 400.0):
            with pytest.raises(ValueError):
                solar_term_for_longitude(bad)

    def test_term_type_alternates_jie_qi(self):
        # The table starts at LiChun (a Jie) and alternates: even indices
        # are Jie terms (month pillar boundaries), odd ones are Qi terms.
        for k in range(24):
            lon = (315.0 + 15.0 * k) % 360.0
            assert solar_term_type(lon) == ("Jie" if k % 2 == 0 else "Qi")

    def test_term_type_holds_through_each_segment(self):
        # Boundary tests pin the edges; midpoints pin the interior, so a
        # term's type cannot flip partway through its 15 degree segment.
        for k in range(24):
            lon = (315.0 + 15.0 * k + 7.5) % 360.0
            assert solar_term_type(lon) == ("Jie" if k % 2 == 0 else "Qi")

    def test_term_type_out_of_range_rejected(self):
        for bad in (-0.1, 360.0, 400.0):
            with pytest.raises(ValueError):
                solar_term_type(bad)


class TestNextSolarTerm:
    def test_matches_known_2024_term_moments(self):
        # True moments of five 2024 terms; the kernel's ~0.006 deg
        # error is about 25 seconds of time, so 10 minutes is generous.
        cases = [
            (utc(2024, 2, 1, 12, 0), utc(2024, 2, 4, 8, 27), "LiChun", "立春"),
            (utc(2024, 3, 17, 12, 0), utc(2024, 3, 20, 3, 6), "ChunFen", "春分"),
            (utc(2024, 6, 17, 12, 0), utc(2024, 6, 20, 20, 51), "XiaZhi", "夏至"),
            (utc(2024, 9, 19, 12, 0), utc(2024, 9, 22, 12, 44), "QiuFen", "秋分"),
            (utc(2024, 12, 18, 12, 0), utc(2024, 12, 21, 9, 20), "DongZhi", "冬至"),
        ]
        for start, expected_moment, expected_en, expected_cn in cases:
            moment, en, cn = next_solar_term(start)
            assert en == expected_en, (start, en)
            assert cn == expected_cn
            assert abs((moment - expected_moment).total_seconds()) < 600, (
                start, moment, expected_moment,
            )

    def test_result_is_aware_utc(self):
        moment, _, _ = next_solar_term(utc(2024, 6, 1, 12, 0))
        assert moment.tzinfo is timezone.utc
        # Naive input is assumed UTC and must give the same moment.
        naive_moment, _, _ = next_solar_term(datetime(2024, 6, 1, 12, 0))
        assert naive_moment == moment

    def test_moment_on_a_boundary_returns_following_term(self):
        # Starting exactly at the true LiChun moment must skip ahead
        # to YuShui (~Feb 19), not return LiChun again.
        moment, en, _ = next_solar_term(utc(2024, 2, 4, 8, 27))
        assert en == "YuShui"
        assert moment > utc(2024, 2, 4, 8, 27)

    def test_successive_calls_walk_the_term_table(self):
        # Chaining next_solar_term must step through the table in
        # order, including the wrap from DaHan back to LiChun.
        moment, en, _ = next_solar_term(utc(2024, 1, 15, 12, 0))
        assert en == "DaHan"
        moment, en, _ = next_solar_term(moment)
        assert en == "LiChun"
        moment, en, _ = next_solar_term(moment)
        assert en == "YuShui"


class TestNextSolarTerms:
    def test_lists_terms_in_order_with_known_moments(self):
        # Same pinned 2024 moments as the single term tests.
        terms = next_solar_terms(utc(2024, 2, 1, 12, 0), 3)
        assert [en for _, en, _ in terms] == ["LiChun", "YuShui", "JingZhe"]
        assert abs((terms[0][0] - utc(2024, 2, 4, 8, 27)).total_seconds()) < 600
        assert terms[0][0] < terms[1][0] < terms[2][0]

    def test_wraps_from_dahan_to_lichun(self):
        terms = next_solar_terms(utc(2024, 12, 18, 12, 0), 3)
        assert [en for _, en, _ in terms] == ["DongZhi", "XiaoHan", "DaHan"]
        terms = next_solar_terms(utc(2024, 12, 18, 12, 0), 4)
        assert terms[3][1] == "LiChun"

    def test_count_one_matches_single_call(self):
        start = utc(2024, 6, 1, 12, 0)
        assert next_solar_terms(start) == [next_solar_term(start)]

    def test_matches_repeated_single_calls(self):
        start = utc(2024, 6, 1, 12, 0)
        cursor = start
        expected = []
        for _ in range(5):
            moment, en, cn = next_solar_term(cursor)
            expected.append((moment, en, cn))
            cursor = moment
        assert next_solar_terms(start, 5) == expected

    def test_naive_input_matches_aware(self):
        terms = next_solar_terms(utc(2024, 6, 1, 12, 0), 2)
        naive = next_solar_terms(datetime(2024, 6, 1, 12, 0), 2)
        assert naive == terms
        assert all(moment.tzinfo is timezone.utc for moment, _, _ in terms)

    def test_invalid_count_rejected(self):
        with pytest.raises(ValueError):
            next_solar_terms(utc(2024, 6, 1, 12, 0), 0)
        with pytest.raises(ValueError):
            next_solar_terms(utc(2024, 6, 1, 12, 0), -2)
        with pytest.raises(TypeError):
            next_solar_terms(utc(2024, 6, 1, 12, 0), "3")


class TestPreviousSolarTerm:
    def test_matches_known_2024_term_moments(self):
        # Same true moments as the next term tests, approached from
        # just after each boundary; 10 minutes is generous.
        cases = [
            (utc(2024, 2, 5, 12, 0), utc(2024, 2, 4, 8, 27), "LiChun", "立春"),
            (utc(2024, 3, 21, 12, 0), utc(2024, 3, 20, 3, 6), "ChunFen", "春分"),
            (utc(2024, 6, 21, 12, 0), utc(2024, 6, 20, 20, 51), "XiaZhi", "夏至"),
            (utc(2024, 9, 23, 12, 0), utc(2024, 9, 22, 12, 44), "QiuFen", "秋分"),
            (utc(2024, 12, 22, 12, 0), utc(2024, 12, 21, 9, 20), "DongZhi", "冬至"),
        ]
        for start, expected_moment, expected_en, expected_cn in cases:
            moment, en, cn = previous_solar_term(start)
            assert en == expected_en, (start, en)
            assert cn == expected_cn
            assert abs((moment - expected_moment).total_seconds()) < 600, (
                start, moment, expected_moment,
            )

    def test_result_is_aware_utc(self):
        moment, _, _ = previous_solar_term(utc(2024, 6, 1, 12, 0))
        assert moment.tzinfo is timezone.utc
        # Naive input is assumed UTC and must give the same moment.
        naive_moment, _, _ = previous_solar_term(datetime(2024, 6, 1, 12, 0))
        assert naive_moment == moment

    def test_moment_on_a_boundary_returns_that_term(self):
        # Starting exactly at the true LiChun moment must return
        # LiChun itself, the term in force, not XiaoHan before it.
        moment, en, _ = previous_solar_term(utc(2024, 2, 4, 8, 27))
        assert en == "LiChun"
        assert abs((moment - utc(2024, 2, 4, 8, 27)).total_seconds()) < 600

    def test_name_matches_term_in_force(self):
        # The returned term must always be the one
        # solar_term_for_longitude names at the starting moment.
        for start in (
            utc(2024, 1, 15, 12, 0), utc(2024, 4, 10, 6, 0),
            utc(2024, 7, 30, 18, 0), utc(2024, 11, 5, 0, 0),
        ):
            _, en, cn = previous_solar_term(start)
            assert (en, cn) == solar_term_for_longitude(
                calculate_solar_longitude(start)
            )

    def test_successive_calls_walk_the_term_table_backward(self):
        # Chaining previous_solar_term must step through the table
        # in reverse, including the wrap from LiChun back to DaHan.
        # Each call returns a moment just before the boundary it
        # names, so the next call steps to the term before it.
        moment, en, _ = previous_solar_term(utc(2024, 1, 15, 12, 0))
        assert en == "XiaoHan"
        moment, en, _ = previous_solar_term(moment)
        assert en == "DongZhi"
        moment, en, _ = previous_solar_term(moment)
        assert en == "DaXue"

    def test_round_trips_with_next_solar_term(self):
        # next of a previous boundary is that boundary itself, and
        # previous of a next boundary is that boundary itself.
        start = utc(2024, 6, 1, 12, 0)
        prev_moment, prev_en, _ = previous_solar_term(start)
        next_moment, next_en, _ = next_solar_term(start)
        assert prev_en == "XiaoMan"
        assert next_en == "MangZhong"
        forward = next_solar_term(prev_moment)[0]
        assert abs((forward - prev_moment).total_seconds()) < 120
        back_moment, back_en, _ = previous_solar_term(next_moment)
        assert back_en == next_en
        assert abs((back_moment - next_moment).total_seconds()) < 120


class TestPreviousSolarTerms:
    def test_lists_terms_in_reverse_order_with_known_moment(self):
        terms = previous_solar_terms(utc(2024, 2, 5, 12, 0), 3)
        assert [en for _, en, _ in terms] == ["LiChun", "DaHan", "XiaoHan"]
        assert abs((terms[0][0] - utc(2024, 2, 4, 8, 27)).total_seconds()) < 600
        assert terms[0][0] > terms[1][0] > terms[2][0]

    def test_wraps_from_lichun_to_dahan(self):
        terms = previous_solar_terms(utc(2024, 2, 5, 12, 0), 2)
        assert [en for _, en, _ in terms] == ["LiChun", "DaHan"]

    def test_count_one_matches_single_call(self):
        start = utc(2024, 6, 1, 12, 0)
        assert previous_solar_terms(start) == [previous_solar_term(start)]

    def test_matches_repeated_single_calls(self):
        start = utc(2024, 6, 1, 12, 0)
        cursor = start
        expected = []
        for _ in range(5):
            moment, en, cn = previous_solar_term(cursor)
            expected.append((moment, en, cn))
            cursor = moment - timedelta(seconds=1)
        assert previous_solar_terms(start, 5) == expected

    def test_naive_input_matches_aware(self):
        terms = previous_solar_terms(utc(2024, 6, 1, 12, 0), 2)
        naive = previous_solar_terms(datetime(2024, 6, 1, 12, 0), 2)
        assert naive == terms
        assert all(moment.tzinfo is timezone.utc for moment, _, _ in terms)

    def test_invalid_count_rejected(self):
        with pytest.raises(ValueError):
            previous_solar_terms(utc(2024, 6, 1, 12, 0), 0)
        with pytest.raises(ValueError):
            previous_solar_terms(utc(2024, 6, 1, 12, 0), -2)
        with pytest.raises(TypeError):
            previous_solar_terms(utc(2024, 6, 1, 12, 0), "2")


class TestToUtc:
    def test_naive_assumed_utc(self):
        out = _to_utc(datetime(2024, 1, 1, 0, 0))
        assert out.tzinfo is timezone.utc

    def test_aware_converted(self):
        from datetime import timezone as tz

        beijing = timezone(timedelta(hours=8))
        out = _to_utc(datetime(2024, 1, 1, 8, 0, tzinfo=beijing))
        assert out == datetime(2024, 1, 1, 0, 0, tzinfo=tz.utc)
