"""Testes unitários — hierarquia VectorStoreError / EmbeddingError (T13)."""

from __future__ import annotations

import unittest

from github_rag.index.vector.errors import (
    EmbeddingError,
    EmbeddingValidationError,
    VectorDimensionError,
    VectorStoreError,
    VectorValidationError,
)


class TestVectorStoreErrorHierarchy(unittest.TestCase):
    """UT-E01, UT-E04."""

    def test_ut_e01_subclasses_of_vector_store_error(self) -> None:
        for cls in (VectorValidationError, VectorDimensionError):
            with self.subTest(cls=cls.__name__):
                self.assertTrue(issubclass(cls, VectorStoreError))
                self.assertTrue(issubclass(cls, Exception))

    def test_ut_e04_message_on_base(self) -> None:
        err = VectorStoreError("falha qdrant")
        self.assertIn("falha qdrant", str(err))


class TestEmbeddingErrorHierarchy(unittest.TestCase):
    """UT-E02, UT-E03."""

    def test_ut_e02_validation_subclass_of_embedding_error(self) -> None:
        self.assertTrue(issubclass(EmbeddingValidationError, EmbeddingError))
        self.assertTrue(issubclass(EmbeddingValidationError, Exception))

    def test_ut_e03_bases_are_distinct(self) -> None:
        self.assertFalse(issubclass(VectorStoreError, EmbeddingError))
        self.assertFalse(issubclass(EmbeddingError, VectorStoreError))
        self.assertFalse(issubclass(VectorValidationError, EmbeddingError))
        self.assertFalse(issubclass(EmbeddingValidationError, VectorStoreError))


if __name__ == "__main__":
    unittest.main()
