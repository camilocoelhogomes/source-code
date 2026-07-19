"""Erros tipados do agendamento (T15).

Responsabilidade deste módulo
    Declarar ``InvalidCronExpressionError`` e ``SchedulerConfigError``.

Motivo da separação
    Distinguir sintaxe cron inválida de misconfiguração de wiring, sem SDKs.
"""

from __future__ import annotations

_MAX_EXPR_IN_MESSAGE = 200


def format_cron_for_message(expression: str) -> str:
    """Trunca expressão para mensagem de erro (≤200 chars da expressão)."""
    text = expression.strip() if expression else expression
    if len(text) <= _MAX_EXPR_IN_MESSAGE:
        return text
    return text[:_MAX_EXPR_IN_MESSAGE] + "…"


class InvalidCronExpressionError(ValueError):
    """Expressão cron inválida (sintaxe/campo).

    Responsabilidade: rejeitar cron inválido sem aplicar parcialmente.
    Motivo da separação: distinto de misconfig de wiring (``SchedulerConfigError``).
    Mensagem: cita a expressão (truncada se > 200 chars); nunca segredos.
    """


class SchedulerConfigError(RuntimeError):
    """Misconfiguração do scheduler (deps ausentes, start inválido).

    Responsabilidade: falhas de wiring/boot do ``DailyScheduler``.
    Motivo da separação: não confundir com erro de sintaxe cron.
    """
