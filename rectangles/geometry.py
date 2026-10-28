"""Core geometric value types: Point, Segment, Side and Rectangle.

Conventions used throughout the package
---------------------------------------
* Rectangles are axis aligned (their sides are parallel to the x and y axes).
* The coordinate system is the usual mathematical one: x grows to the right and
  y grows upward, so ``bottom < top``.  Every algorithm in this package is
  symmetric, so screen coordinates (y growing downward) also work; only the
  names "top" and "bottom" swap meaning.
* Rectangles are closed sets: the four sides belong to the rectangle.
* All algorithms only *compare* coordinates (and take min / max).  They never
  add, subtract, multiply or divide them, so results are exact for ints,
  floats and ``fractions.Fraction`` alike.  No epsilon is needed.
"""

from __future__ import annotations

import math
import numbers
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import TypeAlias

# Coordinates may be ints, floats or Fractions (any finite real except bool).
Number: TypeAlias = int | float | Fraction


def _format_number(value: Number) -> str:
    """Format a coordinate for display: ``2``, ``2.5``, ``1/3``."""
    return str(value)


@dataclass(frozen=True, order=True)
class Point:
    """An immutable point in the plane.

    >>> Point(1, 2)
    Point(x=1, y=2)
    >>> str(Point(1, 2.5))
    '(1, 2.5)'
    """

    x: Number
    y: Number

    def __str__(self) -> str:
        return f"({_format_number(self.x)}, {_format_number(self.y)})"


@dataclass(frozen=True)
class Segment:
    """An immutable, axis aligned line segment with positive length.

    The endpoints are normalised so that ``start < end`` (lexicographically),
    which makes two segments covering the same points compare equal.

    >>> Segment(Point(4, 0), Point(0, 0))
    Segment(start=Point(x=0, y=0), end=Point(x=4, y=0))
    """

    start: Point
    end: Point

    def __post_init__(self) -> None:
        if self.start == self.end:
            raise ValueError("a segment must have positive length")
        if self.start.x != self.end.x and self.start.y != self.end.y:
            raise ValueError("a segment must be horizontal or vertical")
        if self.end < self.start:
            # Frozen dataclass: use object.__setattr__ to normalise in place.
            start, end = self.end, self.start
            object.__setattr__(self, "start", start)
            object.__setattr__(self, "end", end)

    @property
    def is_horizontal(self) -> bool:
        return self.start.y == self.end.y

    @property
    def is_vertical(self) -> bool:
        return self.start.x == self.end.x

    def contains_point(self, point: Point) -> bool:
        """Return True if ``point`` lies on this segment (endpoints included)."""
        return self.start.x <= point.x <= self.end.x and self.start.y <= point.y <= self.end.y

    def __str__(self) -> str:
        return f"{self.start} -> {self.end}"


def intersect_segments(s1: Segment, s2: Segment) -> Point | Segment | None:
    """Intersect two axis aligned segments.

    Returns ``None`` if they do not meet, a ``Point`` if they meet in exactly
    one point, or a ``Segment`` if they are collinear and overlap with
    positive length.

    >>> horizontal = Segment(Point(0, 2), Point(5, 2))
    >>> intersect_segments(horizontal, Segment(Point(3, 0), Point(3, 9)))
    Point(x=3, y=2)
    >>> print(intersect_segments(horizontal, Segment(Point(3, 2), Point(9, 2))))
    (3, 2) -> (5, 2)
    >>> intersect_segments(horizontal, Segment(Point(0, 1), Point(5, 1))) is None
    True
    """
    if s1.is_horizontal and s2.is_horizontal:
        if s1.start.y != s2.start.y:
            return None  # parallel, on different lines
        y = s1.start.y
        lo = max(s1.start.x, s2.start.x)
        hi = min(s1.end.x, s2.end.x)
        if lo > hi:
            return None  # same line, but the ranges do not overlap
        if lo == hi:
            return Point(lo, y)  # touching end to end
        return Segment(Point(lo, y), Point(hi, y))

    if s1.is_vertical and s2.is_vertical:
        if s1.start.x != s2.start.x:
            return None
        x = s1.start.x
        lo = max(s1.start.y, s2.start.y)
        hi = min(s1.end.y, s2.end.y)
        if lo > hi:
            return None
        if lo == hi:
            return Point(x, lo)
        return Segment(Point(x, lo), Point(x, hi))

    # Perpendicular: one horizontal, one vertical. The only candidate point is
    # (x of the vertical segment, y of the horizontal segment).
    horizontal, vertical = (s1, s2) if s1.is_horizontal else (s2, s1)
    x = vertical.start.x
    y = horizontal.start.y
    if horizontal.start.x <= x <= horizontal.end.x and vertical.start.y <= y <= vertical.end.y:
        return Point(x, y)
    return None


