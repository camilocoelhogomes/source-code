"""Unit tests — DefaultIndexingOrchestrator corners."""

from __future__ import annotations

import unittest

from github_rag.catalog.models import RepoOrigin, RepoState
from github_rag.indexing.errors import RepositorySourceError
from github_rag.indexing.orchestrator import snapshot_source_for
from github_rag.snapshot.diff import FileDiffSet
from github_rag.snapshot.models import GitHubSnapshotSource, LocalSnapshotSource
from tests.unit.indexing.helpers import (
    FakeSnapshotProvider,
    RecordingExactIndex,
    RecordingVectorStore,
    make_orchestrator,
    seed_repo,
)


class TestSnapshotSourceFor(unittest.TestCase):
    def test_local(self) -> None:
        from github_rag.catalog.models import CatalogEntry

        entry = CatalogEntry(
            id=1,
            connection_name="c",
            origin=RepoOrigin.LOCAL,
            repo_identifier="svc",
            state=RepoState.NOT_INDEXED,
            active=True,
            row_version=1,
            local_path="/repos/svc",
        )
        src = snapshot_source_for(entry, github_token=None)
        self.assertIsInstance(src, LocalSnapshotSource)

    def test_github_requires_token(self) -> None:
        from github_rag.catalog.models import CatalogEntry

        entry = CatalogEntry(
            id=1,
            connection_name="c",
            origin=RepoOrigin.GITHUB,
            repo_identifier="o/r",
            state=RepoState.NOT_INDEXED,
            active=True,
            row_version=1,
            github_org="o",
        )
        with self.assertRaises(RepositorySourceError):
            snapshot_source_for(entry, github_token=None)
        src = snapshot_source_for(entry, github_token="tok")
        self.assertIsInstance(src, GitHubSnapshotSource)


