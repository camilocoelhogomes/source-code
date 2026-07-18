"""Testes unitários — FileEligibilityFilter / loader / rules (T09).

Extremos, corner cases e contratos conforme unit-test-plan v0.1.0.
"""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from github_rag.eligibility.filter import (
    EligibilityError,
    FileEligibilityFilter,
    PathspecFileEligibilityFilter,
)
from github_rag.eligibility.gitignore import GitignoreSource, load_gitignore_sources
from github_rag.eligibility.rules import (
    CSV_DENYLIST,
    DEFAULT_ELIGIBILITY_RULES,
    IMAGE_DENYLIST,
    EligibilityRules,
)


def _source(relative_dir: str, *lines: str) -> GitignoreSource:
    return GitignoreSource(relative_dir=relative_dir, lines=list(lines))


def _filt(rules: EligibilityRules | None = None) -> PathspecFileEligibilityFilter:
    return PathspecFileEligibilityFilter(rules=rules)


class TestInvalidPaths(unittest.TestCase):
    def test_u01_absolute_path_raises(self) -> None:
        with self.assertRaises(EligibilityError) as ctx:
            _filt().filter(["/abs/x.py"], [])
        self.assertIn("/abs/x.py", str(ctx.exception))

    def test_u02_parent_escape_raises(self) -> None:
        with self.assertRaises(EligibilityError) as ctx:
            _filt().filter(["../outside.py"], [])
        self.assertIn("../outside.py", str(ctx.exception))

    def test_u03_empty_path_raises(self) -> None:
        with self.assertRaises(EligibilityError):
            _filt().filter([""], [])

    def test_u04_dot_paths_raise(self) -> None:
        with self.assertRaises(EligibilityError):
            _filt().filter(["."], [])
        with self.assertRaises(EligibilityError):
            _filt().filter(["./"], [])


class TestNoGitignore(unittest.TestCase):
    def test_u05_empty_sources_type_rules_only(self) -> None:
        result = _filt().filter(
            ["src/App.java", "notes.md", "data.csv", "img/photo.jpg"],
            [],
        )
        self.assertEqual(result, ["src/App.java", "notes.md"])


class TestNestedGitignoreAndNegation(unittest.TestCase):
    def test_u06_nested_gitignore(self) -> None:
        sources = [
            _source("", "node_modules/"),
            _source("docs", "*.tmp"),
        ]
        result = _filt().filter(
            [
                "src/Service.java",
                "docs/guide.md",
                "docs/scratch.tmp",
                "node_modules/pkg/index.js",
            ],
            sources,
        )
        self.assertEqual(result, ["src/Service.java", "docs/guide.md"])

    def test_u07_negation_bang_same_source(self) -> None:
        sources = [
            _source("", "# logs", "*.log", "!keep.log", "build/"),
        ]
        result = _filt().filter(
            ["app.log", "keep.log", "notes.txt", "build/out.bin"],
            sources,
        )
        self.assertEqual(result, ["keep.log", "notes.txt"])


class TestDenylistCaseInsensitive(unittest.TestCase):
    def test_u08_csv_case_insensitive(self) -> None:
        result = _filt().filter(["ok.py", "report.CSV", "data.csv"], [])
        self.assertEqual(result, ["ok.py"])
        self.assertNotIn("report.CSV", result)
        self.assertNotIn("data.csv", result)

    def test_u09_images_case_insensitive(self) -> None:
        result = _filt().filter(
            ["ok.md", "Logo.PNG", "shot.JPEG", "icon.svg", "pic.webp"],
            [],
        )
        self.assertEqual(result, ["ok.md"])


class TestExtensionless(unittest.TestCase):
    def test_u10_extensionless_included(self) -> None:
        result = _filt().filter(["Makefile", "Dockerfile", "LICENSE", "src/a.py"], [])
        self.assertEqual(result, ["Makefile", "Dockerfile", "LICENSE", "src/a.py"])

    def test_u11_extensionless_under_gitignored_dir(self) -> None:
        result = _filt().filter(
            ["Makefile", "node_modules/pkg"],
            [_source("", "node_modules/")],
        )
        self.assertEqual(result, ["Makefile"])
        self.assertNotIn("node_modules/pkg", result)


