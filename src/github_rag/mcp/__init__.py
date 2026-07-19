"""Fronteira MCP de evidências (T17).

Responsabilidade
    Expor ``McpEvidenceServer``, ``DefaultMcpEvidenceServer`` e ``McpToolError``
    para T19, BDD e composition root.

Motivo da separação
    Superfície Cursor/MCP isolada do domínio de consulta (ENG-007 / DEC-008);
    sem narrativa/SLM (BR-011).
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
