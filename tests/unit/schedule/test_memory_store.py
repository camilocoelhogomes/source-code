"""UT-S05/S06 — InMemoryCronPreferenceStore."""

from __future__ import annotations

import unittest

from github_rag.schedule.errors import InvalidCronExpressionError
from github_rag.schedule.memory import InMemoryCronPreferenceStore
from github_rag.schedule.ports import CronPreferenceStore


class TestInMemoryCronPreferenceStore(unittest.TestCase):
    def test_runtime_checkable(self) -> None:
        store = InMemoryCronPreferenceStore()
        self.assertIsInstance(store, CronPreferenceStore)

    def test_get_none_initially(self) -> None:
        store = InMemoryCronPreferenceStore()
        self.assertIsNone(store.get())

    def test_set_get_clear(self) -> None:
        store = InMemoryCronPreferenceStore()
        self.assertEqual(store.set("0 */6 * * *"), "0 */6 * * *")
        self.assertEqual(store.get(), "0 */6 * * *")
        store.clear()
        self.assertIsNone(store.get())

    def test_invalid_set_does_not_persist(self) -> None:
        store = InMemoryCronPreferenceStore()
        store.set("0 2 * * *")
        with self.assertRaises(InvalidCronExpressionError):
            store.set("not-a-cron")
        self.assertEqual(store.get(), "0 2 * * *")


if __name__ == "__main__":
    unittest.main()
