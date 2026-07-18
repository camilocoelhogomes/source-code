"""Fake determinístico de ``MetadataGenerator`` para testes (T12).

Responsabilidade deste módulo
    Sucesso per-chunk e falha tipada no meio da lista sem runtime SLM.

Motivo da separação
    Satisfaz aceite da task e permite T14 testar o loop N× independentemente
    do adaptador OpenAI.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import AbstractSet

from github_rag.index.chunk.types import SemanticChunk
from github_rag.index.metadata.errors import (
    MetadataGenerationError,
    MetadataModelError,
)
from github_rag.index.metadata.types import ChunkMetadata


class FakeMetadataGenerator:
    """Implementação determinística da porta para testes / aceite.

    Responsabilidade
        Mapear ``chunk_id`` → metadata ou levantar erro tipado configurável.

    Motivo da separação
        Evita dependência de runtime SLM nos testes de T12/T14.
    """

    def __init__(
        self,
        *,
        by_chunk_id: Mapping[str, ChunkMetadata] | None = None,
        fail_chunk_ids: AbstractSet[str] | None = None,
        fail_error: type[MetadataGenerationError] = MetadataModelError,
        default_summary_prefix: str = "summary:",
    ) -> None:
        self._by_chunk_id = dict(by_chunk_id or {})
        self._fail_chunk_ids = set(fail_chunk_ids or ())
        self._fail_error = fail_error
        self._default_summary_prefix = default_summary_prefix

    def generate(self, chunk: SemanticChunk) -> ChunkMetadata:
        if chunk.chunk_id in self._fail_chunk_ids:
            raise self._fail_error(
                "falha simulada na geração de metadados",
                chunk_id=chunk.chunk_id,
                path=chunk.path,
            )
        if chunk.chunk_id in self._by_chunk_id:
            return self._by_chunk_id[chunk.chunk_id]
        return ChunkMetadata(
            chunk_id=chunk.chunk_id,
            summary=f"{self._default_summary_prefix}{chunk.chunk_id}",
            symbols=(),
            keywords=(),
            intent="",
            extra=(),
        )
