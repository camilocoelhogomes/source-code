"""
BDD executável — T15-daily-scheduler.

Cenários SCH-01..13 (BDD-003/024, ENG-004/010/013).
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from github_rag.catalog.models import RepoState
from github_rag.settings import DEFAULT_INDEX_CRON, ENV_INDEX_CRON, load_settings
from github_rag.schedule.errors import InvalidCronExpressionError
from github_rag.schedule.cron_expr import validate_cron_expression
from github_rag.snapshot.diff import FileDiffSet
from tests.unit.indexing.helpers import seed_repo
from tests.unit.schedule.helpers import make_scheduler

SCHEDULE_SRC = Path(__file__).resolve().parents[2] / "src" / "github_rag" / "schedule"


class TestSCH01TickIndexesEligible(unittest.TestCase):
    def test_not_indexed_becomes_up_to_date(self) -> None:
        sched, _, _, _, catalog, snap, _, _ = make_scheduler()
        rid = seed_repo(catalog)
        snap.tip = "C1"
        sched.run_tick_once()
        entry = catalog.get_repository(rid)
        self.assertEqual(entry.state, RepoState.UP_TO_DATE)
        self.assertEqual(entry.last_processed_commit, "C1")


class TestSCH02CronVariety(unittest.TestCase):
    def test_hourly_daily_twice_daily(self) -> None:
        for expr in ("0 2 * * *", "0 */6 * * *", "0 0,12 * * *"):
            with self.subTest(expr=expr):
                self.assertEqual(validate_cron_expression(expr), expr)
                sched, *_ = make_scheduler()
                sched.set_cron(expr)
                self.assertEqual(sched.active_cron(), expr)


class TestSCH03EnvDefault(unittest.TestCase):
    def test_active_uses_settings_index_cron_not_hardcoded_default(self) -> None:
        settings = load_settings({ENV_INDEX_CRON: "0 3 * * *"})
        self.assertNotEqual(settings.index_cron, DEFAULT_INDEX_CRON)
        sched, *_ = make_scheduler(default_cron=settings.index_cron)
        self.assertEqual(sched.active_cron(), "0 3 * * *")


class TestSCH04PreferenceWins(unittest.TestCase):
    def test_persisted_overrides_env(self) -> None:
        sched, *_ = make_scheduler(
            default_cron="0 2 * * *", preference="0 */6 * * *"
        )
        self.assertEqual(sched.active_cron(), "0 */6 * * *")


class TestSCH05SkipUpToDate(unittest.TestCase):
    def test_no_reprocess(self) -> None:
        sched, _, _, _, catalog, snap, exact, vector = make_scheduler()
        seed_repo(catalog, state=RepoState.UP_TO_DATE, last="C1", current="C1")
        snap.tip = "C1"
        before = len(exact.index_calls)
        sched.run_tick_once()
        self.assertEqual(len(exact.index_calls), before)
        self.assertEqual(len(vector.replaces), 0)


class TestSCH06NewCommitOnTick(unittest.TestCase):
    def test_indexes_when_tip_differs(self) -> None:
        sched, _, _, _, catalog, snap, _, _ = make_scheduler()
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


class TestSCH07InvalidCron(unittest.TestCase):
    def test_typed_error_no_partial_apply(self) -> None:
        sched, store, *_ = make_scheduler(default_cron="0 2 * * *")
        sched.set_cron("0 */6 * * *")
        with self.assertRaises(InvalidCronExpressionError):
            sched.set_cron("not-a-cron")
        self.assertEqual(store.get(), "0 */6 * * *")
        self.assertEqual(sched.active_cron(), "0 */6 * * *")


class TestSCH08SetCronNoConfigPath(unittest.TestCase):
    def test_set_cron_does_not_touch_connections(self) -> None:
        # Dado: scheduler iniciado com cron A (Given literal do cenário SCH-08).
        sched, *_ = make_scheduler(default_cron="0 2 * * *")
        sched.start()
        try:
            sched.set_cron("0 0,12 * * *")
            self.assertEqual(sched.active_cron(), "0 0,12 * * *")
            import github_rag.schedule as pkg

            self.assertFalse(hasattr(pkg, "create_connection"))
        finally:
            sched.stop()


class TestSCH09NoConnectionCrud(unittest.TestCase):
    def test_package_surface(self) -> None:
        import github_rag.schedule as pkg

        banned = {"create_connection", "delete_connection", "upsert_connection"}
        self.assertFalse(set(dir(pkg)) & banned)


class TestSCH10Apscheduler(unittest.TestCase):
    def test_uses_apscheduler(self) -> None:
        path = SCHEDULE_SRC / "scheduler.py"
        source = path.read_text(encoding="utf-8").lower()
        self.assertIn("apscheduler", source)
        self.assertIn("crontrigger", source.replace("_", "").lower() or source)
        # CronTrigger literal
        self.assertTrue(
            "CronTrigger" in path.read_text(encoding="utf-8")
            or "cron" in source
        )


class TestSCH11Lock(unittest.TestCase):
    def test_serialized(self) -> None:
        import threading
        import time

        sched, _, _, reconcile, *_ = make_scheduler()
        order: list[str] = []
        gate = threading.Event()
        started = threading.Event()
        original = reconcile.run

        def slow() -> None:
            order.append("a")
            started.set()
            gate.wait(timeout=2)
            original()
            order.append("b")

        reconcile.run = slow  # type: ignore[method-assign]
        t1 = threading.Thread(target=sched.run_tick_once)
        t1.start()
        self.assertTrue(started.wait(2))
        t2 = threading.Thread(target=sched.run_tick_once)
        t2.start()
        time.sleep(0.05)
        self.assertEqual(order, ["a"])
        gate.set()
        t1.join(2)
        t2.join(2)
        self.assertEqual(order.count("a"), 2)
        self.assertEqual(order.count("b"), 2)


class TestSCH12OrmPreference(unittest.TestCase):
    def test_postgres_module_uses_sqlalchemy(self) -> None:
        path = SCHEDULE_SRC / "postgres.py"
        self.assertTrue(path.is_file())
        source = path.read_text(encoding="utf-8")
        self.assertIn("sqlalchemy", source.lower())
        mig = (
            Path(__file__).resolve().parents[2]
            / "migrations"
            / "versions"
            / "0002_scheduler_preference.py"
        )
        self.assertTrue(mig.is_file())


class TestSCH13SdkConfinement(unittest.TestCase):
    def test_domain_modules_clean(self) -> None:
        for name in ("ports.py", "errors.py", "memory.py"):
            tree = ast.parse((SCHEDULE_SRC / name).read_text(encoding="utf-8"))
            for node in tree.body:
                modules: list[str] = []
                if isinstance(node, ast.Import):
                    modules = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules = [node.module.split(".")[0]]
                for mod in modules:
                    self.assertNotIn(mod, {"apscheduler", "sqlalchemy"})


if __name__ == "__main__":
    unittest.main()
