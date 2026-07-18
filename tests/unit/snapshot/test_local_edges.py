"""Corner cases adicionais do adaptador local — cobertura T08."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from git.exc import GitCommandError

from github_rag.snapshot.errors import (
    CommitNotFoundError,
    CorruptRepositoryError,
    FileNotFoundInCommitError,
    MainBranchMissingError,
    SnapshotError,
)
from github_rag.snapshot.local import (
    LocalGitSnapshotAdapter,
    _diff_name_status,
    _has_main_head,
    _main_commit,
    _open_repo,
    _read_blob,
    _resolve_commit,
)
from github_rag.snapshot.models import LocalSnapshotSource
from github_rag.snapshot.provider import DefaultMainSnapshotProvider
from tests.unit.snapshot.helpers import init_repo_with_main


class TestLocalEdges(unittest.TestCase):
    def test_open_repo_generic_exception(self) -> None:
        with patch(
            "github_rag.snapshot.local.Repo",
            side_effect=RuntimeError("weird"),
        ):
            with self.assertRaises(CorruptRepositoryError):
                _open_repo("/tmp/x")

    def test_main_commit_missing_via_exception_message(self) -> None:
        repo = MagicMock()
        type(repo).heads = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("main missing"))
        )
        with patch(
            "github_rag.snapshot.local._has_main_head", return_value=False
        ):
            with self.assertRaises(MainBranchMissingError):
                _main_commit(repo)

    def test_has_main_head_true_false(self) -> None:
        repo = MagicMock()
        head = MagicMock()
        head.name = "main"
        repo.heads = [head]
        self.assertTrue(_has_main_head(repo))
        repo.heads = []
        self.assertFalse(_has_main_head(repo))
        repo.heads = property(lambda self: (_ for _ in ()).throw(RuntimeError()))  # type: ignore[assignment]
        # broken heads iteration
        broken = MagicMock()
        broken.heads = None
        type(broken).heads = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("x"))
        )
        self.assertFalse(_has_main_head(broken))

    def test_resolve_commit_generic(self) -> None:
        repo = MagicMock()
        repo.commit.side_effect = RuntimeError("bad")
        with self.assertRaises(CommitNotFoundError):
            _resolve_commit(repo, "a" * 40)

    def test_read_blob_not_file(self) -> None:
        commit = MagicMock()
        tree = MagicMock()
        blob = MagicMock()
        blob.type = "tree"
        tree.__truediv__ = MagicMock(return_value=blob)
        commit.tree = tree
        with self.assertRaises(FileNotFoundInCommitError):
            _read_blob(commit, "dir")

    def test_diff_git_command_error(self) -> None:
        repo = MagicMock()
        repo.git.diff.side_effect = GitCommandError("diff", 1)
        with self.assertRaises(SnapshotError):
            _diff_name_status(repo, "a" * 40, "b" * 40)

    def test_diff_rename_status_fallback(self) -> None:
        repo = MagicMock()
        repo.git.diff.return_value = "R100\told.py\tnew.py\n\nM\tkeep.py\n"
        result = _diff_name_status(repo, "a" * 40, "b" * 40)
        self.assertIn("old.py", result.deleted)
        self.assertIn("new.py", result.added)
        self.assertIn("keep.py", result.modified)

    def test_provider_github_diff_and_type_errors(self) -> None:
        provider = DefaultMainSnapshotProvider(
            clone_port=MagicMock(
                ensure_commits=MagicMock(return_value=Path("/nope"))
            )
        )
        with self.assertRaises(TypeError):
            provider.list_tree(object(), commit_sha="a" * 40)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            provider.read_file(
                object(), commit_sha="a" * 40, path="x"  # type: ignore[arg-type]
            )
        with self.assertRaises(TypeError):
            provider.diff_files(
                object(), from_commit=None, to_commit="a" * 40  # type: ignore[arg-type]
            )

    def test_github_diff_files_via_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            sha_a = init_repo_with_main(workspace, files={"a.py": b"1\n"})
            from tests.unit.snapshot.helpers import commit_files

            sha_b = commit_files(workspace, {"b.py": b"2\n"})

            class Port:
                def ensure_commits(self, **kwargs):  # type: ignore[no-untyped-def]
                    return workspace

            from unittest.mock import MagicMock as MM

            from github_rag.snapshot.models import GitHubSnapshotSource
            from github_rag.snapshot.provider import DefaultMainSnapshotProvider

            def factory(token: str) -> MM:
                gh = MM()
                repo = MM()
                branch = MM()
                commit = MM()
                commit.sha = sha_b
                branch.commit = commit
                repo.get_branch.return_value = branch
                gh.get_repo.return_value = repo
                return gh

            provider = DefaultMainSnapshotProvider(
                clone_port=Port(),  # type: ignore[arg-type]
                github_factory=factory,
            )
            source = GitHubSnapshotSource(full_name="o/r", token="t")
            from github_rag.snapshot.diff import FileDiffSet
            from github_rag.snapshot.models import FirstIndexSignal

            first = provider.diff_files(
                source, from_commit=None, to_commit=sha_b
            )
            self.assertIsInstance(first, FirstIndexSignal)
            diff = provider.diff_files(
                source, from_commit=sha_a, to_commit=sha_b
            )
            self.assertIsInstance(diff, FileDiffSet)
