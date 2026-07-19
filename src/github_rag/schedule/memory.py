"""Fake in-memory de ``CronPreferenceStore`` (T15).

Responsabilidade deste módulo
    Implementar preferência de cron em memória para testes.

Motivo da separação
    Mesma semântica do adaptador PG sem SQLAlchemy (ENG-013 / SCH-13).
"""

from __future__ import annotations

from github_rag.schedule.cron_expr import validate_cron_expression


class InMemoryCronPreferenceStore:
    """Implementação in-memory de ``CronPreferenceStore``."""

    def __init__(self) -> None:
        self._value: str | None = None

    def get(self) -> str | None:
        return self._value

    def set(self, cron_expression: str) -> str:
        normalized = validate_cron_expression(cron_expression)
        self._value = normalized
        return normalized

    def clear(self) -> None:
        self._value = None
