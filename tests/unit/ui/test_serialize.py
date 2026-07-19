"""Unit — serialize CatalogEntry → JSON UI (T18)."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from github_rag.catalog.models import (
    CatalogEntry,
    ExecutionStatus,
    FileProgress,
    IndexingExecution,
    Progress,
    RepoOrigin,
    RepoState,
)
from github_rag.ui.serialize import (
    execution_to_view,
    file_progress_to_view,
    repo_to_detail,
    repo_to_view,
)


class TestSerialize(unittest.TestCase):
    def test_github_and_local_origin(self) -> None:
        gh = CatalogEntry(
            id=1,
            connection_name="gh",
            origin=RepoOrigin.GITHUB,
            repo_identifier="acme/api",
            state=RepoState.NOT_INDEXED,
            active=True,
            row_version=1,
            github_org="acme",
        )
        local = CatalogEntry(
            id=2,
            connection_name="local",
            origin=RepoOrigin.LOCAL,
            repo_identifier="api",
            state=RepoState.UP_TO_DATE,
            active=True,
            row_version=1,
            local_path="/repos/api",
        )
        self.assertEqual(repo_to_view(gh)["origin"], "github")
        self.assertEqual(repo_to_view(gh)["state_label"], "não indexado")
        self.assertEqual(repo_to_view(local)["origin"], "local")
        self.assertEqual(repo_to_view(local)["state_label"], "atualizado")

    def test_progress_none(self) -> None:
        entry = CatalogEntry(
            id=1,
            connection_name="gh",
            origin=RepoOrigin.GITHUB,
            repo_identifier="acme/api",
            state=RepoState.QUEUED,
            active=True,
            row_version=1,
            github_org="acme",
            progress=None,
        )
        self.assertIsNone(repo_to_view(entry)["progress"])

    def test_file_flags(self) -> None:
        fp = FileProgress(
            id=1,
            execution_id=9,
            file_path="src/a.py",
            zoekt_at=datetime.now(UTC),
            tree_sitter_at=None,
            metadata_persisted_at=None,
        )
        view = file_progress_to_view(fp)
        self.assertTrue(view["zoekt"])
        self.assertFalse(view["tree_sitter"])
        self.assertFalse(view["metadata_persisted"])

    def test_execution_failed_fields(self) -> None:
        err_at = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
        ex = IndexingExecution(
            id=3,
            repository_id=1,
            status=ExecutionStatus.FAILED,
            started_at=err_at,
            finished_at=err_at,
            error_message="partial failure",
            error_at=err_at,
            commit_target="abc",
        )
        view = execution_to_view(ex)
        self.assertEqual(view["error_message"], "partial failure")
        self.assertEqual(view["error_at"], err_at.isoformat())

    def test_detail_includes_files(self) -> None:
        entry = CatalogEntry(
            id=1,
            connection_name="gh",
            origin=RepoOrigin.GITHUB,
            repo_identifier="acme/api",
            state=RepoState.INDEXING,
            active=True,
            row_version=2,
            github_org="acme",
            progress=Progress(40, 2, 5, "zoekt"),
            current_execution_id=9,
        )
        files = [
            FileProgress(id=1, execution_id=9, file_path="a.py", zoekt_at=datetime.now(UTC))
        ]
        detail = repo_to_detail(entry, files)
        self.assertEqual(detail["progress"]["percent"], 40)
        self.assertEqual(len(detail["files"]), 1)


if __name__ == "__main__":
    unittest.main()