class TestOrchestratorCorners(unittest.TestCase):
    def test_enqueue_skips_up_to_date(self) -> None:
        orch, _, catalog, _, exact, _ = make_orchestrator()
        rid = seed_repo(
            catalog, state=RepoState.UP_TO_DATE, last="C1", current="C1"
        )
        orch.enqueue([rid])
        orch.run_until_idle()
        self.assertEqual(exact.index_calls, [])

    def test_enqueue_dedupe(self) -> None:
        orch, _, catalog, snap, exact, _ = make_orchestrator()
        rid = seed_repo(catalog)
        snap.tip = "C1"
        orch.enqueue([rid, rid])
        orch.run_until_idle()
        self.assertEqual(len(exact.index_calls), 1)

    def test_index_repository_direct(self) -> None:
        orch, _, catalog, snap, _, _ = make_orchestrator()
        rid = seed_repo(catalog)
        snap.tip = "C1"
        orch.index_repository(rid)
        self.assertEqual(
            catalog.get_repository(rid).state, RepoState.UP_TO_DATE
        )

    def test_first_index_uses_replace(self) -> None:
        vector = RecordingVectorStore()
        orch, _, catalog, snap, _, _ = make_orchestrator(vector=vector)
        rid = seed_repo(catalog)
        snap.tip = "C1"
        orch.index_repository(rid)
        self.assertTrue(vector.replaces)
        self.assertEqual(vector.upserts, [])

    def test_local_path_missing(self) -> None:
        from github_rag.catalog.models import CatalogEntry

        entry = CatalogEntry(
            id=1,
            connection_name="c",
            origin=RepoOrigin.LOCAL,
            repo_identifier="svc",
            state=RepoState.NOT_INDEXED,
            active=True,
            row_version=1,
            local_path=None,
        )
        with self.assertRaises(RepositorySourceError):
            snapshot_source_for(entry, github_token=None)

    def test_enqueue_requeues_indexing(self) -> None:
        orch, _, catalog, snap, exact, _ = make_orchestrator()
        rid = seed_repo(
            catalog, state=RepoState.INDEXING, last=None, current="C1"
        )
        snap.tip = "C1"
        orch.enqueue([rid])
        orch.run_until_idle()
        self.assertEqual(catalog.get_repository(rid).state, RepoState.UP_TO_DATE)
        self.assertEqual(len(exact.index_calls), 1)

    def test_index_from_error_state(self) -> None:
        orch, _, catalog, snap, exact, vector = make_orchestrator()
        rid = seed_repo(catalog, state=RepoState.ERROR)
        snap.tip = "C1"
        orch.index_repository(rid)
        self.assertEqual(catalog.get_repository(rid).state, RepoState.UP_TO_DATE)
        self.assertTrue(exact.delete_calls)
        self.assertTrue(vector.deleted_repos)

    def test_index_while_already_indexing_skip_same_tip(self) -> None:
        orch, _, catalog, snap, exact, _ = make_orchestrator()
        rid = seed_repo(
            catalog, state=RepoState.INDEXING, last="C1", current="C1"
        )
        snap.tip = "C1"
        orch.index_repository(rid)
        self.assertEqual(catalog.get_repository(rid).state, RepoState.UP_TO_DATE)
        self.assertEqual(exact.index_calls, [])

    def test_direct_index_up_to_date_new_tip(self) -> None:
        snap = FakeSnapshotProvider(tip="C2")
        snap.diffs[("C1", "C2")] = FileDiffSet(
            added=(), modified=("src/a.py",), deleted=()
        )
        orch, _, catalog, _, _, vector = make_orchestrator(snapshot=snap)
        rid = seed_repo(
            catalog, state=RepoState.UP_TO_DATE, last="C1", current="C1"
        )
        orch.index_repository(rid)
        self.assertEqual(catalog.get_repository(rid).last_processed_commit, "C2")
        self.assertTrue(vector.upserts or vector.replaces)

    def test_bad_gitignore_bytes(self) -> None:
        snap = FakeSnapshotProvider(
            tip="C1",
            contents={
                "src/a.py": b"a=1\n",
                "README.md": b"#\n",
                ".gitignore": b"\xff\xfe",
            },
        )
        orch, _, catalog, _, _, _ = make_orchestrator(snapshot=snap)
        rid = seed_repo(catalog)
        orch.index_repository(rid)
        self.assertEqual(
            catalog.get_repository(rid).state, RepoState.UP_TO_DATE
        )

    def test_failure_from_up_to_date_marks_error(self) -> None:
        class BoomSnap(FakeSnapshotProvider):
            def get_main_tip(self, source):  # noqa: ANN001
                raise RuntimeError("tip boom")

        orch, _, catalog, _, _, _ = make_orchestrator(snapshot=BoomSnap())
        rid = seed_repo(
            catalog, state=RepoState.UP_TO_DATE, last="C1", current="C1"
        )
        orch.index_repository(rid)
        self.assertEqual(catalog.get_repository(rid).state, RepoState.ERROR)

    def test_last_execution_failed_swallows_list_error(self) -> None:
        orch, _, catalog, snap, _, _ = make_orchestrator()
        rid = seed_repo(catalog)
        snap.tip = "C1"

        def boom(_rid: int):
            raise RuntimeError("db down")

        catalog.list_executions = boom  # type: ignore[method-assign]
        orch.index_repository(rid)
        self.assertEqual(
            catalog.get_repository(rid).state, RepoState.UP_TO_DATE
        )

    def test_gitignore_root_loaded(self) -> None:
        snap = FakeSnapshotProvider(
            tip="C1",
            tree=("src/a.py", "ignored.bin"),
            contents={
                "src/a.py": b"a=1\n",
                "ignored.bin": b"\x00\x01",
                ".gitignore": b"*.bin\n",
            },
        )
        exact = RecordingExactIndex()
        orch, _, catalog, _, _, _ = make_orchestrator(
            snapshot=snap, exact=exact
        )
        rid = seed_repo(catalog)
        orch.index_repository(rid)
        paths = exact.index_calls[0][2]
        self.assertIn("src/a.py", paths)
        # bin may be excluded by eligibility denylist anyway
        self.assertNotIn("ignored.bin", paths)


if __name__ == "__main__":
    unittest.main()
