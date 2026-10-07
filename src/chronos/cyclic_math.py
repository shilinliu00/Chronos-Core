"""
Module: cyclic_math.py
Description: Implements Base-60 (Sexagenary) cyclic arithmetic and data structures.
This module handles the non-decimal temporal coordinates used in the engine.
"""

from typing import Union, Dict

class CyclicVariable:
    """
    Represents a variable in the Sexagenary (Base-60) cycle.
    Mathematically, this operates within the cyclic group Z_60, composed of:
    - Z_10 (Heavenly Stems)
    - Z_12 (Earthly Branches)
    """

    # Memory optimization: Restricts attribute creation to save RAM on large datasets
    __slots__ = ['_index']

    # NaYin (纳音) table: 30 attributes, one per consecutive pair of pillars,
    # following the classic rhyme (六十甲子纳音歌). Each entry: (name_cn, element).
    NAYIN = [
        ("海中金", "Metal"), ("炉中火", "Fire"), ("大林木", "Wood"),
        ("路旁土", "Earth"), ("剑锋金", "Metal"), ("山头火", "Fire"),
        ("涧下水", "Water"), ("城头土", "Earth"), ("白蜡金", "Metal"),
        ("杨柳木", "Wood"), ("泉中水", "Water"), ("屋上土", "Earth"),
        ("霹雳火", "Fire"), ("松柏木", "Wood"), ("长流水", "Water"),
        ("沙中金", "Metal"), ("山下火", "Fire"), ("平地木", "Wood"),
        ("壁上土", "Earth"), ("金箔金", "Metal"), ("覆灯火", "Fire"),
        ("天河水", "Water"), ("大驿土", "Earth"), ("钗钏金", "Metal"),
        ("桑柘木", "Wood"), ("大溪水", "Water"), ("沙中土", "Earth"),
        ("天上火", "Fire"), ("石榴木", "Wood"), ("大海水", "Water"),
    ]

    # Master Data Vectors
    STEMS = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
    BRANCHES = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
    
    # Chinese Character Mappings (Optional for localization)
    STEMS_CN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    BRANCHES_CN = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    # Element Vector: 0-1 Wood, 2-3 Fire, 4-5 Earth, 6-7 Metal, 8-9 Water
    ELEMENT_VECTOR = ["Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"]

    def __init__(self, index: int):
        """
        Creates a variable from a raw position in Z_60.
        The index is normalized into [0, 60), so arithmetic may freely
        overflow the cycle (e.g. CyclicVariable(59) + 1 -> Jia-Zi).
        """
        if not isinstance(index, int):
            raise TypeError("CyclicVariable index must be an integer")
        self._index = index % 60

    @classmethod
    def from_stem_branch(cls, stem_idx: int, branch_idx: int) -> 'CyclicVariable':
        """
        Builds a variable directly from stem and branch indices, in closed form.

        Solves i = stem (mod 10), i = branch (mod 12) via the Chinese
        Remainder Theorem. Write i = stem + 10k; then 10k = branch - stem
        (mod 12). Since gcd(10, 12) = 2, divide through: 5k = (branch - stem)/2
        (mod 6), and 5 is its own inverse mod 6, so
        k = 5 * ((branch - stem) / 2) (mod 6).

        A solution exists only when stem and branch share parity, which holds
        by construction in the sexagenary cycle.
        """
        if not isinstance(stem_idx, int) or not isinstance(branch_idx, int):
            raise TypeError("stem and branch indices must be integers")
        if not 0 <= stem_idx < 10:
            raise ValueError("stem index must be in [0, 10)")
        if not 0 <= branch_idx < 12:
            raise ValueError("branch index must be in [0, 12)")
        if (stem_idx - branch_idx) % 2 != 0:
            raise ValueError(
                f"stem {stem_idx} and branch {branch_idx} have mismatched parity"
            )
        k = (5 * (((branch_idx - stem_idx) % 12) // 2)) % 6
        return cls(stem_idx + 10 * k)

    @property
    def index(self) -> int:
        """Normalized position in Z_60, always in [0, 60)."""
        return self._index

    @property
    def stem_index(self) -> int:
        """Position in Z_10 (Heavenly Stems)."""
        return self._index % 10

    @property
    def branch_index(self) -> int:
        """Position in Z_12 (Earthly Branches)."""
        return self._index % 12

    @property
    def stem(self) -> str:
        """Returns the English string for the Heavenly Stem."""
        return self.STEMS[self.stem_index]

    @property
    def branch(self) -> str:
        """Returns the English string for the Earthly Branch."""
        return self.BRANCHES[self.branch_index]

    @property
    def stem_cn(self) -> str:
        """Returns the Chinese character for the Heavenly Stem."""
        return self.STEMS_CN[self.stem_index]

    @property
    def branch_cn(self) -> str:
        """Returns the Chinese character for the Earthly Branch."""
        return self.BRANCHES_CN[self.branch_index]
    
    @property
    def element(self) -> str:
        """
        Derives the naive elemental attribute (WuXing) of the Stem.
        This is an O(1) vector lookup.
        """
        return self.ELEMENT_VECTOR[self.stem_index]

    @property
    def na_yin(self) -> str:
        """
        NaYin (纳音) name of the pillar, e.g. "海中金".
        Each NaYin spans two consecutive pillars, so index // 2 selects it.
        """
        return self.NAYIN[self._index // 2][0]

    @property
    def na_yin_element(self) -> str:
        """Elemental attribute (WuXing) of the pillar's NaYin."""
        return self.NAYIN[self._index // 2][1]

    def is_clashing(self, other: 'CyclicVariable') -> bool:
        """
        Determines if there is a 'Clash' (Antagonistic relationship) using modular arithmetic.
        In Z_12 (Branches), a clash occurs if the distance is exactly 6 (180 degrees opposite).
        
        :return: Boolean indicating a clash.
        """
        # (Target - Self) % 12 == 6 implies opposition in the dodecagonal cycle
        return (self.branch_index - other.branch_index) % 12 == 6

    def is_combining(self, other: 'CyclicVariable') -> bool:
        """
        Determines if there is a 'Six Combination' (Harmonic relationship).
        Mathematical Logic: sum of indices % 12 == 1 (e.g., Zi(0) + Chou(1) = 1)
        Note: This is a simplified algorithmic representation of the Liu He pairs.
        """
        # Standard Liu He pairs: (0,1), (2,11), (3,10), (4,9), (5,8), (6,7)
        # Sum of indices is 1, 13, 25... -> (sum % 12) == 1
        return (self.branch_index + other.branch_index) % 12 == 1

    def __add__(self, other: int):
        """Supports temporal shifting (e.g., next year -> current + 1)."""
        if isinstance(other, int):
            return CyclicVariable(self._index + other)
        raise TypeError("Can only add integers (time deltas) to CyclicVariable")

    def __sub__(self, other: Union['CyclicVariable', int]):
        """
        Supports calculating temporal distance or shifting backwards.
        - If other is CyclicVariable: Returns distance in the cycle (int).
        - If other is int: Returns new CyclicVariable (obj).
        """

        if isinstance(other, CyclicVariable):
            # Calculate minimal forward distance in the cycle
            return (self._index - other._index) % 60
        if isinstance(other, int):
            return CyclicVariable(self._index - other)
        raise TypeError("Unsupported type for subtraction")

    def __eq__(self, other):
        """Enables equality checks (e.g., if day1 == day2)."""
        if isinstance(other, CyclicVariable):
            return self._index == other._index
        return False

    def __hash__(self):
        """Enables use of CyclicVariable as dictionary keys or in sets."""
        return hash(self._index)

    def __repr__(self):
        return f"<CV({self._index}): {self.stem}{self.branch} ({self.stem_cn}{self.branch_cn})>"

    def to_json(self) -> Dict:
        """Serialization for API responses."""
        return {
            "index": self._index,
            "stem": self.stem,
            "branch": self.branch,
            "element": self.element,
            "na_yin": self.na_yin,
            "na_yin_element": self.na_yin_element,
            "label_cn": f"{self.stem_cn}{self.branch_cn}"
        }
