"""Tests for the command line interface."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from rectangles import Rectangle
from rectangles.cli import main, parse_rectangle

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cli(*argv: str) -> tuple[int, str, str]:
    """Run main() in process and capture (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(list(argv))
        except SystemExit as exit_:
            code = exit_.code
    return code, out.getvalue(), err.getvalue()


class ParseRectangleTest(unittest.TestCase):
    def test_valid_inputs(self) -> None:
        self.assertEqual(parse_rectangle("0,0,4,3"), Rectangle(0, 0, 4, 3))
        self.assertEqual(parse_rectangle("4,3,0,0"), Rectangle(0, 0, 4, 3))
        self.assertEqual(parse_rectangle(" 0.5, 1, 2 ,3 "), Rectangle(0.5, 1, 2, 3))
        self.assertEqual(parse_rectangle("-1,-1,2,2"), Rectangle(-1, -1, 2, 2))

    def test_invalid_inputs(self) -> None:
        for text in ["0,0,4", "0,0,4,3,9", "a,b,c,d", "0,0,0,4", "nan,0,1,1", ""]:
            with self.subTest(text=text), self.assertRaises(argparse.ArgumentTypeError):
                parse_rectangle(text)


class AnalyzeCommandTest(unittest.TestCase):
    def test_text_output(self) -> None:
        code, out, _ = run_cli("analyze", "0,0,4,4", "2,2,6,6")
        self.assertEqual(code, 0)
        self.assertEqual(
            out,
            "A: [(0, 0) -> (4, 4)]\n"
            "B: [(2, 2) -> (6, 6)]\n"
            "Relation: intersecting (their sides cross)\n"
            "\n"
            "Intersection: yes\n"
            "  points:   (2, 4), (4, 2)\n"
            "  segments: none\n"
            "Containment: no\n"
            "Adjacency: no\n",
        )

    def test_json_output(self) -> None:
        code, out, _ = run_cli("analyze", "--json", "0,0,4,4", "2,2,6,6")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["relation"], "intersecting")
        self.assertEqual(data["intersection"]["points"], [[2, 4], [4, 2]])

    def test_negative_coordinates_after_double_dash(self) -> None:
        code, out, _ = run_cli("analyze", "--", "-1,-1,2,2", "0,0,3,3")
        self.assertEqual(code, 0)
        self.assertIn("  points:   (0, 2), (2, 0)", out)

    def test_svg_option_writes_a_picture(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "pair.svg")
            code, _, _ = run_cli("analyze", "0,0,4,4", "2,2,6,6", "--svg", path)
            self.assertEqual(code, 0)
            root = ET.parse(path).getroot()
            self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")

    def test_bad_input_exits_with_code_2(self) -> None:
        for argv in [("analyze", "0,0,4", "1,1,2,2"), ("analyze", "0,0,4,4"), ()]:
            with self.subTest(argv=argv):
                code, _, err = run_cli(*argv)
                self.assertEqual(code, 2)
                self.assertIn("error", err)


class DemoAndGalleryTest(unittest.TestCase):
    def test_demo_text(self) -> None:
        code, out, _ = run_cli("demo")
        self.assertEqual(code, 0)
        self.assertEqual(out.count("=== "), 19)
        self.assertTrue(out.startswith("=== Appendix 1: Intersection ===\n"))

    def test_demo_json(self) -> None:
        code, out, _ = run_cli("demo", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(len(data), 19)
        self.assertEqual(data[0]["name"], "appendix1-intersection")
        self.assertEqual(data[0]["relation"], "intersecting")

    def test_gallery_writes_one_svg_per_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "images")
            code, out, _ = run_cli("gallery", target)
            self.assertEqual(code, 0)
            files = sorted(os.listdir(target))
            self.assertEqual(len(files), 19)
            self.assertIn("appendix3-adjacent-partial.svg", files)
            self.assertEqual(len(out.splitlines()), 19)


class ModuleEntryPointTest(unittest.TestCase):
    def test_python_dash_m_works(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "rectangles", "analyze", "0,0,8,8", "8,0,12,8"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "Adjacency: yes, proper (A's right side and B's left side share (8, 0) -> (8, 8))",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
