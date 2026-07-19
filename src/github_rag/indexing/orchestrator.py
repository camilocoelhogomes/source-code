"""Implementação do ``IndexingOrchestrator`` (T14).

Responsabilidade deste módulo
    Fila, estados REQ-020, Zoekt conjunto tip, RAG incremental/full, BR-005.

Motivo da separação
    Concentra a orquestração; SDKs ficam nos adaptadores injetados (ENG-013).
"""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from threading import Lock

from github_rag.catalog.models import (
    CatalogEntry,
    ExecutionStatus,
    FileStage,
    RepoOrigin,
    RepoState,
)
from github_rag.catalog.repository import CatalogRepository
from github_rag.catalog.transitions import is_up_to_date
from github_rag.concurrency.limiter import WorkerLimiter
from github_rag.eligibility.filter import FileEligibilityFilter
from github_rag.eligibility.gitignore import GitignoreSource
from github_rag.index.vector.ports import VectorStore
from github_rag.index.vector.types import RepoCommitScope, VectorRecord
from github_rag.index.zoekt.models import FileToIndex
from github_rag.index.zoekt.port import ExactCodeIndex
from github_rag.indexing.errors import RepositorySourceError
from github_rag.indexing.pipeline import FileRagPipeline
from github_rag.indexing.progress import compute_progress_percent
from github_rag.snapshot.diff import FileDiffSet
from github_rag.snapshot.models import (
    FirstIndexSignal,
    GitHubSnapshotSource,
    LocalSnapshotSource,
    SnapshotSource,
)
from github_rag.snapshot.provider import MainSnapshotProvider


def snapshot_source_for(
    entry: CatalogEntry, *, github_token: str | None
) -> SnapshotSource:
    """Monta ``SnapshotSource`` a partir do catálogo."""
    if entry.origin == RepoOrigin.GITHUB:
        if not github_token:
            raise RepositorySourceError(
                f"token GitHub ausente para repository_id={entry.id}"
            )
        return GitHubSnapshotSource(
            full_name=entry.repo_identifier, token=github_token
        )
    if not entry.local_path:
        raise RepositorySourceError(
            f"local_path ausente para repository_id={entry.id}"
        )
    return LocalSnapshotSource(local_path=entry.local_path)


