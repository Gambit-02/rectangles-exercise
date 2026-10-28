"""Tests for rectangles.containment."""

from __future__ import annotations

import unittest

from rectangles import Rectangle, contains, strictly_contains

R = Rectangle

# (name, outer, inner, contains(outer, inner), strictly_contains(outer, inner),
#  contains(inner, outer))
CASES = [
    ("strictly inside", R(0, 0, 10, 10), R(2, 2, 4, 4), True, True, False),
    ("flush with one edge", R(0, 0, 10, 10), R(0, 2, 4, 6), True, False, False),
    ("tucked into a corner", R(0, 0, 10, 10), R(0, 0, 4, 4), True, False, False),
    ("identical rectangles", R(0, 0, 4, 4), R(0, 0, 4, 4), True, False, True),
    ("arguments reversed", R(2, 2, 4, 4), R(0, 0, 10, 10), False, False, True),
    ("partial overlap", R(0, 0, 4, 4), R(2, 2, 6, 6), False, False, False),
    ("disjoint", R(0, 0, 4, 4), R(5, 5, 6, 6), False, False, False),
    ("adjacent", R(0, 0, 8, 8), R(8, 0, 12, 8), False, False, False),
    ("cross shape", R(0, 4, 10, 6), R(4, 0, 6, 10), False, False, False),
    ("sticks out by one unit", R(0, 0, 10, 10), R(2, 2, 11, 4), False, False, False),
    ("floats", R(0, 0, 1, 1), R(0.25, 0.25, 0.75, 0.75), True, True, False),
]


class ContainmentTest(unittest.TestCase):
    def test_cases(self) -> None:
        for name, outer, inner, expect, expect_strict, expect_reverse in CASES:
            with self.subTest(name):
                self.assertEqual(contains(outer, inner), expect)
                self.assertEqual(strictly_contains(outer, inner), expect_strict)
                self.assertEqual(contains(inner, outer), expect_reverse)

    def test_every_rectangle_contains_itself_but_not_strictly(self) -> None:
        r = R(-3, -3, 3, 3)
        self.assertTrue(contains(r, r))
        self.assertFalse(strictly_contains(r, r))


if __name__ == "__main__":
    unittest.main()
