"""Unitários do adaptador GitHub com mocks — T08."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Sequence
from unittest.mock import MagicMock

from github import GithubException
from requests.exceptions import ConnectionError as RequestsConnectionError

from github_rag.catalog.models import RepoOrigin
from github_rag.snapshot.errors import (
    CommitNotFoundError,
    GitHubSnapshotNetworkError,
    MainBranchMissingError,
)
from github_rag.snapshot.models import GitHubSnapshotSource
from github_rag.snapshot.provider import DefaultMainSnapshotProvider
from tests.unit.snapshot.helpers import commit_files, init_repo_with_main

TOKEN = "ghp_unit_test_secret_token_T08"


class FakeClonePort:
    """GitClonePort de teste: aponta para repo local já materializado."""

    def __init__(self, workspace: Path, *, missing: bool = False) -> None:
        self.workspace = workspace
        self.missing = missing
        self.calls: list[tuple[str, ...]] = []

    def ensure_commits(
        self,
        *,
        full_name: str,
        token: str,
        commit_shas: Sequence[str],
    ) -> Path:
        self.calls.append(tuple(commit_shas))
        if self.missing:
            raise CommitNotFoundError(
                f"commits não encontrados para {full_name}"
            )
        return self.workspace


def _github_factory_with_tip(sha: str, *, fail: Exception | None = None):
    def factory(token: str) -> MagicMock:
        gh = MagicMock()
        if fail is not None:
            gh.get_repo.side_effect = fail
            return gh
        repo = MagicMock()
        branch = MagicMock()
        commit = MagicMock()
        commit.sha = sha
        branch.commit = commit
        repo.get_branch.return_value = branch
        gh.get_repo.return_value = repo
        return gh

    return factory


class TestGitHubSnapshot(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmpdir.name) / "clone"
        self.sha_old = init_repo_with_main(
            self.workspace, files={"old.txt": b"old\n"}
        )
        self.sha_tip = commit_files(
            self.workspace, {"old.txt": b"new\n", "tip_only.py": b"t\n"}
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _source(self) -> GitHubSnapshotSource:
        return GitHubSnapshotSource(full_name="acme/demo", token=TOKEN)

    def test_u_g01_tip_via_pygithub(self) -> None:
        provider = DefaultMainSnapshotProvider(
            clone_port=FakeClonePort(self.workspace),
            github_factory=_github_factory_with_tip(self.sha_tip),
        )
        tip = provider.get_main_tip(self._source())
        self.assertEqual(tip.commit_sha, self.sha_tip)
        self.assertEqual(tip.origin, RepoOrigin.GITHUB)
        self.assertEqual(tip.repo_key, "acme/demo")
        self.assertEqual(tip.branch, "main")

    def test_u_g02_list_tree_and_read_requested_sha(self) -> None:
        provider = DefaultMainSnapshotProvider(
            clone_port=FakeClonePort(self.workspace),
            github_factory=_github_factory_with_tip(self.sha_tip),
        )
        tree_old = provider.list_tree(
            self._source(), commit_sha=self.sha_old
        )
        self.assertIn("old.txt", tree_old)
        self.assertNotIn("tip_only.py", tree_old)
        data = provider.read_file(
            self._source(), commit_sha=self.sha_old, path="old.txt"
        )
        self.assertEqual(data, b"old\n")

    def test_u_g03_commit_missing(self) -> None:
        provider = DefaultMainSnapshotProvider(
            clone_port=FakeClonePort(self.workspace, missing=True),
            github_factory=_github_factory_with_tip(self.sha_tip),
        )
        with self.assertRaises(CommitNotFoundError):
            provider.list_tree(self._source(), commit_sha="a" * 40)

    def test_u_g04_network_failure_pygithub(self) -> None:
        provider = DefaultMainSnapshotProvider(
            clone_port=FakeClonePort(self.workspace),
            github_factory=_github_factory_with_tip(
                self.sha_tip, fail=RequestsConnectionError("boom")
            ),
        )
        with self.assertRaises(GitHubSnapshotNetworkError) as ctx:
            provider.get_main_tip(self._source())
        self.assertNotIn(TOKEN, str(ctx.exception))
        self.assertNotIn(TOKEN, repr(ctx.exception))

    def test_u_g05_clone_failure(self) -> None:
        class FailingClone:
            def ensure_commits(self, **kwargs):  # type: ignore[no-untyped-def]
                raise GitHubSnapshotNetworkError("clone falhou")

        provider = DefaultMainSnapshotProvider(
            clone_port=FailingClone(),  # type: ignore[arg-type]
            github_factory=_github_factory_with_tip(self.sha_tip),
        )
        with self.assertRaises(GitHubSnapshotNetworkError):
            provider.list_tree(self._source(), commit_sha=self.sha_tip)

    def test_u_g06_token_absent_from_errors(self) -> None:
        provider = DefaultMainSnapshotProvider(
            clone_port=FakeClonePort(self.workspace),
            github_factory=_github_factory_with_tip(
                self.sha_tip,
                fail=GithubException(401, {"message": "bad"}, None),
            ),
        )
        with self.assertRaises(Exception) as ctx:
            provider.get_main_tip(self._source())
        self.assertNotIn(TOKEN, str(ctx.exception))
        self.assertNotIn(TOKEN, repr(ctx.exception))

    def test_u_g07_main_missing_on_api(self) -> None:
        def factory(token: str) -> MagicMock:
            gh = MagicMock()
            repo = MagicMock()
            repo.get_branch.side_effect = GithubException(
                404, {"message": "Branch not found"}, None
            )
            gh.get_repo.return_value = repo
            return gh

        provider = DefaultMainSnapshotProvider(
            clone_port=FakeClonePort(self.workspace),
            github_factory=factory,
        )
        with self.assertRaises(MainBranchMissingError):
            provider.get_main_tip(self._source())