class DefaultIndexingOrchestrator:
    """Implementação de ``IndexingOrchestrator`` via portas injetadas."""

    def __init__(
        self,
        *,
        catalog: CatalogRepository,
        snapshot: MainSnapshotProvider,
        eligibility: FileEligibilityFilter,
        exact_index: ExactCodeIndex,
        rag_pipeline: FileRagPipeline,
        vector_store: VectorStore,
        limiter: WorkerLimiter,
        github_token: str | None = None,
    ) -> None:
        self._catalog = catalog
        self._snapshot = snapshot
        self._eligibility = eligibility
        self._exact = exact_index
        self._rag = rag_pipeline
        self._vector = vector_store
        self._limiter = limiter
        self._github_token = github_token
        self._queue: list[int] = []
        self._queued_ids: set[int] = set()
        self._lock = Lock()

    def enqueue(self, repository_ids: Sequence[int]) -> None:
        for repository_id in repository_ids:
            entry = self._catalog.get_repository(repository_id)
            if entry.state not in {
                RepoState.NOT_INDEXED,
                RepoState.ERROR,
                RepoState.QUEUED,
            }:
                continue
            self._catalog.mark_queued(repository_id)
            with self._lock:
                if repository_id not in self._queued_ids:
                    self._queue.append(repository_id)
                    self._queued_ids.add(repository_id)

    def run_until_idle(self) -> None:
        workers = max(1, self._limiter.capacity)

        def _worker(repository_id: int) -> None:
            with self._limiter.acquire():
                self.index_repository(repository_id)

        while True:
            with self._lock:
                batch = list(self._queue)
                self._queue.clear()
                self._queued_ids.clear()
            if not batch:
                return
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_worker, rid) for rid in batch]
                for fut in as_completed(futures):
                    fut.result()

    def index_repository(self, repository_id: int) -> None:
        entry = self._catalog.get_repository(repository_id)
        restart_full = entry.state == RepoState.ERROR or self._last_execution_failed(
            repository_id
        )

        try:
            if entry.state == RepoState.QUEUED:
                entry = self._catalog.mark_indexing(repository_id)
            elif entry.state == RepoState.ERROR:
                entry = self._catalog.mark_queued(repository_id)
                entry = self._catalog.mark_indexing(repository_id)
            elif entry.state == RepoState.NOT_INDEXED:
                entry = self._catalog.mark_queued(repository_id)
                entry = self._catalog.mark_indexing(repository_id)
            elif entry.state in {RepoState.UP_TO_DATE, RepoState.INDEXING}:
                pass

            source = snapshot_source_for(entry, github_token=self._github_token)
            tip_snap = self._snapshot.get_main_tip(source)
            tip = tip_snap.commit_sha
            entry = self._catalog.update_main_commit(repository_id, tip)

            if is_up_to_date(entry.last_processed_commit, tip):
                if entry.state == RepoState.INDEXING:
                    self._catalog.mark_updated(repository_id, tip)
                return

            if entry.state == RepoState.UP_TO_DATE:
                entry = self._catalog.reconcile_repository(repository_id)
            if entry.state in {RepoState.NOT_INDEXED, RepoState.ERROR}:
                entry = self._catalog.mark_queued(repository_id)
                entry = self._catalog.mark_indexing(repository_id)
                restart_full = restart_full or entry.state == RepoState.INDEXING and self._last_execution_failed(
                    repository_id
                )

            execution = self._catalog.start_execution(repository_id, tip)
            repo_key = str(repository_id)
            scope_tip = RepoCommitScope(repo_id=repo_key, commit_sha=tip)
            last = entry.last_processed_commit
            scope_old = (
                RepoCommitScope(repo_id=repo_key, commit_sha=last)
                if last
                else None
            )

            if restart_full:
                self._exact.delete_repository(repo_key)
                self._vector.delete_repo(repo_key)

            tree = self._snapshot.list_tree(source, commit_sha=tip)
            gitignores = self._load_gitignores(source, tip)
            all_eligible = list(self._eligibility.filter(tree, gitignores))

            zoekt_files = [
                FileToIndex(
                    repository=repo_key,
                    path=path,
                    commit=tip,
                    content=self._snapshot.read_file(
                        source, commit_sha=tip, path=path
                    ),
                )
                for path in all_eligible
            ]
            self._exact.index(repo_key, tip, zoekt_files)
            for path in all_eligible:
                self._catalog.record_file_stage(
                    execution.id, path, FileStage.ZOEKT
                )

            diff = self._snapshot.diff_files(
                source,
                from_commit=None if restart_full else last,
                to_commit=tip,
            )
            first_index = isinstance(diff, FirstIndexSignal) or restart_full

            if first_index:
                rag_paths = list(all_eligible)
            else:
                assert isinstance(diff, FileDiffSet)
                changed = set(diff.added) | set(diff.modified)
                rag_paths = [p for p in all_eligible if p in changed]
                deleted = list(diff.deleted)
                if scope_old is not None and deleted:
                    self._vector.delete_paths(scope_old, deleted)

            total = len(rag_paths)
            all_records: list[VectorRecord] = []
            for i, path in enumerate(rag_paths):
                content = self._snapshot.read_file(
                    source, commit_sha=tip, path=path
                )
                self._catalog.update_progress(
                    repository_id,
                    compute_progress_percent(
                        files_processed=i, files_total=total
                    ),
                    i,
                    total,
                    "tree_sitter",
                )
                records = self._rag.process_file(path=path, content=content)
                self._catalog.record_file_stage(
                    execution.id, path, FileStage.TREE_SITTER
                )
                if not first_index and scope_old is not None:
                    self._vector.delete_paths(scope_old, [path])
                if not first_index:
                    self._vector.upsert(scope_tip, records)
                else:
                    all_records.extend(records)
                self._catalog.record_file_stage(
                    execution.id, path, FileStage.METADATA_PERSISTED
                )
                self._catalog.update_progress(
                    repository_id,
                    compute_progress_percent(
                        files_processed=i + 1, files_total=total
                    ),
                    i + 1,
                    total,
                    "persist",
                )

            if first_index:
                self._vector.replace_repo_commit(scope_tip, all_records)

            self._catalog.update_progress(
                repository_id, 100, total, total, "done"
            )
            self._catalog.mark_updated(repository_id, tip)
        except Exception as exc:  # noqa: BLE001 — boundary do repo
            current = self._catalog.get_repository(repository_id)
            if current.state == RepoState.UP_TO_DATE:
                current = self._catalog.reconcile_repository(repository_id)
                if current.state == RepoState.UP_TO_DATE:
                    current = self._catalog.transition_state(
                        repository_id,
                        RepoState.NOT_INDEXED,
                        expected_version=current.row_version,
                    )
            if current.state in {RepoState.NOT_INDEXED, RepoState.ERROR}:
                self._catalog.mark_queued(repository_id)
                current = self._catalog.get_repository(repository_id)
            if current.state == RepoState.QUEUED:
                self._catalog.mark_indexing(repository_id)
                current = self._catalog.get_repository(repository_id)
            if current.state == RepoState.INDEXING:
                self._catalog.mark_error(
                    repository_id,
                    str(exc),
                    datetime.now(timezone.utc),
                )

    def _last_execution_failed(self, repository_id: int) -> bool:
        try:
            execs = self._catalog.list_executions(repository_id)
        except Exception:  # noqa: BLE001
            return False
        if not execs:
            return False
        latest = max(execs, key=lambda e: e.id)
        return latest.status == ExecutionStatus.FAILED

    def _load_gitignores(
        self, source: SnapshotSource, tip: str
    ) -> list[GitignoreSource]:
        try:
            raw = self._snapshot.read_file(
                source, commit_sha=tip, path=".gitignore"
            )
        except Exception:  # noqa: BLE001 — ausência é válida
            return []
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return []
        return [GitignoreSource(relative_dir="", lines=tuple(text.splitlines()))]
