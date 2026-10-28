"""Every diagram in the assignment's appendix, plus named edge cases."""

from __future__ import annotations

import unittest

from rectangles import AdjacencyType, analyze
from rectangles.scenarios import ALL_SCENARIOS, APPENDIX_SCENARIOS, EDGE_CASE_SCENARIOS

# name -> (intersection points, intersection segments, adjacency kind, shared segment)
DETAILS = {
    "appendix1-intersection": ([(4, 4), (9, 4)], [], None, None),
    "appendix1-no-intersection": ([], [], None, None),
    "appendix2-containment": ([], [], None, None),
    "appendix2-no-containment": ([], [], None, None),
    "appendix2-intersection-no-containment": ([(10, 2), (10, 4)], [], None, None),
    "appendix3-adjacent-sub-line": ([], [], AdjacencyType.SUB_LINE, ((8, 5), (8, 7))),
    "appendix3-adjacent-proper": ([], [], AdjacencyType.PROPER, ((8, 0), (8, 8))),
    "appendix3-adjacent-partial": ([], [], AdjacencyType.PARTIAL, ((8, 5), (8, 8))),
    "appendix3-not-adjacent": ([], [], None, None),
    "edge-corner-touch": ([], [], None, None),
    "edge-flush-containment": ([], [], None, None),
    "edge-corner-containment": ([], [], None, None),
    "edge-b-contains-a": ([], [], None, None),
    "edge-identical": ([], [], None, None),
    "edge-cross": ([(4, 4), (4, 6), (6, 4), (6, 6)], [], None, None),
    "edge-overlap-shared-edge": ([(10, 5)], [((5, 0), (10, 0))], None, None),
    "edge-overlap-collinear-sides": ([], [((0, 5), (0, 10)), ((10, 5), (10, 10))], None, None),
    "edge-sub-line-flush-end": ([], [], AdjacencyType.SUB_LINE, ((8, 0), (8, 4))),
    "edge-adjacent-vertical": ([], [], AdjacencyType.SUB_LINE, ((2, 4), (6, 4))),
}


class ScenarioTest(unittest.TestCase):
    def test_counts_and_unique_names(self) -> None:
        self.assertEqual(len(APPENDIX_SCENARIOS), 9)
        self.assertEqual(len(EDGE_CASE_SCENARIOS), 10)
        names = [s.name for s in ALL_SCENARIOS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), set(DETAILS))

    def test_each_scenario_has_the_expected_relation(self) -> None:
        for s in ALL_SCENARIOS:
            with self.subTest(s.name):
                self.assertIs(analyze(s.a, s.b).relation, s.expected)

    def test_each_scenario_in_detail(self) -> None:
        for s in ALL_SCENARIOS:
            points, segments, kind, shared = DETAILS[s.name]
            with self.subTest(s.name):
                report = analyze(s.a, s.b)
                self.assertEqual([(p.x, p.y) for p in report.intersection.points], points)
                self.assertEqual(
                    [
                        ((g.start.x, g.start.y), (g.end.x, g.end.y))
                        for g in report.intersection.segments
                    ],
                    segments,
                )
                self.assertIs(report.adjacency.kind, kind)
                found = report.adjacency.shared_segment
                if shared is None:
                    self.assertIsNone(found)
                else:
                    self.assertEqual(
                        ((found.start.x, found.start.y), (found.end.x, found.end.y)), shared
                    )


if __name__ == "__main__":
    unittest.main()
