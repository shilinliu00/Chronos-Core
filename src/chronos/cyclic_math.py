"""
Module: cyclic_math.py
Description: Implements Base-60 (Sexagenary) cyclic arithmetic and data structures.
This module handles the non-decimal temporal coordinates used in the engine.
"""

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
