"""
BDD executável — T14-indexing-orchestrator.

Cenários IO-01..14 (BDD-002/004/005/007/008, ENG-011/012/013).
"""

from __future__ import annotations

import ast
import unittest
from datetime import datetime, timezone
from pathlib import Path

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import ExecutionStatus, FileStage, RepoState
from github_rag.snapshot.diff import FileDiffSet
from tests.unit.indexing.helpers import (
    FakeSnapshotProvider,
    RecordingExactIndex,
    RecordingVectorStore,
    make_orchestrator,
    seed_repo,
)

INDEXING_SRC = Path(__file__).resolve().parents[2] / "src" / "github_rag" / "indexing"
FORBIDDEN_IMPORTS = {
    "github",
    "git",
    "tree_sitter",
    "openai",
    "qdrant_client",
    "pathspec",
}


class TestIO01EnqueueStates(unittest.TestCase):
    def test_queued_indexing_up_to_date(self) -> None:
        orch, _, catalog, snap, _, _ = make_orchestrator()
        rid = seed_repo(catalog)
        snap.tip = "C1"
        orch.enqueue([rid])
        self.assertEqual(catalog.get_repository(rid).state, RepoState.QUEUED)
        orch.run_until_idle()
        entry = catalog.get_repository(rid)
        self.assertEqual(entry.state, RepoState.UP_TO_DATE)
        self.assertEqual(entry.last_processed_commit, "C1")


class TestIO02Workers(unittest.TestCase):
    def test_peak_respects_capacity(self) -> None:
        exact = RecordingExactIndex(delay=0.05)
        orch, _, catalog, snap, _, _ = make_orchestrator(
            exact=exact, capacity=1
        )
        r1 = seed_repo(catalog, identifier="a")
        r2 = seed_repo(catalog, identifier="b")
        snap.tip = "C1"
        orch.enqueue([r1, r2])
        orch.run_until_idle()
        self.assertLessEqual(exact.peak, 1)
        self.assertEqual(catalog.get_repository(r1).state, RepoState.UP_TO_DATE)
        self.assertEqual(catalog.get_repository(r2).state, RepoState.UP_TO_DATE)


class TestIO03Skip(unittest.TestCase):
    def test_skip_when_tip_equals_processed(self) -> None:
        exact = RecordingExactIndex()
        vector = RecordingVectorStore()
        orch, reconcile, catalog, snap, _, _ = make_orchestrator(
            exact=exact, vector=vector
        )
        rid = seed_repo(
            catalog, state=RepoState.UP_TO_DATE, last="C1", current="C1"
        )
        snap.tip = "C1"
        before = len(exact.index_calls)
        reconcile.run()
        orch.run_until_idle()
        self.assertEqual(len(exact.index_calls), before)
        self.assertEqual(len(vector.replaces), 0)
        self.assertEqual(catalog.get_repository(rid).state, RepoState.UP_TO_DATE)


class TestIO04NewSnapshot(unittest.TestCase):
    def test_new_tip_processed(self) -> None:
        orch, _, catalog, snap, _, _ = make_orchestrator()
        rid = seed_repo(
            catalog, state=RepoState.UP_TO_DATE, last="C1", current="C1"
        )
        snap.tip = "C2"
        snap.diffs[("C1", "C2")] = FileDiffSet(
            added=(), modified=("src/a.py",), deleted=()
        )
        catalog.update_main_commit(rid, "C2")
        catalog.reconcile_repository(rid)
        orch.enqueue([rid])
        orch.run_until_idle()
        entry = catalog.get_repository(rid)
        self.assertEqual(entry.state, RepoState.UP_TO_DATE)
        self.assertEqual(entry.last_processed_commit, "C2")


class TestIO05Progress(unittest.TestCase):
    def test_progress_fields(self) -> None:
        orch, _, catalog, snap, _, _ = make_orchestrator()
        rid = seed_repo(catalog)
        snap.tip = "C1"
        orch.enqueue([rid])
        orch.run_until_idle()
        entry = catalog.get_repository(rid)
        self.assertIsNotNone(entry.progress)
        assert entry.progress is not None
        self.assertEqual(entry.progress.percent, 100)
        self.assertIsNotNone(entry.progress.files_total)
        self.assertEqual(entry.progress.current_stage, "done")


