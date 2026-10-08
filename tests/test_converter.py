"""Tests for the BaZi pillar engine (converter.py).

Day-pillar anchors are cross-checked against published perpetual calendars
(万年历): 2024-01-01 = 甲子日. Year/month expectations follow the standard
rules: year changes at LiChun (立春), month branches at the solar terms,
"Five Tigers" (五虎遁) month stems and "Five Rats" (五鼠遁) hour stems.
"""
import json
from datetime import datetime, timezone

import pytest

from chronos.converter import TemporalCoordinateEngine


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def plain():
    # Astronomy time-correction off: pillars follow the UTC clock directly,
    # so expectations can be hand-computed.
    return TemporalCoordinateEngine(use_astronomy_correction=False)


@pytest.fixture()
def precise():
    return TemporalCoordinateEngine(use_astronomy_correction=True)


def labels(pillar):
    return pillar["stem"] + pillar["branch"]


class TestDayPillar:
    def test_anchor_2024_01_01_is_jia_zi(self, plain):
        idx = plain._get_day_index(utc(2024, 1, 1, 12, 0))
        assert idx == 0  # 甲子, verified against 万年历

    def test_advances_one_per_day(self, plain):
        idxs = [plain._get_day_index(utc(2024, 1, d, 12, 0)) for d in (1, 2, 10)]
        assert idxs == [0, 1, 9]  # 甲子, 乙丑, 癸酉

    def test_continuous_across_leap_day(self, plain):
        feb28 = plain._get_day_index(utc(2024, 2, 28, 12, 0))
        feb29 = plain._get_day_index(utc(2024, 2, 29, 12, 0))
        mar1 = plain._get_day_index(utc(2024, 3, 1, 12, 0))
        assert (feb29 - feb28) % 60 == 1
        assert (mar1 - feb29) % 60 == 1

    def test_1900_anchor_consistent(self, plain):
        # 1900-01-01 = 甲戌 (index 10); must agree with the 2024 anchor.
        assert plain._get_day_index(utc(1900, 1, 1)) == 10


class TestYearPillar:
    def test_before_lichun_stays_previous_year(self, plain):
        # 2024-02-03: LiChun not yet reached -> still 癸卯 (index 39).
        idx = plain._get_year_index(utc(2024, 2, 3, 12, 0), 300.0)
        assert idx == 39

    def test_after_lichun_new_year(self, plain):
        idx = plain._get_year_index(utc(2024, 2, 5, 12, 0), 316.0)
        assert idx == 40  # 甲辰

    def test_lichun_boundary_with_real_astronomy(self, precise):
        # True LiChun 2024: Feb 4 ~08:27 UTC. Margins avoid the ~25s model error.
        before = precise.get_coordinates(utc(2024, 2, 4, 7, 0), 0.0)
        after = precise.get_coordinates(utc(2024, 2, 4, 10, 0), 0.0)
        assert labels(before["coordinates"]["year"]) == "GuiMao"
        assert labels(after["coordinates"]["year"]) == "JiaChen"

    def test_december_belongs_to_current_year(self, plain):
        idx = plain._get_year_index(utc(2024, 12, 15, 12, 0), 255.0)
        assert idx == 40


class TestMonthPillar:
    def test_january_2024_is_jia_zi(self, plain):
        idx = plain._get_month_index(9, 280.0)  # Gui year stem, 小寒 longitude
        assert idx == 0  # 甲子

    def test_month_branch_follows_solar_terms(self, plain):
        # 2024-03-10: past 惊蛰 (345°) -> 卯月; 甲年 -> 丁卯 (index 3).
        idx = plain._get_month_index(0, 350.0)
        assert idx == 3

    def test_june_2024_is_geng_wu(self, plain):
        # 芒种后午月; 甲辰年五虎遁 -> 庚午 (index 6).
        idx = plain._get_month_index(0, 84.0)
        assert idx == 6

    def test_full_pipeline_month(self, plain):
        res = plain.get_coordinates(utc(2024, 3, 10, 12, 0), 0.0)
        assert labels(res["coordinates"]["month"]) == "DingMao"


class TestHourPillar:
    def test_branch_boundaries(self, plain):
        branches = {
            23: 0, 0: 0,      # Zi  (23:00-01:00)
            1: 1, 2: 1,       # Chou (01:00-03:00)
            3: 2,             # Yin  (03:00-05:00)
            10: 5,            # Si   (09:00-11:00)
            11: 6, 12: 6,     # Wu   (11:00-13:00)
            21: 11, 22: 11,   # Hai  (21:00-23:00)
        }
        for hour, expected_branch in branches.items():
            idx = plain._get_hour_index(0, hour)  # Jia day stem
            assert idx % 12 == expected_branch, hour

    def test_five_rats_stems(self, plain):
        # 甲己还加甲: Jia day + Zi hour -> 甲子 (index 0).
        assert plain._get_hour_index(0, 0) == 0
        # 乙庚丙作初: Yi day + Zi hour -> 丙子 (stem 2, branch 0 -> index 12).
        idx = plain._get_hour_index(1, 0)
        assert idx == 12
        assert (idx % 10, idx % 12) == (2, 0)

    def test_known_hour_2024_01_01_noon(self, plain):
        res = plain.get_coordinates(utc(2024, 1, 1, 12, 0), 0.0)
        assert labels(res["coordinates"]["hour"]) == "GengWu"  # 庚午, cf. 万年历

    def test_late_zi_stays_on_same_day(self, plain):
        # Engine convention: 23:00-24:00 is Zi hour of the *current* day
        # (some schools roll it to the next day; this engine does not).
        res = plain.get_coordinates(utc(2024, 1, 1, 23, 30), 0.0)
        assert labels(res["coordinates"]["day"]) == "JiaZi"
        assert res["coordinates"]["hour"]["branch"] == "Zi"


