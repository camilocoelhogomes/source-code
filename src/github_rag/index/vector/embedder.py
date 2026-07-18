"""Adaptador de embeddings via SDK oficial ``openai`` (T13).

Responsabilidade deste módulo
    Implementar ``Embedder`` com ``embeddings.create`` apenas.

Motivo da separação
    Distinto de MetadataGenerator/chat (T12); sem client HTTP inventado.
"""

from __future__ import annotations

from typing import Any, Sequence

import openai

from github_rag.index.vector.errors import EmbeddingError, EmbeddingValidationError


class OpenAICompatibleEmbedder:
    """Implementação ``Embedder`` sobre cliente ``openai.OpenAI``."""

    def __init__(
        self,
        *,
        client: Any,
        model: str,
        dimensions: int,
    ) -> None:
        self._client = client  # openai.OpenAI (ou stub injetável)
        self._model = model
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()
        for text in texts:
            if not text or not text.strip():
                raise EmbeddingValidationError(
                    "embedding text must be non-empty"
                )
        try:
            response = self._client.embeddings.create(
                model=self._model,
                input=list(texts),
            )
        except EmbeddingError:
            raise
        except Exception as exc:
            raise EmbeddingError(f"embeddings create failed: {exc}") from exc

        items = sorted(response.data, key=lambda item: getattr(item, "index", 0))
        if len(items) != len(texts):
            raise EmbeddingValidationError(
                f"expected {len(texts)} embeddings, got {len(items)}"
            )
        vectors: list[tuple[float, ...]] = []
        for item in items:
            vector = tuple(float(x) for x in item.embedding)
            if len(vector) != self._dimensions:
                raise EmbeddingValidationError(
                    f"embedding length {len(vector)} != {self._dimensions}"
                )
            vectors.append(vector)
        return tuple(vectors)
