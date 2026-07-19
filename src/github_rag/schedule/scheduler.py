"""Implementação ``DefaultDailyScheduler`` via APScheduler (T15 / DEC-015).

Responsabilidade deste módulo
    Lifecycle do job cron, precedência ENG-004 e tick serializado.

Motivo da separação
    Concentra APScheduler; consumidores usam a porta ``DailyScheduler``.
"""

from __future__ import annotations

import logging
from threading import Lock
from zoneinfo import ZoneInfo

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from github_rag.indexing.ports import IndexingOrchestrator, StartupIndexReconcile
from github_rag.schedule.cron_expr import validate_cron_expression
from github_rag.schedule.ports import CronPreferenceStore

_LOG = logging.getLogger(__name__)
_UTC = ZoneInfo("UTC")
_JOB_ID = "index_cron_tick"


class DefaultDailyScheduler:
    """Implementação de ``DailyScheduler`` com ``BackgroundScheduler``."""

    def __init__(
        self,
        *,
        preference_store: CronPreferenceStore,
        reconcile: StartupIndexReconcile,
        orchestrator: IndexingOrchestrator,
        default_cron: str,
    ) -> None:
        self._store = preference_store
        self._reconcile = reconcile
        self._orchestrator = orchestrator
        self._default_cron = default_cron
        self._run_lock = Lock()
        self._scheduler: BackgroundScheduler | None = None

    def active_cron(self) -> str:
        persisted = self._store.get()
        return persisted if persisted is not None else self._default_cron

    def start(self) -> None:
        expression = validate_cron_expression(self.active_cron())
        source = "preference" if self._store.get() is not None else "env"
        if self._scheduler is not None and self._scheduler.running:
            self._reschedule(expression)
            _LOG.info(
                "daily_scheduler already running; rescheduled cron=%s source=%s",
                expression,
                source,
            )
            return
        scheduler = BackgroundScheduler(timezone=_UTC)
        self._add_cron_job(scheduler, expression)
        scheduler.start()
        self._scheduler = scheduler
        _LOG.info(
            "daily_scheduler started cron=%s source=%s", expression, source
        )

    def stop(self) -> None:
        if self._scheduler is None:
            return
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        self._scheduler = None

    def set_cron(self, cron_expression: str) -> str:
        normalized = self._store.set(cron_expression)
        if self._scheduler is not None and self._scheduler.running:
            self._reschedule(normalized)
        return normalized

    def run_tick_once(self) -> None:
        with self._run_lock:
            _LOG.info("daily_scheduler tick start")
            self._reconcile.run()
            self._orchestrator.run_until_idle()
            _LOG.info("daily_scheduler tick end")

    def _cron_trigger(self, expression: str) -> CronTrigger:
        return CronTrigger.from_crontab(expression, timezone=_UTC)

    def _add_cron_job(
        self, scheduler: BackgroundScheduler, expression: str
    ) -> None:
        scheduler.add_job(
            self.run_tick_once,
            trigger=self._cron_trigger(expression),
            id=_JOB_ID,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def _reschedule(self, expression: str) -> None:
        assert self._scheduler is not None
        trigger = self._cron_trigger(expression)
        try:
            self._scheduler.reschedule_job(_JOB_ID, trigger=trigger)
        except JobLookupError:  # job ausente (nunca registrado/removido): recria
            self._add_cron_job(self._scheduler, expression)
