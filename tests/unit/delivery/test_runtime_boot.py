"""Unit — DefaultContainerRuntime / run_container_boot (T19 / UT-B*)."""

from __future__ import annotations

import io
import logging
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock

from github_rag.catalog.sync import CatalogSyncError

from tests.unit.delivery.helpers import (
    SECRET_TOKEN,
    BlockingOrchestrator,
    RecordingReconcile,
    RecordingScheduler,
    RecordingSurfaces,
    RecordingSync,
    base_environ,
    build_runtime,
    patch_infra,
    write_valid_config,
)


class TestBootHappyPathOrder(unittest.TestCase):
    """UT-B01 / UT-B08 — ordem D-T19-003 e reconcile 1×."""

    def test_ut_b01_boot_order_settings_config_migrate_sync_reconcile_scheduler_bind(
        self,
    ) -> None:
        from github_rag.config import ConfigLoader
        from github_rag.settings import load_settings as real_load_settings

        order: list[str] = []

        def load_settings_tracked(*a: Any, **k: Any) -> Any:
            order.append("settings")
            return real_load_settings(*a, **k)

        real_config_load = ConfigLoader.load

        def config_load_tracked(self: Any, path: Any) -> Any:
            order.append("config")
            return real_config_load(self, path)

        def fake_wait(_environ: Any, **_k: Any) -> None:
            order.append("migrate_wait")

        def fake_alembic(_environ: Any) -> None:
            order.append("migrate_alembic")

        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            sync = RecordingSync(on_sync=lambda _c: order.append("sync"))
            reconcile = RecordingReconcile(on_run=lambda: order.append("reconcile"))
            scheduler = RecordingScheduler(on_start=lambda: order.append("scheduler"))
            surfaces = RecordingSurfaces(
                on_bind=lambda name: order.append(f"bind_{name}")
            )

            with (
                mock.patch(
                    "github_rag.delivery.runtime.load_settings",
                    side_effect=load_settings_tracked,
                    create=True,
                ),
                mock.patch(
                    "github_rag.settings.load_settings",
                    side_effect=load_settings_tracked,
                ),
                mock.patch.object(ConfigLoader, "load", config_load_tracked),
                patch_infra(
                    wait_side_effect=fake_wait,
                    alembic_side_effect=fake_alembic,
                ),
            ):
                runtime, _, _, _, _ = build_runtime(
                    config_path=cfg,
                    sync=sync,
                    reconcile=reconcile,
                    scheduler=scheduler,
                    surfaces=surfaces,
                    skip_infra=False,
                )
                runtime.boot()

        for step in (
            "settings",
            "config",
            "migrate_wait",
            "migrate_alembic",
            "sync",
            "reconcile",
            "scheduler",
            "bind_ui",
            "bind_mcp",
        ):
            self.assertIn(step, order, msg=f"etapa ausente: {step}; order={order}")

        self.assertLess(order.index("settings"), order.index("config"))
        self.assertLess(order.index("config"), order.index("migrate_wait"))
        self.assertLess(order.index("migrate_wait"), order.index("migrate_alembic"))
        self.assertLess(order.index("migrate_alembic"), order.index("sync"))
        self.assertLess(order.index("sync"), order.index("reconcile"))
        self.assertLess(order.index("reconcile"), order.index("scheduler"))
        self.assertLess(order.index("scheduler"), order.index("bind_ui"))
        self.assertLess(order.index("scheduler"), order.index("bind_mcp"))
        self.assertEqual(len(sync.calls), 1)
        self.assertEqual(reconcile.calls, 1)

    def test_ut_b08_reconcile_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            reconcile = RecordingReconcile()
            runtime, _, _, _, _ = build_runtime(
                config_path=cfg, reconcile=reconcile
            )
            runtime.boot()
            self.assertEqual(reconcile.calls, 1)


