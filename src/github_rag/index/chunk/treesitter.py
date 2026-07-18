"""Implementação default ``ContextualChunker`` via Tree-sitter (T11).

Responsabilidade deste módulo
    Validar fonte, resolver grammar, parsear, selecionar nós e materializar
    ``SemanticChunk`` com ``chunk_id`` canônico.

Motivo da separação
    Adaptador SDK (DEC-015) atrás da porta; único caminho de produção default.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from tree_sitter import Parser

from github_rag.index.chunk.errors import (
    BinarySourceError,
    EmptySourceError,
    GrammarUnavailableError,
    ParseFailureError,
)
from github_rag.index.chunk.grammar_registry import (
    GrammarRegistry,
    OfficialGrammarRegistry,
)
from github_rag.index.chunk.node_selectors import SelectedNode, select_semantic_nodes
from github_rag.index.chunk.types import (
    ChunkSourceFile,
    SemanticChunk,
    SourceLanguage,
    compute_chunk_id,
    language_from_path,
)


def _path_extension(path: str) -> str:
    return Path(path).suffix.lower()


class TreeSitterContextualChunker:
    """Chunker contextual baseado em Tree-sitter + grammars oficiais.

    Responsabilidade
        Implementar ``ContextualChunker`` via parse oficial + seletores.

    Motivo da separação
        Isola o SDK dos consumidores; registry injetável para testes.
    """

    def __init__(self, grammar_registry: GrammarRegistry | None = None) -> None:
        self._registry: GrammarRegistry = (
            grammar_registry
            if grammar_registry is not None
            else OfficialGrammarRegistry()
        )

    def chunk(self, source: ChunkSourceFile) -> tuple[SemanticChunk, ...]:
        # 1. empty
        if len(source.content) == 0:
            raise EmptySourceError("arquivo vazio", path=source.path)

        # 2. binary (NUL / UTF-8)
        if b"\x00" in source.content:
            raise BinarySourceError("conteúdo binário (NUL)", path=source.path)
        try:
            source.content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BinarySourceError(
                "conteúdo não é UTF-8 válido",
                path=source.path,
            ) from exc

        # 3. language resolve
        language = source.language
        if language is None:
            language = language_from_path(source.path)
        if language is None:
            raise GrammarUnavailableError(
                "extensão/linguagem sem grammar MVP",
                path=source.path,
            )

        path_extension = _path_extension(source.path)

        # 4. registry
        ts_language = self._registry.resolve(
            language,
            path_extension=path_extension,
        )

        # 5. parse
        root_node = self._parse(ts_language, source.content, source.path, language)

        # 6. select
        selected = select_semantic_nodes(language, root_node)

        # 7. materialize
        chunks = self._materialize(source, language, selected)
        if not chunks:
            raise ParseFailureError(
                "impossível materializar chunk com texto não vazio",
                path=source.path,
                language=language,
            )

        chunks.sort(key=lambda c: (c.start_byte, c.end_byte, c.kind))
        return tuple(chunks)

    def _materialize(
        self,
        source: ChunkSourceFile,
        language: SourceLanguage,
        selected: Sequence[SelectedNode],
    ) -> list[SemanticChunk]:
        content = source.content
        chunks: list[SemanticChunk] = []
        for node in selected:
            start = int(node.start_byte)
            end = int(node.end_byte)
            start_point = node.start_point
            end_point = node.end_point
            # Tree-sitter pode reportar root com range vazio em arquivo só
            # whitespace; UT-X02 exige sucesso com texto não vazio.
            if end <= start and len(content) > 0:
                start, end = 0, len(content)
                start_point, end_point = (0, 0), (0, 0)
            if end <= start or end > len(content):
                continue
            slice_text = content[start:end].decode("utf-8")
            if not slice_text:
                continue
            kind = node.kind
            chunks.append(
                SemanticChunk(
                    chunk_id=compute_chunk_id(
                        path=source.path,
                        start_byte=start,
                        end_byte=end,
                        language=language,
                        kind=kind,
                    ),
                    path=source.path,
                    language=language,
                    kind=kind,
                    text=slice_text,
                    start_byte=start,
                    end_byte=end,
                    start_point=start_point,
                    end_point=end_point,
                )
            )
        return chunks

    def _parse(
        self,
        ts_language: Any,
        content: bytes,
        path: str,
        language: SourceLanguage,
    ) -> Any:
        try:
            parser = Parser(ts_language)
            tree = parser.parse(content)
            return tree.root_node
        except Exception as exc:
            raise ParseFailureError(
                f"falha de parse: {exc}",
                path=path,
                language=language,
            ) from exc
