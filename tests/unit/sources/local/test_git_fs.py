"""Testes unitários de git_fs (T06)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from github_rag.sources.local.git_fs import GitFilesystemInspector


def _init_git_repo(path: Path, *, with_main: bool = True) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git_dir = path / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    if with_main:
        heads = git_dir / "refs" / "heads"
        heads.mkdir(parents=True)
        (heads / "main").write_text("abc123\n", encoding="utf-8")


def _init_gitdir_file_repo(work_dir: Path, git_dir: Path) -> None:
    work_dir.mkdir(parents=True)
    git_dir.mkdir(parents=True)
    heads = git_dir / "refs" / "heads"
    heads.mkdir(parents=True)
    (heads / "main").write_text("def456\n", encoding="utf-8")
    (work_dir / ".git").write_text(f"gitdir: {git_dir.resolve()}\n", encoding="utf-8")


class TestGitFilesystemInspector(unittest.TestCase):
    def setUp(self) -> None:
        self.inspector = GitFilesystemInspector()
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_parse_posix_with_glob(self) -> None:
        parsed = self.inspector.parse_file_url("file:///repos/*")
        self.assertEqual(parsed.base_path, Path("/repos"))
        self.assertEqual(parsed.glob_pattern, "*")

    def test_parse_posix_without_glob(self) -> None:
        parsed = self.inspector.parse_file_url("file:///repos/my-repo")
        self.assertEqual(parsed.base_path, Path("/repos/my-repo"))
        self.assertIsNone(parsed.glob_pattern)

    def test_parse_windows_with_glob(self) -> None:
        parsed = self.inspector.parse_file_url("file:///C:/repos/*")
        self.assertEqual(parsed.base_path, Path("C:/repos"))
        self.assertEqual(parsed.glob_pattern, "*")

    def test_is_accessible(self) -> None:
        existing = self.root / "exists"
        existing.mkdir()
        self.assertTrue(self.inspector.is_accessible(existing))
        self.assertFalse(self.inspector.is_accessible(self.root / "missing"))

    def test_expand_candidates_glob_directories_only(self) -> None:
        (self.root / "a").mkdir()
        (self.root / "b").mkdir()
        (self.root / "file.txt").write_text("x", encoding="utf-8")
        found = self.inspector.expand_candidates(self.root, "*")
        names = {p.name for p in found}
        self.assertEqual(names, {"a", "b"})

    def test_expand_candidates_single_base(self) -> None:
        repo = self.root / "single"
        repo.mkdir()
        found = self.inspector.expand_candidates(repo, None)
        self.assertEqual(list(found), [repo])

    def test_inspect_valid_repo_with_main(self) -> None:
        repo = self.root / "repo"
        _init_git_repo(repo)
        result = self.inspector.inspect_repo(repo)
        self.assertTrue(result.is_valid_candidate)

    def test_inspect_gitdir_file(self) -> None:
        work = self.root / "work"
        gitdir = self.root / "actual.git"
        _init_gitdir_file_repo(work, gitdir)
        result = self.inspector.inspect_repo(work)
        self.assertTrue(result.is_valid_candidate)

    def test_inspect_main_in_packed_refs(self) -> None:
        repo = self.root / "packed"
        _init_git_repo(repo, with_main=False)
        packed = repo / ".git" / "packed-refs"
        packed.write_text("# pack\nabc refs/heads/main\n", encoding="utf-8")
        result = self.inspector.inspect_repo(repo)
        self.assertTrue(result.has_main_branch)

    def test_inspect_not_git(self) -> None:
        plain = self.root / "plain"
        plain.mkdir()
        result = self.inspector.inspect_repo(plain)
        self.assertFalse(result.is_git_repo)

    def test_inspect_git_without_main(self) -> None:
        repo = self.root / "no-main"
        _init_git_repo(repo, with_main=False)
        result = self.inspector.inspect_repo(repo)
        self.assertTrue(result.is_git_repo)
        self.assertFalse(result.has_main_branch)

    def test_inspect_not_directory(self) -> None:
        f = self.root / "file"
        f.write_text("x", encoding="utf-8")
        result = self.inspector.inspect_repo(f)
        self.assertFalse(result.is_git_repo)

    def test_parse_invalid_scheme_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.inspector.parse_file_url("https://example.com/x")


if __name__ == "__main__":
    unittest.main()
