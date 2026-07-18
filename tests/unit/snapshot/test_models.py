"""Unitários de models e erros — T08."""

from __future__ import annotations

import unittest

from github_rag.catalog.models import RepoOrigin
from github_rag.snapshot.errors import (
    CommitNotFoundError,
    CorruptRepositoryError,
    FileNotFoundInCommitError,
    GitHubSnapshotNetworkError,
    MainBranchMissingError,
    SnapshotError,
)
from github_rag.snapshot.models import FirstIndexSignal, MainSnapshot


class TestSnapshotModels(unittest.TestCase):
    def test_u_m01_main_snapshot_frozen(self) -> None:
        snap = MainSnapshot(
            origin=RepoOrigin.LOCAL,
            repo_key="/tmp/r",
            commit_sha="a" * 40,
            branch="main",
        )
        with self.assertRaises(Exception):
            snap.commit_sha = "b" * 40  # type: ignore[misc]

    def test_u_m02_first_index_signal(self) -> None:
        signal = FirstIndexSignal(to_commit="c" * 40)
        self.assertEqual(signal.to_commit, "c" * 40)

    def test_u_m03_error_hierarchy(self) -> None:
        for cls in (
            MainBranchMissingError,
            CorruptRepositoryError,
            GitHubSnapshotNetworkError,
            CommitNotFoundError,
            FileNotFoundInCommitError,
        ):
            self.assertTrue(issubclass(cls, SnapshotError))

    def test_u_m04_network_error_no_token_in_str(self) -> None:
        token = "ghp_super_secret_token_value"
        exc = GitHubSnapshotNetworkError("falha de rede ao obter tip")
        self.assertNotIn(token, str(exc))
        self.assertNotIn(token, repr(exc))