class TestDuplicatesNormalizationOrder(unittest.TestCase):
    def test_u12_duplicates_collapsed_first_wins(self) -> None:
        result = _filt().filter(
            ["a.py", "b.md", "a.py", "b.md", "c.java"],
            [],
        )
        self.assertEqual(result, ["a.py", "b.md", "c.java"])

    def test_u13_backslash_normalized(self) -> None:
        result = _filt().filter([r"src\App.java", r"data\report.csv"], [])
        self.assertEqual(result, ["src/App.java"])

    def test_u14_stable_order(self) -> None:
        paths = ["z.md", "a.java", "m.py", "x.csv", "b.png"]
        result = _filt().filter(paths, [])
        self.assertEqual(result, ["z.md", "a.java", "m.py"])


class TestLoadGitignoreSources(unittest.TestCase):
    def test_u15_missing_root_raises(self) -> None:
        missing = Path("/nonexistent/repo/root/for-t09-eligibility")
        with self.assertRaises(EligibilityError):
            load_gitignore_sources(missing)

    def test_u16_skips_git_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("*.o\n", encoding="utf-8")
            git_dir = root / ".git"
            git_dir.mkdir()
            (git_dir / ".gitignore").write_text("should-not-load\n", encoding="utf-8")
            nested_git = git_dir / "objects"
            nested_git.mkdir()
            (nested_git / ".gitignore").write_text("also-skip\n", encoding="utf-8")

            sources = load_gitignore_sources(root)

            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].relative_dir, "")
            self.assertEqual(list(sources[0].lines), ["*.o"])

    def test_u17_nested_sources_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            docs = root / "docs"
            docs.mkdir()
            (docs / ".gitignore").write_text("*.tmp\n", encoding="utf-8")

            sources = load_gitignore_sources(root)
            by_dir = {s.relative_dir: list(s.lines) for s in sources}

            self.assertEqual(by_dir[""], ["node_modules/"])
            self.assertEqual(by_dir["docs"], ["*.tmp"])

    def test_u18_no_gitignore_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "a.py").write_text("x", encoding="utf-8")

            self.assertEqual(load_gitignore_sources(root), [])

    def test_u24_non_utf8_gitignore_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_bytes(b"\xff\xfe invalid utf8 \x80")

            with self.assertRaises(EligibilityError):
                load_gitignore_sources(root)


class TestNoSizeCaps(unittest.TestCase):
    def test_u19_signature_has_no_size_params(self) -> None:
        sig = inspect.signature(PathspecFileEligibilityFilter.filter)
        param_names = {name.lower() for name in sig.parameters}
        for forbidden in ("size", "max_bytes", "max_size", "maxbytes", "filesize"):
            self.assertNotIn(forbidden, param_names)

    def test_u20_no_volume_rejection(self) -> None:
        paths = ["src/HugeService.java", "docs/big.md"]
        result = _filt().filter(paths, [])
        self.assertEqual(result, paths)


class TestIdempotencyAndProtocol(unittest.TestCase):
    def test_u21_idempotent_filter(self) -> None:
        filt = _filt()
        paths = ["a.py", "b.csv", "c.md"]
        first = filt.filter(paths, [])
        second = filt.filter(paths, [])
        self.assertEqual(first, second)
        self.assertEqual(first, ["a.py", "c.md"])

    def test_u22_protocol_runtime(self) -> None:
        self.assertIsInstance(_filt(), FileEligibilityFilter)


class TestRulesConstants(unittest.TestCase):
    def test_u23_denylists_and_extensionless_default(self) -> None:
        self.assertEqual(CSV_DENYLIST, frozenset({".csv"}))
        expected_images = frozenset(
            {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".bmp",
                ".webp",
                ".ico",
                ".tif",
                ".tiff",
                ".heic",
                ".avif",
                ".svg",
            }
        )
        self.assertEqual(IMAGE_DENYLIST, expected_images)
        self.assertTrue(DEFAULT_ELIGIBILITY_RULES.include_extensionless)
        self.assertEqual(DEFAULT_ELIGIBILITY_RULES.csv_extensions, CSV_DENYLIST)
        self.assertEqual(DEFAULT_ELIGIBILITY_RULES.image_extensions, IMAGE_DENYLIST)


if __name__ == "__main__":
    unittest.main()