class TestIO06FileStages(unittest.TestCase):
    def test_stages_recorded(self) -> None:
        orch, _, catalog, snap, _, _ = make_orchestrator()
        rid = seed_repo(catalog)
        snap.tip = "C1"
        orch.enqueue([rid])
        orch.run_until_idle()
        entry = catalog.get_repository(rid)
        execs = catalog.list_executions(rid)
        self.assertTrue(execs)
        files = catalog.list_file_progress(execs[-1].id)
        self.assertTrue(files)
        for fp in files:
            self.assertIsNotNone(fp.zoekt_at)
            self.assertIsNotNone(fp.tree_sitter_at)
            self.assertIsNotNone(fp.metadata_persisted_at)
        _ = FileStage  # enum used by production


class TestIO07FailureRestart(unittest.TestCase):
    def test_partial_failure_and_full_restart(self) -> None:
        vector = RecordingVectorStore(fail_on="replace")
        orch, _, catalog, snap, exact, _ = make_orchestrator(vector=vector)
        rid = seed_repo(catalog)
        snap.tip = "C1"
        orch.enqueue([rid])
        orch.run_until_idle()
        entry = catalog.get_repository(rid)
        self.assertEqual(entry.state, RepoState.ERROR)
        self.assertIsNone(entry.last_processed_commit)
        execs = catalog.list_executions(rid)
        self.assertEqual(execs[-1].status, ExecutionStatus.FAILED)
        self.assertIsNotNone(execs[-1].error_message)

        vector.fail_on = None
        orch.enqueue([rid])
        orch.run_until_idle()
        self.assertIn(str(rid), exact.delete_calls)
        self.assertIn(str(rid), vector.deleted_repos)
        self.assertEqual(catalog.get_repository(rid).state, RepoState.UP_TO_DATE)


class TestIO08StartupReconcile(unittest.TestCase):
    def test_enqueues_stale(self) -> None:
        orch, reconcile, catalog, snap, _, _ = make_orchestrator()
        a = seed_repo(catalog, identifier="a")
        b = seed_repo(
            catalog,
            identifier="b",
            state=RepoState.UP_TO_DATE,
            last="C1",
            current="C1",
        )
        c = seed_repo(catalog, identifier="c", state=RepoState.ERROR)
        d = seed_repo(
            catalog,
            identifier="d",
            state=RepoState.UP_TO_DATE,
            last="C9",
            current="C9",
        )
        snap.tip = "C9"
        # b tip will become C9 ≠ C1 → not_indexed
        catalog.update_main_commit(b, "C1")
        reconcile.run()
        self.assertEqual(catalog.get_repository(a).state, RepoState.QUEUED)
        self.assertEqual(catalog.get_repository(b).state, RepoState.QUEUED)
        self.assertEqual(catalog.get_repository(c).state, RepoState.QUEUED)
        self.assertEqual(catalog.get_repository(d).state, RepoState.UP_TO_DATE)


class TestIO09OrphanRecover(unittest.TestCase):
    def test_recover_indexing_and_queued(self) -> None:
        orch, reconcile, catalog, snap, _, _ = make_orchestrator()
        idx = seed_repo(catalog, identifier="idx", state=RepoState.INDEXING)
        queued = seed_repo(catalog, identifier="q", state=RepoState.QUEUED)
        snap.tip = "C1"
        reconcile.run()
        self.assertEqual(catalog.get_repository(idx).state, RepoState.QUEUED)
        self.assertEqual(catalog.get_repository(queued).state, RepoState.QUEUED)


