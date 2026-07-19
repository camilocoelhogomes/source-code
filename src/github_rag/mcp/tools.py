"""Registro das tools MCP aprovadas (T17).

Responsabilidade deste módulo
    Binding único nome MCP → handler para as 5 operações REQ-028.

Motivo da separação
    Isola decorators/SDK ``FastMCP`` do lifecycle ``build``/``run`` e da
    serialização (I-T17-003 / D-T17-003).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from github_rag.catalog.repository import CatalogRepository
from github_rag.concurrency.limiter import WorkerLimiter
from github_rag.query.ports import QueryService

APPROVED_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "list_repos",
        "search_code",
        "semantic_search",
        "read_file",
        "list_tree",
    }
)
"""Conjunto fechado de tools (I-T17-003).

Responsabilidade: literal de conformidade REQ-028 / MCP-08.
Motivo da separação: evita espalhar a lista nos testes e no server.
"""


def register_tools(
    app: FastMCP,
    *,
    catalog: CatalogRepository,
    query: QueryService,
    query_limiter: WorkerLimiter,
) -> None:
    """Registra as 5 tools aprovadas no ``FastMCP``.

    Responsabilidade
        Único ponto de binding nome MCP → handler (REQ-028). Cada handler
        (implementação) deve adquirir ``query_limiter`` antes da delegação
        (I-T17-006), mapear ``include_*`` → ``DetailFields`` (I-T17-005) e
        nunca passar ``reformulate=True`` em semantic (I-T17-009).

    Motivo da separação
        Isola decorators/SDK do lifecycle ``build``/``run`` e da serialização.

    Stub
        Comportamento completo fica com o Developer (I-T17-015).
    """
    raise NotImplementedError("T17: register_tools pending implementation")
