"""Fake in-memory da porta ``CatalogRepository`` — implementação T03.

Responsabilidade deste módulo
    Fornecer ``InMemoryCatalogRepository``: uma implementação completa da porta
    ``CatalogRepository`` (todos os 16 métodos) que guarda o catálogo em
    estruturas em memória. É a implementação de referência do *domínio* — a que
    torna os testes unitários e o BDD verdes sem PostgreSQL.

Motivo da separação
    Arquitetura hexagonal (design §3.1): o fake concentra a semântica de domínio
    (máquina de estados, lock otimista, idempotência, histórico) de forma
    testável em qualquer OS sem Docker/PG. O adaptador PostgreSQL
    (`catalog/postgres/`) deve reproduzir exatamente este comportamento; ambos
    satisfazem a mesma porta, garantindo paridade semântica.

Decisões fixadas (reviews SUGGESTION I-1/I-2/I-3)
    - I-1: ``mark_updated``/``mark_error`` sem execução corrente aberta aplicam a
      transição e o carimbo de commit, mas não criam nem alteram execução.
    - I-2: ``mark_indexing`` NÃO abre execução implícita; a execução é aberta
      explicitamente por ``start_execution``.
    - I-3: ``execution_id`` inexistente reutiliza ``RepositoryNotFoundError``.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from datetime import datetime, timezone

from .errors import ConcurrencyConflictError, RepositoryNotFoundError
from .models import (
    CatalogEntry,
    ExecutionStatus,
    FileProgress,
    FileStage,
    IndexingExecution,
    Progress,
    RepoOrigin,
    RepoState,
)
from .transitions import ensure_transition_allowed, is_up_to_date

_STAGE_FIELD: dict[FileStage, str] = {
    FileStage.ZOEKT: "zoekt_at",
    FileStage.TREE_SITTER: "tree_sitter_at",
    FileStage.METADATA_PERSISTED: "metadata_persisted_at",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryCatalogRepository:
    """Implementação in-memory da porta ``CatalogRepository`` (design §3.1).

    Estado interno mantido em dicionários; cada mutação de linha do repositório
    incrementa ``row_version`` e devolve um novo ``CatalogEntry`` imutável
    (snapshot de leitura). Não realiza I/O nem levanta ``CatalogPersistenceError``
    (exclusivo do adaptador PG).
    """

    def __init__(self) -> None:
        self._repos: dict[int, CatalogEntry] = {}
        self._executions: dict[int, IndexingExecution] = {}
        # execution_id -> (file_path -> FileProgress)
        self._file_progress: dict[int, dict[str, FileProgress]] = {}
        self._next_repo_id = 1
        self._next_execution_id = 1
        self._next_file_id = 1

    # -- helpers internos ----------------------------------------------------

    def _require_repo(self, repository_id: int) -> CatalogEntry:
        entry = self._repos.get(repository_id)
        if entry is None:
            raise RepositoryNotFoundError(
                f"repositório inexistente: id={repository_id}"
            )
        return entry

    def _require_execution(self, execution_id: int) -> IndexingExecution:
        execution = self._executions.get(execution_id)
        if execution is None:
            raise RepositoryNotFoundError(
                f"execução inexistente: id={execution_id}"
            )
        return execution

    def _save(self, entry: CatalogEntry, **changes: object) -> CatalogEntry:
        """Persiste uma mutação de linha do repo, incrementando ``row_version``."""
        updated = dataclasses.replace(
            entry,
            row_version=entry.row_version + 1,
            updated_at=_now(),
            **changes,  # type: ignore[arg-type]
        )
        self._repos[updated.id] = updated
        return updated

    def _close_current_execution(
        self,
        entry: CatalogEntry,
        *,
        status: ExecutionStatus,
        finished_at: datetime,
        error_message: str | None = None,
        error_at: datetime | None = None,
    ) -> None:
        """Fecha a execução corrente, se houver (I-1: no-op sem execução aberta)."""
        execution_id = entry.current_execution_id
        if execution_id is None:
            return
        execution = self._executions.get(execution_id)
        if execution is None:
            return
        self._executions[execution_id] = dataclasses.replace(
            execution,
            status=status,
            finished_at=finished_at,
            error_message=error_message,
            error_at=error_at,
        )

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
        for existing in self._repos.values():
            if (
                existing.connection_name == connection_name
                and existing.repo_identifier == repo_identifier
            ):
                # Reativa soft-deleted preservando estado/commits; caminho feliz.
                return self._save(
                    existing,
                    active=True,
                    deactivated_at=None,
                    origin=origin,
                    github_org=github_org,
                    local_path=local_path,
                )
        entry = CatalogEntry(
            id=self._next_repo_id,
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
        self._repos[entry.id] = entry
        self._next_repo_id += 1
        return entry

    def deactivate_repository(self, repository_id: int) -> CatalogEntry:
        entry = self._require_repo(repository_id)
        return self._save(entry, active=False, deactivated_at=_now())

    # -- Leitura (T07/T14/T17/T18) ------------------------------------------

    def list_active_catalog(self) -> Sequence[CatalogEntry]:
        return [entry for entry in self._repos.values() if entry.active]

    def get_repository(self, repository_id: int) -> CatalogEntry:
        return self._require_repo(repository_id)

    # -- Máquina de estados (T14) -------------------------------------------

    def transition_state(
        self,
        repository_id: int,
        target_state: RepoState,
        *,
        expected_version: int,
    ) -> CatalogEntry:
        # Ordem congelada: existência → versão → validade (interfaces §6).
        entry = self._require_repo(repository_id)
        if entry.row_version != expected_version:
            raise ConcurrencyConflictError(
                f"conflito de versão: esperado={expected_version} "
                f"atual={entry.row_version}"
            )
        ensure_transition_allowed(entry.state, target_state)
        return self._save(entry, state=target_state)

    def mark_queued(self, repository_id: int) -> CatalogEntry:
        entry = self._require_repo(repository_id)
        ensure_transition_allowed(entry.state, RepoState.QUEUED)
        return self._save(entry, state=RepoState.QUEUED)

    def mark_indexing(self, repository_id: int) -> CatalogEntry:
        entry = self._require_repo(repository_id)
        ensure_transition_allowed(entry.state, RepoState.INDEXING)
        # I-2: nenhuma execução implícita é aberta aqui.
        return self._save(entry, state=RepoState.INDEXING)

    def mark_updated(self, repository_id: int, commit: str) -> CatalogEntry:
        entry = self._require_repo(repository_id)
        ensure_transition_allowed(entry.state, RepoState.UP_TO_DATE)
        self._close_current_execution(
            entry, status=ExecutionStatus.SUCCEEDED, finished_at=_now()
        )
        return self._save(
            entry,
            state=RepoState.UP_TO_DATE,
            last_processed_commit=commit,
            current_main_commit=commit,
        )

    def mark_error(
        self,
        repository_id: int,
        message: str,
        error_at: datetime,
    ) -> CatalogEntry:
        entry = self._require_repo(repository_id)
        ensure_transition_allowed(entry.state, RepoState.ERROR)
        self._close_current_execution(
            entry,
            status=ExecutionStatus.FAILED,
            finished_at=error_at,
            error_message=message,
            error_at=error_at,
        )
        return self._save(entry, state=RepoState.ERROR)

    # -- Comparação de commit / reconcile (T08/T14) -------------------------

    def update_main_commit(self, repository_id: int, commit: str) -> CatalogEntry:
        entry = self._require_repo(repository_id)
        return self._save(entry, current_main_commit=commit)

    def reconcile_repository(self, repository_id: int) -> CatalogEntry:
        entry = self._require_repo(repository_id)
        if entry.state != RepoState.UP_TO_DATE:
            return entry
        # Tip ausente ⇒ permanece up_to_date (interfaces §5.4).
        if entry.current_main_commit is None:
            return entry
        if is_up_to_date(entry.last_processed_commit, entry.current_main_commit):
            return entry
        # Novo commit em main ≠ processado: rebaixa preservando a base (CP-02).
        return self._save(entry, state=RepoState.NOT_INDEXED)

    # -- Progresso da execução corrente (REQ-021; T14) ----------------------

    def update_progress(
        self,
        repository_id: int,
        percent: int,
        files_processed: int,
        files_total: int,
        current_stage: str,
    ) -> CatalogEntry:
        entry = self._require_repo(repository_id)
        progress = Progress(
            percent=percent,
            files_processed=files_processed,
            files_total=files_total,
            current_stage=current_stage,
        )
        return self._save(entry, progress=progress)

    # -- Execuções / histórico (REQ-023; T14/T18) ---------------------------

    def start_execution(
        self,
        repository_id: int,
        commit_target: str,
    ) -> IndexingExecution:
        entry = self._require_repo(repository_id)
        execution = IndexingExecution(
            id=self._next_execution_id,
            repository_id=repository_id,
            status=ExecutionStatus.RUNNING,
            started_at=_now(),
            commit_target=commit_target,
        )
        self._executions[execution.id] = execution
        self._file_progress[execution.id] = {}
        self._next_execution_id += 1
        self._save(entry, current_execution_id=execution.id)
        return execution

    def list_executions(self, repository_id: int) -> Sequence[IndexingExecution]:
        self._require_repo(repository_id)
        return [
            execution
            for execution in self._executions.values()
            if execution.repository_id == repository_id
        ]

    # -- Etapas por arquivo (REQ-022; T14) ----------------------------------

    def record_file_stage(
        self,
        execution_id: int,
        file_path: str,
        stage: FileStage,
    ) -> FileProgress:
        self._require_execution(execution_id)
        rows = self._file_progress.setdefault(execution_id, {})
        existing = rows.get(file_path)
        if existing is None:
            existing = FileProgress(
                id=self._next_file_id,
                execution_id=execution_id,
                file_path=file_path,
            )
            self._next_file_id += 1
        field = _STAGE_FIELD[stage]
        # Idempotência: só marca se ainda não marcada (preserva timestamp).
        if getattr(existing, field) is None:
            existing = dataclasses.replace(existing, **{field: _now()})
        rows[file_path] = existing
        return existing

    def list_file_progress(self, execution_id: int) -> Sequence[FileProgress]:
        self._require_execution(execution_id)
        return list(self._file_progress.get(execution_id, {}).values())