class Side(Enum):
    """The four sides of an axis aligned rectangle."""

    BOTTOM = "bottom"
    RIGHT = "right"
    TOP = "top"
    LEFT = "left"


def _validate_coordinate(name: str, value: object) -> None:
    # bool is a subclass of int in Python; True/False as coordinates is a bug.
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise TypeError(f"{name} must be a real number, got {value!r}")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}")


@dataclass(frozen=True)
class Rectangle:
    """An immutable, axis aligned rectangle with positive width and height.

    Construct it from its four edges (``left < right`` and ``bottom < top``):

    >>> r = Rectangle(0, 0, 4, 3)
    >>> r.width, r.height, r.area
    (4, 3, 12)
    >>> str(r)
    '[(0, 0) -> (4, 3)]'

    or from any two opposite corners, in any order:

    >>> Rectangle.from_corners((4, 3), (0, 0)) == r
    True
    """

    left: Number
    bottom: Number
    right: Number
    top: Number

    def __post_init__(self) -> None:
        for name in ("left", "bottom", "right", "top"):
            _validate_coordinate(name, getattr(self, name))
        if not self.left < self.right:
            raise ValueError(
                f"left ({self.left}) must be less than right ({self.right}); "
                "zero width rectangles are not supported"
            )
        if not self.bottom < self.top:
            raise ValueError(
                f"bottom ({self.bottom}) must be less than top ({self.top}); "
                "zero height rectangles are not supported"
            )

    # ---- alternative constructors -------------------------------------
    @classmethod
    def from_corners(
        cls,
        corner1: Point | tuple[Number, Number],
        corner2: Point | tuple[Number, Number],
    ) -> Rectangle:
        """Build a rectangle from two opposite corners given in any order."""
        x1, y1 = (corner1.x, corner1.y) if isinstance(corner1, Point) else corner1
        x2, y2 = (corner2.x, corner2.y) if isinstance(corner2, Point) else corner2
        return cls(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    @classmethod
    def from_origin_size(cls, x: Number, y: Number, width: Number, height: Number) -> Rectangle:
        """Build a rectangle from its bottom left corner and its size.

        >>> Rectangle.from_origin_size(1, 2, 3, 4)
        Rectangle(left=1, bottom=2, right=4, top=6)
        """
        return cls(x, y, x + width, y + height)

    # ---- derived properties --------------------------------------------
    @property
    def width(self) -> Number:
        return self.right - self.left

    @property
    def height(self) -> Number:
        return self.top - self.bottom

    @property
    def area(self) -> Number:
        return self.width * self.height

    @property
    def corners(self) -> tuple[Point, Point, Point, Point]:
        """Corners in counter clockwise order starting at bottom left."""
        return (
            Point(self.left, self.bottom),
            Point(self.right, self.bottom),
            Point(self.right, self.top),
            Point(self.left, self.top),
        )

    def side(self, which: Side) -> Segment:
        """Return one side of the rectangle as a Segment."""
        if which is Side.BOTTOM:
            return Segment(Point(self.left, self.bottom), Point(self.right, self.bottom))
        if which is Side.RIGHT:
            return Segment(Point(self.right, self.bottom), Point(self.right, self.top))
        if which is Side.TOP:
            return Segment(Point(self.left, self.top), Point(self.right, self.top))
        return Segment(Point(self.left, self.bottom), Point(self.left, self.top))

    def sides(self) -> Iterator[tuple[Side, Segment]]:
        """Yield ``(Side, Segment)`` pairs for all four sides."""
        for which in Side:
            yield which, self.side(which)

    def contains_point(self, point: Point) -> bool:
        """True if ``point`` is inside the rectangle or on its boundary."""
        return self.left <= point.x <= self.right and self.bottom <= point.y <= self.top

    def __str__(self) -> str:
        return f"[{Point(self.left, self.bottom)} -> {Point(self.right, self.top)}]"


def interiors_overlap(a: Rectangle, b: Rectangle) -> bool:
    """True if the open interiors of ``a`` and ``b`` share at least one point.

    In other words: the overlap region has positive area.  Rectangles that
    only touch along an edge or at a corner do *not* overlap.

    >>> interiors_overlap(Rectangle(0, 0, 4, 4), Rectangle(2, 2, 6, 6))
    True
    >>> interiors_overlap(Rectangle(0, 0, 4, 4), Rectangle(4, 0, 8, 4))
    False
    """
    return a.left < b.right and b.left < a.right and a.bottom < b.top and b.bottom < a.top
