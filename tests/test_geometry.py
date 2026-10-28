"""Tests for the value types in rectangles.geometry."""

from __future__ import annotations

import dataclasses
import unittest
from decimal import Decimal
from fractions import Fraction

from rectangles import Point, Rectangle, Segment, Side, interiors_overlap, intersect_segments

P = Point
R = Rectangle


def seg(x1, y1, x2, y2) -> Segment:
    return Segment(P(x1, y1), P(x2, y2))


class PointTest(unittest.TestCase):
    def test_str(self) -> None:
        self.assertEqual(str(P(1, 2.5)), "(1, 2.5)")
        self.assertEqual(str(P(Fraction(1, 3), -2)), "(1/3, -2)")

    def test_points_sort_by_x_then_y(self) -> None:
        self.assertLess(P(0, 5), P(1, 0))
        self.assertLess(P(1, 0), P(1, 2))

    def test_int_and_float_points_are_equal(self) -> None:
        self.assertEqual(P(1, 2), P(1.0, 2.0))
        self.assertEqual(len({P(1, 2), P(1.0, 2.0)}), 1)


class SegmentTest(unittest.TestCase):
    def test_endpoints_are_normalised(self) -> None:
        s = seg(4, 0, 0, 0)
        self.assertEqual((s.start, s.end), (P(0, 0), P(4, 0)))
        self.assertEqual(seg(4, 0, 0, 0), seg(0, 0, 4, 0))

    def test_rejects_zero_length(self) -> None:
        with self.assertRaises(ValueError):
            seg(0, 0, 0, 0)

    def test_rejects_diagonal(self) -> None:
        with self.assertRaises(ValueError):
            seg(0, 0, 1, 1)

    def test_orientation(self) -> None:
        self.assertTrue(seg(0, 0, 4, 0).is_horizontal)
        self.assertFalse(seg(0, 0, 4, 0).is_vertical)
        self.assertTrue(seg(2, 0, 2, 5).is_vertical)

    def test_contains_point(self) -> None:
        s = seg(0, 0, 4, 0)
        self.assertTrue(s.contains_point(P(0, 0)))
        self.assertTrue(s.contains_point(P(4, 0)))
        self.assertTrue(s.contains_point(P(2.5, 0)))
        self.assertFalse(s.contains_point(P(2, 1)))
        self.assertFalse(s.contains_point(P(5, 0)))

    def test_str(self) -> None:
        self.assertEqual(str(seg(0, 0, 4, 0)), "(0, 0) -> (4, 0)")


class IntersectSegmentsTest(unittest.TestCase):
    CASES = [
        # (name, segment 1, segment 2, expected result)
        ("perpendicular crossing", seg(0, 2, 5, 2), seg(3, 0, 3, 9), P(3, 2)),
        ("perpendicular miss", seg(0, 2, 5, 2), seg(7, 0, 7, 9), None),
        ("perpendicular T at an endpoint", seg(0, 2, 5, 2), seg(5, 2, 5, 9), P(5, 2)),
        ("collinear overlap", seg(0, 0, 5, 0), seg(3, 0, 9, 0), seg(3, 0, 5, 0)),
        ("collinear end to end", seg(0, 0, 5, 0), seg(5, 0, 9, 0), P(5, 0)),
        ("collinear with a gap", seg(0, 0, 5, 0), seg(6, 0, 9, 0), None),
        ("parallel on different lines", seg(0, 0, 5, 0), seg(0, 1, 5, 1), None),
        ("vertical collinear overlap", seg(2, 0, 2, 5), seg(2, 3, 2, 9), seg(2, 3, 2, 5)),
        ("one segment inside the other", seg(0, 0, 9, 0), seg(2, 0, 4, 0), seg(2, 0, 4, 0)),
    ]

    def test_cases(self) -> None:
        for name, s1, s2, expected in self.CASES:
            with self.subTest(name):
                self.assertEqual(intersect_segments(s1, s2), expected)
                self.assertEqual(intersect_segments(s2, s1), expected)  # order does not matter


