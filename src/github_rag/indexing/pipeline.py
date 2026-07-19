"""Pipeline RAG por arquivo (T14) — porta interna + adaptador.

Responsabilidade deste módulo
    Declarar ``FileRagPipeline`` e ``DefaultFileRagPipeline``:
    Tree-sitter → SLM por chunk → embed → ``VectorRecord``.

Motivo da separação
    Isola a sequência RAG da fila, estados e Zoekt conjunto tip (I-T14-007).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from github_rag.index.chunk.ports import ContextualChunker
from github_rag.index.chunk.types import ChunkSourceFile
from github_rag.index.metadata.ports import MetadataGenerator
from github_rag.index.vector.ports import Embedder
from github_rag.index.vector.types import EnrichedChunk, VectorRecord
from github_rag.indexing.errors import IndexingPipelineError
from github_rag.indexing.types import to_vector_metadata


@runtime_checkable
class FileRagPipeline(Protocol):
    def process_file(
        self,
        *,
        path: str,
        content: bytes,
    ) -> tuple[VectorRecord, ...]:
        """Tree-sitter → SLM por chunk → embed → ``VectorRecord[]``."""
        ...


class DefaultFileRagPipeline:
    """Implementação de ``FileRagPipeline`` só via portas (ENG-013)."""

    def __init__(
        self,
        *,
        chunker: ContextualChunker,
        metadata_generator: MetadataGenerator,
        embedder: Embedder,
    ) -> None:
        self._chunker = chunker
        self._metadata = metadata_generator
        self._embedder = embedder

    def process_file(
        self,
        *,
        path: str,
        content: bytes,
    ) -> tuple[VectorRecord, ...]:
        try:
            chunks = self._chunker.chunk(
                ChunkSourceFile(path=path, content=content)
            )
            if not chunks:
                return ()
            enriched: list[EnrichedChunk] = []
            for chunk in chunks:
                slm_meta = self._metadata.generate(chunk)
                enriched.append(
                    EnrichedChunk(
                        chunk=chunk,
                        metadata=to_vector_metadata(slm_meta),
                    )
                )
            vectors = self._embedder.embed(tuple(e.chunk.text for e in enriched))
            if len(vectors) != len(enriched):
                raise IndexingPipelineError(
                    "embedder retornou quantidade distinta de vetores"
                )
            return tuple(
                VectorRecord(enriched=e, vector=v)
                for e, v in zip(enriched, vectors, strict=True)
            )
        except IndexingPipelineError:
            raise
        except Exception as exc:  # noqa: BLE001 — boundary tipado
            raise IndexingPipelineError(str(exc)) from exc
