"""Doubles opcionais da superfície MCP (T17).

Responsabilidade deste módulo
    Oferecer um double de ``McpEvidenceServer`` para unitários sem SDK quando
    útil.

Motivo da separação
    BDD principal usa ``DefaultMcpEvidenceServer`` + FastMCP real (MCP-07);
    fake é apoio, não substitui o gate SDK (I-T17 interfaces §3.6).
"""

from __future__ import annotations

from typing import Any, Literal


class FakeMcpEvidenceServer:
    """Double opcional de ``McpEvidenceServer``.

    Responsabilidade
        Permitir testes de composition sem FastMCP real quando o cenário não
        exige conformidade SDK.

    Motivo da separação
        Evita acoplar todo unitário ao runtime ``mcp``; o gate BDD-024 permanece
        em ``DefaultMcpEvidenceServer.build``.
    """

    def build(self) -> Any:
        """Stub: Developer/QA podem especializar nos testes."""
        raise NotImplementedError("T17: FakeMcpEvidenceServer.build pending")

    def run(self, *, transport: Literal["stdio"] = "stdio") -> None:
        """Stub: sem processo real."""
        raise NotImplementedError("T17: FakeMcpEvidenceServer.run pending")