class RectangleConstructionTest(unittest.TestCase):
    def test_fields_and_derived_values(self) -> None:
        r = R(0, 0, 4, 3)
        self.assertEqual((r.left, r.bottom, r.right, r.top), (0, 0, 4, 3))
        self.assertEqual((r.width, r.height, r.area), (4, 3, 12))

    def test_invalid_rectangles_are_rejected(self) -> None:
        cases = [
            ((0, 0, 0, 4), ValueError),  # zero width
            ((0, 0, 4, 0), ValueError),  # zero height
            ((4, 0, 0, 4), ValueError),  # left greater than right
            ((float("nan"), 0, 1, 1), ValueError),
            ((0, 0, float("inf"), 1), ValueError),
            ((True, 0, 1, 1), TypeError),  # bool is not accepted as a number
            (("0", 0, 1, 1), TypeError),
            ((None, 0, 1, 1), TypeError),
            ((Decimal(0), 0, 1, 1), TypeError),  # Decimal is not a numbers.Real
        ]
        for args, error in cases:
            with self.subTest(args=args), self.assertRaises(error):
                R(*args)

    def test_from_corners_accepts_any_opposite_corners(self) -> None:
        expected = R(0, 0, 4, 3)
        self.assertEqual(R.from_corners((4, 3), (0, 0)), expected)
        self.assertEqual(R.from_corners((0, 3), (4, 0)), expected)
        self.assertEqual(R.from_corners(P(0, 0), P(4, 3)), expected)
        self.assertEqual(R.from_corners([0, 0], [4, 3]), expected)

    def test_from_corners_still_rejects_zero_area(self) -> None:
        with self.assertRaises(ValueError):
            R.from_corners((0, 0), (0, 5))

    def test_from_origin_size(self) -> None:
        self.assertEqual(R.from_origin_size(1, 2, 3, 4), R(1, 2, 4, 6))

    def test_fractions_are_supported(self) -> None:
        r = R(Fraction(1, 2), 0, 1, 1)
        self.assertEqual(r.width, Fraction(1, 2))


class RectangleBehaviourTest(unittest.TestCase):
    def setUp(self) -> None:
        self.r = R(0, 0, 4, 3)

    def test_corners_counter_clockwise_from_bottom_left(self) -> None:
        self.assertEqual(self.r.corners, (P(0, 0), P(4, 0), P(4, 3), P(0, 3)))

    def test_sides(self) -> None:
        self.assertEqual(self.r.side(Side.BOTTOM), seg(0, 0, 4, 0))
        self.assertEqual(self.r.side(Side.RIGHT), seg(4, 0, 4, 3))
        self.assertEqual(self.r.side(Side.TOP), seg(0, 3, 4, 3))
        self.assertEqual(self.r.side(Side.LEFT), seg(0, 0, 0, 3))
        self.assertEqual(
            [which for which, _ in self.r.sides()],
            [Side.BOTTOM, Side.RIGHT, Side.TOP, Side.LEFT],
        )

    def test_contains_point_is_inclusive(self) -> None:
        self.assertTrue(self.r.contains_point(P(0, 0)))  # corner
        self.assertTrue(self.r.contains_point(P(4, 1)))  # on the right side
        self.assertTrue(self.r.contains_point(P(2, 1.5)))  # inside
        self.assertFalse(self.r.contains_point(P(5, 1)))  # outside

    def test_is_immutable(self) -> None:
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.r.left = 5  # type: ignore[misc]

    def test_value_equality_and_hashing(self) -> None:
        self.assertEqual(R(0, 0, 1, 1), R(0.0, 0.0, 1.0, 1.0))
        self.assertEqual(len({R(0, 0, 1, 1), R(0.0, 0.0, 1.0, 1.0)}), 1)

    def test_str(self) -> None:
        self.assertEqual(str(self.r), "[(0, 0) -> (4, 3)]")


class InteriorsOverlapTest(unittest.TestCase):
    CASES = [
        ("partial overlap", R(0, 0, 4, 4), R(2, 2, 6, 6), True),
        ("contained", R(0, 0, 10, 10), R(2, 2, 4, 4), True),
        ("identical", R(0, 0, 4, 4), R(0, 0, 4, 4), True),
        ("adjacent (edge only)", R(0, 0, 4, 4), R(4, 0, 8, 4), False),
        ("corner touch", R(0, 0, 4, 4), R(4, 4, 8, 8), False),
        ("disjoint", R(0, 0, 4, 4), R(5, 5, 6, 6), False),
    ]

    def test_cases(self) -> None:
        for name, a, b, expected in self.CASES:
            with self.subTest(name):
                self.assertEqual(interiors_overlap(a, b), expected)
                self.assertEqual(interiors_overlap(b, a), expected)


if __name__ == "__main__":
    unittest.main()
