"""Mapeamento de erros de domínio → HTTP para a UI (T18).

Responsabilidade deste módulo
    Traduzir exceções conhecidas em status/detail sem vazar token.

Motivo da separação
    Handlers FastAPI não embutem regras de mapeamento espalhadas.
"""

from __future__ import annotations

from github_rag.catalog.errors import RepositoryNotFoundError
from github_rag.query.errors import (
    QueryError,
    QueryRepositoryNotFoundError,
    QueryValidationError,
)
from github_rag.schedule.errors import InvalidCronExpressionError


def http_status_for(exc: BaseException) -> int:
    """Devolve status HTTP para exceção de domínio da UI.

    Responsabilidade: classificação estável 400/404/500.
    Motivo da separação: evita ``isinstance`` repetido nas rotas.
    """
    if isinstance(exc, (RepositoryNotFoundError, QueryRepositoryNotFoundError)):
        return 404
    if isinstance(
        exc,
        (InvalidCronExpressionError, QueryValidationError, QueryError),
    ):
        return 400
    return 500


def safe_detail(exc: BaseException) -> str:
    """Mensagem de erro sem substrings típicas de token GitHub.

    Responsabilidade: superfície BR-008 / BDD-014 UI.
    Motivo da separação: redaction centralizada.
    """
    text = str(exc) or exc.__class__.__name__
    for needle in ("ghp_", "github_pat_", "gho_", "ghu_"):
        if needle in text:
            text = text.replace(needle, "[redacted]")
    return text
