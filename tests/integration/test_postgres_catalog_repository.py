"""Testes de integração — ``PostgresCatalogRepository`` contra PostgreSQL real.

Exercem a paridade semântica fake × adaptador PG (design §3.3) aplicando a
migração Alembic inicial num container descartável e verificando o fluxo
principal do catálogo. São marcados ``integration`` e PULADOS automaticamente
quando ``testcontainers`` não está instalado ou o Docker está indisponível —
por isso não bloqueiam o run padrão de domínio (design §D-T03-010).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

# Skip limpo quando o grupo opcional [integration] não está instalado.
postgres_module = pytest.importorskip("testcontainers.postgres")

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from github_rag.catalog import (  # noqa: E402
    ExecutionStatus,
    FileStage,
    InvalidStateTransitionError,
    RepoOrigin,
    RepoState,
    RepositoryNotFoundError,
)
from github_rag.catalog.postgres import create_postgres_catalog_repository  # noqa: E402

pytestmark = pytest.mark.integration

_ERROR_AT = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def database_url() -> str:
    try:
        container = postgres_module.PostgresContainer("postgres:16-alpine")
        container.start()
    except Exception as exc:  # noqa: BLE001 - Docker indisponível ⇒ pula
        pytest.skip(f"Docker/PostgreSQL indisponível para integração: {exc!r}")
    try:
        raw_url = container.get_connection_url()
        url = raw_url.replace("postgresql+psycopg2://", "postgresql+psycopg://")
        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "head")
        yield url
    finally:
        container.stop()


@pytest.fixture()
def repo(database_url: str):
    return create_postgres_catalog_repository({"DATABASE_URL": database_url})


def test_full_success_flow_stamps_commit_and_closes_execution(repo) -> None:
    entry = repo.upsert_repository(
        connection_name="conn-gh",
        origin=RepoOrigin.GITHUB,
        repo_identifier="acme/app",
        github_org="acme",
    )
    assert entry.state == RepoState.NOT_INDEXED
    rid = entry.id
    repo.mark_queued(rid)
    repo.mark_indexing(rid)
    execution = repo.start_execution(rid, "C1")
    assert execution.status == ExecutionStatus.RUNNING
    for stage in FileStage:
        repo.record_file_stage(execution.id, "src/app.py", stage)
    repo.record_file_stage(execution.id, "src/app.py", FileStage.ZOEKT)
    rows = list(repo.list_file_progress(execution.id))
    assert len(rows) == 1
    updated = repo.mark_updated(rid, "C1")
    assert updated.state == RepoState.UP_TO_DATE
    assert updated.last_processed_commit == "C1"
    history = list(repo.list_executions(rid))
    assert history[-1].status == ExecutionStatus.SUCCEEDED


def test_reconcile_reverts_on_new_commit(repo) -> None:
    entry = repo.upsert_repository(
        connection_name="conn-gh",
        origin=RepoOrigin.GITHUB,
        repo_identifier="acme/reconcile",
        github_org="acme",
    )
    rid = entry.id
    repo.mark_queued(rid)
    repo.mark_indexing(rid)
    repo.mark_updated(rid, "C1")
    repo.update_main_commit(rid, "C2")
    reconciled = repo.reconcile_repository(rid)
    assert reconciled.state == RepoState.NOT_INDEXED
    assert reconciled.last_processed_commit == "C1"


def test_error_flow_records_message_and_time(repo) -> None:
    entry = repo.upsert_repository(
        connection_name="conn-gh",
        origin=RepoOrigin.GITHUB,
        repo_identifier="acme/err",
        github_org="acme",
    )
    rid = entry.id
    repo.mark_queued(rid)
    repo.mark_indexing(rid)
    repo.start_execution(rid, "C1")
    errored = repo.mark_error(rid, "boom", _ERROR_AT)
    assert errored.state == RepoState.ERROR
    failed = [e for e in repo.list_executions(rid) if e.status == ExecutionStatus.FAILED]
    assert failed and failed[-1].error_message == "boom"


def test_illegal_transition_and_missing_repo(repo) -> None:
    entry = repo.upsert_repository(
        connection_name="conn-gh",
        origin=RepoOrigin.GITHUB,
        repo_identifier="acme/illegal",
        github_org="acme",
    )
    with pytest.raises(InvalidStateTransitionError):
        repo.mark_updated(entry.id, "C1")
    with pytest.raises(RepositoryNotFoundError):
        repo.get_repository(999_999)
