"""Named example pairs: the spec's appendix diagrams plus edge cases."""

from __future__ import annotations

from dataclasses import dataclass

from .analysis import Relation
from .geometry import Rectangle


@dataclass(frozen=True)
class Scenario:
    name: str
    title: str
    source: str
    a: Rectangle
    b: Rectangle
    expected: Relation


R = Rectangle

APPENDIX_SCENARIOS = (
    Scenario(
        "appendix1-intersection",
        "Intersection",
        "Appendix 1",
        R(0, 4, 10, 10),
        R(4, 1, 9, 7),
        Relation.INTERSECTING,
    ),
    Scenario(
        "appendix1-no-intersection",
        "No Intersection",
        "Appendix 1",
        R(0, 0, 5, 4),
        R(6, 0, 11, 4),
        Relation.DISJOINT,
    ),
    Scenario(
        "appendix2-containment",
        "Containment",
        "Appendix 2",
        R(0, 0, 10, 8),
        R(3, 4, 7, 6),
        Relation.A_CONTAINS_B,
    ),
    Scenario(
        "appendix2-no-containment",
        "No Containment",
        "Appendix 2",
        R(0, 0, 10, 8),
        R(11, 3, 16, 5),
        Relation.DISJOINT,
    ),
    Scenario(
        "appendix2-intersection-no-containment",
        "Intersection - No Containment",
        "Appendix 2",
        R(0, 0, 10, 8),
        R(8, 2, 13, 4),
        Relation.INTERSECTING,
    ),
    Scenario(
        "appendix3-adjacent-sub-line",
        "Adjacent (Sub-line)",
        "Appendix 3",
        R(0, 0, 8, 8),
        R(8, 5, 14, 7),
        Relation.ADJACENT,
    ),
    Scenario(
        "appendix3-adjacent-proper",
        "Adjacent (Proper)",
        "Appendix 3",
        R(0, 0, 8, 8),
        R(8, 0, 12, 8),
        Relation.ADJACENT,
    ),
    Scenario(
        "appendix3-adjacent-partial",
        "Adjacent (Partial)",
        "Appendix 3",
        R(0, 0, 8, 8),
        R(8, 5, 12, 11),
        Relation.ADJACENT,
    ),
    Scenario(
        "appendix3-not-adjacent",
        "Not adjacent",
        "Appendix 3",
        R(0, 0, 8, 8),
        R(10, 2, 14, 4),
        Relation.DISJOINT,
    ),
)

EDGE_CASE_SCENARIOS = (
    Scenario(
        "edge-corner-touch",
        "Corners touch at a single point",
        "Edge case",
        R(0, 0, 4, 4),
        R(4, 4, 8, 8),
        Relation.TOUCHING,
    ),
    Scenario(
        "edge-flush-containment",
        "Contained, flush with one edge",
        "Edge case",
        R(0, 0, 10, 10),
        R(0, 2, 4, 6),
        Relation.A_CONTAINS_B,
    ),
    Scenario(
        "edge-corner-containment",
        "Contained, tucked into a corner",
        "Edge case",
        R(0, 0, 10, 10),
        R(0, 0, 4, 4),
        Relation.A_CONTAINS_B,
    ),
    Scenario(
        "edge-b-contains-a",
        "B contains A",
        "Edge case",
        R(3, 4, 7, 6),
        R(0, 0, 10, 8),
        Relation.B_CONTAINS_A,
    ),
    Scenario(
        "edge-identical",
        "Identical rectangles",
        "Edge case",
        R(0, 0, 4, 4),
        R(0, 0, 4, 4),
        Relation.EQUAL,
    ),
    Scenario(
        "edge-cross",
        "Cross shape (four crossing points)",
        "Edge case",
        R(0, 4, 10, 6),
        R(4, 0, 6, 10),
        Relation.INTERSECTING,
    ),
    Scenario(
        "edge-overlap-shared-edge",
        "Overlapping with a shared edge piece",
        "Edge case",
        R(0, 0, 10, 10),
        R(5, 0, 15, 5),
        Relation.INTERSECTING,
    ),
    Scenario(
        "edge-overlap-collinear-sides",
        "Overlapping strips with collinear sides",
        "Edge case",
        R(0, 0, 10, 10),
        R(0, 5, 10, 15),
        Relation.INTERSECTING,
    ),
    Scenario(
        "edge-sub-line-flush-end",
        "Sub-line share that starts at a corner",
        "Edge case",
        R(0, 0, 8, 8),
        R(8, 0, 12, 4),
        Relation.ADJACENT,
    ),
    Scenario(
        "edge-adjacent-vertical",
        "Adjacent above (top meets bottom)",
        "Edge case",
        R(0, 0, 8, 4),
        R(2, 4, 6, 9),
        Relation.ADJACENT,
    ),
)

ALL_SCENARIOS = APPENDIX_SCENARIOS + EDGE_CASE_SCENARIOS
