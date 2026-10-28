"""Command line interface: ``python3 -m rectangles <command> ...``."""

from __future__ import annotations

import argparse
import json
import os
import sys

from .analysis import analyze
from .geometry import Rectangle
from .scenarios import ALL_SCENARIOS
from .svg import render_svg


def parse_rectangle(text: str) -> Rectangle:
    """Parse ``"x1,y1,x2,y2"`` (two opposite corners) into a Rectangle."""
    pieces = [piece.strip() for piece in text.split(",")]
    if len(pieces) != 4:
        raise argparse.ArgumentTypeError(
            f"expected 4 comma separated numbers like 0,0,4,3 but got {text!r}"
        )
    try:
        x1, y1, x2, y2 = (_parse_number(piece) for piece in pieces)
        return Rectangle.from_corners((x1, y1), (x2, y2))
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid rectangle {text!r}: {error}") from None


def _parse_number(text: str) -> int | float:
    try:
        return int(text)
    except ValueError:
        return float(text)  # raises ValueError for junk such as "abc"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rectangles",
        description="Analyze intersection, containment and adjacency of two rectangles.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser(
        "analyze",
        help="analyze one pair of rectangles",
        epilog="If a rectangle starts with a minus sign, put -- before the rectangles, "
        "for example: rectangles analyze -- -1,-1,2,2 0,0,3,3",
    )
    p_analyze.add_argument("a", type=parse_rectangle, help="rectangle A as x1,y1,x2,y2")
    p_analyze.add_argument("b", type=parse_rectangle, help="rectangle B as x1,y1,x2,y2")
    p_analyze.add_argument("--json", action="store_true", help="print JSON instead of text")
    p_analyze.add_argument("--svg", metavar="FILE", help="also write a picture of the pair")

    p_demo = sub.add_parser("demo", help="analyze the built in example scenarios")
    p_demo.add_argument("--json", action="store_true", help="print JSON instead of text")

    p_gallery = sub.add_parser("gallery", help="write an SVG for every built in scenario")
    p_gallery.add_argument("directory", help="output directory (created if missing)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``python3 -m rectangles`` and the ``rectangles`` command."""
    args = build_parser().parse_args(argv)
    try:
        return _run(args)
    except BrokenPipeError:
        # The output was piped into a program such as "head" that stopped
        # reading early. Send the rest of our output to /dev/null instead of
        # printing a traceback (the approach recommended in the Python docs).
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 1


def _run(args: argparse.Namespace) -> int:
    """Carry out the chosen subcommand and return the exit code."""
    if args.command == "analyze":
        report = analyze(args.a, args.b)
        print(json.dumps(report.to_dict(), indent=2) if args.json else report.describe())
        if args.svg:
            with open(args.svg, "w", encoding="utf-8") as handle:
                handle.write(render_svg(args.a, args.b, report))
        return 0

    if args.command == "demo":
        if args.json:
            payload = [
                {
                    "name": s.name,
                    "title": s.title,
                    "source": s.source,
                    **analyze(s.a, s.b).to_dict(),
                }
                for s in ALL_SCENARIOS
            ]
            print(json.dumps(payload, indent=2))
        else:
            for s in ALL_SCENARIOS:
                print(f"=== {s.source}: {s.title} ===")
                print(analyze(s.a, s.b).describe())
                print()
        return 0

    if args.command == "gallery":
        os.makedirs(args.directory, exist_ok=True)
        for s in ALL_SCENARIOS:
            path = os.path.join(args.directory, f"{s.name}.svg")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(render_svg(s.a, s.b, title=f"{s.source}: {s.title}"))
            print(path)
        return 0

    return 2  # pragma: no cover (argparse enforces a valid command)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
