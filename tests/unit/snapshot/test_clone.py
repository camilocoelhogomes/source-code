"""Unitários de ShallowGitClonePort — T08."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from git.exc import GitCommandError

from github_rag.snapshot.clone import ShallowGitClonePort, _has_commit
from github_rag.snapshot.errors import (
    CommitNotFoundError,
    GitHubSnapshotNetworkError,
)
from tests.unit.snapshot.helpers import init_repo_with_main


class TestShallowGitClonePort(unittest.TestCase):
    def test_invalid_full_name(self) -> None:
        port = ShallowGitClonePort()
        with self.assertRaises(GitHubSnapshotNetworkError):
            port.ensure_commits(
                full_name="nopath",
                token="t",
                commit_shas=["a" * 40],
            )

    def test_reuses_existing_workspace_with_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "acme_demo"
            sha = init_repo_with_main(workspace, files={"a.py": b"1\n"})
            port = ShallowGitClonePort(work_root=root)
            path = port.ensure_commits(
                full_name="acme/demo",
                token="secret",
                commit_shas=[sha],
            )
            self.assertEqual(path, workspace)

    def test_clone_from_fetches_missing_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_repo = MagicMock()
            # first has_commit False, after fetch True
            states = {"fetched": False}

            def commit_lookup(sha: str):
                if states["fetched"]:
                    return MagicMock()
                raise Exception("missing")

            def fetch(*_a, **_k):
                states["fetched"] = True

            fake_repo.commit.side_effect = commit_lookup
            fake_repo.git.fetch.side_effect = fetch
            cw = MagicMock()
            cw.__enter__ = MagicMock(return_value=cw)
            cw.__exit__ = MagicMock(return_value=False)
            cw.has_section.return_value = True
            fake_repo.config_writer.return_value = cw

            with patch(
                "github_rag.snapshot.clone.Repo.clone_from",
                return_value=fake_repo,
            ):
                port = ShallowGitClonePort(work_root=root)
                path = port.ensure_commits(
                    full_name="acme/demo",
                    token="tok",
                    commit_shas=["b" * 40],
                )
                self.assertEqual(path.name, "acme_demo")
                fake_repo.git.fetch.assert_called()
                cw.set.assert_called()

    def test_fetch_failure_commit_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_repo = MagicMock()
            fake_repo.commit.side_effect = Exception("missing")
            fake_repo.git.fetch.side_effect = GitCommandError("fetch", 1)
            cw = MagicMock()
            cw.__enter__ = MagicMock(return_value=cw)
            cw.__exit__ = MagicMock(return_value=False)
            cw.has_section.return_value = False
            fake_repo.config_writer.return_value = cw

            with patch(
                "github_rag.snapshot.clone.Repo.clone_from",
                return_value=fake_repo,
            ):
                port = ShallowGitClonePort(work_root=root)
                with self.assertRaises(CommitNotFoundError):
                    port.ensure_commits(
                        full_name="acme/demo",
                        token="tok",
                        commit_shas=["a" * 40],
                    )

    def test_fetch_succeeds_but_commit_still_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_repo = MagicMock()
            fake_repo.commit.side_effect = Exception("missing")
            fake_repo.git.fetch.return_value = None
            cw = MagicMock()
            cw.__enter__ = MagicMock(return_value=cw)
            cw.__exit__ = MagicMock(return_value=False)
            cw.has_section.return_value = False
            fake_repo.config_writer.return_value = cw

            with patch(
                "github_rag.snapshot.clone.Repo.clone_from",
                return_value=fake_repo,
            ):
                port = ShallowGitClonePort(work_root=root)
                with self.assertRaises(CommitNotFoundError):
                    port.ensure_commits(
                        full_name="acme/demo",
                        token="tok",
                        commit_shas=["a" * 40],
                    )

    def test_clone_generic_failure_hides_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "github_rag.snapshot.clone.Repo.clone_from",
                side_effect=RuntimeError("boom"),
            ):
                port = ShallowGitClonePort(work_root=root)
                with self.assertRaises(GitHubSnapshotNetworkError) as ctx:
                    port.ensure_commits(
                        full_name="acme/demo",
                        token="super_secret_token",
                        commit_shas=["a" * 40],
                    )
                self.assertNotIn("super_secret_token", str(ctx.exception))

    def test_has_commit_helpers(self) -> None:
        ok = MagicMock()
        ok.commit.return_value = MagicMock()
        self.assertTrue(_has_commit(ok, "a" * 40))
        bad = MagicMock()
        bad.commit.side_effect = Exception("nope")
        self.assertFalse(_has_commit(bad, "a" * 40))
