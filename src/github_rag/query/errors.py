"""Hierarquia tipada de falhas de consulta (T16).

Responsabilidade deste módulo
    Declarar QueryError e subclasses por família de backend / validação.

Motivo da separação
    T17/T18 mapeiam tipos estáveis sem ``except Exception`` (I-T16-008).
"""

from __future__ import annotations


class QueryError(Exception):
    """Base das falhas de consulta compartilhada."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class QueryValidationError(QueryError):
    """Pedido inválido: repo ambíguo, path/query vazios, escopo ausente, etc."""


class QueryRepositoryNotFoundError(QueryError):
    """Catálogo: id/key ausente ou ``active=False``."""


class QueryCommitUnavailableError(QueryError):
    """Browse sem ``commit_sha`` e sem ``last_processed_commit``."""


class QueryExactIndexError(QueryError):
    """Falha Zoekt na busca; envolve ``ExactCodeIndexError`` em ``__cause__``."""


class QueryVectorError(QueryError):
    """Falha Qdrant search; envolve ``VectorStoreError`` em ``__cause__``."""


class QueryEmbeddingError(QueryError):
    """Falha Embedder; envolve ``EmbeddingError`` em ``__cause__``."""


class QuerySnapshotError(QueryError):
    """Falha read/tree; envolve ``SnapshotError`` em ``__cause__``."""


class QueryReformulatorError(QueryError):
    """Falha da porta opcional ``QueryReformulator``."""
