"""Unit — boot popula CatalogIssueStore (T25 / UT-D01)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi import FastAPI

from github_rag.sources.local.discovery import LocalDiscoveryIssue
from github_rag.ui.issues import InMemoryCatalogIssueStore
from tests.unit.delivery.helpers import (
    RecordingReconcile,
    RecordingScheduler,
    RecordingSurfaces,
    RecordingSync,
    base_environ,
    patch_infra,
    write_valid_config,
)


class TestBootPopulatesIssueStore(unittest.TestCase):
    def test_ut_d01_boot_replaces_issue_store_from_sync_result(self) -> None:
        from github_rag.delivery import DefaultContainerRuntime

        issue = LocalDiscoveryIssue(
            connection_name="local-missing",
            path="/repos/__missing__",
            message="volume inaccessible",
        )
        store = InMemoryCatalogIssueStore()
        sync = RecordingSync(local_issues=(issue,))
        surfaces = RecordingSurfaces()
        reconcile = RecordingReconcile()
        scheduler = RecordingScheduler()

        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            runtime = DefaultContainerRuntime(
                environ=base_environ(config_path=cfg),
                sync=sync,
                reconcile=reconcile,
                scheduler=scheduler,
                bind_ui=surfaces.bind_ui,
                bind_mcp=surfaces.bind_mcp,
                skip_infra=True,
                issue_store=store,
                ui=mock.Mock(build=mock.Mock(return_value=FastAPI())),
                mcp=mock.Mock(build=mock.Mock(return_value=object())),
            )
            with patch_infra():
                runtime.boot()

        listed = store.list_issues()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].connection_name, "local-missing")
        self.assertIn("inaccessible", listed[0].message.lower())


if __name__ == "__main__":
    unittest.main()
