"""Implementação default de ``McpEvidenceServer`` (T17).

Responsabilidade deste módulo
    Compor ``CatalogRepository`` + ``QueryService`` + ``WorkerLimiter`` e
    materializar ``FastMCP`` / processo stdio.

Motivo da separação
    Materializa I-T17-002/014 sem espalhar registro SDK pelo domínio
    query/catalog (ENG-007).
"""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from github_rag.catalog.repository import CatalogRepository
from github_rag.concurrency.limiter import WorkerLimiter
from github_rag.mcp.errors import McpToolError
from github_rag.mcp.tools import register_tools
from github_rag.query.ports import QueryService

DEFAULT_SERVER_NAME = "github-rag-evidence"
"""Nome default do servidor FastMCP (I-T17-014).

Responsabilidade: literal estável para host MCP / T19.
Motivo da separação: evita string mágica no construtor.
"""


class _EvidenceFastMCP(FastMCP):
    """FastMCP que repropaga ``McpToolError`` tipado ao host de testes/call_tool.

    O SDK envolve qualquer Exception em ``ToolError``. Para preservar o contrato
    I-T17-012 (``McpToolError`` tipado na superfície), desembrulhamos a causa.
    """

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> Any:
        try:
            return await super().call_tool(name, arguments)
        except ToolError as exc:
            cause = exc.__cause__
            if isinstance(cause, McpToolError):
                raise cause from None
            raise


class DefaultMcpEvidenceServer:
    """Composition default do servidor MCP de evidências.

    Responsabilidade
        Guardar deps injetáveis, registrar as 5 tools no ``FastMCP`` e expor
        ``run(transport=\"stdio\")``.

    Motivo da separação
        Porta concreta testável (BDD) sem acoplar Cursor ao composition root
        de índices; sem reformulador SLM na composição (I-T17-009).
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
        """
        app = _EvidenceFastMCP(self._server_name)
        register_tools(
            app,
            catalog=self._catalog,
            query=self._query,
            query_limiter=self._query_limiter,
        )
        return app

    def run(self, *, transport: Literal["stdio"] = "stdio") -> None:
        """Executa o servidor MCP (stdio no MVP — I-T17-011).

        Responsabilidade
            Processo consumido por Cursor/T19.

        Motivo da separação
            Handoff de delivery sem acoplar compose às tools.
        """
        self.build().run(transport=transport)
