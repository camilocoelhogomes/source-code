"""Unitários de FileDiffSet — T08."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from github_rag.snapshot.diff import FileChangeKind, FileDiff, FileDiffSet
from github_rag.snapshot.models import LocalSnapshotSource
from github_rag.snapshot.provider import DefaultMainSnapshotProvider
from tests.unit.snapshot.helpers import (
    commit_files,
    init_repo_with_main,
    rename_and_commit,
)


class TestFileDiffModels(unittest.TestCase):
    def test_u_d01_file_diff_set_fields(self) -> None:
        diff = FileDiffSet(
            added=("b.py",),
            modified=("a.py",),
            deleted=("c.py",),
        )
        self.assertEqual(diff.added, ("b.py",))
        self.assertEqual(diff.modified, ("a.py",))
        self.assertEqual(diff.deleted, ("c.py",))
        item = FileDiff(path="a.py", change=FileChangeKind.MODIFIED)
        self.assertEqual(item.change, FileChangeKind.MODIFIED)


class TestRenameDiff(unittest.TestCase):
    def test_u_d02_rename_as_deleted_and_added(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sha_a = init_repo_with_main(root, files={"old.py": b"x\n"})
            sha_b = rename_and_commit(root, "old.py", "new.py")
            provider = DefaultMainSnapshotProvider()
            source = LocalSnapshotSource(local_path=str(root))
            result = provider.diff_files(
                source, from_commit=sha_a, to_commit=sha_b
            )
            assert isinstance(result, FileDiffSet)
            self.assertIn("old.py", result.deleted)
            self.assertIn("new.py", result.added)
            self.assertNotIn("old.py", result.added)
            self.assertNotIn("new.py", result.deleted)
