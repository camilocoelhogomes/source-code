"""Unit — wiring helpers / env incompleto (T19 / UT-W*)."""

from __future__ import annotations

import inspect
import unittest


class TestWiringIncompleteEnv(unittest.TestCase):
    """UT-W01 / UT-W02 / UT-W04 — factories falham tipadas com env incompleto."""

    def test_ut_w01_wire_catalog_without_database_url(self) -> None:
        from github_rag.delivery.wiring import wire_catalog

        with self.assertRaises(Exception) as ctx:
            wire_catalog({})
        # Qualquer erro tipado; não retornar repositório silencioso
        self.assertIsNotNone(ctx.exception)
        message = str(ctx.exception)
        self.assertNotIn("postgresql+psycopg://u:p@", message)

    def test_ut_w02_wait_for_postgres_timeout_no_url_leak(self) -> None:
        from github_rag.delivery.wiring import wait_for_postgres

        env = {
            "DATABASE_URL": (
                "postgresql+psycopg://secret_user:secret_pass@127.0.0.1:1/db"
            ),
        }
        with self.assertRaises(Exception) as ctx:
            wait_for_postgres(env, timeout_seconds=0.05, interval_seconds=0.01)
        text = str(ctx.exception)
        self.assertNotIn("secret_pass", text)
        self.assertNotIn("secret_user:secret_pass", text)
        self.assertNotIn(env["DATABASE_URL"], text)

    def test_ut_w04_indexing_stack_missing_frontier_env(self) -> None:
        from github_rag.delivery.wiring import wire_indexing_stack

        class _Settings:
            index_workers = 2
            query_workers = 4
            index_cron = "0 2 * * *"
            config_path = None

        with self.assertRaises(Exception):
            wire_indexing_stack(
                {"DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x"},
                catalog=object(),
                settings=_Settings(),
            )


class TestWiringBindHelpers(unittest.TestCase):
    """UT-W03 — bind helpers existem e aceitam environ (UI_*/MCP_*)."""

    def test_ut_w03_default_bind_callables_exist(self) -> None:
        from github_rag.delivery import wiring

        self.assertTrue(callable(getattr(wiring, "default_bind_ui", None)))
        self.assertTrue(callable(getattr(wiring, "default_bind_mcp", None)))
        ui_params = inspect.signature(wiring.default_bind_ui).parameters
        mcp_params = inspect.signature(wiring.default_bind_mcp).parameters
        self.assertIn("environ", ui_params)
        self.assertIn("environ", mcp_params)


