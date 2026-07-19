"""Validação de expressão cron via APScheduler (T15 / DEC-015).

Responsabilidade deste módulo
    Validar sintaxe cron de 5 campos com ``CronTrigger.from_crontab``.

Motivo da separação
    Isola APScheduler da porta ``DailyScheduler`` / store (ENG-013).
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger

from github_rag.schedule.errors import (
    InvalidCronExpressionError,
    format_cron_for_message,
)

_UTC = ZoneInfo("UTC")


def validate_cron_expression(expression: str) -> str:
    """Valida expressão cron de 5 campos via ``CronTrigger.from_crontab``.

    Responsabilidade: único validador de sintaxe do produto.
    Motivo da separação: isola APScheduler da porta ``DailyScheduler``/store.
    Retorno: expressão stripada se válida.
    Erros: ``InvalidCronExpressionError``.
    """
    if expression is None:
        raise InvalidCronExpressionError("cron expression is empty")
    normalized = expression.strip()
    if not normalized:
        raise InvalidCronExpressionError("cron expression is empty")
    try:
        CronTrigger.from_crontab(normalized, timezone=_UTC)
    except (ValueError, TypeError) as exc:
        cited = format_cron_for_message(normalized)
        raise InvalidCronExpressionError(
            f"invalid cron expression: {cited}"
        ) from exc
    return normalized
