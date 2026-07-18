"""
BDD executável — T03-catalog-persistence (camada de persistência).

Valida os critérios de aceite da persistência do catálogo via comportamento
observável através da porta `CatalogRepository` (design T03 §3/§6), usando o
fake in-memory (`InMemoryCatalogRepository`) — sem PostgreSQL real.

Escopo (persistência apenas):
    - BDD-004/005: comparar tip da main × last_processed_commit; estado só
      permanece "atualizado" com igualdade.
    - BDD-007: progresso da execução corrente + etapas por arquivo
      (zoekt, tree_sitter, metadata_persisted).
    - BDD-008: estado de erro com mensagem + horário + histórico de execução.
    - ENG-011: list_active_catalog com estado + last_processed_commit.
    - REQ-020: exatamente os 5 estados; transições válidas.
    - Corner: repositório inexistente; update concorrente básico.

Estado esperado antes da implementação: RED. A API `github_rag.catalog`
(enums, erros e `InMemoryCatalogRepository`) ainda não existe; cada cenário
falha com mensagem explícita até o domínio + fake serem implementados
(gate de interfaces/unitários formaliza assinaturas — design §16).

Execução (após venv com pytest):
    python -m pytest tests/bdd/test_catalog_persistence.py -q

Greenfield / sem pytest (stdlib):
    PYTHONPATH=src python3 -m unittest tests.bdd.test_catalog_persistence -v
"""

from __future__ import annotations

import types
import unittest
from datetime import datetime, timezone

# Nomes públicos esperados da API futura do catálogo (design §4/§6/§7).
_REQUIRED_NAMES = (
    "InMemoryCatalogRepository",
    "RepoState",
    "RepoOrigin",
    "FileStage",
    "CatalogError",
    "RepositoryNotFoundError",
    "InvalidStateTransitionError",
    "ConcurrencyConflictError",
)

_EXPECTED_STATES = {"not_indexed", "queued", "indexing", "up_to_date", "error"}


def _load_api() -> types.SimpleNamespace:
    """Importa a API futura do catálogo ou falha com RED explícito.

    Converte ImportError/AttributeError em AssertionError legível para que a
    ausência da implementação apareça como falha de cenário (RED esperado),
    e não como erro de coleta que derrube a suíte inteira.
    """
    try:
        from github_rag import catalog as cat
    except Exception as exc:  # noqa: BLE001 - RED esperado pré-implementação
        raise AssertionError(
            "github_rag.catalog indisponível — RED esperado até a implementação "
            f"da T03 (domínio + fake in-memory): {exc!r}"
        )
    namespace = types.SimpleNamespace()
    missing = []
    for name in _REQUIRED_NAMES:
        obj = getattr(cat, name, None)
        if obj is None:
            missing.append(name)
        setattr(namespace, name, obj)
    if missing:
        raise AssertionError(
            "API do catálogo incompleta — RED esperado até a implementação da "
            f"T03: símbolos ausentes em github_rag.catalog: {missing}"
        )
    return namespace


def _invoke(obj: object, candidates: tuple[str, ...], *args: object, **kwargs: object):
    """Chama a primeira operação disponível dentre nomes equivalentes.

    Tolera refinamento de nomenclatura no gate de interfaces (design §16) sem
    enfraquecer as asserções de comportamento: apenas o verbo que dispara o
    efeito é flexível; os efeitos observados continuam verificados de forma
    estrita.
    """
    for name in candidates:
        fn = getattr(obj, name, None)
        if callable(fn):
            return fn(*args, **kwargs)
    raise AssertionError(
        f"nenhuma operação {candidates} disponível em {type(obj).__name__} "
        "(RED esperado até implementação/definição de interfaces)"
    )


