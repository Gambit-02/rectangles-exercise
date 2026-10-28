"""One call that runs all three analyses and classifies the pair."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any

from .adjacency import AdjacencyResult, find_adjacency
from .containment import contains
from .geometry import Number, Point, Rectangle, Segment
from .intersection import BoundaryContact, IntersectionResult, boundary_contact, find_intersection


class Relation(Enum):
    """Exactly one of these describes any pair of rectangles (A, B)."""

    DISJOINT = "disjoint"
    TOUCHING = "touching"
    ADJACENT = "adjacent"
    INTERSECTING = "intersecting"
    A_CONTAINS_B = "a_contains_b"
    B_CONTAINS_A = "b_contains_a"
    EQUAL = "equal"


RELATION_TEXT = {
    Relation.DISJOINT: "disjoint (no shared points)",
    Relation.TOUCHING: "touching (they share only a corner point)",
    Relation.ADJACENT: "adjacent (they share part of a side)",
    Relation.INTERSECTING: "intersecting (their sides cross)",
    Relation.A_CONTAINS_B: "A contains B",
    Relation.B_CONTAINS_A: "B contains A",
    Relation.EQUAL: "equal (identical rectangles)",
}


# Relations where the boundaries may touch without "intersecting"; for these the
# text report adds a "Shared boundary" line so the contact is still visible.
_SHOW_CONTACT_FOR = (
    Relation.TOUCHING,
    Relation.A_CONTAINS_B,
    Relation.B_CONTAINS_A,
    Relation.EQUAL,
)


@dataclass(frozen=True)
class RelationshipReport:
    a: Rectangle
    b: Rectangle
    relation: Relation
    intersection: IntersectionResult
    a_contains_b: bool
    b_contains_a: bool
    adjacency: AdjacencyResult
    contact: BoundaryContact

    def describe(self) -> str:
        """Human readable, multi line summary used by the command line tool."""
        lines = [
            f"A: {self.a}",
            f"B: {self.b}",
            f"Relation: {RELATION_TEXT[self.relation]}",
            "",
        ]
        if self.intersection.intersects:
            lines.append("Intersection: yes")
            lines.append(f"  points:   {_join(self.intersection.points)}")
            lines.append(f"  segments: {_join(self.intersection.segments)}")
        else:
            lines.append("Intersection: no")

        if self.a_contains_b and self.b_contains_a:
            lines.append("Containment: yes, A and B are identical (each contains the other)")
        elif self.a_contains_b:
            lines.append("Containment: yes, A contains B")
        elif self.b_contains_a:
            lines.append("Containment: yes, B contains A")
        else:
            lines.append("Containment: no")

        adj = self.adjacency
        if adj.adjacent:
            assert adj.kind and adj.side_of_a and adj.side_of_b
            lines.append(
                f"Adjacency: yes, {adj.kind.value} "
                f"(A's {adj.side_of_a.value} side and B's {adj.side_of_b.value} side "
                f"share {adj.shared_segment})"
            )
        else:
            lines.append("Adjacency: no")

        if self.relation in _SHOW_CONTACT_FOR and not self.contact.is_empty:
            pieces = [str(s) for s in self.contact.segments] + [str(p) for p in self.contact.points]
            lines.append(f"Shared boundary: {', '.join(pieces)}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """JSON friendly representation (used by ``--json``)."""
        adj = self.adjacency
        return {
            "a": _rect_dict(self.a),
            "b": _rect_dict(self.b),
            "relation": self.relation.value,
            "intersection": {
                "intersects": self.intersection.intersects,
                "points": [_point_list(p) for p in self.intersection.points],
                "segments": [_segment_list(s) for s in self.intersection.segments],
            },
            "containment": {
                "a_contains_b": self.a_contains_b,
                "b_contains_a": self.b_contains_a,
            },
            "adjacency": {
                "adjacent": adj.adjacent,
                "kind": adj.kind.value if adj.kind else None,
                "shared_segment": _segment_list(adj.shared_segment) if adj.shared_segment else None,
                "side_of_a": adj.side_of_a.value if adj.side_of_a else None,
                "side_of_b": adj.side_of_b.value if adj.side_of_b else None,
            },
            "boundary_contact": {
                "points": [_point_list(p) for p in self.contact.points],
                "segments": [_segment_list(s) for s in self.contact.segments],
            },
        }


def analyze(a: Rectangle, b: Rectangle) -> RelationshipReport:
    """Run intersection, containment and adjacency and classify the pair.

    >>> analyze(Rectangle(0, 0, 4, 4), Rectangle(2, 2, 6, 6)).relation
    <Relation.INTERSECTING: 'intersecting'>
    """
    intersection = find_intersection(a, b)
    contact = boundary_contact(a, b)
    a_contains_b = contains(a, b)
    b_contains_a = contains(b, a)
    adjacency = find_adjacency(a, b)

    if a_contains_b and b_contains_a:
        relation = Relation.EQUAL
    elif a_contains_b:
        relation = Relation.A_CONTAINS_B
    elif b_contains_a:
        relation = Relation.B_CONTAINS_A
    elif intersection.intersects:
        relation = Relation.INTERSECTING
    elif adjacency.adjacent:
        relation = Relation.ADJACENT
    elif not contact.is_empty:
        relation = Relation.TOUCHING
    else:
        relation = Relation.DISJOINT

    return RelationshipReport(
        a, b, relation, intersection, a_contains_b, b_contains_a, adjacency, contact
    )


# ---- small formatting helpers -----------------------------------------
def _join(items: Any) -> str:
    return ", ".join(str(item) for item in items) if items else "none"


def _json_number(value: Number) -> Any:
    if isinstance(value, Fraction):
        return int(value) if value.denominator == 1 else float(value)
    return value


def _point_list(p: Point) -> list[Any]:
    return [_json_number(p.x), _json_number(p.y)]


def _segment_list(s: Segment | None) -> list[Any] | None:
    if s is None:
        return None
    return [_point_list(s.start), _point_list(s.end)]


def _rect_dict(r: Rectangle) -> dict[str, Any]:
    return {
        "left": _json_number(r.left),
        "bottom": _json_number(r.bottom),
        "right": _json_number(r.right),
        "top": _json_number(r.top),
    }
