"""Tests for rectangles.analysis (the combined report and its output formats)."""

from __future__ import annotations

import json
import unittest
from fractions import Fraction

from rectangles import Rectangle, Relation, analyze
from rectangles.analysis import RELATION_TEXT

R = Rectangle


class DescribeTest(unittest.TestCase):
    """The exact text printed by the command line tool."""

    def test_intersecting(self) -> None:
        expected = "\n".join(
            [
                "A: [(0, 0) -> (4, 4)]",
                "B: [(2, 2) -> (6, 6)]",
                "Relation: intersecting (their sides cross)",
                "",
                "Intersection: yes",
                "  points:   (2, 4), (4, 2)",
                "  segments: none",
                "Containment: no",
                "Adjacency: no",
            ]
        )
        self.assertEqual(analyze(R(0, 0, 4, 4), R(2, 2, 6, 6)).describe(), expected)

    def test_intersecting_with_a_shared_segment(self) -> None:
        text = analyze(R(0, 0, 10, 10), R(5, 0, 15, 5)).describe()
        self.assertIn("  points:   (10, 5)", text)
        self.assertIn("  segments: (5, 0) -> (10, 0)", text)

    def test_adjacent(self) -> None:
        text = analyze(R(0, 0, 8, 8), R(8, 5, 12, 11)).describe()
        self.assertIn("Relation: adjacent (they share part of a side)", text)
        self.assertIn(
            "Adjacency: yes, partial (A's right side and B's left side share (8, 5) -> (8, 8))",
            text,
        )
        self.assertIn("Intersection: no", text)
        self.assertNotIn("Shared boundary", text)

    def test_containment_lines(self) -> None:
        self.assertIn(
            "Containment: yes, A contains B",
            analyze(R(0, 0, 10, 8), R(3, 4, 7, 6)).describe(),
        )
        self.assertIn(
            "Containment: yes, B contains A",
            analyze(R(3, 4, 7, 6), R(0, 0, 10, 8)).describe(),
        )
        self.assertIn(
            "Containment: yes, A and B are identical (each contains the other)",
            analyze(R(0, 0, 4, 4), R(0, 0, 4, 4)).describe(),
        )

    def test_shared_boundary_line_for_touching_and_flush_cases(self) -> None:
        touching = analyze(R(0, 0, 4, 4), R(4, 4, 8, 8)).describe()
        self.assertIn("Relation: touching (they share only a corner point)", touching)
        self.assertTrue(touching.endswith("Shared boundary: (4, 4)"))
        flush = analyze(R(0, 0, 10, 10), R(0, 2, 4, 6)).describe()
        self.assertTrue(flush.endswith("Shared boundary: (0, 2) -> (0, 6)"))
        strictly_inside = analyze(R(0, 0, 10, 8), R(3, 4, 7, 6)).describe()
        self.assertNotIn("Shared boundary", strictly_inside)


class ToDictTest(unittest.TestCase):
    def test_structure(self) -> None:
        data = analyze(R(0, 0, 8, 8), R(8, 0, 12, 8)).to_dict()
        self.assertEqual(
            data,
            {
                "a": {"left": 0, "bottom": 0, "right": 8, "top": 8},
                "b": {"left": 8, "bottom": 0, "right": 12, "top": 8},
                "relation": "adjacent",
                "intersection": {"intersects": False, "points": [], "segments": []},
                "containment": {"a_contains_b": False, "b_contains_a": False},
                "adjacency": {
                    "adjacent": True,
                    "kind": "proper",
                    "shared_segment": [[8, 0], [8, 8]],
                    "side_of_a": "right",
                    "side_of_b": "left",
                },
                "boundary_contact": {"points": [], "segments": [[[8, 0], [8, 8]]]},
            },
        )

    def test_is_json_serialisable_even_with_fractions(self) -> None:
        report = analyze(R(Fraction(1, 2), 0, Fraction(4, 2), 1), R(1, 0, 3, 1))
        data = json.loads(json.dumps(report.to_dict()))
        self.assertEqual(data["a"], {"left": 0.5, "bottom": 0, "right": 2, "top": 1})
        self.assertEqual(data["relation"], "intersecting")


class RelationTest(unittest.TestCase):
    def test_every_relation_has_a_description(self) -> None:
        self.assertEqual(set(RELATION_TEXT), set(Relation))

    def test_each_relation(self) -> None:
        cases = [
            (R(0, 0, 5, 4), R(6, 0, 11, 4), Relation.DISJOINT),
            (R(0, 0, 4, 4), R(4, 4, 8, 8), Relation.TOUCHING),
            (R(0, 0, 8, 8), R(8, 0, 12, 8), Relation.ADJACENT),
            (R(0, 0, 4, 4), R(2, 2, 6, 6), Relation.INTERSECTING),
            (R(0, 0, 10, 8), R(3, 4, 7, 6), Relation.A_CONTAINS_B),
            (R(3, 4, 7, 6), R(0, 0, 10, 8), Relation.B_CONTAINS_A),
            (R(0, 0, 4, 4), R(0, 0, 4, 4), Relation.EQUAL),
        ]
        for a, b, expected in cases:
            with self.subTest(expected=expected):
                self.assertIs(analyze(a, b).relation, expected)


if __name__ == "__main__":
    unittest.main()
