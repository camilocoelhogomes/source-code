"""Testes de integração — ``SqlAlchemyCronPreferenceStore`` contra PostgreSQL real.

Exercem a migração Alembic ``0002_scheduler_preference`` e a semântica
get/set/clear do adaptador (design §7/BR-024) contra um container descartável,
mesma técnica de `tests/integration/test_postgres_catalog_repository.py` (T03).
Marcados ``integration`` e PULADOS automaticamente quando ``testcontainers``
não está instalado ou o Docker está indisponível — por isso não bloqueiam o
run padrão de domínio (design T15 §3.6/D-T15-010; `schedule/postgres.py` é
omitido do gate de cobertura em `pyproject.toml`, mesmo padrão de T03).
"""

from __future__ import annotations

import pytest

# Skip limpo quando o grupo opcional [integration] não está instalado.
postgres_module = pytest.importorskip("testcontainers.postgres")

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from github_rag.schedule.errors import InvalidCronExpressionError  # noqa: E402
from github_rag.schedule.postgres import (  # noqa: E402
    SchedulerPreferenceRow,
    SqlAlchemyCronPreferenceStore,
)

pytestmark = pytest.mark.integration


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
def store(database_url: str) -> SqlAlchemyCronPreferenceStore:
    engine = create_engine(database_url, future=True)
    session_factory = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    return SqlAlchemyCronPreferenceStore(session_factory)


def test_get_none_when_table_empty(store: SqlAlchemyCronPreferenceStore) -> None:
    assert store.get() is None


def test_set_persists_and_get_reads_back(
    store: SqlAlchemyCronPreferenceStore,
) -> None:
    assert store.set("0 */6 * * *") == "0 */6 * * *"
    assert store.get() == "0 */6 * * *"


def test_set_twice_updates_singleton_row_not_duplicate(
    store: SqlAlchemyCronPreferenceStore, database_url: str
) -> None:
    store.set("0 2 * * *")
    store.set("0 0,12 * * *")
    assert store.get() == "0 0,12 * * *"
    engine = create_engine(database_url, future=True)
    session_factory = sessionmaker(bind=engine, future=True)
    with session_factory() as session:
        rows = session.query(SchedulerPreferenceRow).all()
    assert len(rows) == 1


def test_invalid_set_does_not_persist(
    store: SqlAlchemyCronPreferenceStore,
) -> None:
    store.set("0 2 * * *")
    with pytest.raises(InvalidCronExpressionError):
        store.set("not-a-cron")
    assert store.get() == "0 2 * * *"


def test_clear_removes_row(store: SqlAlchemyCronPreferenceStore) -> None:
    store.set("0 */6 * * *")
    store.clear()
    assert store.get() is None
    store.clear()  # idempotente


def test_migration_default_server_timestamp(
    store: SqlAlchemyCronPreferenceStore, database_url: str
) -> None:
    store.set("0 2 * * *")
    engine = create_engine(database_url, future=True)
    session_factory = sessionmaker(bind=engine, future=True)
    with session_factory() as session:
        row = session.get(SchedulerPreferenceRow, 1)
        assert row is not None
        assert row.updated_at is not None
