"""Testes unitários — enums fechados e read models imutáveis (T03).

Escopo
    Contratos de dados de ``github_rag.catalog.models`` (interfaces §2/§3):
    enums fechados (REQ-020 + ``ExecutionStatus`` distinto) e dataclasses
    ``frozen=True`` (`Progress`, `CatalogEntry`, `IndexingExecution`,
    `FileProgress`).

Nota RED
    Os modelos são CONTRATOS DE DADOS já congelados no gate de interfaces (sem
    ``...``), portanto estes casos passam desde já. Estão aqui para blindar a
    forma congelada (fechamento dos enums, imutabilidade, defaults) contra
    regressão durante a implementação do fake/adaptador.
"""

from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timezone

from github_rag.catalog import (
    CatalogEntry,
    ExecutionStatus,
    FileProgress,
    FileStage,
    IndexingExecution,
    Progress,
    RepoOrigin,
    RepoState,
)

_NOW = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)


class TestRepoStateEnum(unittest.TestCase):
    """REQ-020: exatamente 5 estados fechados; sem extras proibidos."""

    def test_exactly_five_closed_values(self) -> None:
        self.assertEqual(
            {m.value for m in RepoState},
            {"not_indexed", "queued", "indexing", "up_to_date", "error"},
        )

    def test_forbidden_labels_absent(self) -> None:
        values = {m.value for m in RepoState}
        self.assertNotIn("desatualizado", values)
        self.assertNotIn("indisponivel", values)
        self.assertNotIn("indisponível", values)

    def test_is_str_subclass_for_value_lookup(self) -> None:
        self.assertIsInstance(RepoState.NOT_INDEXED, str)
        self.assertEqual(RepoState("not_indexed"), RepoState.NOT_INDEXED)
        self.assertEqual(RepoState.UP_TO_DATE.value, "up_to_date")

    def test_unknown_value_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            RepoState("desatualizado")


class TestOtherEnums(unittest.TestCase):
    """RepoOrigin, FileStage e ExecutionStatus fechados e distintos."""

    def test_repo_origin_values(self) -> None:
        self.assertEqual({m.value for m in RepoOrigin}, {"github", "local"})
        self.assertIsInstance(RepoOrigin.GITHUB, str)

    def test_file_stage_values(self) -> None:
        self.assertEqual(
            {m.value for m in FileStage},
            {"zoekt", "tree_sitter", "metadata_persisted"},
        )

    def test_execution_status_values(self) -> None:
        self.assertEqual(
            {m.value for m in ExecutionStatus},
            {"running", "succeeded", "failed"},
        )

    def test_execution_status_is_distinct_from_repo_state(self) -> None:
        # S-2: status de execução NÃO colide com RepoState (REQ-020).
        self.assertTrue({m.value for m in ExecutionStatus}.isdisjoint({m.value for m in RepoState}))


class TestFrozenReadModels(unittest.TestCase):
    """Snapshots de leitura são imutáveis (frozen=True)."""

    def _entry(self) -> CatalogEntry:
        return CatalogEntry(
            id=1,
            connection_name="conn",
            origin=RepoOrigin.GITHUB,
            repo_identifier="acme/app",
            state=RepoState.NOT_INDEXED,
            active=True,
            row_version=1,
            github_org="acme",
        )

    def test_catalog_entry_defaults_are_none(self) -> None:
        entry = self._entry()
        self.assertIsNone(entry.local_path)
        self.assertIsNone(entry.last_processed_commit)
        self.assertIsNone(entry.current_main_commit)
        self.assertIsNone(entry.progress)
        self.assertIsNone(entry.current_execution_id)
        self.assertIsNone(entry.deactivated_at)
        self.assertIsNone(entry.created_at)
        self.assertIsNone(entry.updated_at)

    def test_catalog_entry_is_frozen(self) -> None:
        entry = self._entry()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            entry.state = RepoState.QUEUED  # type: ignore[misc]

    def test_progress_is_frozen_and_holds_values(self) -> None:
        prog = Progress(percent=50, files_processed=5, files_total=10, current_stage="tree_sitter")
        self.assertEqual(prog.percent, 50)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            prog.percent = 60  # type: ignore[misc]

    def test_progress_accepts_none_fields(self) -> None:
        prog = Progress(percent=None, files_processed=None, files_total=None, current_stage=None)
        self.assertIsNone(prog.percent)

    def test_indexing_execution_defaults_and_frozen(self) -> None:
        execution = IndexingExecution(
            id=1,
            repository_id=1,
            status=ExecutionStatus.RUNNING,
            started_at=_NOW,
        )
        self.assertIsNone(execution.finished_at)
        self.assertIsNone(execution.commit_target)
        self.assertIsNone(execution.error_message)
        self.assertIsNone(execution.error_at)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            execution.status = ExecutionStatus.FAILED  # type: ignore[misc]

    def test_file_progress_defaults_and_frozen(self) -> None:
        fp = FileProgress(id=1, execution_id=1, file_path="src/app.py")
        self.assertIsNone(fp.zoekt_at)
        self.assertIsNone(fp.tree_sitter_at)
        self.assertIsNone(fp.metadata_persisted_at)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            fp.zoekt_at = _NOW  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
