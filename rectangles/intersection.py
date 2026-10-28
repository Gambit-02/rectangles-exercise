"""Intersection: where do the sides of two rectangles cross?"""

from __future__ import annotations

from dataclasses import dataclass

from .containment import contains
from .geometry import Point, Rectangle, Segment, interiors_overlap, intersect_segments


@dataclass(frozen=True)
class BoundaryContact:
    """The exact set of points shared by the boundaries of two rectangles.

    The set is described by ``segments`` (pieces where sides lie on top of each
    other) plus ``points`` (isolated points that are not on any of those
    segments).  Both tuples are sorted, so results are deterministic.
    """

    points: tuple[Point, ...]
    segments: tuple[Segment, ...]

    @property
    def is_empty(self) -> bool:
        return not self.points and not self.segments


@dataclass(frozen=True)
class IntersectionResult:
    """Answer to "do the two rectangles intersect, and where?".

    ``points`` and ``segments`` are empty whenever ``intersects`` is False.
    """

    intersects: bool
    points: tuple[Point, ...] = ()
    segments: tuple[Segment, ...] = ()


NO_INTERSECTION = IntersectionResult(intersects=False)


def boundary_contact(a: Rectangle, b: Rectangle) -> BoundaryContact:
    """Compute every point where a side of ``a`` meets a side of ``b``.

    This is pure geometry with no interpretation: touching corners, shared
    edges and true crossings are all reported.  It checks each of the 4 sides
    of ``a`` against each of the 4 sides of ``b`` (16 constant time checks).

    >>> c = boundary_contact(Rectangle(0, 0, 4, 4), Rectangle(2, 2, 6, 6))
    >>> [str(p) for p in c.points], c.segments
    (['(2, 4)', '(4, 2)'], ())
    """
    points: set[Point] = set()
    segments: set[Segment] = set()
    for _, side_a in a.sides():
        for _, side_b in b.sides():
            shared = intersect_segments(side_a, side_b)
            if isinstance(shared, Segment):
                segments.add(shared)
            elif isinstance(shared, Point):
                points.add(shared)
    # A corner where two shared segments meet (or the end of a shared segment)
    # is already described by the segment, so do not list it twice.
    isolated = {p for p in points if not any(s.contains_point(p) for s in segments)}
    return BoundaryContact(
        points=tuple(sorted(isolated)),
        segments=tuple(sorted(segments, key=lambda s: (s.start, s.end))),
    )


def intersects(a: Rectangle, b: Rectangle) -> bool:
    """True if the sides of ``a`` and ``b`` cross each other.

    That happens exactly when the rectangles overlap with positive area but
    neither one contains the other.  Rectangles that only touch (adjacent or
    corner to corner) or that are nested do not intersect.

    >>> intersects(Rectangle(0, 0, 4, 4), Rectangle(2, 2, 6, 6))
    True
    >>> intersects(Rectangle(0, 0, 4, 4), Rectangle(4, 0, 8, 4))   # adjacent
    False
    >>> intersects(Rectangle(0, 0, 10, 10), Rectangle(2, 2, 4, 4))  # contained
    False
    """
    return interiors_overlap(a, b) and not contains(a, b) and not contains(b, a)


def find_intersection(a: Rectangle, b: Rectangle) -> IntersectionResult:
    """Return whether ``a`` and ``b`` intersect and the points of intersection.

    >>> result = find_intersection(Rectangle(0, 0, 4, 4), Rectangle(2, 2, 6, 6))
    >>> result.intersects, [str(p) for p in result.points]
    (True, ['(2, 4)', '(4, 2)'])
    """
    if not intersects(a, b):
        return NO_INTERSECTION
    contact = boundary_contact(a, b)
    return IntersectionResult(True, contact.points, contact.segments)
