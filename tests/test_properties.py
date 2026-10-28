"""Property based and exhaustive tests.

The core idea: for rectangles with small integer coordinates, the exact answer
to every question can be computed by brute force on a fine grid of points.
These tests check the real implementation against that independent "oracle"
for every possible pair of rectangles on a 5 x 5 grid (10,000 ordered pairs).

Why a doubled grid?  All interesting geometry (corners, crossing points, the
ends of shared segments) lands on integer coordinates when the inputs are
integers.  Sampling at half steps (coordinates times 2) additionally lets the
oracle tell "a shared segment from (0,0) to (1,0)" apart from "two separate
points (0,0) and (1,0)", because the segment also contains (0.5, 0).
"""

from __future__ import annotations

import itertools
import random
import unittest

from rectangles import (
    AdjacencyType,
    BoundaryContact,
    Rectangle,
    Relation,
    Side,
    analyze,
    boundary_contact,
    contains,
    find_adjacency,
    find_intersection,
    interiors_overlap,
    intersects,
)

GRID_MAX = 4  # coordinates 0..4  ->  100 rectangles  ->  10,000 ordered pairs


# ---- brute force oracle helpers (doubled integer grid) --------------------
def boundary_points(r: Rectangle) -> frozenset[tuple[int, int]]:
    left, bottom, right, top = 2 * r.left, 2 * r.bottom, 2 * r.right, 2 * r.top
    points = set()
    for x in range(left, right + 1):
        points.add((x, bottom))
        points.add((x, top))
    for y in range(bottom, top + 1):
        points.add((left, y))
        points.add((right, y))
    return frozenset(points)


def closed_points(r: Rectangle) -> frozenset[tuple[int, int]]:
    return frozenset(
        (x, y)
        for x in range(2 * r.left, 2 * r.right + 1)
        for y in range(2 * r.bottom, 2 * r.top + 1)
    )


def interior_points(r: Rectangle) -> frozenset[tuple[int, int]]:
    return frozenset(
        (x, y)
        for x in range(2 * r.left + 1, 2 * r.right)
        for y in range(2 * r.bottom + 1, 2 * r.top)
    )


def side_point_sets(r: Rectangle) -> list[frozenset[tuple[int, int]]]:
    left, bottom, right, top = 2 * r.left, 2 * r.bottom, 2 * r.right, 2 * r.top
    return [
        frozenset((x, bottom) for x in range(left, right + 1)),
        frozenset((x, top) for x in range(left, right + 1)),
        frozenset((left, y) for y in range(bottom, top + 1)),
        frozenset((right, y) for y in range(bottom, top + 1)),
    ]


def rasterize(contact: BoundaryContact) -> frozenset[tuple[int, int]]:
    """Turn a result (points + segments) into doubled grid points."""
    points = {(2 * p.x, 2 * p.y) for p in contact.points}
    for s in contact.segments:
        if s.is_horizontal:
            points.update((x, 2 * s.start.y) for x in range(2 * s.start.x, 2 * s.end.x + 1))
        else:
            points.update((2 * s.start.x, y) for y in range(2 * s.start.y, 2 * s.end.y + 1))
    return frozenset(points)


def all_grid_rectangles(n: int = GRID_MAX) -> list[Rectangle]:
    coords = range(n + 1)
    return [
        Rectangle(left, bottom, right, top)
        for left, right in itertools.combinations(coords, 2)
        for bottom, top in itertools.combinations(coords, 2)
    ]


