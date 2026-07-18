"""Porta de domínio do chunking contextual (T11).

Responsabilidade deste módulo
    Declarar o Protocol ``ContextualChunker`` — única porta de produção de
    chunks RAG a partir de um arquivo-fonte.

Motivo da separação
    Isola Tree-sitter/grammars dos consumidores (T12/T13/T14) e impede
    chunking genérico por tamanho/linhas fora do adaptador (DEC-003).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from github_rag.index.chunk.types import ChunkSourceFile, SemanticChunk


@runtime_checkable
class ContextualChunker(Protocol):
    def chunk(self, source: ChunkSourceFile) -> tuple[SemanticChunk, ...]:
        """Produz chunks semânticos Tree-sitter para um arquivo.

        Responsabilidade
            Única porta de produção de chunks RAG a partir de um arquivo-fonte.

        Motivo da separação
            Isola Tree-sitter/grammars dos consumidores (T12/T13/T14) e impede
            chunking genérico por tamanho/linhas fora do adaptador.
        """
        ...
