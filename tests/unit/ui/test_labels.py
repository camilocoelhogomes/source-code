"""Unit — labels PT REQ-020 (T18)."""

from __future__ import annotations

import unittest

from github_rag.catalog.models import RepoState
from github_rag.ui.labels import STATE_LABELS, state_label


class TestStateLabels(unittest.TestCase):
    def test_all_states_have_pt_labels(self) -> None:
        expected = {
            RepoState.NOT_INDEXED: "não indexado",
            RepoState.QUEUED: "na fila",
            RepoState.INDEXING: "indexando",
            RepoState.UP_TO_DATE: "atualizado",
            RepoState.ERROR: "erro",
        }
        self.assertEqual(dict(STATE_LABELS), expected)
        for state, label in expected.items():
            self.assertEqual(state_label(state), label)

    def test_labels_are_unique(self) -> None:
        labels = list(STATE_LABELS.values())
        self.assertEqual(len(labels), len(set(labels)))


if __name__ == "__main__":
    unittest.main()
