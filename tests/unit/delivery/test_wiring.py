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


if __name__ == "__main__":
    unittest.main()
