"""Unitários do adaptador local via fachada — T08."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from git import Actor, Repo

from github_rag.catalog.models import RepoOrigin
from github_rag.snapshot.diff import FileDiffSet
from github_rag.snapshot.errors import (
    CommitNotFoundError,
    CorruptRepositoryError,
    FileNotFoundInCommitError,
    MainBranchMissingError,
)
from github_rag.snapshot.models import FirstIndexSignal, LocalSnapshotSource
from github_rag.snapshot.provider import DefaultMainSnapshotProvider
from tests.unit.snapshot.helpers import (
    commit_files,
    delete_and_commit,
    init_repo_with_main,
)


class TestLocalSnapshot(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name) / "repo"
        self.provider = DefaultMainSnapshotProvider()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _source(self) -> LocalSnapshotSource:
        return LocalSnapshotSource(local_path=str(self.root))

    def test_u_l01_tip_main(self) -> None:
        sha = init_repo_with_main(self.root, files={"a.py": b"1\n"})
        tip = self.provider.get_main_tip(self._source())
        self.assertEqual(tip.commit_sha, sha)
        self.assertEqual(tip.branch, "main")
        self.assertEqual(tip.origin, RepoOrigin.LOCAL)

    def test_u_l02_list_tree(self) -> None:
        sha = init_repo_with_main(
            self.root, files={"a.py": b"1\n", "src/b.py": b"2\n"}
        )
        tree = self.provider.list_tree(self._source(), commit_sha=sha)
        self.assertIn("a.py", tree)
        self.assertIn("src/b.py", tree)

    def test_u_l03_read_file_full_content(self) -> None:
        content = b"hello full file\n"
        sha = init_repo_with_main(self.root, files={"App.java": content})
        data = self.provider.read_file(
            self._source(), commit_sha=sha, path="App.java"
        )
        self.assertEqual(data, content)

    def test_u_l04_diff_add_mod_del(self) -> None:
        sha_a = init_repo_with_main(
            self.root, files={"a.py": b"old\n", "c.py": b"gone\n"}
        )
        commit_files(self.root, {"a.py": b"new\n", "b.py": b"added\n"})
        sha_b = delete_and_commit(self.root, ["c.py"])
        result = self.provider.diff_files(
            self._source(), from_commit=sha_a, to_commit=sha_b
        )
        assert isinstance(result, FileDiffSet)
        self.assertIn("a.py", result.modified)
        self.assertIn("b.py", result.added)
        self.assertIn("c.py", result.deleted)

    def test_u_l05_uncommitted_ignored(self) -> None:
        sha = init_repo_with_main(self.root, files={"a.py": b"1\n"})
        (self.root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        tip = self.provider.get_main_tip(self._source())
        self.assertEqual(tip.commit_sha, sha)
        tree = self.provider.list_tree(self._source(), commit_sha=sha)
        self.assertNotIn("dirty.txt", tree)
        with self.assertRaises(FileNotFoundInCommitError):
            self.provider.read_file(
                self._source(), commit_sha=sha, path="dirty.txt"
            )

    def test_u_l06_other_branch_ignored(self) -> None:
        sha_main = init_repo_with_main(self.root, files={"a.py": b"main\n"})
        repo = Repo(self.root)
        repo.git.checkout("-b", "feature/x")
        commit_files(self.root, {"feature_only.py": b"x\n"})
        repo.git.checkout("main")
        tip = self.provider.get_main_tip(self._source())
        self.assertEqual(tip.commit_sha, sha_main)
        tree = self.provider.list_tree(self._source(), commit_sha=sha_main)
        self.assertNotIn("feature_only.py", tree)

    def test_u_l07_main_missing(self) -> None:
        self.root.mkdir(parents=True)
        repo = Repo.init(self.root)
        repo.git.checkout("-b", "develop")
        actor = Actor("t08", "t08@test.local")
        (self.root / "f.txt").write_text("x\n", encoding="utf-8")
        repo.index.add(["f.txt"])
        repo.index.commit("init", author=actor, committer=actor)
        with self.assertRaises(MainBranchMissingError):
            self.provider.get_main_tip(self._source())

    def test_u_l08_corrupt_repo(self) -> None:
        self.root.mkdir(parents=True)
        (self.root / "not-git.txt").write_text("x\n", encoding="utf-8")
        with self.assertRaises(CorruptRepositoryError):
            self.provider.get_main_tip(self._source())

    def test_u_l09_commit_not_found(self) -> None:
        init_repo_with_main(self.root, files={"a.py": b"1\n"})
        missing = "deadbeef" * 5
        with self.assertRaises(CommitNotFoundError):
            self.provider.list_tree(self._source(), commit_sha=missing)

    def test_u_l10_file_not_found(self) -> None:
        sha = init_repo_with_main(self.root, files={"a.py": b"1\n"})
        with self.assertRaises(FileNotFoundInCommitError):
            self.provider.read_file(
                self._source(), commit_sha=sha, path="missing.py"
            )

    def test_u_l11_first_index_signal(self) -> None:
        sha = init_repo_with_main(self.root, files={"a.py": b"1\n"})
        result = self.provider.diff_files(
            self._source(), from_commit=None, to_commit=sha
        )
        self.assertIsInstance(result, FirstIndexSignal)
        assert isinstance(result, FirstIndexSignal)
        self.assertEqual(result.to_commit, sha)

    def test_u_l12_uses_gitpython_not_adhoc_git_dir(self) -> None:
        """Garantia estrutural: módulo snapshot.local importa git (GitPython)."""
        import github_rag.snapshot.local as local_mod

        self.assertTrue(hasattr(local_mod, "Repo") or "git" in dir(local_mod))
        source = local_mod.__file__
        assert source is not None
        text = Path(source).read_text(encoding="utf-8")
        self.assertIn("from git", text.replace(" ", ""))
        # não deve abrir refs/heads/main via pathlib ad-hoc como estratégia principal
        self.assertNotIn('refs" / "heads" / "main"', text)

    def test_u_x01_empty_tree_commit(self) -> None:
        self.root.mkdir(parents=True)
        repo = Repo.init(self.root)
        repo.git.checkout("-b", "main")
        actor = Actor("t08", "t08@test.local")
        # empty tree commit
        commit = repo.index.commit(
            "empty", author=actor, committer=actor, skip_hooks=True
        )
        tree = self.provider.list_tree(
            self._source(), commit_sha=commit.hexsha
        )
        self.assertEqual(tree, ())

    def test_u_x02_empty_file(self) -> None:
        sha = init_repo_with_main(self.root, files={"empty.txt": b""})
        data = self.provider.read_file(
            self._source(), commit_sha=sha, path="empty.txt"
        )
        self.assertEqual(data, b"")

    def test_u_x03_nested_posix_paths(self) -> None:
        sha = init_repo_with_main(
            self.root, files={"dir/sub/file.py": b"x\n"}
        )
        tree = self.provider.list_tree(self._source(), commit_sha=sha)
        self.assertIn("dir/sub/file.py", tree)

    def test_u_x04_identical_sha_diff_empty(self) -> None:
        sha = init_repo_with_main(self.root, files={"a.py": b"1\n"})
        result = self.provider.diff_files(
            self._source(), from_commit=sha, to_commit=sha
        )
        assert isinstance(result, FileDiffSet)
        self.assertEqual(result.added, ())
        self.assertEqual(result.modified, ())
        self.assertEqual(result.deleted, ())

    def test_u_x05_read_idempotent(self) -> None:
        content = b"same\n"
        sha = init_repo_with_main(self.root, files={"a.py": content})
        a = self.provider.read_file(
            self._source(), commit_sha=sha, path="a.py"
        )
        b = self.provider.read_file(
            self._source(), commit_sha=sha, path="a.py"
        )
        self.assertEqual(a, b)
        self.assertEqual(a, content)
