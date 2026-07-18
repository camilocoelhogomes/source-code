"""Testes unitários — modelos frozen FileToIndex / ExactMatch / ExactSearchQuery (T10)."""

from __future__ import annotations

import dataclasses
import unittest

from github_rag.index.zoekt.models import ExactMatch, ExactSearchQuery, FileToIndex


class TestFileToIndex(unittest.TestCase):
    def test_holds_fields(self) -> None:
        f = FileToIndex(
            repository="acme/api",
            path="src/main.py",
            commit="abc123",
            content=b"x = 1\n",
        )
        self.assertEqual(f.repository, "acme/api")
        self.assertEqual(f.path, "src/main.py")
        self.assertEqual(f.commit, "abc123")
        self.assertEqual(f.content, b"x = 1\n")

    def test_is_frozen(self) -> None:
        f = FileToIndex(
            repository="acme/api",
            path="a.py",
            commit="c1",
            content=b"",
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            f.path = "b.py"  # type: ignore[misc]


class TestExactMatch(unittest.TestCase):
    def test_line_number_defaults_to_none(self) -> None:
        m = ExactMatch(
            repository="acme/api",
            path="a.py",
            commit="abc123",
            snippet="needle",
        )
        self.assertIsNone(m.line_number)
        self.assertEqual(m.snippet, "needle")

    def test_is_frozen(self) -> None:
        m = ExactMatch(
            repository="acme/api",
            path="a.py",
            commit="abc123",
            snippet="x",
            line_number=3,
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            m.snippet = "y"  # type: ignore[misc]


class TestExactSearchQuery(unittest.TestCase):
    def test_defaults(self) -> None:
        q = ExactSearchQuery(pattern="def authenticate")
        self.assertEqual(q.pattern, "def authenticate")
        self.assertIsNone(q.repository)
        self.assertIsNone(q.path_prefix)
        self.assertIsNone(q.max_matches)
        self.assertEqual(q.context_lines, 2)

    def test_is_frozen(self) -> None:
        q = ExactSearchQuery(pattern="x")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            q.pattern = "y"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
