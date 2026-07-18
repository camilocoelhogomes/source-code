"""Seletores estruturais de nós Tree-sitter (T11).

Responsabilidade deste módulo
    Escolher nós semânticos (e root fallback) por linguagem, com dedupe de
    range idêntico e ordenação determinística.

Motivo da separação
    Política de chunking estrutural testável sem I/O de grammar (I-T11-006).
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any

from github_rag.index.chunk.types import SourceLanguage

# Prioridade de kind no dedupe de range idêntico (maior vence).
# export_statement (wrapper) tem prioridade baixa; declarações internas ganham.
_KIND_PRIORITY: dict[str, int] = {
    "export_statement": 10,
    "decorated_definition": 40,
    "function_definition": 50,
    "class_definition": 50,
    "function_declaration": 50,
    "class_declaration": 50,
    "method_definition": 50,
    "method_declaration": 50,
    "constructor_declaration": 50,
    "interface_declaration": 50,
    "section": 50,
    "atx_heading": 50,
    "setext_heading": 50,
    "document": 40,
    "block_mapping_pair": 50,
    "object": 45,
    "array": 45,
    "pair": 50,
    "element": 50,
    "table": 50,
}

_TARGETS: dict[SourceLanguage, frozenset[str]] = {
    SourceLanguage.PYTHON: frozenset(
        {
            "function_definition",
            "class_definition",
            "decorated_definition",
        }
    ),
    SourceLanguage.JAVA: frozenset(
        {
            "class_declaration",
            "interface_declaration",
            "method_declaration",
            "constructor_declaration",
        }
    ),
    SourceLanguage.JAVASCRIPT: frozenset(
        {
            "function_declaration",
            "class_declaration",
            "method_definition",
            "export_statement",
        }
    ),
    SourceLanguage.TYPESCRIPT: frozenset(
        {
            "function_declaration",
            "class_declaration",
            "method_definition",
            "export_statement",
        }
    ),
    SourceLanguage.MARKDOWN: frozenset(
        {
            "section",
            "atx_heading",
            "setext_heading",
        }
    ),
    SourceLanguage.YAML: frozenset(
        {
            "document",
            "block_mapping_pair",
        }
    ),
    SourceLanguage.JSON: frozenset(
        {
            "object",
            "pair",
            "array",
        }
    ),
    SourceLanguage.XML: frozenset(
        {
            "element",
        }
    ),
    SourceLanguage.TOML: frozenset(
        {
            "table",
            "pair",
        }
    ),
}


@dataclass(frozen=True)
class SelectedNode:
    """Nó estrutural escolhido antes da materialização em ``SemanticChunk``.

    Responsabilidade
        Representar kind + ranges sem ``text``/``chunk_id``/``path``.

    Motivo da separação
        Permite testar seleção/dedupe/ordem sem decodificar bytes nem hash.
    """

    kind: str
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]
    end_point: tuple[int, int]


def _iter_nodes(node: Any) -> Iterator[Any]:
    """DFS via ``children`` (FakeNode e Node tree-sitter moderno)."""
    yield node
    for child in node.children:
        yield from _iter_nodes(child)


def _as_point(point: Any) -> tuple[int, int]:
    # tree_sitter.Point é Sequence-like (isinstance tuple == True) e tem row/col.
    return (int(point[0]), int(point[1]))


def _to_selected(node: Any) -> SelectedNode:
    return SelectedNode(
        kind=str(node.type),
        start_byte=int(node.start_byte),
        end_byte=int(node.end_byte),
        start_point=_as_point(node.start_point),
        end_point=_as_point(node.end_point),
    )


def _priority(kind: str) -> int:
    return _KIND_PRIORITY.get(kind, 30)


def select_semantic_nodes(
    language: SourceLanguage,
    root_node: Any,
) -> Sequence[SelectedNode]:
    """Escolher nós estruturais (e root fallback) conforme design §4.4."""
    targets = _TARGETS[language]
    by_range: dict[tuple[int, int], SelectedNode] = {}

    for node in _iter_nodes(root_node):
        kind = str(node.type)
        if kind not in targets:
            continue
        selected = _to_selected(node)
        key = (selected.start_byte, selected.end_byte)
        existing = by_range.get(key)
        if existing is None or _priority(selected.kind) > _priority(existing.kind):
            by_range[key] = selected

    if not by_range:
        return (_to_selected(root_node),)

    ordered = sorted(
        by_range.values(),
        key=lambda n: (n.start_byte, n.end_byte, n.kind),
    )
    return tuple(ordered)
