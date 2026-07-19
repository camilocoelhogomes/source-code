"""Testes unitários de git_fs (T06 + T20 GitPython)."""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from git import Repo

from github_rag.sources.local import git_fs
from github_rag.sources.local.git_fs import GitFilesystemInspector, remap_repos_mount_path


def _init_git_repo(path: Path, *, with_main: bool = True) -> Repo:
    """Cria worktree Git real (GitPython-válido) para inspeção."""
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    if with_main:
        (path / "README").write_text("x", encoding="utf-8")
        repo.index.add(["README"])
        repo.index.commit("init")
        if "main" not in repo.heads:
            repo.create_head("main")
        repo.heads.main.checkout()
    else:
        (path / "README").write_text("x", encoding="utf-8")
        repo.index.add(["README"])
        repo.index.commit("init")
        if "main" in repo.heads:
            # rename main away if git defaulted to main
            repo.create_head("develop")
            repo.heads.develop.checkout()
            repo.delete_head("main", force=True)
    return repo


def _init_gitdir_file_repo(work_dir: Path, git_dir: Path) -> None:
    """Worktree com `.git` file apontando para um git dir real."""
    import shutil

    donor = work_dir.parent / f"{work_dir.name}-donor"
    _init_git_repo(donor)
    work_dir.mkdir(parents=True, exist_ok=True)
    if git_dir.exists():
        shutil.rmtree(git_dir)
    shutil.copytree(donor / ".git", git_dir)
    (work_dir / ".git").write_text(
        f"gitdir: {git_dir.resolve()}\n", encoding="utf-8"
    )


