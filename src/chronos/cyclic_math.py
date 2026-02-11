"""
Module: cyclic_math.py
Description: Implements Base-60 (Sexagenary) cyclic arithmetic and data structures.
This module handles the non-decimal temporal coordinates used in the engine.
"""

from typing import Union, Tuple, Dict

class CyclicVariable:
    """
    Represents a variable in the Sexagenary (Base-60) cycle.
    Mathematically, this operates within the cyclic group Z_60, composed of:
    - Z_10 (Heavenly Stems)
    - Z_12 (Earthly Branches)
    """

    # Memory optimization: Restricts attribute creation to save RAM on large datasets
    __slots__ = ['_index']

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
        Initializes the variable with a 0-59 index.
        Input is automatically normalized to the [0, 59] cyclic group.
        :param index: Integer representing the coordinate.
        """
        self._index = index % 60

    @property
    def index(self) -> int:
        """Returns the raw index in Z_60."""
        return self._index

    @property
    def stem_index(self) -> int:
        """Returns the index in Z_10 (Heavenly Stem)."""
        return self._index % 10

    @property
    def branch_index(self) -> int:
        """Returns the index in Z_12 (Earthly Branch)."""
        return self._index % 12

class CyclicVariable:
    """
    Represents a variable in the Sexagenary (Base-60) cycle.
    Acts as a tuple of (Heavenly Stem, Earthly Branch).
    """
    
    STEMS = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
    BRANCHES = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
    
    def __init__(self, index: int):
        """
        Initializes the variable with a 0-59 index.
        :param index: Integer between 0 and 59.
        """
        self.index = index % 60
    
    @property
    def stem(self) -> str:
        """Returns the Heavenly Stem (Base-10 component)."""
        return self.STEMS[self.index % 10]

    @property
    def branch(self) -> str:
        """Returns the Earthly Branch (Base-12 component)."""
        return self.BRANCHES[self.index % 12]
    
    @property
    def element(self) -> str:
        """
        Derives the naive elemental attribute (WuXing) of the Stem.
        Mapping: 0-1 Wood, 2-3 Fire, 4-5 Earth, 6-7 Metal, 8-9 Water.
        """
        # Optimized bitwise-like mapping or simple lookup
        elements = ["Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"]
        return elements[self.index % 10]

    def __add__(self, other):
        """Supports temporal shifting (e.g., current_year + 10)."""
        if isinstance(other, int):
            return CyclicVariable(self.index + other)
        raise TypeError("Can only add integers to CyclicVariable")

    def __sub__(self, other):
        """Supports calculating temporal distance."""
        if isinstance(other, CyclicVariable):
            # Calculate distance in the cycle
            return (self.index - other.index) % 60
        if isinstance(other, int):
            return CyclicVariable(self.index - other)
        raise TypeError("Unsupported type for subtraction")

    def __repr__(self):
        return f"<CyclicVar [{self.index}]: {self.stem}-{self.branch}>"

    def to_json(self):
        return {
            "index": self.index,
            "stem": self.stem,
            "branch": self.branch,
            "element": self.element
        }
