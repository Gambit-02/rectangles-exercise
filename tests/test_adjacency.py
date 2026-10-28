"""Tests for rectangles.adjacency."""

from __future__ import annotations

import unittest

from rectangles import AdjacencyType, Rectangle, Side, find_adjacency, is_adjacent

R = Rectangle
PROPER, SUB_LINE, PARTIAL = AdjacencyType.PROPER, AdjacencyType.SUB_LINE, AdjacencyType.PARTIAL
LEFT, RIGHT, TOP, BOTTOM = Side.LEFT, Side.RIGHT, Side.TOP, Side.BOTTOM

# (name, a, b, kind, shared segment, side of a, side of b)
ADJACENT = [
    (
        "proper, B to the right",
        R(0, 0, 8, 8),
        R(8, 0, 12, 8),
        PROPER,
        ((8, 0), (8, 8)),
        RIGHT,
        LEFT,
    ),
    ("proper, B to the left", R(8, 0, 12, 8), R(0, 0, 8, 8), PROPER, ((8, 0), (8, 8)), LEFT, RIGHT),
    ("proper, B above", R(0, 0, 4, 4), R(0, 4, 4, 9), PROPER, ((0, 4), (4, 4)), TOP, BOTTOM),
    ("proper, B below", R(0, 4, 4, 9), R(0, 0, 4, 4), PROPER, ((0, 4), (4, 4)), BOTTOM, TOP),
    (
        "sub-line (appendix 3)",
        R(0, 0, 8, 8),
        R(8, 5, 14, 7),
        SUB_LINE,
        ((8, 5), (8, 7)),
        RIGHT,
        LEFT,
    ),
    ("sub-line, reversed", R(8, 5, 14, 7), R(0, 0, 8, 8), SUB_LINE, ((8, 5), (8, 7)), LEFT, RIGHT),
    (
        "sub-line from a corner",
        R(0, 0, 8, 8),
        R(8, 0, 12, 4),
        SUB_LINE,
        ((8, 0), (8, 4)),
        RIGHT,
        LEFT,
    ),
    (
        "sub-line, A's top inside B",
        R(2, 0, 6, 4),
        R(0, 4, 8, 6),
        SUB_LINE,
        ((2, 4), (6, 4)),
        TOP,
        BOTTOM,
    ),
    (
        "partial (appendix 3)",
        R(0, 0, 8, 8),
        R(8, 5, 12, 11),
        PARTIAL,
        ((8, 5), (8, 8)),
        RIGHT,
        LEFT,
    ),
    ("partial, B lower", R(0, 0, 8, 8), R(8, -3, 12, 2), PARTIAL, ((8, 0), (8, 2)), RIGHT, LEFT),
    (
        "floats",
        R(0, 0, 1.5, 1),
        R(1.5, 0.25, 3, 0.75),
        SUB_LINE,
        ((1.5, 0.25), (1.5, 0.75)),
        RIGHT,
        LEFT,
    ),
]

# (name, a, b): pairs that are not adjacent
NOT_ADJACENT = [
    ("corners touch at one point", R(0, 0, 4, 4), R(4, 4, 8, 8)),
    ("small gap", R(0, 0, 8, 8), R(9, 0, 12, 8)),
    ("on the same line but not touching", R(0, 0, 4, 4), R(4, 5, 8, 9)),
    ("contained, flush with an edge", R(0, 0, 10, 10), R(0, 2, 4, 6)),
    ("overlapping with a shared edge piece", R(0, 0, 10, 10), R(5, 0, 15, 5)),
    ("identical", R(0, 0, 4, 4), R(0, 0, 4, 4)),
    ("appendix 3 not adjacent", R(0, 0, 8, 8), R(10, 2, 14, 4)),
]


class AdjacencyTest(unittest.TestCase):
    def test_adjacent_pairs(self) -> None:
        for name, a, b, kind, shared, side_a, side_b in ADJACENT:
            with self.subTest(name):
                result = find_adjacency(a, b)
                self.assertTrue(result.adjacent)
                self.assertTrue(is_adjacent(a, b))
                self.assertIs(result.kind, kind)
                segment = result.shared_segment
                self.assertEqual(
                    ((segment.start.x, segment.start.y), (segment.end.x, segment.end.y)), shared
                )
                self.assertIs(result.side_of_a, side_a)
                self.assertIs(result.side_of_b, side_b)

    def test_adjacency_is_symmetric(self) -> None:
        for name, a, b, *_ in ADJACENT:
            with self.subTest(name):
                forward, backward = find_adjacency(a, b), find_adjacency(b, a)
                self.assertIs(forward.kind, backward.kind)
                self.assertEqual(forward.shared_segment, backward.shared_segment)
                self.assertIs(forward.side_of_a, backward.side_of_b)

    def test_pairs_that_are_not_adjacent(self) -> None:
        for name, a, b in NOT_ADJACENT:
            with self.subTest(name):
                result = find_adjacency(a, b)
                self.assertFalse(result.adjacent)
                self.assertFalse(is_adjacent(a, b))
                self.assertIsNone(result.kind)
                self.assertIsNone(result.shared_segment)


if __name__ == "__main__":
    unittest.main()
