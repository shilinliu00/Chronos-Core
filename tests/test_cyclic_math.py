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

    def test_bool_index_rejected(self):
        # bool is an int subclass, so True must not silently act as 1.
        with pytest.raises(TypeError):
            CyclicVariable(True)
        with pytest.raises(TypeError):
            CyclicVariable(False)
        with pytest.raises(TypeError):
            CyclicVariable.from_stem_branch(True, 0)
        with pytest.raises(TypeError):
            CyclicVariable.from_stem_branch(0, False)
        with pytest.raises(TypeError):
            CyclicVariable(0) + True
        with pytest.raises(TypeError):
            CyclicVariable(0) - False

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

    def test_from_label_cn_round_trips_all_sixty(self):
        for i in range(60):
            assert CyclicVariable.from_label_cn(str(CyclicVariable(i))) == CyclicVariable(i)

    def test_from_label_en_round_trips_all_sixty(self):
        for i in range(60):
            v = CyclicVariable(i)
            assert CyclicVariable.from_label_en(v.stem + v.branch) == v

    def test_from_label_en_known_values(self):
        assert CyclicVariable.from_label_en("JiaZi") == CyclicVariable(0)
        assert CyclicVariable.from_label_en("GengShen") == CyclicVariable(56)
        assert CyclicVariable.from_label_en("GuiHai") == CyclicVariable(59)
        assert CyclicVariable.from_label_en("WuWu") == CyclicVariable(54)

    def test_from_label_en_ignores_letter_case(self):
        # Pinyin labels parse in any case, including the Ji/Jia
        # prefix trap: "jiazi" must split as Jia+Zi, not Ji+azi.
        for i in range(60):
            v = CyclicVariable(i)
            label = v.stem + v.branch
            assert CyclicVariable.from_label_en(label.lower()) == v
            assert CyclicVariable.from_label_en(label.upper()) == v
        assert CyclicVariable.from_label_en("jiazi") == CyclicVariable(0)
        assert CyclicVariable.from_label_en("JIAZI") == CyclicVariable(0)
        assert CyclicVariable.from_label_en("jiaZi") == CyclicVariable(0)
        assert CyclicVariable.from_label_en("gengshen") == CyclicVariable(56)
        assert CyclicVariable.from_label_en("JiChou") == CyclicVariable(25)
        assert CyclicVariable.from_label_en("jichou") == CyclicVariable(25)

    def test_from_label_en_accepts_one_separator(self):
        # One space or hyphen between stem and branch parses the
        # same as the joined label, for all sixty pillars.
        for i in range(60):
            v = CyclicVariable(i)
            assert CyclicVariable.from_label_en(v.stem + "-" + v.branch) == v
            assert CyclicVariable.from_label_en(v.stem + " " + v.branch) == v
        assert CyclicVariable.from_label_en("jia-zi") == CyclicVariable(0)
        assert CyclicVariable.from_label_en("Geng Shen") == CyclicVariable(56)

    def test_from_label_en_ignores_surrounding_whitespace(self):
        assert CyclicVariable.from_label_en(" JiaZi ") == CyclicVariable(0)
        assert CyclicVariable.from_label_en("\tGengShen\n") == CyclicVariable(56)

    def test_from_label_cn_ignores_surrounding_whitespace(self):
        assert CyclicVariable.from_label_cn(" 甲子 ") == CyclicVariable(0)
        assert CyclicVariable.from_label_cn("\t庚申\n") == CyclicVariable(56)

    def test_from_label_en_rejects_bad_labels(self):
        with pytest.raises(TypeError):
            CyclicVariable.from_label_en(0)
        for bad in ("", "Jia", "JiaZiYi", "JiaX", "JiaChou", "ZiJia", " "):
            with pytest.raises(ValueError):
                CyclicVariable.from_label_en(bad)

    def test_from_label_en_rejects_bad_separators(self):
        # Two separators, a separator at either end, or a mix of
        # space and hyphen never parses.
        for bad in (
            "Jia--Zi", "Jia  Zi", "-JiaZi", "JiaZi-",
            "Jia- Zi", "Jia -Zi", "Jia-zi-",
        ):
            with pytest.raises(ValueError):
                CyclicVariable.from_label_en(bad)

    def test_from_label_cn_rejects_bad_labels(self):
        with pytest.raises(TypeError):
            CyclicVariable.from_label_cn(0)
        for bad in ("", "甲", "甲子乙", "甲甲", "子甲", "甲X", "甲丑", "甲 子", " "):
            with pytest.raises(ValueError):
                CyclicVariable.from_label_cn(bad)

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

    def test_six_harms(self):
        # Liu Hai pairs: (0,7), (1,6), (2,5), (3,4), (8,11), (9,10).
        for a, b in [(0, 7), (1, 6), (2, 5), (3, 4), (8, 11), (9, 10)]:
            assert CyclicVariable(a).is_harming(CyclicVariable(b)), (a, b)
            assert CyclicVariable(b).is_harming(CyclicVariable(a)), (b, a)
        assert not CyclicVariable(0).is_harming(CyclicVariable(1))
        assert not CyclicVariable(0).is_harming(CyclicVariable(6))
        # Twice an index is even mod 12, so no branch harms itself.
        for a in range(12):
            assert not CyclicVariable(a).is_harming(CyclicVariable(a))

    def test_harming_is_symmetric(self):
        # The harm check is a sum mod 12, so it must read the same
        # in either direction for every pair of branches.
        for a in range(12):
            for b in range(12):
                x, y = CyclicVariable(a), CyclicVariable(b)
                assert x.is_harming(y) == y.is_harming(x), (a, b)

    def test_harming_rejects_wrong_type(self):
        for bad in (0, "JiaZi", None):
            with pytest.raises(TypeError):
                CyclicVariable(0).is_harming(bad)

    def test_three_punishments(self):
        # San Xing directed pairs: Zi/Mao mutual, Yin -> Si -> Shen
        # -> Yin, Chou -> Wei -> Xu -> Chou, and the four self
        # punishments Chen, Wu, You, Hai.
        directed = [
            (0, 3), (3, 0),
            (2, 5), (5, 8), (8, 2),
            (1, 7), (7, 10), (10, 1),
            (4, 4), (6, 6), (9, 9), (11, 11),
        ]
        for a, b in directed:
            assert CyclicVariable(a).is_penalizing(CyclicVariable(b)), (a, b)
        # The triad cycles run one way only: the reverse direction
        # of each step is not a punishment.
        for a, b in [(5, 2), (8, 5), (2, 8), (7, 1), (10, 7), (1, 10)]:
            assert not CyclicVariable(a).is_penalizing(CyclicVariable(b)), (a, b)
        # Exactly the twelve listed pairs punish, out of all 144.
        count = sum(
            CyclicVariable(a).is_penalizing(CyclicVariable(b))
            for a in range(12) for b in range(12)
        )
        assert count == 12
        # Only the four self punishment branches penalize themselves.
        for a in range(12):
            x = CyclicVariable(a)
            assert x.is_penalizing(x) == (a in (4, 6, 9, 11)), a

    def test_penalizing_rejects_wrong_type(self):
        for bad in (0, "JiaZi", None):
            with pytest.raises(TypeError):
                CyclicVariable(0).is_penalizing(bad)

    def test_three_harmonies(self):
        # San He triads: (0,4,8), (1,5,9), (2,6,10), (3,7,11).
        for group in [(0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)]:
            for a in group:
                for b in group:
                    if a != b:
                        assert CyclicVariable(a).is_harmonizing(
                            CyclicVariable(b)
                        ), (a, b)
        assert not CyclicVariable(0).is_harmonizing(CyclicVariable(1))
        assert not CyclicVariable(0).is_harmonizing(CyclicVariable(2))
        assert not CyclicVariable(0).is_harmonizing(CyclicVariable(0))

    def test_harmonizing_is_symmetric(self):
        # Same modular check both ways, so the relation must read the
        # same in either direction for every pair of branches.
        for a in range(12):
            for b in range(12):
                x, y = CyclicVariable(a), CyclicVariable(b)
                assert x.is_harmonizing(y) == y.is_harmonizing(x), (a, b)

    def test_clash_and_combine_are_symmetric(self):
        # Both relations are defined on branch distance, so they must
        # read the same in either direction for every pair of branches.
        for a in range(12):
            for b in range(12):
                x, y = CyclicVariable(a), CyclicVariable(b)
                assert x.is_clashing(y) == y.is_clashing(x), (a, b)
                assert x.is_combining(y) == y.is_combining(x), (a, b)
        # No branch clashes or combines with itself: distance 0 is
        # neither 6 apart nor summing to 1 mod 12.
        for a in range(12):
            x = CyclicVariable(a)
            assert not x.is_clashing(x)
            assert not x.is_combining(x)

    def test_clash_and_combine_reject_wrong_types(self):
        for bad in (0, "JiaZi", None):
            with pytest.raises(TypeError):
                CyclicVariable(0).is_clashing(bad)
            with pytest.raises(TypeError):
                CyclicVariable(0).is_combining(bad)
            with pytest.raises(TypeError):
                CyclicVariable(0).is_harmonizing(bad)

    def test_ten_gods_for_yang_day_stem(self):
        # Jia (index 0, yang Wood) day stem against all ten stems.
        day = CyclicVariable(0)
        expected = [
            "比肩", "劫财", "食神", "伤官", "偏财",
            "正财", "七杀", "正官", "偏印", "正印",
        ]
        for stem, god in enumerate(expected):
            assert day.ten_god(CyclicVariable(stem)) == god, stem

    def test_ten_gods_for_yin_day_stem(self):
        # Yi (index 1, yin Wood) flips the same/different polarity
        # outcomes relative to the yang day stem above.
        day = CyclicVariable(1)
        expected = [
            "劫财", "比肩", "伤官", "食神", "正财",
            "偏财", "正官", "七杀", "正印", "偏印",
        ]
        for stem, god in enumerate(expected):
            assert day.ten_god(CyclicVariable(stem)) == god, stem

    def test_ten_gods_for_metal_and_water_day_stems(self):
        # Wood rows are pinned above; the element rotation must also
        # hold for the other element groups, so pin a yang Metal row
        # (Geng) and a yin Water row (Gui) against all ten stems.
        geng = CyclicVariable(6)
        expected_geng = [
            "偏财", "正财", "七杀", "正官", "偏印",
            "正印", "比肩", "劫财", "食神", "伤官",
        ]
        for stem, god in enumerate(expected_geng):
            assert geng.ten_god(CyclicVariable(stem)) == god, stem
        gui = CyclicVariable(9)
        expected_gui = [
            "伤官", "食神", "正财", "偏财", "正官",
            "七杀", "正印", "偏印", "劫财", "比肩",
        ]
        for stem, god in enumerate(expected_gui):
            assert gui.ten_god(CyclicVariable(stem)) == god, stem

    def test_ten_god_rejects_wrong_type(self):
        with pytest.raises(TypeError):
            CyclicVariable(0).ten_god("丙")


