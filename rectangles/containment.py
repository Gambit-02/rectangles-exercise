"""Containment: is one rectangle wholly inside another?"""

from __future__ import annotations

from .geometry import Rectangle


def contains(outer: Rectangle, inner: Rectangle) -> bool:
    """True if ``inner`` lies wholly within ``outer``.

    Containment is *inclusive*: ``inner`` may touch or share edges with
    ``outer``, and every rectangle contains itself.

    >>> contains(Rectangle(0, 0, 10, 10), Rectangle(2, 2, 4, 4))
    True
    >>> contains(Rectangle(0, 0, 10, 10), Rectangle(0, 2, 4, 4))   # flush with the left edge
    True
    >>> contains(Rectangle(2, 2, 4, 4), Rectangle(0, 0, 10, 10))   # the other way round
    False
    """
    return (
        outer.left <= inner.left
        and inner.right <= outer.right
        and outer.bottom <= inner.bottom
        and inner.top <= outer.top
    )


def strictly_contains(outer: Rectangle, inner: Rectangle) -> bool:
    """True if ``inner`` lies inside ``outer`` without touching its boundary.

    >>> strictly_contains(Rectangle(0, 0, 10, 10), Rectangle(2, 2, 4, 4))
    True
    >>> strictly_contains(Rectangle(0, 0, 10, 10), Rectangle(0, 2, 4, 4))
    False
    """
    return (
        outer.left < inner.left
        and inner.right < outer.right
        and outer.bottom < inner.bottom
        and inner.top < outer.top
    )
