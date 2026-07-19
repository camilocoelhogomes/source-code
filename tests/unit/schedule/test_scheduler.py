"""UT-S07..S14, S18/S19/S20 — DefaultDailyScheduler."""

from __future__ import annotations

import threading
import time
import unittest

from github_rag.catalog.models import RepoState
from github_rag.schedule.errors import InvalidCronExpressionError
from github_rag.schedule.ports import DailyScheduler
from github_rag.snapshot.diff import FileDiffSet
from tests.unit.indexing.helpers import seed_repo
from tests.unit.schedule.helpers import make_scheduler


class TestActiveCronPrecedence(unittest.TestCase):
    def test_default_when_no_preference(self) -> None:
        sched, *_ = make_scheduler(default_cron="0 3 * * *")
        self.assertEqual(sched.active_cron(), "0 3 * * *")

    def test_preference_overrides_default(self) -> None:
        sched, *_ = make_scheduler(
            default_cron="0 2 * * *", preference="0 */6 * * *"
        )
        self.assertEqual(sched.active_cron(), "0 */6 * * *")

    def test_runtime_checkable(self) -> None:
        sched, *_ = make_scheduler()
        self.assertIsInstance(sched, DailyScheduler)


class TestSetCron(unittest.TestCase):
    def test_invalid_leaves_active_unchanged(self) -> None:
        sched, store, *_ = make_scheduler(default_cron="0 2 * * *")
        with self.assertRaises(InvalidCronExpressionError):
            sched.set_cron("not-a-cron")
        self.assertEqual(sched.active_cron(), "0 2 * * *")
        self.assertIsNone(store.get())

    def test_valid_updates_active_and_store(self) -> None:
        sched, store, *_ = make_scheduler(default_cron="0 2 * * *")
        self.assertEqual(sched.set_cron("0 0,12 * * *"), "0 0,12 * * *")
        self.assertEqual(sched.active_cron(), "0 0,12 * * *")
        self.assertEqual(store.get(), "0 0,12 * * *")

    def test_clear_via_store_returns_to_default(self) -> None:
        sched, store, *_ = make_scheduler(
            default_cron="0 3 * * *", preference="0 */6 * * *"
        )
        store.clear()
        self.assertEqual(sched.active_cron(), "0 3 * * *")

    def test_start_with_invalid_default_raises(self) -> None:
        sched, *_ = make_scheduler(default_cron="not-a-cron")
        with self.assertRaises(InvalidCronExpressionError):
            sched.start()
        sched.stop()

    def test_valid_reschedules_while_running_without_restart(self) -> None:
        """SCH-08/D-T15-009: set_cron com scheduler já iniciado reagenda em
        runtime sem exigir stop()+start() do processo (única chamada a
        start() neste teste)."""
        sched, store, *_ = make_scheduler(default_cron="0 2 * * *")
        sched.start()
        try:
            self.assertEqual(sched.set_cron("0 */6 * * *"), "0 */6 * * *")
            self.assertEqual(sched.active_cron(), "0 */6 * * *")
            self.assertEqual(store.get(), "0 */6 * * *")
        finally:
            sched.stop()


