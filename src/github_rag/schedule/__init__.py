"""Agendamento cron de indexação (T15).

Responsabilidade deste pacote
    ``DailyScheduler``, preferência de cron e validação via APScheduler.

Motivo da separação
    Fronteira ``schedule`` do plano; sem CRUD de conexões (BR-017).
"""

from github_rag.schedule.cron_expr import validate_cron_expression
from github_rag.schedule.errors import (
    InvalidCronExpressionError,
    SchedulerConfigError,
)
from github_rag.schedule.memory import InMemoryCronPreferenceStore
from github_rag.schedule.ports import CronPreferenceStore, DailyScheduler
from github_rag.schedule.scheduler import DefaultDailyScheduler

__all__ = [
    "CronPreferenceStore",
    "DailyScheduler",
    "DefaultDailyScheduler",
    "InMemoryCronPreferenceStore",
    "InvalidCronExpressionError",
    "SchedulerConfigError",
    "validate_cron_expression",
]
