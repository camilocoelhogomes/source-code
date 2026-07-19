"""Harness para testes T15 — DailyScheduler."""

from __future__ import annotations

from github_rag.schedule.memory import InMemoryCronPreferenceStore
from github_rag.schedule.scheduler import DefaultDailyScheduler
from tests.unit.indexing.helpers import make_orchestrator, seed_repo


def make_scheduler(
    *,
    default_cron: str = "0 2 * * *",
    preference: str | None = None,
):
    """Monta DefaultDailyScheduler + fakes T14."""
    orch, reconcile, catalog, snap, exact, vector = make_orchestrator()
    store = InMemoryCronPreferenceStore()
    if preference is not None:
        store.set(preference)
    scheduler = DefaultDailyScheduler(
        preference_store=store,
        reconcile=reconcile,
        orchestrator=orch,
        default_cron=default_cron,
    )
    return scheduler, store, orch, reconcile, catalog, snap, exact, vector