def _init_packed_main_repo(path: Path) -> None:
    """Repo com main apenas em packed-refs (sem loose ref)."""
    repo = _init_git_repo(path, with_main=True)
    main_ref = path / ".git" / "refs" / "heads" / "main"
    sha = main_ref.read_text(encoding="utf-8").strip()
    packed = path / ".git" / "packed-refs"
    packed.write_text(f"# pack-refs with: peeled fully-peeled\n{sha} refs/heads/main\n", encoding="utf-8")
    main_ref.unlink()
    # ensure heads dir empty of main
    repo.close()


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
        _init_packed_main_repo(repo)
        result = self.inspector.inspect_repo(repo)
        self.assertTrue(result.has_main_branch)
        self.assertTrue(result.is_valid_candidate)

    def test_inspect_not_git(self) -> None:
        plain = self.root / "plain"
        plain.mkdir()
        result = self.inspector.inspect_repo(plain)
        self.assertFalse(result.is_git_repo)
        self.assertEqual(result.reason, "not a git repository")

    def test_inspect_git_without_main(self) -> None:
        repo = self.root / "no-main"
        _init_git_repo(repo, with_main=False)
        result = self.inspector.inspect_repo(repo)
        self.assertTrue(result.is_git_repo)
        self.assertFalse(result.has_main_branch)
        self.assertEqual(result.reason, "main branch not found")

    def test_inspect_not_directory(self) -> None:
        f = self.root / "file"
        f.write_text("x", encoding="utf-8")
        result = self.inspector.inspect_repo(f)
        self.assertFalse(result.is_git_repo)
        self.assertEqual(result.reason, "not a directory")

    def test_parse_invalid_scheme_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.inspector.parse_file_url("https://example.com/x")

    def test_parse_empty_path_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.inspector.parse_file_url("file://")

    def test_parse_relative_path_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.inspector.parse_file_url("file:relative/path")

    def test_expand_candidates_base_not_directory(self) -> None:
        f = self.root / "not-dir"
        f.write_text("x", encoding="utf-8")
        self.assertEqual(self.inspector.expand_candidates(f, "*"), ())

    def test_expand_candidates_non_star_prefix_pattern(self) -> None:
        nested = self.root / "nest" / "svc"
        nested.mkdir(parents=True)
        found = self.inspector.expand_candidates(self.root, "svc")
        self.assertEqual(list(found), [nested])

    def test_to_native_path_windows_drive_without_leading_slash(self) -> None:
        with mock.patch.object(git_fs.os, "name", "nt"):
            self.assertEqual(git_fs._to_native_path("C:/repos"), Path("C:/repos"))

    # --- T34: remap HOST_REPOS ---

    def test_t34_remap_without_host_repos_unchanged(self) -> None:
        self.assertEqual(remap_repos_mount_path(Path("/repos"), None), Path("/repos"))
        self.assertEqual(
            remap_repos_mount_path(Path("/repos/foo"), ""),
            Path("/repos/foo"),
        )

    def test_t34_remap_root_and_subpath(self) -> None:
        host = self.root / "host-repos"
        host.mkdir()
        self.assertEqual(
            remap_repos_mount_path(Path("/repos"), str(host)),
            host.resolve(),
        )
        self.assertEqual(
            remap_repos_mount_path(Path("/repos/sample-local"), str(host)),
            (host / "sample-local").resolve(),
        )

    def test_t34_remap_non_repos_path_unchanged(self) -> None:
        host = self.root / "host-repos"
        host.mkdir()
        other = Path("/mnt/data")
        self.assertEqual(remap_repos_mount_path(other, str(host)), other)

    # --- T20: conformidade GitPython / DT-001 ---

    def test_t20_inspect_uses_gitpython_repo(self) -> None:
        """UT-T20-09: inspect_repo deve abrir via git.Repo."""
        repo_path = self.root / "spy-repo"
        _init_git_repo(repo_path)
        with mock.patch.object(
            git_fs, "Repo", wraps=Repo, create=True
        ) as repo_cls:
            result = self.inspector.inspect_repo(repo_path)
        self.assertTrue(result.is_valid_candidate)
        self.assertTrue(repo_cls.called, "GitPython Repo must be used")

    def test_t20_bare_repo_rejected(self) -> None:
        """UT-T20-07: bare rejeitado (paridade T06 / D-T20-006)."""
        work = self.root / "bare-donor"
        _init_git_repo(work)
        bare = self.root / "bare.git"
        Repo(work).clone(bare, bare=True)
        result = self.inspector.inspect_repo(bare)
        self.assertFalse(result.is_valid_candidate)
        self.assertEqual(result.reason, "not a git repository")

    def test_t20_incomplete_git_dir_rejected(self) -> None:
        """UT-T20-08: .git sem objects → not a git repository (delta §3.2)."""
        repo = self.root / "incomplete"
        repo.mkdir()
        git_dir = repo / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
        heads = git_dir / "refs" / "heads"
        heads.mkdir(parents=True)
        (heads / "main").write_text("a" * 40 + "\n", encoding="utf-8")
        result = self.inspector.inspect_repo(repo)
        self.assertFalse(result.is_git_repo)
        self.assertEqual(result.reason, "not a git repository")

    def test_t20_no_adhoc_packed_refs_or_loose_ref_parse(self) -> None:
        """UT-T20-11: produção sem parse ad-hoc de refs/packed-refs."""
        source = inspect.getsource(git_fs)
        self.assertNotIn("packed-refs", source)
        self.assertNotIn("_PACKED_REF_MAIN", source)
        self.assertNotIn("_resolve_git_dir", source)
        self.assertNotIn("_has_main_branch", source)
        self.assertNotIn('refs" / "heads"', source)
        self.assertNotIn("refs/heads", source)

    def test_t20_repo_opened_as_context_manager(self) -> None:
        """UT-T20-10: Repo usado como context manager."""
        source = inspect.getsource(GitFilesystemInspector.inspect_repo)
        self.assertRegex(
            source,
            r"with\s+Repo\s*\(",
            msg="inspect_repo must open GitPython Repo as context manager",
        )


if __name__ == "__main__":
    unittest.main()
