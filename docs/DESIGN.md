# Design notes

This document explains the decisions behind the code: what each feature means precisely, why it was defined that way, how each algorithm works and why it is correct, and how the tests establish that.

## 1. Goals and non goals

**Goals**

* Answer the three questions in the assignment (intersection, containment, adjacency) for any pair of axis aligned rectangles, with exact results.
* Make every ambiguous case an explicit, documented, tested decision.
* Run anywhere Python 3.10+ runs, with zero dependencies.
* Stay small and readable: each feature fits on one screen.

**Non goals**

* Rotated rectangles or general polygons.
* Degenerate rectangles (zero width or height).
* Large scale batch processing of many rectangles (discussed in section 9).

## 2. Model

### Representation

A `Rectangle` stores its four edges: `left, bottom, right, top`, with `left < right` and `bottom < top`. I chose edges over `x, y, width, height` because every algorithm then becomes a pure comparison of edges, with no additions such as `x + width`. The other form is still accepted through `Rectangle.from_origin_size(x, y, width, height)`, and `Rectangle.from_corners(p1, p2)` accepts any two opposite corners in any order.

The coordinate system is mathematical (y grows upward). Every algorithm is symmetric, so screen coordinates (y grows downward) give the same answers; only the words "top" and "bottom" swap.

Rectangles are **closed**: the four sides belong to the rectangle. The **interior** is the rectangle without its sides; the **boundary** is the four sides.

### Validation

The constructor rejects:

