"""Unit — env_loader (T29)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from github_rag.e2e.env_loader import load_dotenv_file, parse_dotenv_text


class TestParseDotenvText(unittest.TestCase):
    def test_index_cron_with_spaces(self) -> None:
        self.assertEqual(parse_dotenv_text("INDEX_CRON=0 2 * * *\n")["INDEX_CRON"], "0 2 * * *")

    def test_quoted_value(self) -> None:
        self.assertEqual(parse_dotenv_text('KEY="quoted value"\n')["KEY"], "quoted value")

    def test_comments_ignored(self) -> None:
        self.assertEqual(parse_dotenv_text("# c\n\nFOO=bar\n"), {"FOO": "bar"})


class TestLoadDotenvFile(unittest.TestCase):
    def test_missing_file_noop(self) -> None:
        env: dict[str, str] = {"EXISTING": "1"}
        self.assertEqual(load_dotenv_file("/nonexistent/.env", environ=env), {})
        self.assertEqual(env, {"EXISTING": "1"})

    def test_no_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / ".env"
            p.write_text("FOO=from_file\nBAR=baz\n", encoding="utf-8")
            env: dict[str, str] = {"FOO": "existing"}
            load_dotenv_file(p, environ=env)
            self.assertEqual(env["FOO"], "existing")
            self.assertEqual(env["BAR"], "baz")