class TestWiringHelpersCoverage(unittest.TestCase):
    """Cobertura adicional de factories/binds (sem infra real)."""

    def test_wait_for_postgres_missing_database_url(self) -> None:
        from github_rag.delivery.wiring import DeliveryWiringError, wait_for_postgres

        with self.assertRaises(DeliveryWiringError):
            wait_for_postgres({})

    def test_run_alembic_upgrade_missing_database_url(self) -> None:
        from github_rag.delivery.wiring import DeliveryWiringError, run_alembic_upgrade

        with self.assertRaises(DeliveryWiringError):
            run_alembic_upgrade({})

    def test_resolve_delivery_root_honours_app_root_override(self) -> None:
        import os
        from pathlib import Path
        from unittest import mock

        from github_rag.delivery.wiring import (
            DeliveryWiringError,
            _resolve_delivery_root,
        )

        repo = Path(__file__).resolve().parents[3]
        with mock.patch.dict(os.environ, {"GITHUB_RAG_APP_ROOT": str(repo)}):
            self.assertEqual(_resolve_delivery_root(), repo)

    def test_resolve_delivery_root_fails_when_override_missing_ini(self) -> None:
        import os
        from unittest import mock

        from github_rag.delivery.wiring import (
            DeliveryWiringError,
            _resolve_delivery_root,
        )

        with mock.patch.dict(os.environ, {"GITHUB_RAG_APP_ROOT": "/tmp/nowhere"}):
            with self.assertRaises(DeliveryWiringError):
                _resolve_delivery_root()

    def test_wire_catalog_sync_builds(self) -> None:
        from github_rag.delivery.wiring import wire_catalog_sync

        sync = wire_catalog_sync({}, catalog=object())
        self.assertTrue(hasattr(sync, "sync"))

    def test_t34_wire_catalog_sync_passes_host_repos(self) -> None:
        from unittest import mock

        from github_rag.delivery.wiring import wire_catalog_sync

        with mock.patch(
            "github_rag.sources.local.discovery.LocalRepoDiscovery"
        ) as discovery_cls:
            discovery_cls.return_value = object()
            with mock.patch("github_rag.catalog.sync.CatalogSync") as sync_cls:
                sync_cls.return_value = object()
                wire_catalog_sync(
                    {"HOST_REPOS": "/tmp/e2e-fixtures/repos"},
                    catalog=object(),
                )
        discovery_cls.assert_called_once_with(host_repos="/tmp/e2e-fixtures/repos")

    def test_wire_query_service_missing_frontier_env(self) -> None:
        from github_rag.delivery.wiring import wire_query_service

        class _Settings:
            index_workers = 2
            query_workers = 4
            index_cron = "0 2 * * *"
            config_path = None

        with self.assertRaises(Exception):
            wire_query_service({}, catalog=object(), settings=_Settings())

    def test_wire_scheduler_missing_database_url(self) -> None:
        from github_rag.delivery.wiring import wire_scheduler

        class _Settings:
            index_cron = "0 2 * * *"

        with self.assertRaises(Exception):
            wire_scheduler(
                {},
                catalog=object(),
                orchestrator=object(),
                settings=_Settings(),
                reconcile=object(),
            )

    def test_default_bind_ui_invalid_port(self) -> None:
        from github_rag.delivery.wiring import DeliveryWiringError, default_bind_ui

        with self.assertRaises(DeliveryWiringError):
            default_bind_ui(object(), {"UI_PORT": "not-a-port"})

    def test_default_bind_mcp_invalid_port(self) -> None:
        from github_rag.delivery.wiring import DeliveryWiringError, default_bind_mcp

        with self.assertRaises(DeliveryWiringError):
            default_bind_mcp(object(), {"MCP_PORT": "bad"})

    def test_default_bind_ui_calls_uvicorn(self) -> None:
        from unittest import mock

        from github_rag.delivery.wiring import default_bind_ui

        with mock.patch("uvicorn.run") as run:
            default_bind_ui(object(), {"UI_HOST": "127.0.0.1", "UI_PORT": "9090"})
        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs["host"], "127.0.0.1")
        self.assertEqual(run.call_args.kwargs["port"], 9090)

    def test_default_bind_mcp_calls_run(self) -> None:
        from github_rag.delivery.wiring import default_bind_mcp

        class _Settings:
            port = 0
            host = ""

        class _Mcp:
            def __init__(self) -> None:
                self.settings = _Settings()
                self.calls: list[str] = []

            def run(self, *, transport: str) -> None:
                self.calls.append(transport)

        mcp = _Mcp()
        default_bind_mcp(
            mcp, {"MCP_PORT": "8001", "MCP_TRANSPORT": "sse", "MCP_HOST": "0.0.0.0"}
        )
        self.assertEqual(mcp.calls, ["sse"])
        self.assertEqual(mcp.settings.port, 8001)

    def test_wire_ui_and_mcp_compose(self) -> None:
        from unittest import mock

        from github_rag.delivery.wiring import wire_mcp_server, wire_ui_app

        with mock.patch("github_rag.ui.DefaultManagementUiApi") as ui_cls:
            ui_cls.return_value = "ui-builder"
            built = wire_ui_app(
                catalog=object(),
                orchestrator=object(),
                scheduler=object(),
                query=object(),
            )
        self.assertEqual(built, "ui-builder")
        ui_cls.assert_called_once()

        with mock.patch("github_rag.mcp.DefaultMcpEvidenceServer") as mcp_cls:
            mcp_cls.return_value.build.return_value = "mcp-app"
            built = wire_mcp_server(
                catalog=object(), query=object(), query_limiter=object()
            )
        self.assertEqual(built, "mcp-app")


if __name__ == "__main__":
    unittest.main()
