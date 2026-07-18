"""Testes unitários — hierarquia ChunkingError (T11)."""

from __future__ import annotations

import unittest

from github_rag.index.chunk.errors import (
    BinarySourceError,
    ChunkingError,
    EmptySourceError,
    GrammarUnavailableError,
    ParseFailureError,
)
from github_rag.index.chunk.types import SourceLanguage


class TestChunkingErrorHierarchy(unittest.TestCase):
    """UT-E01."""

    def test_ut_e01_subclasses_of_chunking_error(self) -> None:
        for cls in (
            EmptySourceError,
            BinarySourceError,
            GrammarUnavailableError,
            ParseFailureError,
        ):
            with self.subTest(cls=cls.__name__):
                self.assertTrue(issubclass(cls, ChunkingError))
                self.assertTrue(issubclass(cls, Exception))


class TestChunkingErrorMessage(unittest.TestCase):
    """UT-E02."""

    def test_ut_e02_path_in_empty_source_message(self) -> None:
        err = EmptySourceError("arquivo vazio", path="src/empty.py")
        self.assertEqual(err.path, "src/empty.py")
        self.assertIn("src/empty.py", str(err))

    def test_language_attr_optional(self) -> None:
        err = GrammarUnavailableError(
            "sem grammar",
            path="main.rs",
            language=None,
        )
        self.assertIsNone(err.language)
        err_py = GrammarUnavailableError(
            "sem pacote",
            path="a.py",
            language=SourceLanguage.PYTHON,
        )
        self.assertEqual(err_py.language, SourceLanguage.PYTHON)

    def test_empty_message_with_path_and_language(self) -> None:
        err = ChunkingError(path="p.py", language=SourceLanguage.PYTHON)
        self.assertIn("path=p.py", str(err))
        self.assertIn("language=python", str(err))

    def test_message_already_contains_path_not_duplicated(self) -> None:
        err = EmptySourceError("falha em src/empty.py", path="src/empty.py")
        self.assertEqual(str(err).count("src/empty.py"), 1)


if __name__ == "__main__":
    unittest.main()
