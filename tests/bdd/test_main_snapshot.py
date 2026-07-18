"""
BDD executável — T08-main-snapshot.

Valida MS-01..12 (BDD-005, BDD-017, corner cases) conforme bdd.md 0.1.0.

Execução:
    .venv/bin/python -m pytest tests/bdd/test_main_snapshot.py -q
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Sequence
from unittest.mock import MagicMock

from git import Actor, Repo
from requests.exceptions import ConnectionError as RequestsConnectionError

from github_rag.catalog.models import RepoOrigin
from github_rag.snapshot.diff import FileDiffSet
from github_rag.snapshot.errors import (
    CommitNotFoundError,
    CorruptRepositoryError,
    GitHubSnapshotNetworkError,
    MainBranchMissingError,
)
from github_rag.snapshot.models import (
    FirstIndexSignal,
    GitHubSnapshotSource,
    LocalSnapshotSource,
)
from github_rag.snapshot.provider import DefaultMainSnapshotProvider
from tests.unit.snapshot.helpers import (
    commit_files,
    delete_and_commit,
    init_repo_with_main,
    rename_and_commit,
)

TOKEN = "ghp_bdd_secret_token_value_T08"


class FakeClonePort:
    def __init__(self, workspace: Path, *, missing: bool = False) -> None:
        self.workspace = workspace
        self.missing = missing

    def ensure_commits(
        self,
        *,
        full_name: str,
        token: str,
        commit_shas: Sequence[str],
    ) -> Path:
        if self.missing:
            raise CommitNotFoundError("sha ausente")
        return self.workspace


class TestMainSnapshotBdd(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name) / "repo"
        self.provider = DefaultMainSnapshotProvider()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _local(self) -> LocalSnapshotSource:
        return LocalSnapshotSource(local_path=str(self.root))

    def test_ms01_get_main_tip(self) -> None:
        """MS-01 / BDD-005: tip main exposto."""
        sha = init_repo_with_main(self.root, files={"a.py": b"1\n"})
        tip = self.provider.get_main_tip(self._local())
        self.assertEqual(tip.commit_sha, sha)
        self.assertEqual(tip.branch, "main")
        self.assertEqual(tip.origin, RepoOrigin.LOCAL)

    def test_ms02_diff_paths_between_commits(self) -> None:
        """MS-02 / ENG-012: diff add/mod/del."""
        sha_a = init_repo_with_main(
            self.root, files={"a.py": b"old\n", "c.py": b"x\n"}
        )
        commit_files(self.root, {"a.py": b"new\n", "b.py": b"add\n"})
        sha_b = delete_and_commit(self.root, ["c.py"])
        result = self.provider.diff_files(
            self._local(), from_commit=sha_a, to_commit=sha_b
        )
        assert isinstance(result, FileDiffSet)
        self.assertIn("a.py", result.modified)
        self.assertIn("b.py", result.added)
        self.assertIn("c.py", result.deleted)

    def test_ms03_full_file_content_at_tip(self) -> None:
        """MS-03: conteúdo = arquivo completo."""
        content = b"public class App {}\n"
        sha = init_repo_with_main(self.root, files={"src/App.java": content})
        data = self.provider.read_file(
            self._local(), commit_sha=sha, path="src/App.java"
        )
        self.assertEqual(data, content)

    def test_ms04_ignore_uncommitted_and_other_branches(self) -> None:
        """MS-04 / BDD-017 / BR-015."""
        sha_a = init_repo_with_main(self.root, files={"a.py": b"main\n"})
        repo = Repo(self.root)
        repo.git.checkout("-b", "feature/x")
        commit_files(self.root, {"only_feature.py": b"f\n"})
        repo.git.checkout("main")
        (self.root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        tip = self.provider.get_main_tip(self._local())
        self.assertEqual(tip.commit_sha, sha_a)
        tree = self.provider.list_tree(self._local(), commit_sha=sha_a)
        self.assertNotIn("dirty.txt", tree)
        self.assertNotIn("only_feature.py", tree)

    def test_ms05_first_index_signal(self) -> None:
        """MS-05: from_commit None → FirstIndexSignal."""
        sha = init_repo_with_main(self.root, files={"a.py": b"1\n"})
        result = self.provider.diff_files(
            self._local(), from_commit=None, to_commit=sha
        )
        self.assertIsInstance(result, FirstIndexSignal)
        assert isinstance(result, FirstIndexSignal)
        self.assertEqual(result.to_commit, sha)

    def test_ms06_main_missing(self) -> None:
        """MS-06: main ausente."""
        self.root.mkdir(parents=True)
        repo = Repo.init(self.root)
        repo.git.checkout("-b", "develop")
        actor = Actor("t08", "t08@test.local")
        (self.root / "f.txt").write_text("x\n", encoding="utf-8")
        repo.index.add(["f.txt"])
        repo.index.commit("init", author=actor, committer=actor)
        with self.assertRaises(MainBranchMissingError):
            self.provider.get_main_tip(self._local())

    def test_ms07_corrupt_repo(self) -> None:
        """MS-07: repo corrompido / não-git."""
        self.root.mkdir(parents=True)
        (self.root / "x.txt").write_text("nope\n", encoding="utf-8")
        with self.assertRaises(CorruptRepositoryError):
            self.provider.get_main_tip(self._local())

    def test_ms08_github_network_failure(self) -> None:
        """MS-08: falha de rede GitHub."""

        def factory(token: str) -> MagicMock:
            gh = MagicMock()
            gh.get_repo.side_effect = RequestsConnectionError("down")
            return gh

        provider = DefaultMainSnapshotProvider(
            clone_port=FakeClonePort(self.root),
            github_factory=factory,
        )
        with self.assertRaises(GitHubSnapshotNetworkError) as ctx:
            provider.get_main_tip(
                GitHubSnapshotSource(full_name="acme/r", token=TOKEN)
            )
        self.assertNotIn(TOKEN, str(ctx.exception))

    def test_ms09_github_tip_and_requested_sha(self) -> None:
        """MS-09: tip GitHub + tree/read no commit pedido."""
        workspace = Path(self._tmpdir.name) / "gh"
        sha_old = init_repo_with_main(workspace, files={"f.txt": b"old\n"})
        sha_tip = commit_files(workspace, {"f.txt": b"new\n", "extra.py": b"e\n"})

        def factory(token: str) -> MagicMock:
            gh = MagicMock()
            repo = MagicMock()
            branch = MagicMock()
            commit = MagicMock()
            commit.sha = sha_tip
            branch.commit = commit
            repo.get_branch.return_value = branch
            gh.get_repo.return_value = repo
            return gh

        provider = DefaultMainSnapshotProvider(
            clone_port=FakeClonePort(workspace),
            github_factory=factory,
        )
        source = GitHubSnapshotSource(full_name="acme/demo", token=TOKEN)
        tip = provider.get_main_tip(source)
        self.assertEqual(tip.origin, RepoOrigin.GITHUB)
        self.assertEqual(tip.commit_sha, sha_tip)
        tree = provider.list_tree(source, commit_sha=sha_old)
        self.assertIn("f.txt", tree)
        self.assertNotIn("extra.py", tree)
        self.assertEqual(
            provider.read_file(source, commit_sha=sha_old, path="f.txt"),
            b"old\n",
        )
        missing_provider = DefaultMainSnapshotProvider(
            clone_port=FakeClonePort(workspace, missing=True),
            github_factory=factory,
        )
        with self.assertRaises(CommitNotFoundError):
            missing_provider.list_tree(source, commit_sha="a" * 40)

    def test_ms10_gitpython_compliance(self) -> None:
        """MS-10 / BDD-024: snapshot.local usa GitPython."""
        import github_rag.snapshot.local as local_mod

        text = Path(local_mod.__file__).read_text(encoding="utf-8")  # type: ignore[arg-type]
        self.assertIn("from git import", text)
        self.assertNotIn('Path(".git")', text)

    def test_ms11_rename_deleted_and_added(self) -> None:
        """MS-11: rename → deleted + added."""
        sha_a = init_repo_with_main(self.root, files={"old.py": b"x\n"})
        sha_b = rename_and_commit(self.root, "old.py", "new.py")
        result = self.provider.diff_files(
            self._local(), from_commit=sha_a, to_commit=sha_b
        )
        assert isinstance(result, FileDiffSet)
        self.assertIn("old.py", result.deleted)
        self.assertIn("new.py", result.added)

    def test_ms12_token_absent_from_errors(self) -> None:
        """MS-12 / BR-008."""

        def factory(token: str) -> MagicMock:
            gh = MagicMock()
            gh.get_repo.side_effect = RequestsConnectionError("down")
            return gh

        provider = DefaultMainSnapshotProvider(
            clone_port=FakeClonePort(self.root),
            github_factory=factory,
        )
        with self.assertRaises(GitHubSnapshotNetworkError) as ctx:
            provider.get_main_tip(
                GitHubSnapshotSource(full_name="acme/r", token=TOKEN)
            )
        self.assertNotIn(TOKEN, str(ctx.exception))
        self.assertNotIn(TOKEN, repr(ctx.exception))
