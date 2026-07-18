"""
BDD executável — T09-file-eligibility.

Valida BDD-006, corners e BDD-024/pathspec conforme design 0.1.0 (ELIG-01..07).

Execução:
    python -m pytest tests/bdd/test_file_eligibility.py -q
"""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path


def _filter():
    from github_rag.eligibility.filter import PathspecFileEligibilityFilter

    return PathspecFileEligibilityFilter()


def _source(relative_dir: str, *lines: str):
    from github_rag.eligibility.gitignore import GitignoreSource

    return GitignoreSource(relative_dir=relative_dir, lines=list(lines))


class TestELIG01Bdd006EligibleFilter(unittest.TestCase):
    """ELIG-01 / BDD-006 — textuais/MD/Java in; CSV, imagens, gitignore out."""

    def test_includes_textuals_excludes_csv_images_gitignore(self) -> None:
        filt = _filter()
        paths = [
            "src/App.java",
            "docs/readme.md",
            "src/main.py",
            "data/report.csv",
            "assets/logo.png",
            "target/Foo.class",
        ]
        sources = [_source("", "target/")]

        result = filt.filter(paths, sources)

        self.assertEqual(
            result,
            ["src/App.java", "docs/readme.md", "src/main.py"],
        )
        self.assertNotIn("data/report.csv", result)
        self.assertNotIn("assets/logo.png", result)
        self.assertNotIn("target/Foo.class", result)


class TestELIG02NoGitignore(unittest.TestCase):
    """ELIG-02 — sem .gitignore: só regras de tipo."""

    def test_empty_sources_only_type_rules(self) -> None:
        filt = _filter()
        paths = [
            "src/App.java",
            "notes.md",
            "data.csv",
            "img/photo.jpg",
        ]

        result = filt.filter(paths, [])

        self.assertEqual(result, ["src/App.java", "notes.md"])
        self.assertNotIn("data.csv", result)
        self.assertNotIn("img/photo.jpg", result)


class TestELIG03NestedGitignore(unittest.TestCase):
    """ELIG-03 — gitignore aninhado + loader."""

    def test_nested_sources_exclude_tmp_and_node_modules(self) -> None:
        filt = _filter()
        paths = [
            "src/Service.java",
            "docs/guide.md",
            "docs/scratch.tmp",
            "node_modules/pkg/index.js",
        ]
        sources = [
            _source("", "node_modules/"),
            _source("docs", "*.tmp"),
        ]

        result = filt.filter(paths, sources)

        self.assertEqual(result, ["src/Service.java", "docs/guide.md"])
        self.assertNotIn("docs/scratch.tmp", result)
        self.assertNotIn("node_modules/pkg/index.js", result)

    def test_load_gitignore_sources_nested_tree(self) -> None:
        from github_rag.eligibility.gitignore import load_gitignore_sources

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            docs = root / "docs"
            docs.mkdir()
            (docs / ".gitignore").write_text("*.tmp\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "Service.java").write_text("class S {}", encoding="utf-8")
            (docs / "guide.md").write_text("# g", encoding="utf-8")
            (docs / "scratch.tmp").write_text("tmp", encoding="utf-8")
            nm = root / "node_modules" / "pkg"
            nm.mkdir(parents=True)
            (nm / "index.js").write_text("module.exports={}", encoding="utf-8")

            sources = load_gitignore_sources(root)
            paths = [
                "src/Service.java",
                "docs/guide.md",
                "docs/scratch.tmp",
                "node_modules/pkg/index.js",
            ]
            result = _filter().filter(paths, sources)

            self.assertEqual(result, ["src/Service.java", "docs/guide.md"])


class TestELIG04MixedExtensions(unittest.TestCase):
    """ELIG-04 — extensões mistas + case-insensitive denylist."""

    def test_mixed_extensions_same_snapshot(self) -> None:
        filt = _filter()
        paths = [
            "a.md",
            "b.java",
            "c.py",
            "d.ts",
            "e.yml",
            "f.csv",
            "g.png",
            "h.svg",
            "i.jpg",
            "j.JPEG",
            "report.CSV",
            "Logo.PNG",
        ]

        result = filt.filter(paths, [])

        self.assertEqual(result, ["a.md", "b.java", "c.py", "d.ts", "e.yml"])
        for excluded in (
            "f.csv",
            "g.png",
            "h.svg",
            "i.jpg",
            "j.JPEG",
            "report.CSV",
            "Logo.PNG",
        ):
            self.assertNotIn(excluded, result)


class TestELIG05Extensionless(unittest.TestCase):
    """ELIG-05 — sem extensão: include-by-default salvo gitignore."""

    def test_makefile_dockerfile_included_gitignored_excluded(self) -> None:
        filt = _filter()
        paths = [
            "Makefile",
            "Dockerfile",
            "LICENSE",
            "node_modules/pkg",
        ]
        sources = [_source("", "node_modules/")]

        result = filt.filter(paths, sources)

        self.assertEqual(result, ["Makefile", "Dockerfile", "LICENSE"])
        self.assertNotIn("node_modules/pkg", result)


class TestELIG06PathspecNotHomemade(unittest.TestCase):
    """ELIG-06 / BDD-024 — GitWildMatch via pathspec."""

    def test_gitwildmatch_comment_negation_and_glob(self) -> None:
        filt = _filter()
        paths = [
            "app.log",
            "keep.log",
            "notes.txt",
            "build/out.bin",
        ]
        sources = [
            _source(
                "",
                "# ignore logs except keep.log",
                "*.log",
                "!keep.log",
                "build/",
            )
        ]

        result = filt.filter(paths, sources)

        self.assertEqual(result, ["keep.log", "notes.txt"])
        self.assertNotIn("app.log", result)
        self.assertNotIn("build/out.bin", result)

    def test_implementation_uses_pathspec_library(self) -> None:
        import github_rag.eligibility.filter as filter_mod

        source = inspect.getsource(filter_mod)
        self.assertIn("pathspec", source)
        self.assertRegex(
            source,
            r"gitwildmatch|GitWildMatchPattern",
            msg="matching deve usar pathspec GitWildMatch (D-T09-002 / BDD-024)",
        )
        # Garante dependência importável (SDK OSS), não parser caseiro.
        import pathspec  # noqa: F401


class TestELIG07NoSizeCaps(unittest.TestCase):
    """ELIG-07 / REQ-019 — filtro sem caps de tamanho."""

    def test_does_not_reject_by_size_and_signature_has_no_size_params(self) -> None:
        from github_rag.eligibility.filter import PathspecFileEligibilityFilter

        filt = PathspecFileEligibilityFilter()
        paths = ["src/HugeService.java", "docs/big.md"]

        result = filt.filter(paths, [])

        self.assertEqual(result, paths)

        sig = inspect.signature(PathspecFileEligibilityFilter.filter)
        param_names = {name.lower() for name in sig.parameters}
        for forbidden in ("size", "max_bytes", "max_size", "maxbytes", "filesize"):
            self.assertNotIn(
                forbidden,
                param_names,
                msg="D-T09-006: filter não deve receber parâmetros de tamanho",
            )


if __name__ == "__main__":
    unittest.main()
