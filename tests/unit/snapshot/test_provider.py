"""Unitários da fachada DefaultMainSnapshotProvider — T08."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Sequence
from unittest.mock import MagicMock

from github_rag.catalog.models import RepoOrigin
from github_rag.snapshot.models import (
    GitHubSnapshotSource,
    LocalSnapshotSource,
)
from github_rag.snapshot.provider import DefaultMainSnapshotProvider
from tests.unit.snapshot.helpers import init_repo_with_main


class FakeClonePort:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def ensure_commits(
        self,
        *,
        full_name: str,
        token: str,
        commit_shas: Sequence[str],
    ) -> Path:
        return self.workspace


class TestDefaultProvider(unittest.TestCase):
    def test_u_p01_dispatches_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sha = init_repo_with_main(root, files={"a.py": b"1\n"})
            tip = DefaultMainSnapshotProvider().get_main_tip(
                LocalSnapshotSource(local_path=str(root))
            )
            self.assertEqual(tip.origin, RepoOrigin.LOCAL)
            self.assertEqual(tip.commit_sha, sha)

    def test_u_p02_dispatches_github(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            sha = init_repo_with_main(workspace, files={"a.py": b"1\n"})

            def factory(token: str) -> MagicMock:
                gh = MagicMock()
                repo = MagicMock()
                branch = MagicMock()
                commit = MagicMock()
                commit.sha = sha
                branch.commit = commit
                repo.get_branch.return_value = branch
                gh.get_repo.return_value = repo
                return gh

            tip = DefaultMainSnapshotProvider(
                clone_port=FakeClonePort(workspace),
                github_factory=factory,
            ).get_main_tip(
                GitHubSnapshotSource(full_name="o/r", token="t")
            )
            self.assertEqual(tip.origin, RepoOrigin.GITHUB)
            self.assertEqual(tip.commit_sha, sha)

    def test_u_p03_invalid_source_type(self) -> None:
        provider = DefaultMainSnapshotProvider()
        with self.assertRaises((TypeError, AttributeError)):
            provider.get_main_tip(object())  # type: ignore[arg-type]
