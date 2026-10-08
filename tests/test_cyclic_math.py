"""Tests for the Z_60 cyclic arithmetic kernel (cyclic_math.py)."""
import pytest

from chronos.cyclic_math import CyclicVariable


class TestConstruction:
    def test_index_normalizes_into_cycle(self):
        assert CyclicVariable(60) == CyclicVariable(0)
        assert CyclicVariable(61) == CyclicVariable(1)
        assert CyclicVariable(-1) == CyclicVariable(59)
        assert CyclicVariable(-61) == CyclicVariable(59)

    def test_non_integer_index_rejected(self):
        with pytest.raises(TypeError):
            CyclicVariable(1.5)
        with pytest.raises(TypeError):
            CyclicVariable("0")

    def test_from_stem_branch_round_trips_all_sixty(self):
        # Closed-form CRT lookup must agree with the raw index everywhere.
        for i in range(60):
            v = CyclicVariable(i)
            built = CyclicVariable.from_stem_branch(v.stem_index, v.branch_index)
            assert built == v, i

    def test_from_stem_branch_known_values(self):
        assert CyclicVariable.from_stem_branch(0, 0) == CyclicVariable(0)    # Jia-Zi
        assert CyclicVariable.from_stem_branch(6, 8) == CyclicVariable(56)   # Geng-Shen
        assert CyclicVariable.from_stem_branch(9, 11) == CyclicVariable(59)  # Gui-Hai

    def test_from_stem_branch_rejects_mismatched_parity(self):
        # Stem/branch parity always matches inside Z_60, so (0, 1) is impossible.
        with pytest.raises(ValueError):
            CyclicVariable.from_stem_branch(0, 1)

    def test_from_stem_branch_rejects_out_of_range(self):
        with pytest.raises(ValueError):
            CyclicVariable.from_stem_branch(10, 0)
        with pytest.raises(ValueError):
            CyclicVariable.from_stem_branch(0, 12)
        with pytest.raises(TypeError):
            CyclicVariable.from_stem_branch(1.0, 1)

    def test_stem_branch_indices(self):
        v = CyclicVariable(0)  # Jia-Zi
        assert (v.stem_index, v.branch_index) == (0, 0)
        v = CyclicVariable(10)  # Jia-Xu
        assert (v.stem_index, v.branch_index) == (0, 10)
        v = CyclicVariable(59)  # Gui-Hai
        assert (v.stem_index, v.branch_index) == (9, 11)

    def test_index_property_returns_normalized_index(self):
        assert CyclicVariable(0).index == 0
        assert CyclicVariable(59).index == 59
        assert CyclicVariable(119).index == 59


class TestLabels:
    def test_english_labels(self):
        v = CyclicVariable(0)
        assert v.stem == "Jia" and v.branch == "Zi"

    def test_chinese_labels(self):
        v = CyclicVariable(59)
        assert v.stem_cn == "癸" and v.branch_cn == "亥"

    def test_element_lookup(self):
        assert CyclicVariable(0).element == "Wood"   # Jia
        assert CyclicVariable(2).element == "Fire"   # Bing
        assert CyclicVariable(4).element == "Earth"  # Wu
        assert CyclicVariable(6).element == "Metal"  # Geng
        assert CyclicVariable(8).element == "Water"  # Ren


class TestRelations:
    def test_clash_is_180_degrees(self):
        assert CyclicVariable(0).is_clashing(CyclicVariable(6))   # Zi vs Wu
        assert CyclicVariable(6).is_clashing(CyclicVariable(0))
        assert not CyclicVariable(0).is_clashing(CyclicVariable(5))
        assert not CyclicVariable(0).is_clashing(CyclicVariable(0))

    def test_six_combinations(self):
        # Liu He pairs: (0,1), (2,11), (3,10), (4,9), (5,8), (6,7)
        for a, b in [(0, 1), (2, 11), (3, 10), (4, 9), (5, 8), (6, 7)]:
            assert CyclicVariable(a).is_combining(CyclicVariable(b)), (a, b)
        assert not CyclicVariable(0).is_combining(CyclicVariable(2))
        assert not CyclicVariable(0).is_combining(CyclicVariable(6))


class TestArithmetic:
    def test_add_wraps_cycle(self):
        assert CyclicVariable(59) + 1 == CyclicVariable(0)
        assert CyclicVariable(0) + 60 == CyclicVariable(0)

    def test_sub_int_wraps_cycle(self):
        assert CyclicVariable(0) - 1 == CyclicVariable(59)

    def test_sub_variable_gives_forward_distance(self):
        assert CyclicVariable(10) - CyclicVariable(4) == 6
        assert CyclicVariable(4) - CyclicVariable(10) == 54  # wraps forward

    def test_add_sub_reject_wrong_types(self):
        with pytest.raises(TypeError):
            CyclicVariable(0) + "1"
        with pytest.raises(TypeError):
            CyclicVariable(0) - 1.5


class TestIdentity:
    def test_eq_and_hash(self):
        a, b = CyclicVariable(7), CyclicVariable(7)
        assert a == b
        assert hash(a) == hash(b)
        assert len({a, b, CyclicVariable(8)}) == 2
        assert (a == "7") is False

    def test_usable_as_dict_key(self):
        counts = {CyclicVariable(0): 3}
        counts[CyclicVariable(60)] += 1
        assert counts[CyclicVariable(0)] == 4

    def test_to_json_shape(self):
        j = CyclicVariable(0).to_json()
        assert j == {
            "index": 0,
            "stem": "Jia",
            "branch": "Zi",
            "element": "Wood",
            "na_yin": "海中金",
            "na_yin_element": "Metal",
            "label_cn": "甲子",
        }

    def test_repr(self):
        assert repr(CyclicVariable(0)) == "<CV(0): JiaZi (甲子)>"

    def test_str_returns_chinese_label(self):
        assert str(CyclicVariable(0)) == "甲子"
        assert str(CyclicVariable(59)) == "癸亥"


class TestNaYin:
    def test_table_has_thirty_entries(self):
        assert len(CyclicVariable.NAYIN) == 30

    def test_na_yin_endpoints(self):
        assert CyclicVariable(0).na_yin == "海中金"    # Jia-Zi
        assert CyclicVariable(1).na_yin == "海中金"    # Yi-Chou, same pair
        assert CyclicVariable(59).na_yin == "大海水"   # Gui-Hai

    def test_na_yin_mid_cycle_spots(self):
        assert CyclicVariable(8).na_yin == "剑锋金"    # Ren-Shen pair
        assert CyclicVariable(24).na_yin == "霹雳火"   # Wu-Zi pair

    def test_na_yin_element_tracks_table(self):
        assert CyclicVariable(0).na_yin_element == "Metal"   # 海中金
        assert CyclicVariable(2).na_yin_element == "Fire"    # 炉中火
        assert CyclicVariable(4).na_yin_element == "Wood"    # 大林木
        assert CyclicVariable(6).na_yin_element == "Earth"   # 路旁土
        assert CyclicVariable(59).na_yin_element == "Water"  # 大海水

    def test_na_yin_shifts_only_every_two_pillars(self):
        for i in range(0, 60, 2):
            assert CyclicVariable(i).na_yin == CyclicVariable(i + 1).na_yin
        assert CyclicVariable(1).na_yin != CyclicVariable(2).na_yin