class TestArithmetic:
    def test_add_wraps_cycle(self):
        assert CyclicVariable(59) + 1 == CyclicVariable(0)
        assert CyclicVariable(0) + 60 == CyclicVariable(0)

    def test_radd_matches_add(self):
        assert 1 + CyclicVariable(59) == CyclicVariable(0)
        assert 60 + CyclicVariable(0) == CyclicVariable(0)
        assert -1 + CyclicVariable(0) == CyclicVariable(59)

    def test_radd_rejects_wrong_types(self):
        with pytest.raises(TypeError):
            "1" + CyclicVariable(0)
        with pytest.raises(TypeError):
            True + CyclicVariable(0)

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

    def test_from_json_round_trips_all_sixty(self):
        for i in range(60):
            v = CyclicVariable(i)
            assert CyclicVariable.from_json(v.to_json()) == v

    def test_from_json_rejects_bad_data(self):
        with pytest.raises(TypeError):
            CyclicVariable.from_json("JiaZi")
        with pytest.raises(TypeError):
            CyclicVariable.from_json({})
        with pytest.raises(TypeError):
            CyclicVariable.from_json({"index": True})
        with pytest.raises(TypeError):
            CyclicVariable.from_json({"index": "0"})
        with pytest.raises(ValueError):
            CyclicVariable.from_json({"index": 0, "label_cn": "乙丑"})
        # Label may be omitted; the index alone rebuilds the pillar.
        assert CyclicVariable.from_json({"index": 59}) == CyclicVariable(59)

    def test_to_json_shape(self):
        j = CyclicVariable(0).to_json()
        assert j == {
            "index": 0,
            "stem": "Jia",
            "branch": "Zi",
            "element": "Wood",
            "na_yin": "海中金",
            "na_yin_element": "Metal",
            "hidden_stems": ["Gui"],
            "hidden_stems_cn": ["癸"],
            "label_cn": "甲子",
        }

    def test_to_json_hidden_stems_track_branch(self):
        # Yi-Chou hides Ji, Gui, Xin; Gui-Hai hides Ren, Jia.
        assert CyclicVariable(1).to_json()["hidden_stems"] == ["Ji", "Gui", "Xin"]
        assert CyclicVariable(59).to_json()["hidden_stems_cn"] == ["壬", "甲"]

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