class ExhaustiveOracleTest(unittest.TestCase):
    """Every ordered pair of rectangles on the grid, checked against brute force."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rects = all_grid_rectangles()
        cls.cache = {
            r: (boundary_points(r), closed_points(r), interior_points(r), side_point_sets(r))
            for r in cls.rects
        }

    def test_grid_size(self) -> None:
        self.assertEqual(len(self.rects), 100)

    def test_every_pair_matches_the_oracle(self) -> None:
        for a in self.rects:
            for b in self.rects:
                boundary_a, closed_a, interior_a, sides_a = self.cache[a]
                boundary_b, closed_b, interior_b, sides_b = self.cache[b]
                truth = boundary_a & boundary_b
                overlap = bool(interior_a & interior_b)
                a_has_b = closed_b <= closed_a
                b_has_a = closed_a <= closed_b
                expect_intersects = overlap and not a_has_b and not b_has_a
                expect_adjacent = not overlap and len(truth) >= 2

                # 1. boundary_contact is exactly the shared boundary
                contact = boundary_contact(a, b)
                self.assertEqual(rasterize(contact), truth, (a, b))
                self.assertEqual(list(contact.points), sorted(set(contact.points)))
                for p in contact.points:
                    self.assertFalse(any(s.contains_point(p) for s in contact.segments))

                # 2. containment and interior overlap
                self.assertEqual(contains(a, b), a_has_b, (a, b))
                self.assertEqual(interiors_overlap(a, b), overlap, (a, b))

                # 3. intersection
                self.assertEqual(intersects(a, b), expect_intersects, (a, b))
                result = find_intersection(a, b)
                self.assertEqual(result.intersects, expect_intersects)
                if expect_intersects:
                    found = BoundaryContact(result.points, result.segments)
                    self.assertEqual(rasterize(found), truth)
                else:
                    self.assertEqual((result.points, result.segments), ((), ()))

                # 4. adjacency and its kind
                adjacency = find_adjacency(a, b)
                self.assertEqual(adjacency.adjacent, expect_adjacent, (a, b))
                if expect_adjacent:
                    full_side_a = truth in sides_a
                    full_side_b = truth in sides_b
                    if full_side_a and full_side_b:
                        expected_kind = AdjacencyType.PROPER
                    elif full_side_a or full_side_b:
                        expected_kind = AdjacencyType.SUB_LINE
                    else:
                        expected_kind = AdjacencyType.PARTIAL
                    self.assertEqual(adjacency.kind, expected_kind, (a, b))
                    shared = BoundaryContact((), (adjacency.shared_segment,))
                    self.assertEqual(rasterize(shared), truth)

                # 5. overall relation
                if a_has_b and b_has_a:
                    expected_relation = Relation.EQUAL
                elif a_has_b:
                    expected_relation = Relation.A_CONTAINS_B
                elif b_has_a:
                    expected_relation = Relation.B_CONTAINS_A
                elif expect_intersects:
                    expected_relation = Relation.INTERSECTING
                elif expect_adjacent:
                    expected_relation = Relation.ADJACENT
                elif truth:
                    expected_relation = Relation.TOUCHING
                else:
                    expected_relation = Relation.DISJOINT
                self.assertEqual(analyze(a, b).relation, expected_relation, (a, b))


_MIRROR = {
    Relation.A_CONTAINS_B: Relation.B_CONTAINS_A,
    Relation.B_CONTAINS_A: Relation.A_CONTAINS_B,
}
_TRANSPOSE_SIDE = {
    Side.LEFT: Side.BOTTOM,
    Side.BOTTOM: Side.LEFT,
    Side.RIGHT: Side.TOP,
    Side.TOP: Side.RIGHT,
}


def _transpose(r: Rectangle) -> Rectangle:
    """Mirror across the line y = x (swap the roles of x and y)."""
    return Rectangle(r.bottom, r.left, r.top, r.right)


class InvariantTest(unittest.TestCase):
    """Properties that must hold for any pair, checked on random pairs."""

    def setUp(self) -> None:
        rng = random.Random(485)  # fixed seed: the test is deterministic
        self.pairs = []
        for _ in range(2000):
            coords = [rng.randint(-6, 6) for _ in range(8)]
            try:
                a = Rectangle.from_corners(coords[0:2], coords[2:4])
                b = Rectangle.from_corners(coords[4:6], coords[6:8])
            except ValueError:
                continue  # skip zero width / zero height draws
            self.pairs.append((a, b))
        self.assertGreater(len(self.pairs), 1000)

    def test_swapping_arguments(self) -> None:
        for a, b in self.pairs:
            forward, backward = analyze(a, b), analyze(b, a)
            self.assertEqual(_MIRROR.get(forward.relation, forward.relation), backward.relation)
            self.assertEqual(forward.intersection, backward.intersection)
            self.assertEqual(forward.adjacency.kind, backward.adjacency.kind)
            self.assertEqual(forward.adjacency.shared_segment, backward.adjacency.shared_segment)
            self.assertEqual(forward.adjacency.side_of_a, backward.adjacency.side_of_b)

    def test_translation_does_not_change_the_answer(self) -> None:
        dx, dy = 17, -23
        for a, b in self.pairs:
            moved_a = Rectangle(a.left + dx, a.bottom + dy, a.right + dx, a.top + dy)
            moved_b = Rectangle(b.left + dx, b.bottom + dy, b.right + dx, b.top + dy)
            original, moved = analyze(a, b), analyze(moved_a, moved_b)
            self.assertEqual(original.relation, moved.relation)
            self.assertEqual(
                [(p.x + dx, p.y + dy) for p in original.intersection.points],
                [(p.x, p.y) for p in moved.intersection.points],
            )
            self.assertEqual(original.adjacency.kind, moved.adjacency.kind)

    def test_transposing_does_not_change_the_answer(self) -> None:
        for a, b in self.pairs:
            original, flipped = analyze(a, b), analyze(_transpose(a), _transpose(b))
            self.assertEqual(original.relation, flipped.relation)
            self.assertEqual(
                sorted((p.y, p.x) for p in original.intersection.points),
                [(p.x, p.y) for p in flipped.intersection.points],
            )
            self.assertEqual(original.adjacency.kind, flipped.adjacency.kind)
            if original.adjacency.adjacent:
                self.assertEqual(
                    _TRANSPOSE_SIDE[original.adjacency.side_of_a], flipped.adjacency.side_of_a
                )

    def test_exactly_one_feature_family_applies(self) -> None:
        for a, b in self.pairs:
            report = analyze(a, b)
            flags = [
                report.intersection.intersects,
                report.a_contains_b or report.b_contains_a,
                report.adjacency.adjacent,
            ]
            self.assertLessEqual(sum(flags), 1, (a, b))


if __name__ == "__main__":
    unittest.main()