class TestBootFailFastConfig(unittest.TestCase):
    """UT-B02..B05 / UT-B11 / UT-B13 / UT-B14 / UT-B17 — fail-fast sem parcial."""

    def _assert_exit_no_partial(self, environ: dict[str, str]) -> None:
        from github_rag.delivery import DefaultContainerRuntime

        sync = RecordingSync()
        reconcile = RecordingReconcile()
        scheduler = RecordingScheduler()
        surfaces = RecordingSurfaces()
        runtime = DefaultContainerRuntime(
            environ=environ,
            sync=sync,
            reconcile=reconcile,
            scheduler=scheduler,
            bind_ui=surfaces.bind_ui,
            bind_mcp=surfaces.bind_mcp,
            skip_infra=True,
        )
        with self.assertRaises(SystemExit) as ctx:
            runtime.boot()
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(sync.calls, [])
        self.assertEqual(reconcile.calls, 0)
        self.assertEqual(scheduler.started, 0)
        self.assertFalse(surfaces.ui_bound)
        self.assertFalse(surfaces.mcp_bound)

    def test_ut_b02_missing_config_path(self) -> None:
        env = base_environ()
        env.pop("CONFIG_PATH", None)
        self._assert_exit_no_partial(env)

    def test_ut_b03_blank_config_path(self) -> None:
        self._assert_exit_no_partial(base_environ(config_path="   "))

    def test_ut_b04_missing_config_file(self) -> None:
        self._assert_exit_no_partial(
            base_environ(config_path="/no/such/delivery-unit-config.json")
        )

    def test_ut_b05_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not-json", encoding="utf-8")
            self._assert_exit_no_partial(base_environ(config_path=bad))

    def test_ut_b11_run_container_boot_missing_config(self) -> None:
        from github_rag.delivery import run_container_boot

        with self.assertRaises(SystemExit) as ctx:
            run_container_boot(
                {
                    "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x",
                    "GITHUB_TOKEN": SECRET_TOKEN,
                }
            )
        self.assertEqual(ctx.exception.code, 1)

    def test_ut_b13_failure_does_not_leak_secrets(self) -> None:
        from github_rag.delivery import DefaultContainerRuntime

        db_url = (
            "postgresql+psycopg://secret_user:secret_pass@postgres:5432/github_rag"
        )
        env = base_environ(config_path="/no/such/delivery-unit-config.json")
        env["DATABASE_URL"] = db_url
        buf_out, buf_err = io.StringIO(), io.StringIO()
        log_buf = io.StringIO()
        handler = logging.StreamHandler(log_buf)
        logging.getLogger().addHandler(handler)
        try:
            with redirect_stdout(buf_out), redirect_stderr(buf_err):
                with self.assertRaises(SystemExit):
                    DefaultContainerRuntime(environ=env, skip_infra=True).boot()
        finally:
            logging.getLogger().removeHandler(handler)
        text = buf_out.getvalue() + buf_err.getvalue() + log_buf.getvalue()
        self.assertNotIn(SECRET_TOKEN, text)
        self.assertNotIn("ghp_", text)
        self.assertNotIn("secret_pass", text)
        self.assertNotIn(db_url, text)

    def test_ut_b14_invalid_index_workers_exits_without_bind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            env = base_environ(config_path=cfg)
            env["INDEX_WORKERS"] = "not-an-int"
            self._assert_exit_no_partial(env)

    def test_ut_b17_missing_github_token_exits_without_partial(self) -> None:
        """Secret ausente (ConfigLoadError) → exit 1 sem sync/reconcile/bind."""
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            env = base_environ(config_path=cfg)
            env.pop("GITHUB_TOKEN", None)
            self._assert_exit_no_partial(env)