class TestHiddenStems:
    def test_table_covers_all_twelve_branches(self):
        assert len(CyclicVariable._HIDDEN_STEMS) == 12

    def test_full_table_matches_classic_cang_gan(self):
        # Stem indices: Jia 0, Yi 1, Bing 2, Ding 3, Wu 4,
        # Ji 5, Geng 6, Xin 7, Ren 8, Gui 9.
        expected = {
            0: ("Gui",),                  # Zi 子
            1: ("Ji", "Gui", "Xin"),      # Chou 丑
            2: ("Jia", "Bing", "Wu"),     # Yin 寅
            3: ("Yi",),                   # Mao 卯
            4: ("Wu", "Yi", "Gui"),       # Chen 辰
            5: ("Bing", "Geng", "Wu"),    # Si 巳
            6: ("Ding", "Ji"),            # Wu 午
            7: ("Ji", "Yi", "Ding"),      # Wei 未
            8: ("Geng", "Ren", "Wu"),     # Shen 申
            9: ("Xin",),                  # You 酉
            10: ("Wu", "Xin", "Ding"),    # Xu 戌
            11: ("Ren", "Jia"),           # Hai 亥
        }
        for branch, stems in expected.items():
            v = CyclicVariable.from_stem_branch(branch % 2, branch)
            assert v.hidden_stems == stems, branch

    def test_chinese_names_match_english_ones(self):
        assert CyclicVariable(0).hidden_stems_cn == ("癸",)        # Jia-Zi
        assert CyclicVariable(1).hidden_stems_cn == ("己", "癸", "辛")  # Yi-Chou
        assert CyclicVariable(2).hidden_stems_cn == ("甲", "丙", "戊")  # Bing-Yin
        assert CyclicVariable(59).hidden_stems_cn == ("壬", "甲")  # Gui-Hai

    def test_hidden_stems_depend_on_branch_only(self):
        # Jia-Zi and Wu-Zi share branch Zi, so both hide only Gui.
        assert CyclicVariable(0).hidden_stems == CyclicVariable(24).hidden_stems
        assert CyclicVariable(0).hidden_stems == ("Gui",)

    def test_main_qi_is_first(self):
        # The first hidden stem is the branch's main qi (本气).
        assert CyclicVariable(0).hidden_stems[0] == "Gui"    # Zi
        assert CyclicVariable(3).hidden_stems[0] == "Yi"     # Mao
        assert CyclicVariable(6).hidden_stems[0] == "Ding"   # Wu
        assert CyclicVariable(9).hidden_stems[0] == "Xin"    # You
