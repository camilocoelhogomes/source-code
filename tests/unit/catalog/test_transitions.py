"""Testes unitários — máquina de estados e regras puras de commit (T03).

Escopo
    Domínio puro de ``github_rag.catalog.transitions`` (sem I/O, sem PG):
    ``ALLOWED_TRANSITIONS``, ``IDEMPOTENT_SELF_STATES``, ``is_transition_allowed``,
    ``ensure_transition_allowed`` e ``is_up_to_date`` (interfaces §5; resolve S-1).

Estratégia RED (pré-implementação)
    As três funções permanecem stub (``...`` ⇒ retornam ``None``). Os casos de
    comportamento asseram valores/exceções ESTRITOS (``assertIs(..., True/False)``
    e ``assertRaises``); com o stub retornando ``None`` e não levantando, esses
    casos FALHAM pela razão esperada até o Developer preencher as funções. Os
    casos de estrutura de dados (``ALLOWED_TRANSITIONS``/``IDEMPOTENT_SELF_STATES``)
    passam desde já — são contratos declarativos congelados nas interfaces.
"""

from __future__ import annotations

import unittest

from github_rag.catalog import (
    ALLOWED_TRANSITIONS,
    IDEMPOTENT_SELF_STATES,
    InvalidStateTransitionError,
    RepoState,
    ensure_transition_allowed,
    is_transition_allowed,
    is_up_to_date,
)

S = RepoState

# Conjunto FECHADO de transições válidas (interfaces §5.1). Fonte de verdade dos
# casos positivos/negativos abaixo; qualquer par ausente é ilegal.
_VALID_PAIRS = frozenset(
    {
        (S.NOT_INDEXED, S.QUEUED),
        (S.QUEUED, S.INDEXING),
        (S.INDEXING, S.UP_TO_DATE),
        (S.INDEXING, S.ERROR),
        (S.ERROR, S.QUEUED),
        (S.ERROR, S.NOT_INDEXED),
        (S.UP_TO_DATE, S.NOT_INDEXED),
    }
)

# Auto-transições (target == current) que são no-op idempotente (interfaces §5.2).
_IDEMPOTENT_SELF = frozenset({(S.NOT_INDEXED, S.NOT_INDEXED), (S.QUEUED, S.QUEUED)})

# Auto-transições ilegais (target == current) — interfaces §5.2.
_ILLEGAL_SELF = frozenset(
    {(S.INDEXING, S.INDEXING), (S.UP_TO_DATE, S.UP_TO_DATE), (S.ERROR, S.ERROR)}
)


class TestAllowedTransitionsContract(unittest.TestCase):
    """A tabela declarativa é o contrato congelado da máquina de estados."""

    def test_allowed_transitions_matches_frozen_spec(self) -> None:
        expected = {
            S.NOT_INDEXED: frozenset({S.QUEUED}),
            S.QUEUED: frozenset({S.INDEXING}),
            S.INDEXING: frozenset({S.UP_TO_DATE, S.ERROR}),
            S.UP_TO_DATE: frozenset({S.NOT_INDEXED}),
            S.ERROR: frozenset({S.QUEUED, S.NOT_INDEXED}),
        }
        self.assertEqual(ALLOWED_TRANSITIONS, expected)

    def test_every_repo_state_is_a_source_key(self) -> None:
        self.assertEqual(set(ALLOWED_TRANSITIONS.keys()), set(RepoState))

    def test_idempotent_self_states_are_exactly_not_indexed_and_queued(self) -> None:
        self.assertEqual(
            IDEMPOTENT_SELF_STATES, frozenset({S.NOT_INDEXED, S.QUEUED})
        )

    def test_terminal_working_states_have_no_self_idempotency(self) -> None:
        for state in (S.INDEXING, S.UP_TO_DATE, S.ERROR):
            self.assertNotIn(state, IDEMPOTENT_SELF_STATES)