class _CatalogBddTestCase(unittest.TestCase):
    """Base: carrega a API futura e prepara o fake in-memory por cenário."""

    def setUp(self) -> None:
        self.api = _load_api()
        self.repo = self.api.InMemoryCatalogRepository()

    # --- helpers de domínio -------------------------------------------------

    def _state(self, value: str):
        return self.api.RepoState(value)

    def _register_github_repo(self):
        entry = _invoke(
            self.repo,
            ("upsert_repository",),
            connection_name="conn-gh",
            origin=self.api.RepoOrigin("github"),
            github_org="acme",
            repo_identifier="acme/app",
        )
        return entry

    def _get(self, repo_id):
        return _invoke(self.repo, ("get_repository", "get", "find"), repo_id)

    def _active_by_id(self, repo_id):
        for item in _invoke(self.repo, ("list_active_catalog", "list_active")):
            if item.id == repo_id:
                return item
        return None

    def _drive_to_up_to_date(self, commit: str):
        """not_indexed → queued → indexing → up_to_date(commit)."""
        entry = self._register_github_repo()
        rid = entry.id
        _invoke(self.repo, ("mark_queued",), rid)
        _invoke(self.repo, ("mark_indexing",), rid)
        _invoke(self.repo, ("mark_updated", "mark_up_to_date"), rid, commit)
        return rid

    def _read_progress(self, entry):
        prog = getattr(entry, "progress", None)
        if prog is not None:
            return (
                prog.percent,
                prog.files_processed,
                prog.files_total,
                prog.current_stage,
            )
        return (
            entry.progress_percent,
            entry.files_processed,
            entry.files_total,
            entry.current_stage,
        )


class TestCP01CommitEqualStaysUpToDate(_CatalogBddTestCase):
    """CP-01 (BDD-004): tip da main == último commit processado ⇒ 'atualizado'."""

    def test_up_to_date_preserved_when_main_matches_processed_commit(self) -> None:
        rid = self._drive_to_up_to_date("C1")
        _invoke(
            self.repo,
            ("update_main_commit", "record_main_commit", "set_current_main_commit"),
            rid,
            "C1",
        )
        _invoke(self.repo, ("reconcile", "reconcile_repository"), rid)
        entry = self._get(rid)
        self.assertEqual(entry.state, self._state("up_to_date"))
        self.assertEqual(entry.last_processed_commit, "C1")


class TestCP02NewCommitRevertsToNotIndexed(_CatalogBddTestCase):
    """CP-02 (BDD-005): novo commit na main ⇒ volta a 'não indexado' (ENG-011)."""

    def test_new_main_commit_reverts_state_to_not_indexed(self) -> None:
        rid = self._drive_to_up_to_date("C1")
        _invoke(
            self.repo,
            ("update_main_commit", "record_main_commit", "set_current_main_commit"),
            rid,
            "C2",
        )
        _invoke(self.repo, ("reconcile", "reconcile_repository"), rid)
        entry = self._get(rid)
        self.assertEqual(entry.state, self._state("not_indexed"))
        self.assertEqual(
            entry.last_processed_commit,
            "C1",
            "último commit processado deve permanecer como base de comparação",
        )


class TestCP03MarkUpdatedStampsCommits(_CatalogBddTestCase):
    """CP-03 (BDD-004/005): concluir indexação grava processado e tip iguais."""

    def test_successful_indexing_stamps_processed_and_main_commit(self) -> None:
        entry = self._register_github_repo()
        rid = entry.id
        _invoke(self.repo, ("mark_queued",), rid)
        _invoke(self.repo, ("mark_indexing",), rid)
        _invoke(self.repo, ("start_execution", "open_execution"), rid, "C1")
        _invoke(self.repo, ("mark_updated", "mark_up_to_date"), rid, "C1")
        entry = self._get(rid)
        self.assertEqual(entry.state, self._state("up_to_date"))
        self.assertEqual(entry.last_processed_commit, "C1")
        self.assertEqual(entry.current_main_commit, "C1")


