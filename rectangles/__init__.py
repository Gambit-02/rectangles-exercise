"""rectangles: intersection, containment and adjacency of axis aligned rectangles."""

from .adjacency import AdjacencyResult, AdjacencyType, find_adjacency, is_adjacent
from .analysis import Relation, RelationshipReport, analyze
from .containment import contains, strictly_contains
from .geometry import Point, Rectangle, Segment, Side, interiors_overlap, intersect_segments
from .intersection import (
    BoundaryContact,
    IntersectionResult,
    boundary_contact,
    find_intersection,
    intersects,
)

__all__ = [
    "AdjacencyResult",
    "AdjacencyType",
    "BoundaryContact",
    "IntersectionResult",
    "Point",
    "Rectangle",
    "Relation",
    "RelationshipReport",
    "Segment",
    "Side",
    "analyze",
    "boundary_contact",
    "contains",
    "find_adjacency",
    "find_intersection",
    "interiors_overlap",
    "intersect_segments",
    "intersects",
    "is_adjacent",
    "strictly_contains",
]
__version__ = "1.0.0"