class TestIsTransitionAllowed(unittest.TestCase):
    """Predicado puro: True/False estritos (interfaces §5.1/§5.2)."""

    def test_all_valid_pairs_are_allowed(self) -> None:
        for current, target in _VALID_PAIRS:
            with self.subTest(current=current, target=target):
                self.assertIs(is_transition_allowed(current, target), True)

    def test_idempotent_self_transitions_are_allowed(self) -> None:
        for current, target in _IDEMPOTENT_SELF:
            with self.subTest(current=current, target=target):
                self.assertIs(is_transition_allowed(current, target), True)

    def test_illegal_self_transitions_are_rejected(self) -> None:
        for current, target in _ILLEGAL_SELF:
            with self.subTest(current=current, target=target):
                self.assertIs(is_transition_allowed(current, target), False)

    def test_all_other_pairs_are_rejected(self) -> None:
        for current in RepoState:
            for target in RepoState:
                pair = (current, target)
                if pair in _VALID_PAIRS or pair in _IDEMPOTENT_SELF:
                    continue
                with self.subTest(current=current, target=target):
                    self.assertIs(is_transition_allowed(current, target), False)

    def test_representative_illegal_shortcuts_are_rejected(self) -> None:
        # Corner cases explícitos citados no BDD/interfaces (pulos ilegais).
        for current, target in (
            (S.NOT_INDEXED, S.UP_TO_DATE),  # BDD CP-10
            (S.NOT_INDEXED, S.INDEXING),
            (S.NOT_INDEXED, S.ERROR),
            (S.QUEUED, S.UP_TO_DATE),
            (S.QUEUED, S.ERROR),
            (S.QUEUED, S.NOT_INDEXED),
            (S.UP_TO_DATE, S.QUEUED),
            (S.UP_TO_DATE, S.INDEXING),
            (S.UP_TO_DATE, S.ERROR),
            (S.ERROR, S.INDEXING),
            (S.ERROR, S.UP_TO_DATE),
            (S.INDEXING, S.QUEUED),
            (S.INDEXING, S.NOT_INDEXED),
        ):
            with self.subTest(current=current, target=target):
                self.assertIs(is_transition_allowed(current, target), False)


class TestEnsureTransitionAllowed(unittest.TestCase):
    """Guarda de escrita: no-op em transição válida, erro tipado em ilegal."""

    def test_valid_transition_does_not_raise_and_returns_none(self) -> None:
        for current, target in _VALID_PAIRS | _IDEMPOTENT_SELF:
            with self.subTest(current=current, target=target):
                self.assertIsNone(ensure_transition_allowed(current, target))

    def test_illegal_transition_raises_invalid_state_transition(self) -> None:
        for current, target in _ILLEGAL_SELF | {
            (S.NOT_INDEXED, S.UP_TO_DATE),
            (S.UP_TO_DATE, S.QUEUED),
            (S.ERROR, S.INDEXING),
        }:
            with self.subTest(current=current, target=target):
                with self.assertRaises(InvalidStateTransitionError):
                    ensure_transition_allowed(current, target)


class TestIsUpToDate(unittest.TestCase):
    """Comparação pura de commit (BR-002/004; interfaces §5.3)."""

    def test_true_only_when_both_present_and_equal(self) -> None:
        self.assertIs(is_up_to_date("C1", "C1"), True)

    def test_false_when_commits_differ(self) -> None:
        self.assertIs(is_up_to_date("C1", "C2"), False)

    def test_false_when_processed_commit_is_none(self) -> None:
        self.assertIs(is_up_to_date(None, "C1"), False)

    def test_false_when_main_tip_is_none(self) -> None:
        self.assertIs(is_up_to_date("C1", None), False)

    def test_false_when_both_none(self) -> None:
        self.assertIs(is_up_to_date(None, None), False)

    def test_comparison_is_case_sensitive(self) -> None:
        self.assertIs(is_up_to_date("abc123", "ABC123"), False)

    def test_full_length_sha_equality(self) -> None:
        sha = "a" * 40
        self.assertIs(is_up_to_date(sha, sha), True)


if __name__ == "__main__":
    unittest.main()
