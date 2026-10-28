"""Tests for rectangles.intersection."""

from __future__ import annotations

import unittest
from fractions import Fraction as F

from rectangles import Rectangle, boundary_contact, find_intersection, intersects

R = Rectangle


def as_tuples(result):
    """Convert points and segments into plain tuples for easy comparison."""
    points = [(p.x, p.y) for p in result.points]
    segments = [((s.start.x, s.start.y), (s.end.x, s.end.y)) for s in result.segments]
    return points, segments


# (name, a, b, expected points, expected segments)
INTERSECTING = [
    ("corner overlap", R(0, 0, 4, 4), R(2, 2, 6, 6), [(2, 4), (4, 2)], []),
    ("appendix 1 drawing", R(0, 4, 10, 10), R(4, 1, 9, 7), [(4, 4), (9, 4)], []),
    ("pokes out of one side", R(0, 0, 10, 8), R(8, 2, 13, 4), [(10, 2), (10, 4)], []),
    ("cross shape", R(0, 4, 10, 6), R(4, 0, 6, 10), [(4, 4), (4, 6), (6, 4), (6, 6)], []),
    ("T shape", R(0, 0, 10, 10), R(2, 5, 8, 15), [(2, 10), (8, 10)], []),
    (
        "band through the middle",
        R(0, 0, 10, 10),
        R(-5, 4, 15, 6),
        [(0, 4), (0, 6), (10, 4), (10, 6)],
        [],
    ),
    ("corner poked in", R(0, 0, 10, 10), R(8, 8, 12, 12), [(8, 10), (10, 8)], []),
    ("shared edge piece", R(0, 0, 10, 10), R(5, 0, 15, 5), [(10, 5)], [((5, 0), (10, 0))]),
    (
        "collinear sides",
        R(0, 0, 10, 10),
        R(0, 5, 10, 15),
        [],
        [((0, 5), (0, 10)), ((10, 5), (10, 10))],
    ),
    ("negative coordinates", R(-5, -5, 0, 0), R(-2, -2, 3, 3), [(-2, 0), (0, -2)], []),
    ("floats", R(0.5, 0.5, 2.5, 2.5), R(1.5, 1.5, 3.5, 3.5), [(1.5, 2.5), (2.5, 1.5)], []),
    (
        "fractions",
        R(F(1, 2), F(1, 2), F(5, 2), F(5, 2)),
        R(F(3, 2), F(3, 2), F(7, 2), F(7, 2)),
        [(F(3, 2), F(5, 2)), (F(5, 2), F(3, 2))],
        [],
    ),
]

# (name, a, b): pairs whose sides do not cross
NOT_INTERSECTING = [
    ("disjoint", R(0, 0, 5, 4), R(6, 0, 11, 4)),
    ("strictly contained", R(0, 0, 10, 10), R(2, 2, 4, 4)),
    ("contained, flush with an edge", R(0, 0, 10, 10), R(0, 2, 4, 6)),
    ("B contains A", R(3, 4, 7, 6), R(0, 0, 10, 8)),
    ("identical", R(0, 0, 4, 4), R(0, 0, 4, 4)),
    ("adjacent", R(0, 0, 8, 8), R(8, 0, 12, 8)),
    ("corners touch", R(0, 0, 4, 4), R(4, 4, 8, 8)),
]


class FindIntersectionTest(unittest.TestCase):
    def test_intersecting_pairs(self) -> None:
        for name, a, b, points, segments in INTERSECTING:
            with self.subTest(name):
                self.assertTrue(intersects(a, b))
                result = find_intersection(a, b)
                self.assertTrue(result.intersects)
                self.assertEqual(as_tuples(result), (points, segments))

    def test_order_of_arguments_does_not_matter(self) -> None:
        for name, a, b, _, _ in INTERSECTING:
            with self.subTest(name):
                self.assertEqual(find_intersection(a, b), find_intersection(b, a))

    def test_non_intersecting_pairs_have_no_points(self) -> None:
        for name, a, b in NOT_INTERSECTING:
            with self.subTest(name):
                self.assertFalse(intersects(a, b))
                self.assertFalse(intersects(b, a))
                result = find_intersection(a, b)
                self.assertFalse(result.intersects)
                self.assertEqual(result.points, ())
                self.assertEqual(result.segments, ())


# (name, a, b, expected points, expected segments)
CONTACT = [
    ("corner touch", R(0, 0, 4, 4), R(4, 4, 8, 8), [(4, 4)], []),
    ("flush containment", R(0, 0, 10, 10), R(0, 2, 4, 6), [], [((0, 2), (0, 6))]),
    (
        "corner containment",
        R(0, 0, 10, 10),
        R(0, 0, 4, 4),
        [],
        [((0, 0), (0, 4)), ((0, 0), (4, 0))],
    ),
    (
        "identical",
        R(0, 0, 4, 4),
        R(0, 0, 4, 4),
        [],
        [((0, 0), (0, 4)), ((0, 0), (4, 0)), ((0, 4), (4, 4)), ((4, 0), (4, 4))],
    ),
    ("adjacent", R(0, 0, 8, 8), R(8, 0, 12, 8), [], [((8, 0), (8, 8))]),
    ("strictly contained", R(0, 0, 10, 10), R(2, 2, 4, 4), [], []),
    ("disjoint", R(0, 0, 5, 4), R(6, 0, 11, 4), [], []),
    ("shared edge piece", R(0, 0, 10, 10), R(5, 0, 15, 5), [(10, 5)], [((5, 0), (10, 0))]),
]


class BoundaryContactTest(unittest.TestCase):
    def test_cases(self) -> None:
        for name, a, b, points, segments in CONTACT:
            with self.subTest(name):
                contact = boundary_contact(a, b)
                self.assertEqual(as_tuples(contact), (points, segments))
                self.assertEqual(contact.is_empty, not points and not segments)

    def test_points_on_a_shared_segment_are_not_repeated(self) -> None:
        # (5, 0) and (10, 0) are corners where sides meet, but they already lie
        # on the shared segment, so only the true crossing (10, 5) is listed.
        contact = boundary_contact(R(0, 0, 10, 10), R(5, 0, 15, 5))
        self.assertEqual([(p.x, p.y) for p in contact.points], [(10, 5)])


if __name__ == "__main__":
    unittest.main()
