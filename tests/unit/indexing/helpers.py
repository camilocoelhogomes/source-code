"""Fakes e harness para testes T14."""

from __future__ import annotations

import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass, field

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoOrigin, RepoState
from github_rag.concurrency.limiter import SemaphoreWorkerLimiter
from github_rag.eligibility.filter import PathspecFileEligibilityFilter
from github_rag.index.chunk.types import (
    ChunkSourceFile,
    SemanticChunk,
    SourceLanguage,
    compute_chunk_id,
)
from github_rag.index.metadata.fakes import FakeMetadataGenerator
from github_rag.index.vector.types import RepoCommitScope, VectorRecord
from github_rag.index.zoekt.fake import FakeExactCodeIndex
from github_rag.indexing.orchestrator import DefaultIndexingOrchestrator
from github_rag.indexing.pipeline import DefaultFileRagPipeline
from github_rag.indexing.startup_reconcile import DefaultStartupIndexReconcile
from github_rag.snapshot.diff import FileDiffSet
from github_rag.snapshot.models import FirstIndexSignal, MainSnapshot, SnapshotSource


@dataclass
class FakeSnapshotProvider:
    tip: str = "C1"
    tree: tuple[str, ...] = ("src/a.py", "README.md")
    contents: dict[str, bytes] = field(
        default_factory=lambda: {
            "src/a.py": b"def a():\n    return 1\n",
            "README.md": b"# hi\n",
        }
    )
    diffs: dict[tuple[str | None, str], FileDiffSet | FirstIndexSignal] = field(
        default_factory=dict
    )
    read_calls: list[tuple[str, str]] = field(default_factory=list)

    def get_main_tip(self, source: SnapshotSource) -> MainSnapshot:
        key = getattr(source, "local_path", None) or getattr(
            source, "full_name", "repo"
        )
        return MainSnapshot(
            origin=RepoOrigin.LOCAL,
            repo_key=str(key),
            commit_sha=self.tip,
            branch="main",
        )

    def list_tree(self, source: SnapshotSource, *, commit_sha: str) -> tuple[str, ...]:
        return self.tree

    def read_file(
        self, source: SnapshotSource, *, commit_sha: str, path: str
    ) -> bytes:
        self.read_calls.append((commit_sha, path))
        if path not in self.contents:
            raise FileNotFoundError(path)
        return self.contents[path]

    def diff_files(
        self,
        source: SnapshotSource,
        *,
        from_commit: str | None,
        to_commit: str,
    ) -> FileDiffSet | FirstIndexSignal:
        key = (from_commit, to_commit)
        if key in self.diffs:
            return self.diffs[key]
        if from_commit is None:
            return FirstIndexSignal(to_commit=to_commit)
        return FileDiffSet(added=(), modified=(), deleted=())


class FakeChunker:
    def chunk(self, source: ChunkSourceFile) -> tuple[SemanticChunk, ...]:
        text = source.content.decode("utf-8", errors="replace")
        if not text.strip():
            return ()
        lang = SourceLanguage.PYTHON
        cid = compute_chunk_id(
            path=source.path, language=lang, kind="module", start_byte=0, end_byte=len(source.content)
        )
        return (
            SemanticChunk(
                chunk_id=cid,
                path=source.path,
                language=lang,
                kind="module",
                text=text,
                start_byte=0,
                end_byte=len(source.content),
                start_point=(0, 0),
                end_point=(text.count("\n"), 0),
            ),
        )


class FakeEmbedder:
    dimensions = 3

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        return tuple((float(i), 0.0, 1.0) for i, _ in enumerate(texts))


@dataclass
class RecordingVectorStore:
    upserts: list[tuple[RepoCommitScope, tuple[VectorRecord, ...]]] = field(
        default_factory=list
    )
    deletes_paths: list[tuple[RepoCommitScope, tuple[str, ...]]] = field(
        default_factory=list
    )
    replaces: list[tuple[RepoCommitScope, tuple[VectorRecord, ...]]] = field(
        default_factory=list
    )
    deleted_repos: list[str] = field(default_factory=list)
    purge_calls: list[RepoCommitScope] = field(default_factory=list)
    fail_on: str | None = None

    def upsert(self, scope: RepoCommitScope, records: Sequence[VectorRecord]) -> None:
        if self.fail_on == "upsert":
            raise RuntimeError("vector upsert failed")
        self.upserts.append((scope, tuple(records)))

    def purge_other_commits(self, scope: RepoCommitScope) -> None:
        self.purge_calls.append(scope)

    def replace_repo_commit(
        self, scope: RepoCommitScope, records: Sequence[VectorRecord]
    ) -> None:
        if self.fail_on == "replace":
            raise RuntimeError("vector replace failed")
        self.replaces.append((scope, tuple(records)))

    def delete_repo(self, repo_id: str) -> None:
        self.deleted_repos.append(repo_id)

    def delete_paths(self, scope: RepoCommitScope, paths: Sequence[str]) -> None:
        self.deletes_paths.append((scope, tuple(paths)))

    def search(self, query_vector, *, limit, repo_ids=None):  # noqa: ANN001
        return ()


