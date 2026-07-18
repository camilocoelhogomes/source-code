"""Modelos imutáveis de entrada/saída da porta ExactCodeIndex (T10).

Responsabilidade deste módulo
    Declarar ``FileToIndex``, ``ExactMatch`` e ``ExactSearchQuery`` como DTOs
    frozen do domínio de busca exata.

Motivo da separação
    T14/T16 acoplam apenas a modelos estáveis; não conhecem argv CLI, JSON
    Zoekt nem paths de shard (D-T10-003).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileToIndex:
    """Arquivo integral elegível a indexar no tip.

    Responsabilidade
        Carregar o conteúdo integral de um arquivo elegível no tip a ser
        indexado (ENG-012: arquivo inteiro).

    Motivo da separação
        DTO de entrada estável para a porta; T14 não acopla a argv CLI, temp
        dirs nem formato de shard Zoekt.
    """

    repository: str
    path: str
    commit: str
    content: bytes


@dataclass(frozen=True)
class ExactMatch:
    """Hit de busca exata com metadados mínimos (BDD-009).

    Responsabilidade
        Evidência de match exato com metadados para T16/UI/MCP.

    Motivo da separação
        Saída de domínio independente do JSON Zoekt (``FileMatches``/fragments).
    """

    repository: str
    path: str
    commit: str
    snippet: str
    line_number: int | None = None


@dataclass(frozen=True)
class ExactSearchQuery:
    """Intenção de busca literal + filtros opcionais.

    Responsabilidade
        Descrever busca literal + filtros sem expor a query language Zoekt
        aos callers.

    Motivo da separação
        T16 monta intenção de produto; só o adaptador conhece ``Q`` / ``Opts``.
    """

    pattern: str
    repository: str | None = None
    path_prefix: str | None = None
    max_matches: int | None = None
    context_lines: int = 2
