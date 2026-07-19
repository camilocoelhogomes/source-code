"""Portas de domínio da fachada de consulta (T16).

Responsabilidade deste módulo
    Declarar Protocols ``QueryService``, ``QueryReformulator`` e
    ``SnapshotSourceResolver``.

Motivo da separação
    UI/MCP não acoplam a Zoekt/Qdrant/Git; reformulador e resolver ficam
    injetáveis e testáveis sem backends reais (I-T16-002/006/010).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from github_rag.catalog.models import CatalogEntry
from github_rag.query.types import (
    ExactSearchRequest,
    FileContent,
    ListTreeRequest,
    QueryHits,
    ReadFileRequest,
    SemanticSearchRequest,
    TreeListing,
)
from github_rag.snapshot.models import SnapshotSource


@runtime_checkable
class QueryService(Protocol):
    """Fachada única de consulta compartilhada (exact, semantic, read, tree).

    Responsabilidade
        Expor BDD-009/010 e browse via portas T10/T13/T08 com projeção BDD-012.

    Motivo da separação
        ENG-007 / BR-023 — UI e MCP não tocam índices nem Git diretamente.
    """

    def search_exact(self, request: ExactSearchRequest) -> QueryHits:
        """Busca exata via ExactCodeIndex; retorna hits projetados."""
        ...

    def search_semantic(self, request: SemanticSearchRequest) -> QueryHits:
        """Busca semântica via Embedder+VectorStore; hits = evidências."""
        ...

    def read_file(self, request: ReadFileRequest) -> FileContent:
        """Lê bytes do snapshot no commit resolvido."""
        ...

    def list_tree(self, request: ListTreeRequest) -> TreeListing:
        """Lista paths do snapshot; aplica path_prefix se pedido."""
        ...


@runtime_checkable
class QueryReformulator(Protocol):
    """Porta opcional: reformula só o texto da query (REQ-027 / BR-011).

    Responsabilidade
        Transformar a string de consulta antes do embedding (UI).

    Motivo da separação
        Não mistura com MetadataGenerator nem gera evidência/prosa.
    """

    def reformulate(self, query: str) -> str:
        """Devolve somente string de query reformulada."""
        ...


@runtime_checkable
class SnapshotSourceResolver(Protocol):
    """CatalogEntry → SnapshotSource (composition root injeta token).

    Responsabilidade
        Mapear origem local/GitHub do catálogo para o DTO T08.

    Motivo da separação
        T16 não importa PyGithub/GitPython; token fica fora da orquestração.
    """

    def resolve(self, entry: CatalogEntry) -> SnapshotSource:
        """Monta SnapshotSource a partir do CatalogEntry."""
        ...
