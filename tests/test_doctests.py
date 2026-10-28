"""Run the examples written in the docstrings as tests, so docs never go stale."""

import doctest
import unittest

from rectangles import adjacency, analysis, containment, geometry, intersection


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
    for module in (geometry, containment, intersection, adjacency, analysis):
        tests.addTests(doctest.DocTestSuite(module))
    return tests
