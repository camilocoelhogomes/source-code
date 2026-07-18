"""Porta de domínio para geração de metadados SLM (T12).

Responsabilidade deste módulo
    Declarar o Protocol ``MetadataGenerator`` (BR-009).

Motivo da separação
    Isola provedor/modelo do orquestrador (T14) e do VectorStore (T13);
    impede uso da SLM para inventar chunks ou prosa MCP (BR-010).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from github_rag.index.chunk.types import SemanticChunk
from github_rag.index.metadata.types import ChunkMetadata


@runtime_checkable
class MetadataGenerator(Protocol):
    def generate(self, chunk: SemanticChunk) -> ChunkMetadata:
        """Gera metadados contextuais SLM para um chunk Tree-sitter.

        Responsabilidade
            Única porta de geração de metadados de indexação a partir de
            um SemanticChunk.

        Motivo da separação
            Isola provedor/modelo (BR-009) do orquestrador (T14) e do
            VectorStore (T13); impede uso da SLM para inventar chunks
            ou prosa/tools MCP (BR-010).
        """
        ...
