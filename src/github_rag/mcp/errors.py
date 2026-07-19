"""Erros tipados da superfície MCP (T17).

Responsabilidade deste módulo
    Declarar ``McpToolError`` e o mapeamento ``QueryError`` → mensagem segura.

Motivo da separação
    Distingue falhas de tool de ``QueryError`` crus; centraliza BDD-014 / BR-008
    (sem eco de token em ``str``/``repr``) — I-T17-012.
"""

from __future__ import annotations

from github_rag.query.errors import QueryError


class McpToolError(Exception):
    """Falha tipada exposta pela superfície MCP.

    Responsabilidade
        Sinalizar falha de tool com ``kind`` lógico e mensagem estável sem
        segredos.

    Motivo da separação
        Handlers e o host MCP mapeiam um tipo estável sem ``except Exception``
        nem ``str(query_error)`` bruto (BDD-014 / MCP-05/12).
    """

    def __init__(self, message: str = "", *, kind: str = "error") -> None:
        self.message = message
        self.kind = kind
        super().__init__(message)


def map_query_error(exc: QueryError) -> McpToolError:
    """Mapeia ``QueryError`` → ``McpToolError`` sem vazar segredos.

    Responsabilidade
        Traduzir família T16 em ``kind``/``message`` seguros para o host MCP.

    Motivo da separação
        Centraliza política BDD-014; handlers não montam ``str(exc)`` bruto.

    Stub
        Comportamento completo fica com o Developer (I-T17-015).
    """
    raise NotImplementedError("T17: map_query_error pending implementation")