class TestTickBehavior(unittest.TestCase):
    def test_tick_indexes_not_indexed(self) -> None:
        sched, _, _, _, catalog, snap, exact, _ = make_scheduler()
        rid = seed_repo(catalog)
        snap.tip = "C1"
        before = len(exact.index_calls)
        sched.run_tick_once()
        entry = catalog.get_repository(rid)
        self.assertEqual(entry.state, RepoState.UP_TO_DATE)
        self.assertEqual(entry.last_processed_commit, "C1")
        self.assertGreater(len(exact.index_calls), before)

    def test_tick_skips_up_to_date_same_commit(self) -> None:
        sched, _, _, _, catalog, snap, exact, vector = make_scheduler()
        rid = seed_repo(
            catalog, state=RepoState.UP_TO_DATE, last="C1", current="C1"
        )
        snap.tip = "C1"
        before_i = len(exact.index_calls)
        before_v = len(vector.replaces)
        sched.run_tick_once()
        self.assertEqual(len(exact.index_calls), before_i)
        self.assertEqual(len(vector.replaces), before_v)
        self.assertEqual(
            catalog.get_repository(rid).state, RepoState.UP_TO_DATE
        )

    def test_tick_indexes_when_tip_differs(self) -> None:
        sched, _, _, _, catalog, snap, exact, _ = make_scheduler()
        rid = seed_repo(
            catalog, state=RepoState.UP_TO_DATE, last="C1", current="C1"
        )
        snap.tip = "C2"
        snap.diffs[("C1", "C2")] = FileDiffSet(
            added=("src/a.py",), modified=(), deleted=()
        )
        sched.run_tick_once()
        entry = catalog.get_repository(rid)
        self.assertEqual(entry.state, RepoState.UP_TO_DATE)
        self.assertEqual(entry.last_processed_commit, "C2")
        self.assertGreater(len(exact.index_calls), 0)


class TestTickLock(unittest.TestCase):
    def test_run_tick_once_serializes(self) -> None:
        sched, _, orch, reconcile, *_ = make_scheduler()
        order: list[str] = []
        gate = threading.Event()
        started = threading.Event()

        original_run = reconcile.run

        def slow_run() -> None:
            order.append("enter")
            started.set()
            gate.wait(timeout=2)
            original_run()
            order.append("exit")

        reconcile.run = slow_run  # type: ignore[method-assign]

        t1 = threading.Thread(target=sched.run_tick_once)
        t1.start()
        self.assertTrue(started.wait(timeout=2))
        t2 = threading.Thread(target=sched.run_tick_once)
        t2.start()
        time.sleep(0.05)
        self.assertEqual(order, ["enter"])
        gate.set()
        t1.join(timeout=2)
        t2.join(timeout=2)
        self.assertEqual(order, ["enter", "exit", "enter", "exit"])


class TestStopIdempotent(unittest.TestCase):
    def test_stop_without_start(self) -> None:
        sched, *_ = make_scheduler()
        sched.stop()
        sched.stop()

    def test_stop_when_scheduler_already_shutdown_externally(self) -> None:
        """stop() não chama shutdown() duas vezes se o BackgroundScheduler já
        não está `.running` (ex.: encerrado por fora do DailyScheduler)."""
        sched, *_ = make_scheduler()
        sched.start()
        sched._scheduler.shutdown(wait=False)  # noqa: SLF001 — simula shutdown externo
        sched.stop()


class TestStartIdempotent(unittest.TestCase):
    def test_start_twice_reschedules_instead_of_raising_or_duplicating(
        self,
    ) -> None:
        """start() chamado com o job já rodando reagenda (mesmo caminho de
        set_cron) em vez de duplicar o job ou lançar erro (docstring de
        DailyScheduler.start em ports.py)."""
        sched, store, *_ = make_scheduler(default_cron="0 2 * * *")
        sched.start()
        try:
            store.set("0 */6 * * *")
            sched.start()
            self.assertEqual(sched.active_cron(), "0 */6 * * *")
            jobs = sched._scheduler.get_jobs()  # noqa: SLF001 — inspeção de teste
            self.assertEqual(len(jobs), 1)
        finally:
            sched.stop()

    def test_reschedule_recreates_job_when_missing_from_store(self) -> None:
        """_reschedule captura só JobLookupError (job removido do
        BackgroundScheduler por fora do DailyScheduler) e recria o job em vez
        de propagar; qualquer outra exceção do APScheduler deve propagar."""
        sched, store, *_ = make_scheduler(default_cron="0 2 * * *")
        sched.start()
        try:
            sched._scheduler.remove_job("index_cron_tick")  # noqa: SLF001
            sched.set_cron("0 */6 * * *")
            self.assertEqual(sched.active_cron(), "0 */6 * * *")
            jobs = sched._scheduler.get_jobs()  # noqa: SLF001
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0].id, "index_cron_tick")
        finally:
            sched.stop()


if __name__ == "__main__":
    unittest.main()
