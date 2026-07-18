"""``PostgresCatalogRepository`` — adaptador concreto da porta (design §6).

Responsabilidade deste módulo
    Implementar todos os métodos da porta ``CatalogRepository`` contra
    PostgreSQL, reproduzindo a MESMA semântica de domínio do fake in-memory
    (máquina de estados, lock otimista, idempotência, histórico) — garantindo
    paridade fake × PG (design §3.3).

Motivo da separação
    Concentra o I/O SQL e a tradução linha ORM → snapshot de leitura imutável.
    Erros de infraestrutura são encapsulados em ``CatalogPersistenceError`` (sem
    vazar credenciais — §8); erros de domínio (not found, transição,
    concorrência) são idênticos aos do fake.

Cobertura
    Só exercível contra PostgreSQL real (testes ``integration``); omitido do
    gate de cobertura do run padrão (`pyproject.toml`).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..errors import (
    CatalogPersistenceError,
    ConcurrencyConflictError,
    RepositoryNotFoundError,
)
from ..models import (
    CatalogEntry,
    ExecutionStatus,
    FileProgress,
    FileStage,
    IndexingExecution,
    Progress,
    RepoOrigin,
    RepoState,
)
from ..transitions import ensure_transition_allowed, is_up_to_date
from .models import (
    CatalogRepositoryRow,
    FileProcessingRow,
    IndexingExecutionRow,
)

_STAGE_FIELD: dict[FileStage, str] = {
    FileStage.ZOEKT: "zoekt_at",
    FileStage.TREE_SITTER: "tree_sitter_at",
    FileStage.METADATA_PERSISTED: "metadata_persisted_at",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PostgresCatalogRepository:
    """Implementação PostgreSQL da porta ``CatalogRepository``."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    # -- infraestrutura ------------------------------------------------------

    @contextmanager
    def _unit_of_work(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except (RepositoryNotFoundError, ConcurrencyConflictError):
            session.rollback()
            raise
        except SQLAlchemyError as exc:
            session.rollback()
            raise CatalogPersistenceError(
                "falha de infraestrutura no adaptador PostgreSQL do catálogo"
            ) from exc
        finally:
            session.close()

    def _require_repo_row(
        self, session: Session, repository_id: int
    ) -> CatalogRepositoryRow:
        row = session.get(CatalogRepositoryRow, repository_id)
        if row is None:
            raise RepositoryNotFoundError(
                f"repositório inexistente: id={repository_id}"
            )
        return row

    def _require_execution_row(
        self, session: Session, execution_id: int
    ) -> IndexingExecutionRow:
        row = session.get(IndexingExecutionRow, execution_id)
        if row is None:
            raise RepositoryNotFoundError(
                f"execução inexistente: id={execution_id}"
            )
        return row

    # -- tradução linha → snapshot ------------------------------------------

    def _to_entry(self, row: CatalogRepositoryRow) -> CatalogEntry:
        progress: Progress | None = None
        if row.progress_percent is not None or row.current_stage is not None:
            progress = Progress(
                percent=row.progress_percent,
                files_processed=row.files_processed,
                files_total=row.files_total,
                current_stage=row.current_stage,
            )
        return CatalogEntry(
            id=row.id,
            connection_name=row.connection_name,
            origin=row.origin,
            repo_identifier=row.repo_identifier,
            state=row.state,
            active=row.active,
            row_version=row.row_version,
            github_org=row.github_org,
            local_path=row.local_path,
            last_processed_commit=row.last_processed_commit,
            current_main_commit=row.current_main_commit,
            progress=progress,
            current_execution_id=row.current_execution_id,
            deactivated_at=row.deactivated_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_execution(self, row: IndexingExecutionRow) -> IndexingExecution:
        return IndexingExecution(
            id=row.id,
            repository_id=row.repository_id,
            status=row.status,
            started_at=row.started_at,
            finished_at=row.finished_at,
            commit_target=row.commit_target,
            error_message=row.error_message,
            error_at=row.error_at,
        )

    def _to_file_progress(self, row: FileProcessingRow) -> FileProgress:
        return FileProgress(
            id=row.id,
            execution_id=row.execution_id,
            file_path=row.file_path,
            zoekt_at=row.zoekt_at,
            tree_sitter_at=row.tree_sitter_at,
            metadata_persisted_at=row.metadata_persisted_at,
        )

    def _touch(self, row: CatalogRepositoryRow) -> None:
        row.row_version += 1
        row.updated_at = _now()

    def _close_current_execution(
        self,
        session: Session,
        row: CatalogRepositoryRow,
        *,
        status: ExecutionStatus,
        finished_at: datetime,
        error_message: str | None = None,
        error_at: datetime | None = None,
    ) -> None:
        if row.current_execution_id is None:
            return
        execution = session.get(IndexingExecutionRow, row.current_execution_id)
        if execution is None:
            return
        execution.status = status
        execution.finished_at = finished_at
        execution.error_message = error_message
        execution.error_at = error_at

    # -- Sincronização do catálogo (T07) ------------------------------------

    def upsert_repository(
        self,
        *,
        connection_name: str,
        origin: RepoOrigin,
        repo_identifier: str,
        github_org: str | None = None,
        local_path: str | None = None,
    ) -> CatalogEntry:
        with self._unit_of_work() as session:
            existing = session.scalars(
                select(CatalogRepositoryRow).where(
                    CatalogRepositoryRow.connection_name == connection_name,
                    CatalogRepositoryRow.repo_identifier == repo_identifier,
                )
            ).first()
            if existing is not None:
                existing.active = True
                existing.deactivated_at = None
                existing.origin = origin
                existing.github_org = github_org
                existing.local_path = local_path
                self._touch(existing)
                session.flush()
                return self._to_entry(existing)
            row = CatalogRepositoryRow(
                connection_name=connection_name,
                origin=origin,
                repo_identifier=repo_identifier,
                state=RepoState.NOT_INDEXED,
                active=True,
                row_version=0,
                github_org=github_org,
                local_path=local_path,
                created_at=_now(),
                updated_at=_now(),
            )
            session.add(row)
            session.flush()
            return self._to_entry(row)

    def deactivate_repository(self, repository_id: int) -> CatalogEntry:
        with self._unit_of_work() as session:
            row = self._require_repo_row(session, repository_id)
            row.active = False
            row.deactivated_at = _now()
            self._touch(row)
            session.flush()
            return self._to_entry(row)

    # -- Leitura (T07/T14/T17/T18) ------------------------------------------

    def list_active_catalog(self) -> Sequence[CatalogEntry]:
        with self._unit_of_work() as session:
            rows = session.scalars(
                select(CatalogRepositoryRow).where(CatalogRepositoryRow.active)
            ).all()
            return [self._to_entry(row) for row in rows]

    def get_repository(self, repository_id: int) -> CatalogEntry:
        with self._unit_of_work() as session:
            return self._to_entry(self._require_repo_row(session, repository_id))

    # -- Máquina de estados (T14) -------------------------------------------

    def transition_state(
        self,
        repository_id: int,
        target_state: RepoState,
        *,
        expected_version: int,
    ) -> CatalogEntry:
        with self._unit_of_work() as session:
            row = self._require_repo_row(session, repository_id)
            if row.row_version != expected_version:
                raise ConcurrencyConflictError(
                    f"conflito de versão: esperado={expected_version} "
                    f"atual={row.row_version}"
                )
            ensure_transition_allowed(row.state, target_state)
            row.state = target_state
            self._touch(row)
            session.flush()
            return self._to_entry(row)

    def mark_queued(self, repository_id: int) -> CatalogEntry:
        with self._unit_of_work() as session:
            row = self._require_repo_row(session, repository_id)
            ensure_transition_allowed(row.state, RepoState.QUEUED)
            row.state = RepoState.QUEUED
            self._touch(row)
            session.flush()
            return self._to_entry(row)

    def mark_indexing(self, repository_id: int) -> CatalogEntry:
        with self._unit_of_work() as session:
            row = self._require_repo_row(session, repository_id)
            ensure_transition_allowed(row.state, RepoState.INDEXING)
            row.state = RepoState.INDEXING
            self._touch(row)
            session.flush()
            return self._to_entry(row)

    def mark_updated(self, repository_id: int, commit: str) -> CatalogEntry:
        with self._unit_of_work() as session:
            row = self._require_repo_row(session, repository_id)
            ensure_transition_allowed(row.state, RepoState.UP_TO_DATE)
            self._close_current_execution(
                session, row, status=ExecutionStatus.SUCCEEDED, finished_at=_now()
            )
            row.state = RepoState.UP_TO_DATE
            row.last_processed_commit = commit
            row.current_main_commit = commit
            self._touch(row)
            session.flush()
            return self._to_entry(row)

    def mark_error(
        self,
        repository_id: int,
        message: str,
        error_at: datetime,
    ) -> CatalogEntry:
        with self._unit_of_work() as session:
            row = self._require_repo_row(session, repository_id)
            ensure_transition_allowed(row.state, RepoState.ERROR)
            self._close_current_execution(
                session,
                row,
                status=ExecutionStatus.FAILED,
                finished_at=error_at,
                error_message=message,
                error_at=error_at,
            )
            row.state = RepoState.ERROR
            self._touch(row)
            session.flush()
            return self._to_entry(row)

    # -- Comparação de commit / reconcile (T08/T14) -------------------------

    def update_main_commit(self, repository_id: int, commit: str) -> CatalogEntry:
        with self._unit_of_work() as session:
            row = self._require_repo_row(session, repository_id)
            row.current_main_commit = commit
            self._touch(row)
            session.flush()
            return self._to_entry(row)

    def reconcile_repository(self, repository_id: int) -> CatalogEntry:
        with self._unit_of_work() as session:
            row = self._require_repo_row(session, repository_id)
            if row.state != RepoState.UP_TO_DATE:
                return self._to_entry(row)
            if row.current_main_commit is None:
                return self._to_entry(row)
            if is_up_to_date(row.last_processed_commit, row.current_main_commit):
                return self._to_entry(row)
            row.state = RepoState.NOT_INDEXED
            self._touch(row)
            session.flush()
            return self._to_entry(row)

    # -- Progresso da execução corrente (REQ-021; T14) ----------------------

    def update_progress(
        self,
        repository_id: int,
        percent: int,
        files_processed: int,
        files_total: int,
        current_stage: str,
    ) -> CatalogEntry:
        with self._unit_of_work() as session:
            row = self._require_repo_row(session, repository_id)
            row.progress_percent = percent
            row.files_processed = files_processed
            row.files_total = files_total
            row.current_stage = current_stage
            self._touch(row)
            session.flush()
            return self._to_entry(row)

    # -- Execuções / histórico (REQ-023; T14/T18) ---------------------------

    def start_execution(
        self,
        repository_id: int,
        commit_target: str,
    ) -> IndexingExecution:
        with self._unit_of_work() as session:
            row = self._require_repo_row(session, repository_id)
            execution = IndexingExecutionRow(
                repository_id=repository_id,
                status=ExecutionStatus.RUNNING,
                started_at=_now(),
                commit_target=commit_target,
            )
            session.add(execution)
            session.flush()
            row.current_execution_id = execution.id
            self._touch(row)
            session.flush()
            return self._to_execution(execution)

    def list_executions(self, repository_id: int) -> Sequence[IndexingExecution]:
        with self._unit_of_work() as session:
            self._require_repo_row(session, repository_id)
            rows = session.scalars(
                select(IndexingExecutionRow)
                .where(IndexingExecutionRow.repository_id == repository_id)
                .order_by(IndexingExecutionRow.id)
            ).all()
            return [self._to_execution(row) for row in rows]

    # -- Etapas por arquivo (REQ-022; T14) ----------------------------------

    def record_file_stage(
        self,
        execution_id: int,
        file_path: str,
        stage: FileStage,
    ) -> FileProgress:
        with self._unit_of_work() as session:
            self._require_execution_row(session, execution_id)
            row = session.scalars(
                select(FileProcessingRow).where(
                    FileProcessingRow.execution_id == execution_id,
                    FileProcessingRow.file_path == file_path,
                )
            ).first()
            if row is None:
                row = FileProcessingRow(
                    execution_id=execution_id, file_path=file_path
                )
                session.add(row)
            field = _STAGE_FIELD[stage]
            if getattr(row, field) is None:
                setattr(row, field, _now())
            session.flush()
            return self._to_file_progress(row)

    def list_file_progress(self, execution_id: int) -> Sequence[FileProgress]:
        with self._unit_of_work() as session:
            self._require_execution_row(session, execution_id)
            rows = session.scalars(
                select(FileProcessingRow)
                .where(FileProcessingRow.execution_id == execution_id)
                .order_by(FileProcessingRow.id)
            ).all()
            return [self._to_file_progress(row) for row in rows]
