"""Helpers compartilhados — unit/BDD UI (T18)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import (
    FileStage,
    RepoOrigin,
    RepoState,
)
from github_rag.query.fake import FakeQueryService
from github_rag.query.types import QueryHit, QueryHits
from github_rag.schedule.memory import InMemoryCronPreferenceStore
from github_rag.schedule.scheduler import DefaultDailyScheduler
from github_rag.ui.api import DefaultManagementUiApi

REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_ROOT = REPO_ROOT / "web"
UI_PKG = REPO_ROOT / "src" / "github_rag" / "ui"


class SpyOrchestrator:
    """Double de IndexingOrchestrator para UI."""

    def __init__(self, catalog: InMemoryCatalogRepository) -> None:
        self._catalog = catalog
        self.enqueued: list[int] = []
        self.idle_calls = 0

    def enqueue(self, repository_ids: Sequence[int]) -> None:
        for rid in repository_ids:
            entry = self._catalog.get_repository(rid)
            if entry.state is RepoState.UP_TO_DATE:
                entry = self._catalog.transition_state(
                    rid,
                    RepoState.NOT_INDEXED,
                    expected_version=entry.row_version,
                )
            if entry.state in {RepoState.NOT_INDEXED, RepoState.ERROR}:
                self._catalog.mark_queued(rid)
            self.enqueued.append(rid)

    def run_until_idle(self) -> None:
        self.idle_calls += 1
        for rid in list(self.enqueued):
            entry = self._catalog.get_repository(rid)
            if entry.state is RepoState.QUEUED:
                entry = self._catalog.mark_indexing(rid)
            if entry.state is RepoState.INDEXING:
                self._catalog.mark_updated(
                    rid, commit=entry.current_main_commit or "C1"
                )

    def index_repository(self, repository_id: int) -> None:
        self.enqueue([repository_id])
        self.run_until_idle()


class NoopReconcile:
    def run(self) -> None:
        return None


def seed_repo(
    catalog: InMemoryCatalogRepository,
    *,
    origin: RepoOrigin = RepoOrigin.GITHUB,
    state: RepoState = RepoState.NOT_INDEXED,
    identifier: str = "acme/api",
    connection_name: str = "gh",
) -> int:
    entry = catalog.upsert_repository(
        connection_name=connection_name,
        origin=origin,
        repo_identifier=identifier,
        github_org="acme" if origin is RepoOrigin.GITHUB else None,
        local_path="/repos/api" if origin is RepoOrigin.LOCAL else None,
    )
    rid = entry.id
    if state is RepoState.NOT_INDEXED:
        return rid
    if state is RepoState.QUEUED:
        catalog.mark_queued(rid)
    elif state is RepoState.INDEXING:
        catalog.mark_queued(rid)
        catalog.mark_indexing(rid)
    elif state is RepoState.UP_TO_DATE:
        catalog.mark_queued(rid)
        catalog.mark_indexing(rid)
        catalog.mark_updated(rid, commit="abc123")
    elif state is RepoState.ERROR:
        catalog.mark_queued(rid)
        catalog.mark_indexing(rid)
        catalog.start_execution(rid, commit_target="abc123")
        catalog.mark_error(
            rid, message="boom", error_at=datetime.now(UTC)
        )
    return rid


def build_client(
    *,
    catalog: InMemoryCatalogRepository | None = None,
    query: FakeQueryService | None = None,
    drain_on_index: bool = True,
    default_cron: str = "0 2 * * *",
) -> tuple[
    TestClient,
    InMemoryCatalogRepository,
    SpyOrchestrator,
    Any,
    FakeQueryService,
]:
    catalog = catalog or InMemoryCatalogRepository()
    orch = SpyOrchestrator(catalog)
    store = InMemoryCronPreferenceStore()
    scheduler = DefaultDailyScheduler(
        preference_store=store,
        reconcile=NoopReconcile(),
        orchestrator=orch,
        default_cron=default_cron,
    )
    query = query or FakeQueryService(
        exact_hits=QueryHits(
            hits=(
                QueryHit(
                    kind="exact",
                    score=1.0,
                    repository="acme/api",
                    path="src/auth.py",
                    commit="abc123",
                    snippet="def authenticate",
                    line_number=10,
                ),
            )
        ),
        semantic_hits=QueryHits(
            hits=(
                QueryHit(
                    kind="semantic",
                    score=0.9,
                    repository="acme/api",
                    path="src/auth.py",
                    commit="abc123",
                    snippet="login flow",
                    chunk_metadata_summary="auth",
                ),
            )
        ),
    )
    api = DefaultManagementUiApi(
        catalog=catalog,
        orchestrator=orch,
        scheduler=scheduler,
        query=query,
        drain_on_index=drain_on_index,
        web_root=WEB_ROOT,
    )
    client = TestClient(api.build())
    return client, catalog, orch, scheduler, query


def put_progress(catalog: InMemoryCatalogRepository, rid: int) -> None:
    entry = catalog.get_repository(rid)
    if entry.state is RepoState.NOT_INDEXED:
        catalog.mark_queued(rid)
        entry = catalog.get_repository(rid)
    if entry.state is RepoState.QUEUED:
        catalog.mark_indexing(rid)
    exec_row = catalog.start_execution(rid, commit_target="abc123")
    catalog.update_progress(
        rid,
        percent=40,
        files_processed=2,
        files_total=5,
        current_stage="tree_sitter",
    )
    catalog.record_file_stage(exec_row.id, "src/a.py", FileStage.ZOEKT)
    catalog.record_file_stage(exec_row.id, "src/a.py", FileStage.TREE_SITTER)


def seed_error_history(catalog: InMemoryCatalogRepository, rid: int) -> None:
    entry = catalog.get_repository(rid)
    if entry.state is RepoState.NOT_INDEXED:
        catalog.mark_queued(rid)
        catalog.mark_indexing(rid)
    elif entry.state is RepoState.QUEUED:
        catalog.mark_indexing(rid)
    catalog.start_execution(rid, commit_target="c1")
    catalog.mark_error(
        rid,
        message="partial failure",
        error_at=datetime(2026, 7, 18, 12, 0, tzinfo=UTC),
    )
    catalog.mark_queued(rid)
    catalog.mark_indexing(rid)
    catalog.start_execution(rid, commit_target="c1")
    catalog.mark_error(
        rid,
        message="still failing",
        error_at=datetime(2026, 7, 18, 13, 0, tzinfo=UTC),
    )
