"""Helpers compartilhados dos unitários T13 (não são testes)."""

from __future__ import annotations

import inspect
import math
from typing import Any
from unittest.mock import MagicMock

from github_rag.index.chunk.types import SemanticChunk, SourceLanguage
from github_rag.index.vector.embedder import OpenAICompatibleEmbedder
from github_rag.index.vector.qdrant_store import QdrantVectorStore
from github_rag.index.vector.types import (
    ChunkMetadata,
    EnrichedChunk,
    VectorRecord,
)

VECTOR_SIZE = 4
CHUNKING_PARAM_NAMES = frozenset(
    {"max_chars", "chunk_size", "overlap", "max_lines", "window_size"}
)


def normalize(v: tuple[float, ...]) -> tuple[float, ...]:
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return tuple(x / norm for x in v)


def make_chunk(
    *,
    chunk_id: str,
    path: str = "src/app.py",
    text: str = "def hello():\n    return 1\n",
    kind: str = "function",
    language: SourceLanguage = SourceLanguage.PYTHON,
    start_byte: int | None = None,
    end_byte: int | None = None,
    start_point: tuple[int, int] = (0, 0),
    end_point: tuple[int, int] = (1, 0),
) -> SemanticChunk:
    encoded = text.encode("utf-8")
    sb = 0 if start_byte is None else start_byte
    eb = len(encoded) if end_byte is None else end_byte
    return SemanticChunk(
        chunk_id=chunk_id,
        path=path,
        language=language,
        kind=kind,
        text=text,
        start_byte=sb,
        end_byte=eb,
        start_point=start_point,
        end_point=end_point,
    )


def make_enriched(
    chunk: SemanticChunk,
    *,
    summary: str = "função hello",
    keywords: tuple[str, ...] = ("hello",),
    symbols: tuple[str, ...] = ("hello",),
) -> EnrichedChunk:
    return EnrichedChunk(
        chunk=chunk,
        metadata=ChunkMetadata(summary=summary, keywords=keywords, symbols=symbols),
    )


def make_record(
    enriched: EnrichedChunk,
    vector: tuple[float, ...],
) -> VectorRecord:
    return VectorRecord(enriched=enriched, vector=vector)


def make_store(vector_size: int = VECTOR_SIZE) -> QdrantVectorStore:
    from qdrant_client import QdrantClient

    client = QdrantClient(":memory:")
    return QdrantVectorStore(
        client=client,
        collection_name="github_rag_chunks_unit",
        vector_size=vector_size,
    )


def make_embedder(
    *,
    client: Any | None = None,
    dimensions: int = VECTOR_SIZE,
    model: str = "test-embedding",
) -> OpenAICompatibleEmbedder:
    stub = client if client is not None else MagicMock()
    return OpenAICompatibleEmbedder(
        client=stub,
        model=model,
        dimensions=dimensions,
    )


def assert_no_chunking_params(cls: type) -> None:
    items: list[Any] = [cls.__init__]
    for name, member in inspect.getmembers(cls):
        if name.startswith("_"):
            continue
        if inspect.isfunction(member) or inspect.ismethod(member):
            items.append(member)
    for fn in items:
        try:
            params = inspect.signature(fn).parameters
        except (TypeError, ValueError):
            continue
        overlap = CHUNKING_PARAM_NAMES.intersection(params)
        assert not overlap, f"{cls.__name__}.{fn.__name__} expõe {overlap}"
