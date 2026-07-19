"""Tipos e helpers de adaptação do orquestrador (T14).

Responsabilidade deste módulo
    Mapear ``ChunkMetadata`` T12 → contrato mínimo T13.

Motivo da separação
    Os dois tipos coexistentes na main não devem ser misturados ad hoc
    no meio do orquestrador (D-T14-009).
"""

from __future__ import annotations

from github_rag.index.metadata.types import ChunkMetadata as SlmChunkMetadata
from github_rag.index.vector.types import ChunkMetadata as VectorChunkMetadata


def to_vector_metadata(meta: SlmChunkMetadata) -> VectorChunkMetadata:
    """Extrai summary/keywords/symbols de T12 para o contrato T13.

    Responsabilidade: adaptar metadados SLM ao payload vetorial.
    Motivo da separação: D-T14-009 — único ponto de mapeamento.
    """
    return VectorChunkMetadata(
        summary=meta.summary,
        keywords=meta.keywords,
        symbols=meta.symbols,
    )
