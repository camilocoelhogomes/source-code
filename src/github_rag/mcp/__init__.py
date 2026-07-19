"""Fronteira MCP de evidências (T17).

Responsabilidade
    Expor a porta pública ``McpEvidenceServer``, a implementação
    ``DefaultMcpEvidenceServer``, ``DEFAULT_SERVER_NAME`` e ``McpToolError``
    para composition root, BDD e handoff T19 (processo stdio).

Motivo da separação
    Superfície Cursor/MCP isolada do domínio de consulta (ENG-007 / DEC-008);
    usa apenas o SDK oficial ``mcp`` (``FastMCP``); sem narrativa/SLM (BR-011).

API pública
    - ``McpEvidenceServer`` — Protocol (``build`` / ``run``)
    - ``DefaultMcpEvidenceServer`` — composition catalog + QueryService + limiter
    - ``DEFAULT_SERVER_NAME`` — nome FastMCP default (``github-rag-evidence``)
    - ``McpToolError`` — falha tipada da superfície (BDD-014)

Tools registradas (REQ-028): ``list_repos``, ``search_code``,
``semantic_search``, ``read_file``, ``list_tree``.
"""

from github_rag.mcp.errors import McpToolError
from github_rag.mcp.ports import McpEvidenceServer
from github_rag.mcp.server import DEFAULT_SERVER_NAME, DefaultMcpEvidenceServer

__all__ = [
    "DEFAULT_SERVER_NAME",
    "DefaultMcpEvidenceServer",
    "McpEvidenceServer",
    "McpToolError",
]
