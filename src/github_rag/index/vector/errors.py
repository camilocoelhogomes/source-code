"""Hierarquia de erros tipados do índice vetorial (T13).

Responsabilidade deste módulo
    Sinalizar falhas de store e embeddings sem fallback silencioso.

Motivo da separação
    Distingue falhas Qdrant de falhas de embedding para T14 (BR-005).
"""

from __future__ import annotations


class VectorStoreError(Exception):
    """Base das falhas de persistência/busca vetorial."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class VectorValidationError(VectorStoreError):
    """Record ou scope inválido (summary/text/chunk_id/scope vazios)."""


class VectorDimensionError(VectorStoreError):
    """``len(vector)`` ≠ ``vector_size`` da collection."""


class EmbeddingError(Exception):
    """Base das falhas de embedding."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class EmbeddingValidationError(EmbeddingError):
    """Texto vazio/whitespace ou dimensões inconsistentes no retorno."""