* zero or negative width or height (`ValueError`): a degenerate rectangle is a line or a point, and every definition below would need special cases;
* `nan` and infinities (`ValueError`);
* anything that is not a real number (`TypeError`), including `bool` (in Python `True == 1`, so a boolean coordinate is almost certainly a bug), strings, `None`, and `Decimal` (which is not part of Python's `numbers.Real` hierarchy and does not compare cleanly with floats).

### Immutability

`Point`, `Segment`, `Rectangle` and all result types are frozen dataclasses. They are hashable (usable in sets and as dictionary keys), compare by value, and can never be changed after validation, so a rectangle that passed validation stays valid.

`Segment.__post_init__` normalizes its endpoints so that `start < end`. Because the dataclass is frozen, it has to use `object.__setattr__` to do that. Normalizing means two segments covering the same points always compare equal, which the adjacency classification relies on.

### Exactness

The algorithms only compare coordinates and take minimums and maximums. They never compute new coordinates with arithmetic. Every point or segment endpoint they return is made of input coordinates, so there is no rounding error and no need for an epsilon. Results are exact for `int`, `float` and `Fraction` inputs. (Only `width`, `height`, `area` and the SVG drawing do arithmetic.)

## 3. Semantics contract

| Name | Function | Rule |
|---|---|---|
| Boundary contact | `boundary_contact(a, b)` | The exact set of points the two boundaries share: a sorted tuple of shared segments plus a sorted tuple of isolated points not lying on those segments. No interpretation. |
| Interiors overlap | `interiors_overlap(a, b)` | `a.left < b.right and b.left < a.right and a.bottom < b.top and b.bottom < a.top` (the overlap has positive area). |
| Containment | `contains(outer, inner)` | `outer.left <= inner.left and inner.right <= outer.right and outer.bottom <= inner.bottom and inner.top <= outer.top`. `strictly_contains` uses `<` everywhere. |
| Intersection | `intersects(a, b)`, `find_intersection(a, b)` | Interiors overlap and neither contains the other. When true, the result's points and segments are the boundary contact; when false, both are empty. |
| Adjacency | `find_adjacency(a, b)` | Interiors do not overlap and a side of A shares a segment of positive length with a side of B. Proper: the segment equals both sides. Sub-line: it equals exactly one side. Partial: neither. |
| Relation | `analyze(a, b).relation` | The first that applies of: `EQUAL`, `A_CONTAINS_B`, `B_CONTAINS_A`, `INTERSECTING`, `ADJACENT`, `TOUCHING` (boundaries share only a corner point), `DISJOINT`. |

Intersection, containment and adjacency are mutually exclusive: containment implies the interiors overlap (so not adjacent) and excludes intersection by definition; adjacency requires the interiors not to overlap (so not intersecting).

## 4. Decision log

1. **Nested rectangles do not intersect.** The assignment says intersection is about "intersecting lines", and Appendix 2 labels a nested rectangle "Containment" but a rectangle poking through the edge "Intersection - No Containment". So intersection must be about sides crossing, not areas overlapping. A plain bounding box overlap test would wrongly report nested rectangles as intersecting.
2. **Flush containment is containment, not adjacency.** If B sits inside A against A's left edge, B is still wholly within A. Read literally, "sharing at least one side" would also make it sub-line adjacent, but then a rectangle could be both inside and next to another, and every Appendix 3 drawing shows adjacent rectangles side by side. I treat adjacency the way people use the word for rooms or map regions: neighbors that do not overlap. The text report still prints the shared boundary, so the contact is visible.
3. **Adjacent rectangles do not intersect.** The assignment presents adjacency as its own feature. Two floor tiles touch but do not intersect. Counting a shared edge as an intersection would also mean "infinitely many points of intersection".
4. **Corner to corner contact is "touching".** A single point is not a line segment, so it is not a partial share. It is not a crossing either. The `TOUCHING` relation and the shared boundary line in the report make the contact visible without misclassifying it.
5. **Identical rectangles are `EQUAL`, and each contains the other.** This follows from inclusive containment. They are not reported as intersecting, consistent with decision 1.
6. **Overlapping rectangles can have segments in their intersection.** For A = (0,0,10,10) and B = (5,0,15,5) the bottoms lie on top of each other from (5,0) to (10,0), and the sides cross at (10,5). The exact answer is one segment plus one point, so the result type carries both. Listing only the segment's endpoints would lose information.
7. **A sub-line share that starts at a corner is still sub-line.** For A = (0,0,8,8) and B = (8,0,12,4), B's whole left side lies on A's right side, which is the definition of sub-line, even though the two shapes line up at the bottom.
8. **Degenerate rectangles are rejected** (see section 2).
9. **No tolerance for floating point.** Exactness (section 2) makes it unnecessary for this problem. If a client's data came from noisy measurements, a tolerance mode would be a deliberate change to the definitions, not a bug fix.
10. **Argument order:** intersection points, adjacency kind and shared segment do not depend on the order of the arguments. Containment and the relation mirror (`A_CONTAINS_B` becomes `B_CONTAINS_A`). Results are always sorted, so output is deterministic.

## 5. Algorithms and why they are correct

### Segment intersection

Every rectangle side is horizontal or vertical, so only three cases exist:

* **Both horizontal:** they can only meet if they share the same y. The common x range is `[max(starts), min(ends)]`. If `lo > hi` it is empty; if `lo == hi` they touch at one point; if `lo < hi` they overlap in a segment.
* **Both vertical:** the same with x and y swapped.
* **One of each:** the only possible meeting point is (x of the vertical, y of the horizontal), which counts if it lies within both segments.

### Boundary contact

Compare each of A's four sides with each of B's four sides: 16 constant time checks. Collect shared segments and points. Points that lie on a shared segment (for example the end of a shared edge) are removed, so each shared point is described exactly once and the representation is minimal. Both lists are sorted.

**At most four isolated points.** An isolated contact point lies in both rectangles and on a vertical side of one and a horizontal side of the other. Lying on a vertical side of B while being inside A forces its x to be either the larger of the two lefts or the smaller of the two rights; the same holds for y with bottoms and tops. So every such point is a corner of the overlap rectangle, and a rectangle has four corners. The cross shape reaches that maximum. (The exhaustive tests confirm it.)

### Intersection

`intersects(a, b)` is `interiors_overlap(a, b) and not contains(a, b) and not contains(b, a)`.

**Why this captures "the sides cross".** Suppose the interiors overlap and neither contains the other. B is not inside A, so B has a point outside A; B also has a point in A's interior. Moving between those two points inside B crosses A's boundary, so part of A's boundary lies in B. A is not inside B, so part of A's boundary lies outside B. A's boundary is one connected loop with points both in B and outside B, so it must meet B's boundary. Every other way for two boundaries to meet (touching corners, neighbors sharing an edge, a flush edge inside a container, identical rectangles) is classified separately, so "intersecting" is exactly the case where the sides pass through each other.

### Containment

Four comparisons (inclusive). `strictly_contains` uses strict comparisons and means "inside without touching".

### Adjacency

If the interiors overlap, the rectangles are not adjacent. Otherwise they are separated by a vertical or horizontal line (that is what "the x ranges or the y ranges do not overlap" means). Only the sides lying on that line can share points, and those are always a facing pair: A's right with B's left, A's left with B's right, A's top with B's bottom, or A's bottom with B's top. So checking those four pairs is enough, and at most one of them can share a segment. If it does, comparing the shared segment with each full side gives the kind: equal to both is proper, equal to exactly one is sub-line, equal to neither is partial.

### Relation

`analyze` evaluates the features and picks the first relation that applies in the order of section 3. Equality must come before containment (identical rectangles contain each other) and containment before intersection.

## 6. Complexity

Every function is O(1) in time and space for a pair of rectangles. `boundary_contact` does 16 segment checks; everything else is a handful of comparisons.

## 7. Testing strategy

* **Hand checked vectors** for each module, including every appendix diagram and every case in the decision log.
* **Exhaustive oracle.** For small integer coordinates, the true answer to every question can be computed by brute force: list every point of each rectangle on a grid and compare sets. The oracle does exactly that for all 10,000 ordered pairs on a 5 by 5 grid. It shares no logic with the library (point sets versus interval reasoning), so agreement is strong evidence of correctness. Coordinates are doubled before sampling: a shared segment from (0,0) to (1,0) then contains the grid point (0.5, 0), which two separate endpoints would not, so the oracle can tell them apart. For a small finite domain, checking everything beats random sampling because no case can be missed.
* **Invariants** on 2,000 seeded random pairs: swapping arguments mirrors the answer, translating both rectangles shifts the points, mirroring across y = x maps left/right sides to bottom/top sides.
* **Doctests** keep the examples in the docstrings honest.
* **CI** runs everything on Ubuntu with Python 3.10 to 3.13.

## 8. Architecture

* **Value object plus free functions.** `Rectangle` is a pure value object. Intersection, containment and adjacency are symmetric operations on two rectangles, so they live as functions in their own modules rather than as methods on one of the two rectangles. That keeps each feature in one short file with its own test file, and avoids circular imports.
* **Result objects instead of bare booleans.** The assignment asks for the points of intersection, and the adjacency kind is part of the answer, so results carry evidence. Plain booleans are still available: `intersects`, `contains`, `is_adjacent`.
* **`analyze` as a facade** that runs everything and produces the report, the text output and the JSON output.
* **Scenarios as data.** The appendix diagrams live in one table that drives the demo, the gallery images and the scenario tests, so they can never disagree.

## 9. How I would extend it

* **Rotated rectangles:** represent each rectangle by its four corners; detect overlap with the separating axis theorem; compute crossing points with segment intersection using orientation tests (cross products); adjacency becomes collinear overlap of sides. Arithmetic is now required, so a tolerance policy becomes necessary.
* **Many rectangles:** sort by left edge and sweep a vertical line across the plane, keeping active rectangles in an interval tree keyed on y, which finds all overlapping pairs in about O(n log n + k). A spatial index such as an R tree serves repeated queries.
* **A service:** wrap `analyze` in a small REST endpoint that accepts and returns the JSON format already produced by `to_dict()`, with the SVG renderer as a visual response.
