"""DTOs de pedido/resposta da fachada QueryService (T16).

Responsabilidade deste módulo
    Declarar DetailFields, requests, QueryHit/QueryHits, FileContent e
    TreeListing como contratos frozen para T17/T18.

Motivo da separação
    Isola a forma de evidência projetada (BDD-012) dos DTOs crus de
    ExactMatch/SemanticHit (I-T16-004).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class DetailFields:
    """Flags de projeção dos quatro campos opcionais (BDD-012 / REQ-030).

    Responsabilidade
        Declarar quais campos o caller deseja na resposta.

    Motivo da separação
        Isola a política “só sob demanda” da forma crua dos hits de índice.
    """

    repository: bool = False
    path: bool = False
    commit: bool = False
    snippet: bool = False


@dataclass(frozen=True)
class ExactSearchRequest:
    """Pedido de busca exata (BDD-009).

    Responsabilidade
        Descrever intenção de busca literal sem expor ExactSearchQuery Zoekt.

    Motivo da separação
        Superfícies falam DTO de produto; só DefaultQueryService monta T10.
    """

    pattern: str
    details: DetailFields = field(default_factory=DetailFields)
    repo_key: str | None = None
    repository_id: int | None = None
    path_prefix: str | None = None
    max_matches: int | None = None
    context_lines: int = 2


@dataclass(frozen=True)
class SemanticSearchRequest:
    """Pedido de busca semântica (BDD-010) + gancho de reformulação.

    Responsabilidade
        Descrever query semântica e flag opcional reformulate (REQ-027).

    Motivo da separação
        Mantém Embedder+VectorStore atrás da fachada; reformulate ≠ evidência.
    """

    query: str
    details: DetailFields = field(default_factory=DetailFields)
    repo_key: str | None = None
    repository_id: int | None = None
    limit: int = 10
    reformulate: bool = False


@dataclass(frozen=True)
class ReadFileRequest:
    """Pedido de leitura de arquivo no commit indexado (T08).

    Responsabilidade
        Pedir bytes de um path no commit resolvido.

    Motivo da separação
        Browse compartilhado sem acoplar superfícies a SnapshotSource.
    """

    path: str
    repo_key: str | None = None
    repository_id: int | None = None
    commit_sha: str | None = None
    details: DetailFields = field(default_factory=DetailFields)


@dataclass(frozen=True)
class ListTreeRequest:
    """Pedido de listagem de árvore com filtro opcional de prefixo.

    Responsabilidade
        Listar paths do snapshot no commit resolvido.

    Motivo da separação
        Mesma fachada de browse que read_file; filtro na camada serviço.
    """

    repo_key: str | None = None
    repository_id: int | None = None
    commit_sha: str | None = None
    path_prefix: str | None = None
    details: DetailFields = field(default_factory=DetailFields)


@dataclass(frozen=True)
class QueryHit:
    """Evidência mínima + campos opcionais sob demanda.

    Responsabilidade
        Forma estável de evidência para T17/T18 após projeção.

    Motivo da separação
        Callers não recebem ExactMatch/SemanticHit crus (I-T16-004).
    """

    kind: Literal["exact", "semantic"]
    score: float | None
    repository: str | None = None
    path: str | None = None
    commit: str | None = None
    snippet: str | None = None
    chunk_metadata_summary: str | None = None
    line_number: int | None = None


@dataclass(frozen=True)
class QueryHits:
    """Coleção imutável de QueryHit."""

    hits: tuple[QueryHit, ...]


@dataclass(frozen=True)
class FileContent:
    """Resultado de read_file com metadados opcionais projetados."""

    content: bytes
    repository: str | None = None
    path: str | None = None
    commit: str | None = None


@dataclass(frozen=True)
class TreeListing:
    """Resultado de list_tree com metadados opcionais projetados."""

    paths: tuple[str, ...]
    repository: str | None = None
    commit: str | None = None
