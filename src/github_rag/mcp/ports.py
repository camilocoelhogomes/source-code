"""Porta pública do servidor MCP de evidências (T17).

Responsabilidade deste módulo
    Declarar o Protocol ``McpEvidenceServer`` (``build`` / ``run``).

Motivo da separação
    Isola o contrato estável consumido por T19/Cursor da implementação
    FastMCP e dos handlers de tools (ENG-007 / I-T17-002).
"""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from mcp.server.fastmcp import FastMCP


@runtime_checkable
class McpEvidenceServer(Protocol):
    """Porta pública da superfície MCP de evidências.

    Responsabilidade
        Expor ``build`` (app FastMCP com as 5 tools) e ``run`` (processo stdio).

    Motivo da separação
        ENG-007 — host/Cursor não acoplam a Zoekt/Qdrant/Git/ORM; T19 só chama
        ``run()``. Mantém DEC-008 (só evidências) na fronteira de processo.
    """

    def build(self) -> FastMCP:
        """Monta FastMCP com as 5 tools registradas.

        Responsabilidade
            Produzir o app MCP pronto para list/call pelo host.

        Motivo da separação
            Isola lifecycle SDK do composition root e do domínio query/catalog.
        """
        ...

    def run(self, *, transport: Literal["stdio"] = "stdio") -> None:
        """Executa o servidor MCP (stdio no MVP).

        Responsabilidade
            Expor o processo consumido por Cursor/T19.

        Motivo da separação
            Handoff de delivery sem acoplar compose à lógica das tools.
        """
        ...
