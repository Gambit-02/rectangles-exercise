"""Tests for the SVG renderer."""

from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from fractions import Fraction

from rectangles import Rectangle
from rectangles.scenarios import ALL_SCENARIOS
from rectangles.svg import MIN_WIDTH, render_svg

NS = "{http://www.w3.org/2000/svg}"
BY_NAME = {s.name: s for s in ALL_SCENARIOS}

# scenario name -> (number of highlighted lines, number of highlighted dots)
EXPECTED_MARKS = {
    "appendix1-intersection": (0, 2),
    "appendix2-containment": (0, 0),
    "appendix3-adjacent-proper": (1, 0),
    "edge-cross": (0, 4),
    "edge-identical": (4, 0),
    "edge-overlap-shared-edge": (1, 1),
    "edge-corner-touch": (0, 1),
    "edge-flush-containment": (1, 0),
}


class RenderSvgTest(unittest.TestCase):
    def test_every_scenario_renders_valid_svg(self) -> None:
        for s in ALL_SCENARIOS:
            with self.subTest(s.name):
                svg = render_svg(s.a, s.b, title=s.title)
                root = ET.fromstring(svg)
                self.assertEqual(root.tag, NS + "svg")
                self.assertEqual(len(root.findall(NS + "rect")), 3)  # background, A, B
                self.assertGreaterEqual(float(root.get("width")), MIN_WIDTH)

    def test_highlights_match_the_shared_boundary(self) -> None:
        for name, (lines, dots) in EXPECTED_MARKS.items():
            with self.subTest(name):
                root = ET.fromstring(render_svg(BY_NAME[name].a, BY_NAME[name].b))
                self.assertEqual(len(root.findall(NS + "line")), lines)
                self.assertEqual(len(root.findall(NS + "circle")), dots)

    def test_y_axis_points_up(self) -> None:
        # A sits higher than B in world coordinates, so it must have the
        # smaller SVG y value (SVG's y axis points down).
        s = BY_NAME["appendix1-intersection"]
        background, rect_a, rect_b = ET.fromstring(render_svg(s.a, s.b)).findall(NS + "rect")
        self.assertLess(float(rect_a.get("y")), float(rect_b.get("y")))

    def test_title_is_escaped(self) -> None:
        svg = render_svg(Rectangle(0, 0, 1, 1), Rectangle(2, 2, 3, 3), title="A & B <test>")
        ET.fromstring(svg)  # would raise if the text were not escaped
        self.assertNotIn("<test>", svg)

    def test_fraction_coordinates(self) -> None:
        a = Rectangle(Fraction(1, 2), 0, 1, 1)
        b = Rectangle(Fraction(3, 4), Fraction(1, 3), 2, 2)
        ET.fromstring(render_svg(a, b))


if __name__ == "__main__":
    unittest.main()
