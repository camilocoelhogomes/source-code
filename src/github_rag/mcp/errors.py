"""Erros tipados da superfície MCP (T17).

Responsabilidade deste módulo
    Declarar ``McpToolError`` e o mapeamento ``QueryError`` → mensagem segura.

Motivo da separação
    Distingue falhas de tool de ``QueryError`` crus; centraliza BDD-014 / BR-008
    (sem eco de token em ``str``/``repr``) — I-T17-012.
"""

from __future__ import annotations

import re

from github_rag.query.errors import (
    QueryCommitUnavailableError,
    QueryEmbeddingError,
    QueryError,
    QueryExactIndexError,
    QueryRepositoryNotFoundError,
    QuerySnapshotError,
    QueryValidationError,
    QueryVectorError,
)

# Padrões de segredo a remover de mensagens (BDD-014 / BR-008).
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ghp_[A-Za-z0-9_]+"),
    re.compile(r"(?i)token[=:\s]+\S+"),
    re.compile(r"(?i)bearer\s+\S+"),
)

_KIND_BY_TYPE: tuple[tuple[type[QueryError], str], ...] = (
    (QueryValidationError, "validation"),
    (QueryRepositoryNotFoundError, "repository_not_found"),
    (QueryCommitUnavailableError, "commit_unavailable"),
    (QueryExactIndexError, "exact_index"),
    (QueryVectorError, "vector"),
    (QueryEmbeddingError, "embedding"),
    (QuerySnapshotError, "snapshot"),
)

_SAFE_MESSAGES: dict[str, str] = {
    "validation": "validation error",
    "repository_not_found": "repository not found",
    "commit_unavailable": "commit unavailable",
    "exact_index": "exact index error",
    "vector": "vector store error",
    "embedding": "embedding error",
    "snapshot": "snapshot error",
    "query": "query error",
}


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


def redact_secrets(text: str) -> str:
    """Remove padrões de token/segredo de uma string.

    Responsabilidade
        Garantir que mensagens/logs da superfície não ecoem credenciais.

    Motivo da separação
        Centraliza redaction BDD-014 fora dos handlers.
    """
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def map_query_error(exc: QueryError) -> McpToolError:
    """Mapeia ``QueryError`` → ``McpToolError`` sem vazar segredos.

    Responsabilidade
        Traduzir família T16 em ``kind``/``message`` seguros para o host MCP.

    Motivo da separação
        Centraliza política BDD-014; handlers não montam ``str(exc)`` bruto.
    """
    kind = "query"
    for exc_type, mapped_kind in _KIND_BY_TYPE:
        if isinstance(exc, exc_type):
            kind = mapped_kind
            break
    message = _SAFE_MESSAGES.get(kind, "query error")
    # Garante ausência mesmo se a tabela for estendida com texto derivado.
    message = redact_secrets(message)
    return McpToolError(message, kind=kind)