class TestPipeline:
    def test_full_chart_2024_01_01(self, plain):
        res = plain.get_coordinates(utc(2024, 1, 1, 12, 0), 0.0)
        coords = res["coordinates"]
        assert labels(coords["year"]) == "GuiMao"
        assert labels(coords["month"]) == "JiaZi"
        assert labels(coords["day"]) == "JiaZi"
        assert labels(coords["hour"]) == "GengWu"

    def test_result_is_json_serializable(self, plain):
        res = plain.get_coordinates(utc(2024, 6, 15, 8, 30), -74.006)
        json.dumps(res)
        assert set(res) == {"metadata", "coordinates"}
        assert set(res["coordinates"]) == {"year", "month", "day", "hour"}

    def test_precise_mode_shifts_hour_by_longitude(self, precise, plain):
        # 120E at 00:30 UTC: true solar time ≈ 08:26 -> Chen hour;
        # uncorrected clock stays at 00:30 -> Zi hour.
        dt = utc(2024, 1, 1, 0, 30)
        p_hour = labels(precise.get_coordinates(dt, 120.0)["coordinates"]["hour"])
        u_hour = labels(plain.get_coordinates(dt, 120.0)["coordinates"]["hour"])
        assert p_hour != u_hour
        assert precise.get_coordinates(dt, 120.0)["coordinates"]["hour"]["branch"] == "Chen"

    def test_non_precise_mode_still_gets_year_month_right(self, plain):
        # Regression: solar_lambda must not be mocked to 0.0 when the
        # time correction is off; year/month are location-independent.
        res = plain.get_coordinates(utc(2024, 6, 15, 12, 0), 0.0)
        assert labels(res["coordinates"]["year"]) == "JiaChen"
        assert labels(res["coordinates"]["month"]) == "GengWu"

    def test_naive_datetime_accepted(self, plain):
        res = plain.get_coordinates(datetime(2024, 1, 1, 12, 0), 0.0)
        assert labels(res["coordinates"]["day"]) == "JiaZi"

    def test_longitude_outside_range_rejected(self, plain):
        with pytest.raises(ValueError):
            plain.get_coordinates(utc(2024, 1, 1, 12, 0), 181.0)
        with pytest.raises(ValueError):
            plain.get_coordinates(utc(2024, 1, 1, 12, 0), -180.1)

    def test_longitude_endpoints_accepted(self, plain):
        for lon in (-180.0, 180.0):
            res = plain.get_coordinates(utc(2024, 1, 1, 12, 0), lon)
            assert res["metadata"]["longitude"] == lon


class TestBoundaries:
    def test_year_flips_exactly_at_315_degrees(self, plain):
        dt = utc(2024, 2, 4, 12, 0)
        assert plain._get_year_index(dt, 315.0) == 40    # Jia-Chen
        assert plain._get_year_index(dt, 314.99) == 39   # still Gui-Mao

    def test_month_flips_exactly_at_315_degrees(self, plain):
        # At LiChun the month becomes Yin (Bing-Yin for a Jia year);
        # a hair below it is still Chou of the previous year (Gui year).
        assert plain._get_month_index(0, 315.0) == 2     # Bing-Yin
        assert plain._get_month_index(8, 314.99) == 49   # Gui-Chou

    def test_month_flips_exactly_at_345_degrees(self, plain):
        # JingZhe: Yin month ends, Mao month begins (Jia year).
        assert plain._get_month_index(0, 344.99) == 2   # Bing-Yin
        assert plain._get_month_index(0, 345.0) == 3    # Ding-Mao

    def test_month_consistent_across_degree_wrap(self, plain):
        # 359.9 deg and 0.1 deg are adjacent on the circle; the month
        # branch must not jump at the 360/0 discontinuity.
        assert plain._get_month_index(0, 359.9) == plain._get_month_index(0, 0.1)

    def test_early_zi_belongs_to_new_day(self, plain):
        # Engine convention, complement to test_late_zi_stays_on_same_day:
        # 00:00-01:00 is Zi hour of the day that just began.
        res = plain.get_coordinates(utc(2024, 1, 2, 0, 30), 0.0)
        assert labels(res["coordinates"]["day"]) == "YiChou"
        assert labels(res["coordinates"]["hour"]) == "BingZi"
