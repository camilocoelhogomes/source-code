"""Implementação default de ``McpEvidenceServer`` (T17).

Responsabilidade deste módulo
    Compor ``CatalogRepository`` + ``QueryService`` + ``WorkerLimiter`` e
    materializar ``FastMCP`` / processo stdio.

Motivo da separação
    Materializa I-T17-002/014 sem espalhar registro SDK pelo domínio
    query/catalog (ENG-007).
"""

from __future__ import annotations

from typing import Literal

from mcp.server.fastmcp import FastMCP

from github_rag.catalog.repository import CatalogRepository
from github_rag.concurrency.limiter import WorkerLimiter
from github_rag.query.ports import QueryService

DEFAULT_SERVER_NAME = "github-rag-evidence"
"""Nome default do servidor FastMCP (I-T17-014).

Responsabilidade: literal estável para host MCP / T19.
Motivo da separação: evita string mágica no construtor.
"""


class DefaultMcpEvidenceServer:
    """Composition default do servidor MCP de evidências.

    Responsabilidade
        Guardar deps injetáveis e, na implementação completa, registrar as 5
        tools no ``FastMCP`` e expor ``run(transport=\"stdio\")``.

    Motivo da separação
        Porta concreta testável (BDD) sem acoplar Cursor ao composition root
        de índices; sem ``QueryReformulator`` / ``MetadataGenerator`` (I-T17-009).
    """

    def __init__(
        self,
        *,
        catalog: CatalogRepository,
        query: QueryService,
        query_limiter: WorkerLimiter,
        server_name: str = DEFAULT_SERVER_NAME,
    ) -> None:
        self._catalog = catalog
        self._query = query
        self._query_limiter = query_limiter
        self._server_name = server_name

    def build(self) -> FastMCP:
        """Monta ``FastMCP`` com as 5 tools (I-T17-001/003).

        Responsabilidade
            Produzir o app MCP para list/call.

        Motivo da separação
            Isola lifecycle SDK da execução ``run``.

        Stub
            Developer implementa registro + acquire (I-T17-015).
        """
        raise NotImplementedError("T17: DefaultMcpEvidenceServer.build pending")

    def run(self, *, transport: Literal["stdio"] = "stdio") -> None:
        """Executa o servidor MCP (stdio no MVP — I-T17-011).

        Responsabilidade
            Processo consumido por Cursor/T19.

        Motivo da separação
            Handoff de delivery sem acoplar compose às tools.

        Stub
            Developer implementa (I-T17-015).
        """
        raise NotImplementedError("T17: DefaultMcpEvidenceServer.run pending")
