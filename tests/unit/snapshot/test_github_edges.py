"""Corners adicionais do adaptador GitHub — cobertura T08."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from github import GithubException
from github.GithubException import UnknownObjectException

from github_rag.snapshot.errors import (
    CommitNotFoundError,
    GitHubSnapshotNetworkError,
    MainBranchMissingError,
)
from github_rag.snapshot.github import GitHubGitSnapshotAdapter, _default_github
from github_rag.snapshot.models import GitHubSnapshotSource


class FakeClone:
    def __init__(self, path: Path | None = None, *, boom: Exception | None = None) -> None:
        self.path = path
        self.boom = boom

    def ensure_commits(self, **kwargs):  # type: ignore[no-untyped-def]
        if self.boom is not None:
            raise self.boom
        assert self.path is not None
        return self.path


class TestGitHubEdges(unittest.TestCase):
    def test_default_github_factory(self) -> None:
        with patch("github_rag.snapshot.github.Github") as gh_cls:
            with patch("github_rag.snapshot.github.Auth.Token") as token_cls:
                token_cls.return_value = "auth"
                _default_github("tok")
                gh_cls.assert_called_once()

    def test_unknown_object_main_missing(self) -> None:
        def factory(token: str) -> MagicMock:
            gh = MagicMock()
            repo = MagicMock()
            repo.get_branch.side_effect = UnknownObjectException(
                404, {"message": "Not Found"}, None
            )
            gh.get_repo.return_value = repo
            return gh

        adapter = GitHubGitSnapshotAdapter(
            clone_port=FakeClone(),  # type: ignore[arg-type]
            github_factory=factory,
        )
        with self.assertRaises(MainBranchMissingError):
            adapter.get_main_tip(
                GitHubSnapshotSource(full_name="o/r", token="t")
            )

    def test_generic_exception_network(self) -> None:
        def factory(token: str) -> MagicMock:
            gh = MagicMock()
            gh.get_repo.side_effect = RuntimeError("weird")
            return gh

        adapter = GitHubGitSnapshotAdapter(
            clone_port=FakeClone(),
            github_factory=factory,
        )
        with self.assertRaises(GitHubSnapshotNetworkError):
            adapter.get_main_tip(
                GitHubSnapshotSource(full_name="o/r", token="t")
            )

    def test_github_exception_non_404(self) -> None:
        def factory(token: str) -> MagicMock:
            gh = MagicMock()
            gh.get_repo.side_effect = GithubException(
                500, {"message": "err"}, None
            )
            return gh

        adapter = GitHubGitSnapshotAdapter(
            clone_port=FakeClone(),
            github_factory=factory,
        )
        with self.assertRaises(GitHubSnapshotNetworkError):
            adapter.get_main_tip(
                GitHubSnapshotSource(full_name="o/r", token="t")
            )

    def test_materialize_unexpected_exception(self) -> None:
        def factory(token: str) -> MagicMock:
            return MagicMock()

        adapter = GitHubGitSnapshotAdapter(
            clone_port=FakeClone(boom=ValueError("x")),
            github_factory=factory,
        )
        with self.assertRaises(GitHubSnapshotNetworkError):
            adapter.list_tree(
                GitHubSnapshotSource(full_name="o/r", token="t"),
                commit_sha="a" * 40,
            )

    def test_materialize_commit_not_found_propagates(self) -> None:
        adapter = GitHubGitSnapshotAdapter(
            clone_port=FakeClone(boom=CommitNotFoundError("missing")),
            github_factory=lambda t: MagicMock(),
        )
        with self.assertRaises(CommitNotFoundError):
            adapter.read_file(
                GitHubSnapshotSource(full_name="o/r", token="t"),
                commit_sha="a" * 40,
                path="a.py",
            )

    def test_read_file_happy_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            from tests.unit.snapshot.helpers import init_repo_with_main

            workspace = Path(tmp)
            sha = init_repo_with_main(workspace, files={"a.py": b"z\n"})
            adapter = GitHubGitSnapshotAdapter(
                clone_port=FakeClone(workspace),
                github_factory=lambda t: MagicMock(),
            )
            data = adapter.read_file(
                GitHubSnapshotSource(full_name="o/r", token="t"),
                commit_sha=sha,
                path="a.py",
            )
            self.assertEqual(data, b"z\n")