class TestCP04ProgressPersisted(_CatalogBddTestCase):
    """CP-04 (BDD-007): progresso da execução corrente persistido e legível."""

    def test_progress_is_stored_and_readable(self) -> None:
        entry = self._register_github_repo()
        rid = entry.id
        _invoke(self.repo, ("mark_queued",), rid)
        _invoke(self.repo, ("mark_indexing",), rid)
        _invoke(self.repo, ("start_execution", "open_execution"), rid, "C1")
        _invoke(
            self.repo,
            ("update_progress",),
            rid,
            50,
            5,
            10,
            "tree_sitter",
        )
        entry = self._active_by_id(rid)
        self.assertIsNotNone(entry, "repositório ativo deve aparecer no catálogo")
        percent, done, total, stage = self._read_progress(entry)
        self.assertEqual(percent, 50)
        self.assertEqual(done, 5)
        self.assertEqual(total, 10)
        self.assertEqual(stage, "tree_sitter")


class TestCP05FileStagesIdempotent(_CatalogBddTestCase):
    """CP-05 (BDD-007): etapas por arquivo registradas idempotentemente."""

    def test_file_stages_recorded_and_idempotent(self) -> None:
        entry = self._register_github_repo()
        rid = entry.id
        _invoke(self.repo, ("mark_queued",), rid)
        _invoke(self.repo, ("mark_indexing",), rid)
        execution = _invoke(self.repo, ("start_execution", "open_execution"), rid, "C1")
        exec_id = execution.id
        path = "src/app.py"
        for stage in ("zoekt", "tree_sitter", "metadata_persisted"):
            _invoke(
                self.repo,
                ("record_file_stage",),
                exec_id,
                path,
                self.api.FileStage(stage),
            )
        # Idempotência: re-registrar a mesma etapa não deve falhar nem duplicar.
        _invoke(
            self.repo,
            ("record_file_stage",),
            exec_id,
            path,
            self.api.FileStage("zoekt"),
        )
        rows = [
            fp
            for fp in _invoke(
                self.repo,
                ("list_file_progress", "list_file_stages"),
                exec_id,
            )
            if fp.file_path == path
        ]
        self.assertEqual(len(rows), 1, "arquivo não deve ser duplicado por etapa repetida")
        fp = rows[0]
        self.assertIsNotNone(fp.zoekt_at)
        self.assertIsNotNone(fp.tree_sitter_at)
        self.assertIsNotNone(fp.metadata_persisted_at)


class TestCP06ErrorStateWithMessageAndTime(_CatalogBddTestCase):
    """CP-06 (BDD-008): estado de erro guarda mensagem e horário."""

    def test_error_records_message_and_timestamp(self) -> None:
        entry = self._register_github_repo()
        rid = entry.id
        _invoke(self.repo, ("mark_queued",), rid)
        _invoke(self.repo, ("mark_indexing",), rid)
        _invoke(self.repo, ("start_execution", "open_execution"), rid, "C1")
        error_at = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)
        _invoke(
            self.repo,
            ("mark_error",),
            rid,
            "tree-sitter crashed",
            error_at,
        )
        entry = self._get(rid)
        self.assertEqual(entry.state, self._state("error"))
        history = list(
            _invoke(self.repo, ("list_execution_history", "list_executions"), rid)
        )
        failed = [e for e in history if e.error_message is not None]
        self.assertTrue(failed, "histórico deve conter a execução falha")
        self.assertEqual(failed[-1].error_message, "tree-sitter crashed")
        self.assertEqual(failed[-1].error_at, error_at)


