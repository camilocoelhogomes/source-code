"""Unit tests — DefaultStartupIndexReconcile corners."""

from __future__ import annotations

import unittest

from github_rag.catalog.models import RepoState
from tests.unit.indexing.helpers import (
    FakeSnapshotProvider,
    make_orchestrator,
    seed_repo,
)


class TestStartupReconcileCorners(unittest.TestCase):
    def test_tip_failure_still_recovers_by_state(self) -> None:
        class BoomSnap(FakeSnapshotProvider):
            def get_main_tip(self, source):  # noqa: ANN001
                raise RuntimeError("no tip")

        _orch, reconcile, catalog, _, _, _ = make_orchestrator(
            snapshot=BoomSnap()
        )
        rid = seed_repo(catalog, state=RepoState.QUEUED)
        reconcile.run()
        self.assertEqual(catalog.get_repository(rid).state, RepoState.QUEUED)

    def test_defer_enqueue_skips_queue(self) -> None:
        from github_rag.indexing.startup_reconcile import DefaultStartupIndexReconcile

        orch, _reconcile, catalog, snap, _, _ = make_orchestrator()
        snap.tip = "C1"
        rid = seed_repo(catalog, state=RepoState.NOT_INDEXED)
        defer = DefaultStartupIndexReconcile(
            catalog=catalog,
            snapshot=snap,
            orchestrator=orch,
            defer_enqueue=True,
        )
        defer.run()
        self.assertEqual(catalog.get_repository(rid).state, RepoState.NOT_INDEXED)


if __name__ == "__main__":
    unittest.main()
