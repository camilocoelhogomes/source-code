"""Testes unitários de contrato — InMemoryCatalogRepository (T03).

Escopo
    Comportamento observável da porta ``CatalogRepository`` (interfaces §6/§7)
    exercido contra o fake in-memory ``InMemoryCatalogRepository``. Cobre
    contratos, extremos, corner cases, entradas inválidas, estados vazios,
    falhas, concorrência/idempotência, a máquina de estados (válidas e inválidas)
    e o histórico de execução — tudo sem PostgreSQL.

Estratégia RED (pré-implementação)
    O fake ``InMemoryCatalogRepository`` AINDA NÃO EXISTE
    (``github_rag.catalog.memory`` não é criado neste gate — é trabalho do
    Developer). Portanto o import de topo abaixo FALHA na coleta com
    ``ModuleNotFoundError`` — RED esperado e documentado no plano. Quando o
    Developer criar o módulo, esta suíte de contrato passa a coletar e deve
    ficar verde (paridade com o adaptador PG).

Decisões fixadas no plano (reviews SUGGESTION I-1/I-2/I-3)
    - I-1: ``mark_updated``/``mark_error`` SEM execução corrente aberta = no-op de
      fechamento — a transição de estado e o carimbo de commit ocorrem mesmo
      assim; nenhuma execução é criada nem alterada.
    - I-2: ``mark_indexing`` NÃO abre execução implícita (evita execução
      duplicada); a execução é aberta explicitamente via ``start_execution``.
    - I-3: ``execution_id`` inexistente reutiliza ``RepositoryNotFoundError``.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from github_rag.catalog import (
    ConcurrencyConflictError,
    ExecutionStatus,
    FileStage,
    InvalidStateTransitionError,
    RepoOrigin,
    RepoState,
    RepositoryNotFoundError,
)

# RED esperado: módulo do fake não existe neste gate (import falha na coleta).
from github_rag.catalog.memory import InMemoryCatalogRepository

_ERROR_AT = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)
_MISSING_ID = 999_999


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryCatalogRepository()

    def _register(self, repo_identifier: str = "acme/app") -> object:
        return self.repo.upsert_repository(
            connection_name="conn-gh",
            origin=RepoOrigin.GITHUB,
            repo_identifier=repo_identifier,
            github_org="acme",
        )

    def _drive_to_indexing(self, repo_identifier: str = "acme/app") -> int:
        entry = self._register(repo_identifier)
        self.repo.mark_queued(entry.id)
        self.repo.mark_indexing(entry.id)
        return entry.id

    def _drive_to_up_to_date(self, commit: str = "C1") -> int:
        rid = self._drive_to_indexing()
        self.repo.mark_updated(rid, commit)
        return rid


# --------------------------------------------------------------------------- #
# upsert / get / soft-delete / list_active_catalog
# --------------------------------------------------------------------------- #


class TestUpsertAndRead(_Base):
    def test_upsert_creates_entry_in_not_indexed_active(self) -> None:
        entry = self._register()
        self.assertEqual(entry.state, RepoState.NOT_INDEXED)
        self.assertTrue(entry.active)
        self.assertEqual(entry.origin, RepoOrigin.GITHUB)
        self.assertEqual(entry.github_org, "acme")
        self.assertEqual(entry.repo_identifier, "acme/app")
        self.assertIsInstance(entry.id, int)
        self.assertIsInstance(entry.row_version, int)

    def test_upsert_local_origin_sets_local_path(self) -> None:
        entry = self.repo.upsert_repository(
            connection_name="conn-local",
            origin=RepoOrigin.LOCAL,
            repo_identifier="/srv/repo",
            local_path="/srv/repo",
        )
        self.assertEqual(entry.origin, RepoOrigin.LOCAL)
        self.assertEqual(entry.local_path, "/srv/repo")

    def test_upsert_preserves_state_and_commit_on_reupsert(self) -> None:
        rid = self._drive_to_up_to_date("C1")
        again = self.repo.upsert_repository(
            connection_name="conn-gh",
            origin=RepoOrigin.GITHUB,
            repo_identifier="acme/app",
            github_org="acme",
        )
        self.assertEqual(again.id, rid)
        self.assertEqual(again.state, RepoState.UP_TO_DATE)
        self.assertEqual(again.last_processed_commit, "C1")

    def test_upsert_reactivates_soft_deleted_same_identity(self) -> None:
        entry = self._register()
        self.repo.deactivate_repository(entry.id)
        reactivated = self.repo.upsert_repository(
            connection_name="conn-gh",
            origin=RepoOrigin.GITHUB,
            repo_identifier="acme/app",
            github_org="acme",
        )
        self.assertEqual(reactivated.id, entry.id)
        self.assertTrue(reactivated.active)
        self.assertIsNone(reactivated.deactivated_at)

    def test_get_repository_returns_current_snapshot(self) -> None:
        entry = self._register()
        fetched = self.repo.get_repository(entry.id)
        self.assertEqual(fetched.id, entry.id)
        self.assertEqual(fetched.state, RepoState.NOT_INDEXED)

    def test_get_repository_missing_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get_repository(_MISSING_ID)

    def test_list_active_catalog_empty_returns_empty_sequence(self) -> None:
        self.assertEqual(list(self.repo.list_active_catalog()), [])

    def test_list_active_catalog_excludes_soft_deleted(self) -> None:
        active_id = self._drive_to_up_to_date("C1")
        removed = self._register("acme/old")
        self.repo.deactivate_repository(removed.id)
        active = list(self.repo.list_active_catalog())
        ids = {item.id for item in active}
        self.assertIn(active_id, ids)
        self.assertNotIn(removed.id, ids)

    def test_list_active_catalog_exposes_state_and_commit(self) -> None:
        active_id = self._drive_to_up_to_date("C1")
        item = next(i for i in self.repo.list_active_catalog() if i.id == active_id)
        self.assertEqual(item.state, RepoState.UP_TO_DATE)
        self.assertEqual(item.last_processed_commit, "C1")

    def test_deactivate_sets_flags(self) -> None:
        entry = self._register()
        deactivated = self.repo.deactivate_repository(entry.id)
        self.assertFalse(deactivated.active)
        self.assertIsNotNone(deactivated.deactivated_at)

    def test_deactivate_missing_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.deactivate_repository(_MISSING_ID)


# --------------------------------------------------------------------------- #
# transition_state — ordem congelada: existência → versão → validade
# --------------------------------------------------------------------------- #


class TestTransitionState(_Base):
    def test_valid_transition_advances_state_and_bumps_version(self) -> None:
        entry = self._register()
        updated = self.repo.transition_state(
            entry.id, RepoState.QUEUED, expected_version=entry.row_version
        )
        self.assertEqual(updated.state, RepoState.QUEUED)
        self.assertGreater(updated.row_version, entry.row_version)

    def test_idempotent_self_transition_is_noop_without_error(self) -> None:
        entry = self._register()
        queued = self.repo.transition_state(
            entry.id, RepoState.QUEUED, expected_version=entry.row_version
        )
        again = self.repo.transition_state(
            queued.id, RepoState.QUEUED, expected_version=queued.row_version
        )
        self.assertEqual(again.state, RepoState.QUEUED)

    def test_missing_repository_checked_before_version_and_validity(self) -> None:
        # Ordem congelada: existência primeiro, mesmo com versão/alvo inválidos.
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.transition_state(
                _MISSING_ID, RepoState.UP_TO_DATE, expected_version=-1
            )

    def test_stale_version_raises_conflict_even_when_target_valid(self) -> None:
        entry = self._register()
        stale = entry.row_version
        self.repo.mark_queued(entry.id)  # bump da versão por outro "processo"
        with self.assertRaises(ConcurrencyConflictError):
            self.repo.transition_state(
                entry.id, RepoState.INDEXING, expected_version=stale
            )

    def test_version_checked_before_validity(self) -> None:
        # Versão stale + transição ilegal ⇒ ConcurrencyConflictError (versão antes).
        entry = self._register()
        stale = entry.row_version
        self.repo.mark_queued(entry.id)
        with self.assertRaises(ConcurrencyConflictError):
            self.repo.transition_state(
                entry.id, RepoState.UP_TO_DATE, expected_version=stale
            )

    def test_illegal_transition_with_correct_version_raises_and_preserves_state(
        self,
    ) -> None:
        entry = self._register()
        with self.assertRaises(InvalidStateTransitionError):
            self.repo.transition_state(
                entry.id, RepoState.UP_TO_DATE, expected_version=entry.row_version
            )
        self.assertEqual(self.repo.get_repository(entry.id).state, RepoState.NOT_INDEXED)

    def test_reusing_consumed_version_raises_conflict(self) -> None:
        entry = self._register()
        first = self.repo.transition_state(
            entry.id, RepoState.QUEUED, expected_version=entry.row_version
        )
        self.assertEqual(first.state, RepoState.QUEUED)
        with self.assertRaises(ConcurrencyConflictError):
            self.repo.transition_state(
                entry.id, RepoState.INDEXING, expected_version=entry.row_version
            )


# --------------------------------------------------------------------------- #
# atalhos mark_* e efeitos colaterais congelados (interfaces §7)
# --------------------------------------------------------------------------- #


class TestMarkShortcuts(_Base):
    def test_mark_queued_from_not_indexed(self) -> None:
        entry = self._register()
        self.assertEqual(self.repo.mark_queued(entry.id).state, RepoState.QUEUED)

    def test_mark_queued_from_error_restarts(self) -> None:
        rid = self._drive_to_indexing()
        self.repo.mark_error(rid, "boom", _ERROR_AT)
        self.assertEqual(self.repo.mark_queued(rid).state, RepoState.QUEUED)

    def test_mark_queued_is_idempotent_from_queued(self) -> None:
        entry = self._register()
        self.repo.mark_queued(entry.id)
        self.assertEqual(self.repo.mark_queued(entry.id).state, RepoState.QUEUED)

    def test_mark_queued_illegal_from_up_to_date(self) -> None:
        rid = self._drive_to_up_to_date("C1")
        with self.assertRaises(InvalidStateTransitionError):
            self.repo.mark_queued(rid)

    def test_mark_queued_missing_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.mark_queued(_MISSING_ID)

    def test_mark_indexing_from_queued(self) -> None:
        entry = self._register()
        self.repo.mark_queued(entry.id)
        self.assertEqual(self.repo.mark_indexing(entry.id).state, RepoState.INDEXING)

    def test_mark_indexing_does_not_open_execution_implicitly(self) -> None:
        # I-2: nenhuma execução implícita é aberta por mark_indexing.
        rid = self._drive_to_indexing()
        self.assertEqual(list(self.repo.list_executions(rid)), [])

    def test_mark_indexing_illegal_from_not_indexed(self) -> None:
        entry = self._register()
        with self.assertRaises(InvalidStateTransitionError):
            self.repo.mark_indexing(entry.id)

    def test_mark_indexing_missing_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.mark_indexing(_MISSING_ID)

    def test_mark_updated_stamps_commits_and_state(self) -> None:
        rid = self._drive_to_indexing()
        self.repo.start_execution(rid, "C1")
        updated = self.repo.mark_updated(rid, "C1")
        self.assertEqual(updated.state, RepoState.UP_TO_DATE)
        self.assertEqual(updated.last_processed_commit, "C1")
        self.assertEqual(updated.current_main_commit, "C1")

    def test_mark_updated_closes_current_execution_succeeded(self) -> None:
        rid = self._drive_to_indexing()
        self.repo.start_execution(rid, "C1")
        self.repo.mark_updated(rid, "C1")
        history = list(self.repo.list_executions(rid))
        self.assertEqual(len(history), 1)
        self.assertEqual(history[-1].status, ExecutionStatus.SUCCEEDED)
        self.assertIsNotNone(history[-1].finished_at)

    def test_mark_updated_without_open_execution_is_noop_closure(self) -> None:
        # I-1: sem execução corrente, transição + carimbo ocorrem; nada criado.
        rid = self._drive_to_indexing()
        updated = self.repo.mark_updated(rid, "C1")
        self.assertEqual(updated.state, RepoState.UP_TO_DATE)
        self.assertEqual(updated.last_processed_commit, "C1")
        self.assertEqual(list(self.repo.list_executions(rid)), [])

    def test_mark_updated_illegal_from_queued(self) -> None:
        entry = self._register()
        self.repo.mark_queued(entry.id)
        with self.assertRaises(InvalidStateTransitionError):
            self.repo.mark_updated(entry.id, "C1")

    def test_mark_error_sets_state_and_execution_failure(self) -> None:
        rid = self._drive_to_indexing()
        self.repo.start_execution(rid, "C1")
        errored = self.repo.mark_error(rid, "tree-sitter crashed", _ERROR_AT)
        self.assertEqual(errored.state, RepoState.ERROR)
        history = list(self.repo.list_executions(rid))
        failed = [e for e in history if e.status == ExecutionStatus.FAILED]
        self.assertTrue(failed)
        self.assertEqual(failed[-1].error_message, "tree-sitter crashed")
        self.assertEqual(failed[-1].error_at, _ERROR_AT)

    def test_mark_error_without_open_execution_is_noop_closure(self) -> None:
        # I-1: sem execução corrente, transição para error ocorre; nada criado.
        rid = self._drive_to_indexing()
        errored = self.repo.mark_error(rid, "boom", _ERROR_AT)
        self.assertEqual(errored.state, RepoState.ERROR)
        self.assertEqual(list(self.repo.list_executions(rid)), [])

    def test_mark_error_illegal_from_not_indexed(self) -> None:
        entry = self._register()
        with self.assertRaises(InvalidStateTransitionError):
            self.repo.mark_error(entry.id, "boom", _ERROR_AT)


# --------------------------------------------------------------------------- #
# update_main_commit / reconcile_repository
# --------------------------------------------------------------------------- #


class TestMainCommitAndReconcile(_Base):
    def test_update_main_commit_sets_tip_without_changing_state(self) -> None:
        rid = self._drive_to_up_to_date("C1")
        updated = self.repo.update_main_commit(rid, "C2")
        self.assertEqual(updated.current_main_commit, "C2")
        self.assertEqual(updated.state, RepoState.UP_TO_DATE)

    def test_update_main_commit_missing_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.update_main_commit(_MISSING_ID, "C2")

    def test_reconcile_keeps_up_to_date_when_commit_matches(self) -> None:
        rid = self._drive_to_up_to_date("C1")
        self.repo.update_main_commit(rid, "C1")
        reconciled = self.repo.reconcile_repository(rid)
        self.assertEqual(reconciled.state, RepoState.UP_TO_DATE)
        self.assertEqual(reconciled.last_processed_commit, "C1")

    def test_reconcile_reverts_to_not_indexed_on_new_commit(self) -> None:
        rid = self._drive_to_up_to_date("C1")
        self.repo.update_main_commit(rid, "C2")
        reconciled = self.repo.reconcile_repository(rid)
        self.assertEqual(reconciled.state, RepoState.NOT_INDEXED)
        self.assertEqual(
            reconciled.last_processed_commit,
            "C1",
            "base de comparação deve ser preservada",
        )

    def test_reconcile_stays_up_to_date_when_tip_absent(self) -> None:
        # tip desconhecido (current_main_commit None após mark_updated define==commit)
        rid = self._drive_to_indexing()
        self.repo.start_execution(rid, "C1")
        self.repo.mark_updated(rid, "C1")
        # mark_updated define current_main_commit == C1; reconcile mantém.
        reconciled = self.repo.reconcile_repository(rid)
        self.assertEqual(reconciled.state, RepoState.UP_TO_DATE)

    def test_reconcile_is_noop_for_non_up_to_date_states(self) -> None:
        entry = self._register()
        self.repo.mark_queued(entry.id)
        reconciled = self.repo.reconcile_repository(entry.id)
        self.assertEqual(reconciled.state, RepoState.QUEUED)

    def test_reconcile_missing_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.reconcile_repository(_MISSING_ID)


# --------------------------------------------------------------------------- #
# update_progress (REQ-021)
# --------------------------------------------------------------------------- #


class TestProgress(_Base):
    def test_progress_stored_and_readable(self) -> None:
        rid = self._drive_to_indexing()
        self.repo.start_execution(rid, "C1")
        self.repo.update_progress(rid, 50, 5, 10, "tree_sitter")
        entry = self.repo.get_repository(rid)
        self.assertIsNotNone(entry.progress)
        self.assertEqual(entry.progress.percent, 50)
        self.assertEqual(entry.progress.files_processed, 5)
        self.assertEqual(entry.progress.files_total, 10)
        self.assertEqual(entry.progress.current_stage, "tree_sitter")

    def test_progress_boundaries_zero_and_hundred(self) -> None:
        rid = self._drive_to_indexing()
        self.repo.start_execution(rid, "C1")
        self.assertEqual(self.repo.update_progress(rid, 0, 0, 10, "zoekt").progress.percent, 0)
        self.assertEqual(
            self.repo.update_progress(rid, 100, 10, 10, "metadata_persisted").progress.percent,
            100,
        )

    def test_progress_missing_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.update_progress(_MISSING_ID, 50, 5, 10, "tree_sitter")


# --------------------------------------------------------------------------- #
# start_execution / list_executions (REQ-023, histórico)
# --------------------------------------------------------------------------- #


class TestExecutions(_Base):
    def test_start_execution_creates_running_and_links_current(self) -> None:
        rid = self._drive_to_indexing()
        execution = self.repo.start_execution(rid, "C1")
        self.assertEqual(execution.status, ExecutionStatus.RUNNING)
        self.assertEqual(execution.repository_id, rid)
        self.assertEqual(execution.commit_target, "C1")
        self.assertEqual(self.repo.get_repository(rid).current_execution_id, execution.id)

    def test_start_execution_missing_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.start_execution(_MISSING_ID, "C1")

    def test_list_executions_empty_returns_empty_sequence(self) -> None:
        rid = self._drive_to_indexing()
        self.assertEqual(list(self.repo.list_executions(rid)), [])

    def test_list_executions_missing_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.list_executions(_MISSING_ID)

    def test_history_retains_failed_execution_across_retry(self) -> None:
        rid = self._drive_to_indexing()
        self.repo.start_execution(rid, "C1")
        self.repo.mark_error(rid, "boom", _ERROR_AT)
        # nova tentativa (BR-005): error → queued → indexing → nova execução
        self.repo.mark_queued(rid)
        self.repo.mark_indexing(rid)
        self.repo.start_execution(rid, "C2")
        history = list(self.repo.list_executions(rid))
        self.assertGreaterEqual(len(history), 2)
        failed = [e for e in history if e.error_message == "boom"]
        self.assertTrue(failed)
        self.assertEqual(failed[-1].error_at, _ERROR_AT)
        self.assertEqual(failed[-1].status, ExecutionStatus.FAILED)

    def test_history_retained_after_soft_delete(self) -> None:
        rid = self._drive_to_indexing()
        self.repo.start_execution(rid, "C1")
        self.repo.mark_error(rid, "boom", _ERROR_AT)
        self.repo.deactivate_repository(rid)
        history = list(self.repo.list_executions(rid))
        self.assertTrue(any(e.error_message == "boom" for e in history))


# --------------------------------------------------------------------------- #
# record_file_stage / list_file_progress (REQ-022, idempotência)
# --------------------------------------------------------------------------- #


class TestFileStages(_Base):
    def _open_execution(self) -> int:
        rid = self._drive_to_indexing()
        return self.repo.start_execution(rid, "C1").id

    def test_record_all_stages_sets_three_timestamps(self) -> None:
        exec_id = self._open_execution()
        for stage in FileStage:
            self.repo.record_file_stage(exec_id, "src/app.py", stage)
        rows = [fp for fp in self.repo.list_file_progress(exec_id) if fp.file_path == "src/app.py"]
        self.assertEqual(len(rows), 1)
        fp = rows[0]
        self.assertIsNotNone(fp.zoekt_at)
        self.assertIsNotNone(fp.tree_sitter_at)
        self.assertIsNotNone(fp.metadata_persisted_at)

    def test_record_same_stage_is_idempotent_no_duplicate(self) -> None:
        exec_id = self._open_execution()
        first = self.repo.record_file_stage(exec_id, "src/app.py", FileStage.ZOEKT)
        second = self.repo.record_file_stage(exec_id, "src/app.py", FileStage.ZOEKT)
        rows = [fp for fp in self.repo.list_file_progress(exec_id) if fp.file_path == "src/app.py"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(first.zoekt_at, second.zoekt_at)

    def test_distinct_files_produce_distinct_rows(self) -> None:
        exec_id = self._open_execution()
        self.repo.record_file_stage(exec_id, "a.py", FileStage.ZOEKT)
        self.repo.record_file_stage(exec_id, "b.py", FileStage.ZOEKT)
        paths = {fp.file_path for fp in self.repo.list_file_progress(exec_id)}
        self.assertEqual(paths, {"a.py", "b.py"})

    def test_record_file_stage_missing_execution_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.record_file_stage(_MISSING_ID, "src/app.py", FileStage.ZOEKT)

    def test_list_file_progress_empty_returns_empty_sequence(self) -> None:
        exec_id = self._open_execution()
        self.assertEqual(list(self.repo.list_file_progress(exec_id)), [])

    def test_list_file_progress_missing_execution_raises_not_found(self) -> None:
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.list_file_progress(_MISSING_ID)


if __name__ == "__main__":
    unittest.main()