class TestBootFailInfraAndSync(unittest.TestCase):
    """UT-B06 / UT-B07 / UT-B15 / UT-B16 — migrate/wait/sync e skip_infra."""

    def test_ut_b06_alembic_failure_exits_without_sync_or_bind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            sync = RecordingSync()
            reconcile = RecordingReconcile()
            scheduler = RecordingScheduler()
            surfaces = RecordingSurfaces()

            with patch_infra(
                wait_side_effect=lambda *_a, **_k: None,
                alembic_side_effect=RuntimeError("alembic boom"),
            ):
                runtime, _, _, _, _ = build_runtime(
                    config_path=cfg,
                    sync=sync,
                    reconcile=reconcile,
                    scheduler=scheduler,
                    surfaces=surfaces,
                    skip_infra=False,
                )
                with self.assertRaises(SystemExit) as ctx:
                    runtime.boot()
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(sync.calls, [])
            self.assertEqual(reconcile.calls, 0)
            self.assertEqual(scheduler.started, 0)
            self.assertFalse(surfaces.ui_bound)
            self.assertFalse(surfaces.mcp_bound)

    def test_ut_b15_wait_postgres_failure_exits_without_sync_or_bind(self) -> None:
        """PG timeout/falha no boot → exit 1 sem sync/reconcile/scheduler/bind."""
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            sync = RecordingSync()
            reconcile = RecordingReconcile()
            scheduler = RecordingScheduler()
            surfaces = RecordingSurfaces()

            with patch_infra(
                wait_side_effect=TimeoutError("postgres not ready"),
                alembic_side_effect=lambda *_a, **_k: None,
            ):
                runtime, _, _, _, _ = build_runtime(
                    config_path=cfg,
                    sync=sync,
                    reconcile=reconcile,
                    scheduler=scheduler,
                    surfaces=surfaces,
                    skip_infra=False,
                )
                with self.assertRaises(SystemExit) as ctx:
                    runtime.boot()
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(sync.calls, [])
            self.assertEqual(reconcile.calls, 0)
            self.assertEqual(scheduler.started, 0)
            self.assertFalse(surfaces.ui_bound)
            self.assertFalse(surfaces.mcp_bound)

    def test_ut_b16_skip_infra_omits_wait_and_alembic(self) -> None:
        """I-T19-011 — skip_infra=True não chama wait PG / alembic."""
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            with patch_infra() as (wait_mock, alembic_mock):
                runtime, sync, reconcile, scheduler, surfaces = build_runtime(
                    config_path=cfg,
                    skip_infra=True,
                )
                runtime.boot()
            wait_mock.assert_not_called()
            alembic_mock.assert_not_called()
            self.assertEqual(len(sync.calls), 1)
            self.assertEqual(reconcile.calls, 1)
            self.assertEqual(scheduler.started, 1)
            self.assertTrue(surfaces.ui_bound)
            self.assertTrue(surfaces.mcp_bound)

    def test_ut_b07_sync_error_exits_without_reconcile_or_bind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            sync = RecordingSync(fail=CatalogSyncError("sync failed"))
            reconcile = RecordingReconcile()
            scheduler = RecordingScheduler()
            surfaces = RecordingSurfaces()
            runtime, _, _, _, _ = build_runtime(
                config_path=cfg,
                sync=sync,
                reconcile=reconcile,
                scheduler=scheduler,
                surfaces=surfaces,
            )
            with self.assertRaises(SystemExit) as ctx:
                runtime.boot()
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(len(sync.calls), 1)
            self.assertEqual(reconcile.calls, 0)
            self.assertEqual(scheduler.started, 0)
            self.assertFalse(surfaces.ui_bound)
            self.assertFalse(surfaces.mcp_bound)


class TestBootIdempotencyAndConcurrency(unittest.TestCase):
    """UT-B09 / UT-B10 / UT-B12."""

    def test_ut_b09_second_boot_does_not_double_reconcile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            reconcile = RecordingReconcile()
            runtime, _, _, _, _ = build_runtime(
                config_path=cfg, reconcile=reconcile
            )
            runtime.boot()
            self.assertEqual(reconcile.calls, 1)
            try:
                runtime.boot()
            except SystemExit as exc:
                self.assertEqual(exc.code, 1)
                self.assertEqual(reconcile.calls, 1)
                return
            self.assertEqual(
                reconcile.calls,
                1,
                "segunda boot não deve chamar reconcile.run() de novo",
            )

    def test_ut_b10_blocking_orchestrator_idle_does_not_block_bind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            orch = BlockingOrchestrator()
            surfaces = RecordingSurfaces()
            runtime, _, reconcile, scheduler, _ = build_runtime(
                config_path=cfg,
                surfaces=surfaces,
                orchestrator=orch,
            )
            runtime.boot()
            self.assertEqual(reconcile.calls, 1)
            self.assertEqual(scheduler.started, 1)
            self.assertTrue(surfaces.ui_bound)
            self.assertTrue(surfaces.mcp_bound)
            self.assertEqual(
                orch.idle_calls,
                0,
                "boot não deve chamar run_until_idle no caminho de bind",
            )

    def test_ut_b12_container_runtime_protocol(self) -> None:
        from github_rag.delivery import ContainerRuntime, DefaultContainerRuntime

        self.assertTrue(callable(DefaultContainerRuntime))
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            runtime, _, _, _, _ = build_runtime(config_path=cfg)
            self.assertIsInstance(runtime, ContainerRuntime)


if __name__ == "__main__":
    unittest.main()
