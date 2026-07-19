"""UT-S01/S02 — AppSettings.index_cron."""

from __future__ import annotations

import unittest

from github_rag.settings import (
    DEFAULT_INDEX_CRON,
    ENV_INDEX_CRON,
    load_settings,
)


class TestIndexCronSettings(unittest.TestCase):
    def test_default_when_absent(self) -> None:
        settings = load_settings({})
        self.assertEqual(settings.index_cron, DEFAULT_INDEX_CRON)
        self.assertEqual(DEFAULT_INDEX_CRON, "0 2 * * *")
        self.assertEqual(ENV_INDEX_CRON, "INDEX_CRON")

    def test_default_when_blank(self) -> None:
        for blank in ("", "  ", "\t"):
            with self.subTest(blank=repr(blank)):
                settings = load_settings({ENV_INDEX_CRON: blank})
                self.assertEqual(settings.index_cron, DEFAULT_INDEX_CRON)

    def test_explicit_value_distinct_from_product_default(self) -> None:
        settings = load_settings({ENV_INDEX_CRON: "0 3 * * *"})
        self.assertEqual(settings.index_cron, "0 3 * * *")
        self.assertNotEqual(settings.index_cron, DEFAULT_INDEX_CRON)


if __name__ == "__main__":
    unittest.main()
