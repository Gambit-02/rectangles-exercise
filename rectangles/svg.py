"""Render a pair of rectangles and their relationship as a standalone SVG."""

from __future__ import annotations

from xml.sax.saxutils import escape

from .analysis import RELATION_TEXT, RelationshipReport, analyze
from .geometry import Number, Rectangle

COLOR_A = "#1f77b4"
COLOR_B = "#ff7f0e"
COLOR_HIT = "#d62728"
MIN_WIDTH = 460.0


def render_svg(
    a: Rectangle,
    b: Rectangle,
    report: RelationshipReport | None = None,
    title: str | None = None,
    size: int = 360,
) -> str:
    """Return an SVG document (as a string) that draws ``a``, ``b`` and the
    geometry found by the analysis (intersection points, shared segments)."""
    if report is None:
        report = analyze(a, b)
    margin = 30
    header = 40
    min_x = min(a.left, b.left)
    max_x = max(a.right, b.right)
    min_y = min(a.bottom, b.bottom)
    max_y = max(a.top, b.top)
    span = max(max_x - min_x, max_y - min_y)
    scale = (size - 2 * margin) / span
    # Keep a minimum width so long titles are never clipped.
    width = max(float((max_x - min_x) * scale + 2 * margin), MIN_WIDTH)
    height = float((max_y - min_y) * scale + 2 * margin + header)

    def sx(x: Number) -> float:  # world x -> svg x
        return round(float((x - min_x) * scale + margin), 2)

    def sy(y: Number) -> float:  # world y -> svg y (svg y grows downward, so flip)
        return round(float((max_y - y) * scale + margin + header), 2)

    def rect(r: Rectangle, color: str, label: str) -> str:
        w = round(float(r.width * scale), 2)
        h = round(float(r.height * scale), 2)
        x, y = sx(r.left), sy(r.top)
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" '
            f'fill-opacity="0.25" stroke="{color}" stroke-width="2"/>'
            f'<text x="{x + 4}" y="{y + 14}" font-size="12" fill="{color}">{label}</text>'
        )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{round(width)}" height="{round(height)}" '
        f'viewBox="0 0 {round(width, 2)} {round(height, 2)}" font-family="sans-serif">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{margin}" y="20" font-size="14" font-weight="bold">'
        f"{escape(title or 'Rectangles')}</text>",
        f'<text x="{margin}" y="36" font-size="12">{escape(RELATION_TEXT[report.relation])}</text>',
        rect(a, COLOR_A, "A"),
        rect(b, COLOR_B, "B"),
    ]
    # Highlight every place where the two boundaries meet: crossing points,
    # shared edges of adjacent rectangles, a touching corner, flush edges.
    for seg in report.contact.segments:
        x1, y1, x2, y2 = sx(seg.start.x), sy(seg.start.y), sx(seg.end.x), sy(seg.end.y)
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{COLOR_HIT}" stroke-width="5" stroke-linecap="round"/>'
        )
    for p in report.contact.points:
        parts.append(f'<circle cx="{sx(p.x)}" cy="{sy(p.y)}" r="5" fill="{COLOR_HIT}"/>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
