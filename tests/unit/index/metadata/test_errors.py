"""Testes unitários — hierarquia MetadataGenerationError (T12)."""

from __future__ import annotations

import unittest

from github_rag.index.metadata.errors import (
    MetadataConfigError,
    MetadataGenerationError,
    MetadataModelError,
    MetadataResponseParseError,
)


class TestMetadataErrorHierarchy(unittest.TestCase):
    """UT-E01."""

    def test_ut_e01_subclasses(self) -> None:
        for cls in (
            MetadataConfigError,
            MetadataModelError,
            MetadataResponseParseError,
        ):
            with self.subTest(cls=cls.__name__):
                self.assertTrue(issubclass(cls, MetadataGenerationError))
                self.assertTrue(issubclass(cls, Exception))


class TestMetadataErrorAttributes(unittest.TestCase):
    """UT-E02, UT-E03."""

    def test_ut_e02_chunk_id_and_path(self) -> None:
        err = MetadataModelError(
            "falha no modelo",
            chunk_id="c-9",
            path="src/app.py",
        )
        self.assertEqual(err.chunk_id, "c-9")
        self.assertEqual(err.path, "src/app.py")
        text = str(err)
        self.assertIn("c-9", text)
        self.assertIn("src/app.py", text)

    def test_ut_e03_message_must_not_leak_api_key_value(self) -> None:
        secret = "sk-super-secret-value-xyz"
        err = MetadataModelError(
            "falha de autenticação no runtime (campo api_key rejeitado)",
            chunk_id="c-1",
            path="a.py",
        )
        # Contrato: mensagens podem citar o nome do campo, nunca o valor do secret;
        # a classe não armazena api_key (vazamento via attrs/repr).
        self.assertNotIn(secret, str(err))
        self.assertNotIn(secret, repr(err))
        self.assertFalse(hasattr(err, "api_key"))
        self.assertIn("api_key", err.args[0])


if __name__ == "__main__":
    unittest.main()