class RecordingExactIndex(FakeExactCodeIndex):
    def __init__(self, *, delay: float = 0.0, fail_operations=None) -> None:  # noqa: ANN001
        super().__init__(fail_operations=fail_operations)
        self.index_calls: list[tuple[str, str, tuple[str, ...]]] = []
        self.delete_calls: list[str] = []
        self.active = 0
        self.peak = 0
        self._lock = threading.Lock()
        self.delay = delay

    def index(self, repository, commit, files):  # noqa: ANN001
        with self._lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
        try:
            if self.delay:
                time.sleep(self.delay)
            paths = tuple(f.path for f in files)
            self.index_calls.append((repository, commit, paths))
            return super().index(repository, commit, files)
        finally:
            with self._lock:
                self.active -= 1

    def delete_repository(self, repository: str) -> None:
        self.delete_calls.append(repository)
        return super().delete_repository(repository)


def seed_repo(
    catalog: InMemoryCatalogRepository,
    *,
    identifier: str = "svc",
    state: RepoState = RepoState.NOT_INDEXED,
    last: str | None = None,
    current: str | None = None,
) -> int:
    entry = catalog.upsert_repository(
        connection_name="local",
        origin=RepoOrigin.LOCAL,
        repo_identifier=identifier,
        local_path=f"/repos/{identifier}",
    )
    rid = entry.id
    if current:
        catalog.update_main_commit(rid, current)
    if last is not None or state != RepoState.NOT_INDEXED:
        # Force state machine to desired end state for tests.
        if state == RepoState.QUEUED:
            catalog.mark_queued(rid)
        elif state == RepoState.INDEXING:
            catalog.mark_queued(rid)
            catalog.mark_indexing(rid)
        elif state == RepoState.UP_TO_DATE:
            catalog.mark_queued(rid)
            catalog.mark_indexing(rid)
            catalog.mark_updated(rid, last or current or "C0")
        elif state == RepoState.ERROR:
            catalog.mark_queued(rid)
            catalog.mark_indexing(rid)
            from datetime import datetime, timezone

            catalog.mark_error(rid, "boom", datetime.now(timezone.utc))
        if last is not None and state == RepoState.UP_TO_DATE:
            pass
        elif last is not None and state != RepoState.UP_TO_DATE:
            # stash last_processed via mark_updated path only; for others patch memory
            entry = catalog.get_repository(rid)
            catalog._repos[rid] = entry.__class__(  # noqa: SLF001
                **{**entry.__dict__, "last_processed_commit": last}
            )
    return rid


def make_orchestrator(
    *,
    catalog: InMemoryCatalogRepository | None = None,
    snapshot: FakeSnapshotProvider | None = None,
    exact: RecordingExactIndex | None = None,
    vector: RecordingVectorStore | None = None,
    capacity: int = 2,
    fail_metadata: bool = False,
):
    catalog = catalog or InMemoryCatalogRepository()
    snapshot = snapshot or FakeSnapshotProvider()
    exact = exact or RecordingExactIndex()
    vector = vector or RecordingVectorStore()
    meta = FakeMetadataGenerator(
        fail_chunk_ids={"fail"} if fail_metadata else set()
    )
    rag = DefaultFileRagPipeline(
        chunker=FakeChunker(),
        metadata_generator=meta,
        embedder=FakeEmbedder(),
    )
    orch = DefaultIndexingOrchestrator(
        catalog=catalog,
        snapshot=snapshot,
        eligibility=PathspecFileEligibilityFilter(),
        exact_index=exact,
        rag_pipeline=rag,
        vector_store=vector,
        limiter=SemaphoreWorkerLimiter(capacity=capacity, pool="index"),
    )
    reconcile = DefaultStartupIndexReconcile(
        catalog=catalog, snapshot=snapshot, orchestrator=orch
    )
    return orch, reconcile, catalog, snapshot, exact, vector
