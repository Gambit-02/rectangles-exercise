"""Adjacency: do two rectangles sit side by side, sharing part of a side?"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .geometry import Rectangle, Segment, Side, interiors_overlap, intersect_segments


class AdjacencyType(Enum):
    """How much of a side the two rectangles share."""

    PROPER = "proper"  # the two sides are identical
    SUB_LINE = "sub-line"  # one side lies wholly within the other side
    PARTIAL = "partial"  # the sides overlap, but neither contains the other


@dataclass(frozen=True)
class AdjacencyResult:
    adjacent: bool
    kind: AdjacencyType | None = None
    shared_segment: Segment | None = None
    side_of_a: Side | None = None
    side_of_b: Side | None = None


NOT_ADJACENT = AdjacencyResult(adjacent=False)

# Only sides that face each other can be shared by rectangles that do not
# overlap: A's right with B's left, A's top with B's bottom, and so on.
_FACING_SIDES = (
    (Side.RIGHT, Side.LEFT),
    (Side.LEFT, Side.RIGHT),
    (Side.TOP, Side.BOTTOM),
    (Side.BOTTOM, Side.TOP),
)


def find_adjacency(a: Rectangle, b: Rectangle) -> AdjacencyResult:
    """Detect whether ``a`` and ``b`` are adjacent and classify the share.

    Two rectangles are adjacent when their interiors do not overlap and a side
    of one shares a segment of positive length with a side of the other.

    >>> r = find_adjacency(Rectangle(0, 0, 8, 8), Rectangle(8, 0, 12, 8))
    >>> r.adjacent, r.kind.value, str(r.shared_segment)
    (True, 'proper', '(8, 0) -> (8, 8)')
    >>> find_adjacency(Rectangle(0, 0, 4, 4), Rectangle(4, 4, 8, 8)).adjacent  # corner only
    False
    """
    if interiors_overlap(a, b):
        return NOT_ADJACENT
    for side_a, side_b in _FACING_SIDES:
        segment_a = a.side(side_a)
        segment_b = b.side(side_b)
        shared = intersect_segments(segment_a, segment_b)
        if not isinstance(shared, Segment):
            continue  # nothing shared, or only a single point
        if shared == segment_a and shared == segment_b:
            kind = AdjacencyType.PROPER
        elif shared == segment_a or shared == segment_b:
            kind = AdjacencyType.SUB_LINE
        else:
            kind = AdjacencyType.PARTIAL
        return AdjacencyResult(True, kind, shared, side_a, side_b)
    return NOT_ADJACENT


def is_adjacent(a: Rectangle, b: Rectangle) -> bool:
    """Convenience wrapper: True if ``a`` and ``b`` are adjacent."""
    return find_adjacency(a, b).adjacent