class TestCP07HistoryRetainedAcrossRetry(_CatalogBddTestCase):
    """CP-07 (BDD-008): histórico retém falhas entre novas tentativas."""

    def test_history_keeps_failed_execution_after_retry(self) -> None:
        entry = self._register_github_repo()
        rid = entry.id
        _invoke(self.repo, ("mark_queued",), rid)
        _invoke(self.repo, ("mark_indexing",), rid)
        _invoke(self.repo, ("start_execution", "open_execution"), rid, "C1")
        error_at = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)
        _invoke(self.repo, ("mark_error",), rid, "boom", error_at)
        # Nova tentativa reinicia o repo (BR-005): error → queued → indexing.
        _invoke(self.repo, ("mark_queued",), rid)
        _invoke(self.repo, ("mark_indexing",), rid)
        _invoke(self.repo, ("start_execution", "open_execution"), rid, "C2")
        history = list(
            _invoke(self.repo, ("list_execution_history", "list_executions"), rid)
        )
        self.assertGreaterEqual(len(history), 2, "falha e nova execução devem coexistir")
        failed = [e for e in history if e.error_message == "boom"]
        self.assertTrue(failed, "execução falha deve ser retida no histórico")
        self.assertEqual(failed[-1].error_at, error_at)


class TestCP08ListActiveCatalog(_CatalogBddTestCase):
    """CP-08 (ENG-011): list_active_catalog só ativos, com estado + commit."""

    def test_only_active_entries_with_state_and_commit(self) -> None:
        active_id = self._drive_to_up_to_date("C1")
        removed = _invoke(
            self.repo,
            ("upsert_repository",),
            connection_name="conn-gh",
            origin=self.api.RepoOrigin("github"),
            github_org="acme",
            repo_identifier="acme/old",
        )
        _invoke(
            self.repo,
            ("deactivate_repository", "deactivate"),
            removed.id,
        )
        active = list(_invoke(self.repo, ("list_active_catalog", "list_active")))
        ids = {item.id for item in active}
        self.assertIn(active_id, ids)
        self.assertNotIn(removed.id, ids, "repo desativado não aparece no catálogo ativo")
        entry = self._active_by_id(active_id)
        self.assertEqual(entry.state, self._state("up_to_date"))
        self.assertEqual(entry.last_processed_commit, "C1")


class TestCP09ClosedStateSet(_CatalogBddTestCase):
    """CP-09 (REQ-020): exatamente 5 estados; sem 'desatualizado'/'indisponível'."""

    def test_repo_state_has_exactly_five_closed_values(self) -> None:
        values = {member.value for member in self.api.RepoState}
        self.assertEqual(values, _EXPECTED_STATES)
        self.assertNotIn("desatualizado", values)
        self.assertNotIn("indisponivel", values)
        self.assertNotIn("indisponível", values)


class TestCP10InvalidTransitionRejected(_CatalogBddTestCase):
    """CP-10 (REQ-020): transição ilegal é rejeitada e estado é preservado."""

    def test_illegal_transition_raises_and_keeps_state(self) -> None:
        entry = self._register_github_repo()
        rid = entry.id
        with self.assertRaises(self.api.InvalidStateTransitionError):
            _invoke(
                self.repo,
                ("transition_state", "transition"),
                rid,
                self._state("up_to_date"),
                expected_version=entry.row_version,
            )
        after = self._get(rid)
        self.assertEqual(after.state, self._state("not_indexed"))


class TestCP11RepositoryNotFound(_CatalogBddTestCase):
    """CP-11 (Corner): operação sobre repo inexistente falha explicitamente."""

    def test_missing_repository_raises_not_found(self) -> None:
        with self.assertRaises(self.api.RepositoryNotFoundError):
            _invoke(self.repo, ("get_repository", "get", "find"), 999_999)


class TestCP12ConcurrentUpdateRejected(_CatalogBddTestCase):
    """CP-12 (Corner): update concorrente com versão desatualizada é rejeitado."""

    def test_stale_expected_version_raises_conflict(self) -> None:
        entry = self._register_github_repo()
        rid = entry.id
        stale_version = entry.row_version
        # Outro processo altera o repo, incrementando a versão da linha.
        _invoke(self.repo, ("mark_queued",), rid)
        with self.assertRaises(self.api.ConcurrencyConflictError):
            _invoke(
                self.repo,
                ("transition_state", "transition"),
                rid,
                self._state("indexing"),
                expected_version=stale_version,
            )


if __name__ == "__main__":
    unittest.main()
