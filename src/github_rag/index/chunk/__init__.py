"""Chunking contextual Tree-sitter (T11)."""

from github_rag.index.chunk.errors import (
    BinarySourceError,
    ChunkingError,
    EmptySourceError,
    GrammarUnavailableError,
    ParseFailureError,
)
from github_rag.index.chunk.ports import ContextualChunker
from github_rag.index.chunk.treesitter import TreeSitterContextualChunker
from github_rag.index.chunk.types import (
    ChunkSourceFile,
    SemanticChunk,
    SourceLanguage,
    compute_chunk_id,
)

__all__ = [
    "BinarySourceError",
    "ChunkSourceFile",
    "ChunkingError",
    "ContextualChunker",
    "EmptySourceError",
    "GrammarUnavailableError",
    "ParseFailureError",
    "SemanticChunk",
    "SourceLanguage",
    "TreeSitterContextualChunker",
    "compute_chunk_id",
]