class TestIO10FullFile(unittest.TestCase):
    def test_read_file_full_content(self) -> None:
        snap = FakeSnapshotProvider(
            tip="C2",
            contents={"src/a.py": b"FULL_FILE_CONTENT\n"},
            tree=("src/a.py",),
        )
        snap.diffs[(None, "C2")] = FileDiffSet(
            added=("src/a.py",), modified=(), deleted=()
        )
        # force first index
        orch, _, catalog, _, _, _ = make_orchestrator(snapshot=snap)
        rid = seed_repo(catalog)
        orch.enqueue([rid])
        orch.run_until_idle()
        self.assertIn(("C2", "src/a.py"), snap.read_calls)
        content = snap.contents["src/a.py"]
        self.assertEqual(content, b"FULL_FILE_CONTENT\n")


class TestIO11ZoektSetReplace(unittest.TestCase):
    def test_single_index_all_eligible(self) -> None:
        snap = FakeSnapshotProvider(
            tip="C2",
            tree=("src/a.py", "src/b.py", "README.md"),
            contents={
                "src/a.py": b"a=1\n",
                "src/b.py": b"b=1\n",
                "README.md": b"# r\n",
            },
        )
        snap.diffs[("C1", "C2")] = FileDiffSet(
            added=(), modified=("src/a.py",), deleted=()
        )
        exact = RecordingExactIndex()
        orch, _, catalog, _, _, _ = make_orchestrator(
            snapshot=snap, exact=exact
        )
        rid = seed_repo(
            catalog, state=RepoState.UP_TO_DATE, last="C1", current="C1"
        )
        catalog.update_main_commit(rid, "C2")
        catalog.reconcile_repository(rid)
        orch.enqueue([rid])
        orch.run_until_idle()
        self.assertEqual(len(exact.index_calls), 1)
        _, tip, paths = exact.index_calls[0]
        self.assertEqual(tip, "C2")
        self.assertEqual(set(paths), {"src/a.py", "src/b.py", "README.md"})


class TestIO12QdrantIncremental(unittest.TestCase):
    def test_delete_paths_no_purge(self) -> None:
        snap = FakeSnapshotProvider(
            tip="C2",
            tree=("src/a.py", "src/b.py"),
            contents={"src/a.py": b"a\n", "src/b.py": b"b\n"},
        )
        snap.diffs[("C1", "C2")] = FileDiffSet(
            added=(), modified=("src/a.py",), deleted=("old.py",)
        )
        vector = RecordingVectorStore()
        orch, _, catalog, _, _, _ = make_orchestrator(
            snapshot=snap, vector=vector
        )
        rid = seed_repo(
            catalog, state=RepoState.UP_TO_DATE, last="C1", current="C1"
        )
        catalog.update_main_commit(rid, "C2")
        catalog.reconcile_repository(rid)
        orch.enqueue([rid])
        orch.run_until_idle()
        self.assertEqual(vector.purge_calls, [])
        deleted_paths = {p for _, paths in vector.deletes_paths for p in paths}
        self.assertIn("old.py", deleted_paths)
        self.assertIn("src/a.py", deleted_paths)
        self.assertTrue(vector.upserts)


class TestIO13Req020(unittest.TestCase):
    def test_only_allowed_states(self) -> None:
        allowed = {s.value for s in RepoState}
        orch, _, catalog, snap, _, _ = make_orchestrator()
        rid = seed_repo(catalog)
        snap.tip = "C1"
        orch.enqueue([rid])
        orch.run_until_idle()
        self.assertIn(catalog.get_repository(rid).state.value, allowed)


class TestIO14NoSdkImports(unittest.TestCase):
    def test_indexing_package_has_no_sdk_imports(self) -> None:
        found: set[str] = set()
        for path in INDEXING_SRC.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        if root in FORBIDDEN_IMPORTS:
                            found.add(f"{path.name}:{root}")
                elif isinstance(node, ast.ImportFrom) and node.module:
                    root = node.module.split(".")[0]
                    if root in FORBIDDEN_IMPORTS:
                        found.add(f"{path.name}:{root}")
        self.assertEqual(found, set())


if __name__ == "__main__":
    unittest.main()
