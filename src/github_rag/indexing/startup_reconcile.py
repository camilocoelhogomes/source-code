"""Startup index reconcile (T14 / ENG-011).

Responsabilidade deste módulo
    Implementar ``DefaultStartupIndexReconcile``.

Motivo da separação
    T07 é sync-only; boot (T19) chama esta porta após o sync (D-T14-003).
"""

from __future__ import annotations

from datetime import datetime, timezone

from github_rag.catalog.models import RepoState
from github_rag.catalog.repository import CatalogRepository
from github_rag.indexing.orchestrator import snapshot_source_for
from github_rag.indexing.ports import IndexingOrchestrator
from github_rag.snapshot.provider import MainSnapshotProvider


class DefaultStartupIndexReconcile:
    """Implementação de ``StartupIndexReconcile``."""

    def __init__(
        self,
        *,
        catalog: CatalogRepository,
        snapshot: MainSnapshotProvider,
        orchestrator: IndexingOrchestrator,
        github_token: str | None = None,
        defer_enqueue: bool = False,
    ) -> None:
        self._catalog = catalog
        self._snapshot = snapshot
        self._orchestrator = orchestrator
        self._github_token = github_token
        self._defer_enqueue = defer_enqueue

    def run(self) -> None:
        for entry in list(self._catalog.list_active_catalog()):
            try:
                source = snapshot_source_for(
                    entry, github_token=self._github_token
                )
                tip = self._snapshot.get_main_tip(source).commit_sha
                self._catalog.update_main_commit(entry.id, tip)
                entry = self._catalog.reconcile_repository(entry.id)
            except Exception:  # noqa: BLE001 — tip falhou: segue por estado
                entry = self._catalog.get_repository(entry.id)

            if entry.state == RepoState.INDEXING:
                self._catalog.mark_error(
                    entry.id,
                    "orphaned indexing after restart",
                    datetime.now(timezone.utc),
                )
                self._catalog.mark_queued(entry.id)
                if not self._defer_enqueue:
                    self._orchestrator.enqueue([entry.id])
            elif entry.state == RepoState.QUEUED:
                if not self._defer_enqueue:
                    self._orchestrator.enqueue([entry.id])
            elif entry.state in {RepoState.NOT_INDEXED, RepoState.ERROR}:
                if not self._defer_enqueue:
                    self._orchestrator.enqueue([entry.id])
