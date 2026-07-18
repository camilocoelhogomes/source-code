"""Testes unitários — SlmClientSettings (T12)."""

from __future__ import annotations

import dataclasses
import unittest

from github_rag.index.metadata.config import SlmClientSettings


class TestSlmClientSettings(unittest.TestCase):
    """UT-C01..UT-C04."""

    def test_ut_c01_default_model_qwen_coder_3b(self) -> None:
        settings = SlmClientSettings(base_url="http://127.0.0.1:11434/v1")
        self.assertEqual(settings.model, "qwen2.5-coder:3b")

    def test_ut_c02_default_api_key_and_timeout(self) -> None:
        settings = SlmClientSettings(base_url="http://127.0.0.1:11434/v1")
        self.assertEqual(settings.api_key, "local")
        self.assertEqual(settings.timeout_seconds, 60.0)

    def test_ut_c03_frozen(self) -> None:
        settings = SlmClientSettings(base_url="http://127.0.0.1:11434/v1")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            settings.model = "other"  # type: ignore[misc]

    def test_ut_c04_model_override(self) -> None:
        settings = SlmClientSettings(
            base_url="http://127.0.0.1:11434/v1",
            model="custom-coder:7b",
        )
        self.assertEqual(settings.model, "custom-coder:7b")


if __name__ == "__main__":
    unittest.main()
