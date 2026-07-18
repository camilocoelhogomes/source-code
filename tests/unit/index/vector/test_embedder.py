"""Testes unitários — OpenAICompatibleEmbedder (T13)."""

from __future__ import annotations

import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from github_rag.index.vector.embedder import OpenAICompatibleEmbedder
from github_rag.index.vector.errors import EmbeddingError, EmbeddingValidationError
from tests.unit.index.vector.fixtures import (
    VECTOR_SIZE,
    assert_no_chunking_params,
    make_embedder,
)


def _embedding_response(vectors: list[list[float]]) -> SimpleNamespace:
    data = [
        SimpleNamespace(embedding=vec, index=i) for i, vec in enumerate(vectors)
    ]
    return SimpleNamespace(data=data)


class TestEmbedderValidation(unittest.TestCase):
    """UT-EM01, UT-EM02, UT-X04."""

    def test_ut_em01_empty_batch_no_io(self) -> None:
        stub = MagicMock()
        embedder = make_embedder(client=stub)
        self.assertEqual(embedder.embed(()), ())
        stub.embeddings.create.assert_not_called()

    def test_ut_em02_blank_and_empty_text(self) -> None:
        stub = MagicMock()
        embedder = make_embedder(client=stub)
        for texts in (("   ",), ("",), ("ok", "  ")):
            with self.subTest(texts=texts):
                stub.reset_mock()
                with self.assertRaises(EmbeddingValidationError) as ctx:
                    embedder.embed(texts)
                self.assertIsInstance(ctx.exception, EmbeddingError)
                stub.embeddings.create.assert_not_called()

    def test_ut_x04_valid_after_empty_batch(self) -> None:
        stub = MagicMock()
        stub.embeddings.create.return_value = _embedding_response(
            [[0.1, 0.2, 0.3, 0.4]]
        )
        embedder = make_embedder(client=stub)
        self.assertEqual(embedder.embed(()), ())
        stub.embeddings.create.assert_not_called()
        result = embedder.embed(("hello",))
        self.assertEqual(len(result), 1)
        stub.embeddings.create.assert_called_once()


class TestEmbedderHappyAndFailures(unittest.TestCase):
    """UT-EM03, UT-EM04, UT-EM05, UT-EM07, UT-EM08."""

    def test_ut_em03_preserves_order_and_dimensions(self) -> None:
        stub = MagicMock()
        stub.embeddings.create.return_value = _embedding_response(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
            ]
        )
        embedder = make_embedder(client=stub)
        result = embedder.embed(("alpha", "beta"))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], (1.0, 0.0, 0.0, 0.0))
        self.assertEqual(result[1], (0.0, 1.0, 0.0, 0.0))
        for vec in result:
            self.assertEqual(len(vec), VECTOR_SIZE)

    def test_ut_em04_dimension_mismatch_on_return(self) -> None:
        stub = MagicMock()
        stub.embeddings.create.return_value = _embedding_response([[1.0, 0.0]])
        embedder = make_embedder(client=stub, dimensions=4)
        with self.assertRaises(EmbeddingValidationError):
            embedder.embed(("text",))

    def test_ut_em05_sdk_failure_maps_to_embedding_error(self) -> None:
        stub = MagicMock()
        stub.embeddings.create.side_effect = RuntimeError("network down")
        embedder = make_embedder(client=stub)
        with self.assertRaises(EmbeddingError) as ctx:
            embedder.embed(("text",))
        self.assertNotIsInstance(ctx.exception, EmbeddingValidationError)

    def test_ut_em07_dimensions_property(self) -> None:
        embedder = make_embedder(dimensions=8)
        self.assertEqual(embedder.dimensions, 8)

    def test_ut_em08_create_receives_model(self) -> None:
        stub = MagicMock()
        stub.embeddings.create.return_value = _embedding_response(
            [[0.0, 0.0, 0.0, 0.0]]
        )
        embedder = make_embedder(client=stub, model="my-emb-model")
        embedder.embed(("x",))
        kwargs = stub.embeddings.create.call_args.kwargs
        self.assertEqual(kwargs.get("model"), "my-emb-model")

    def test_ut_em09_count_mismatch_on_return(self) -> None:
        stub = MagicMock()
        stub.embeddings.create.return_value = _embedding_response(
            [[0.1, 0.2, 0.3, 0.4]]
        )
        embedder = make_embedder(client=stub)
        with self.assertRaises(EmbeddingValidationError) as ctx:
            embedder.embed(("a", "b"))
        self.assertIn("expected 2", str(ctx.exception))


class TestEmbedderSdkConformity(unittest.TestCase):
    """UT-EM06 / VS-06."""

    def test_ut_em06_openai_embeddings_only_no_chat(self) -> None:
        import openai  # noqa: F401

        source = inspect.getsource(OpenAICompatibleEmbedder)
        self.assertIn("openai", source.lower())
        self.assertIn("embeddings", source.lower())
        self.assertNotIn("chat.completions", source)
        self.assertNotIn("requests.", source)
        self.assertNotIn("httpx.", source)
        assert_no_chunking_params(OpenAICompatibleEmbedder)


if __name__ == "__main__":
    unittest.main()
