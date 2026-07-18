"""Índice vetorial Qdrant + embeddings OpenAI-compatible (T13)."""

from github_rag.index.vector.embedder import OpenAICompatibleEmbedder
from github_rag.index.vector.errors import (
    EmbeddingError,
    EmbeddingValidationError,
    VectorDimensionError,
    VectorStoreError,
    VectorValidationError,
)
from github_rag.index.vector.ports import Embedder, VectorStore
from github_rag.index.vector.qdrant_store import QdrantVectorStore
from github_rag.index.vector.types import (
    ChunkMetadata,
    EnrichedChunk,
    RepoCommitScope,
    SemanticHit,
    VectorRecord,
)

__all__ = [
    "ChunkMetadata",
    "EmbeddingError",
    "EmbeddingValidationError",
    "Embedder",
    "EnrichedChunk",
    "OpenAICompatibleEmbedder",
    "QdrantVectorStore",
    "RepoCommitScope",
    "SemanticHit",
    "VectorDimensionError",
    "VectorRecord",
    "VectorStore",
    "VectorStoreError",
    "VectorValidationError",
]
