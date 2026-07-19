"""Unit — ordem /healthz vs StaticFiles (T31 / UT-H03)."""

from __future__ import annotations

import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.query.fake import FakeQueryService
from github_rag.ui.app import create_app

from tests.unit.ui.helpers import NoopReconcile, SpyOrchestrator, WEB_ROOT
from github_rag.schedule.memory import InMemoryCronPreferenceStore
from github_rag.schedule.scheduler import DefaultDailyScheduler


class TestCreateAppHealthMountOrder(unittest.TestCase):
    """UT-H03a — health registrado antes do mount estático."""

    def test_create_app_healthz_before_static_mount(self) -> None:
        web_root = WEB_ROOT
        self.assertTrue(web_root.is_dir(), "fixture web/ deve existir no repo")

        catalog = InMemoryCatalogRepository()
        orch = SpyOrchestrator(catalog)
        scheduler = DefaultDailyScheduler(
            preference_store=InMemoryCronPreferenceStore(),
            reconcile=NoopReconcile(),
            orchestrator=orch,
            default_cron="0 2 * * *",
        )

        app = create_app(
            catalog=catalog,
            orchestrator=orch,
            scheduler=scheduler,
            query=FakeQueryService(),
            drain_on_index=False,
            web_root=web_root,
            get_state=lambda: {"ui_ready": True, "mcp_ready": True},
        )
        client = TestClient(app)

        health = client.get("/healthz")
        self.assertEqual(health.status_code, 200)
        body = health.json()
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("ui"), "ready")
        self.assertEqual(body.get("mcp"), "ready")

        root = client.get("/")
        self.assertEqual(root.status_code, 200)

        api = client.get("/api/repos")
        self.assertEqual(api.status_code, 200)

    def test_ut_h03c_health_after_static_mount_returns_404(self) -> None:
        """Guarda regressão F-W1-001 — ordem invertida produz 404."""
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles

        from github_rag.delivery.health import register_health_routes

        web_root = WEB_ROOT
        app = FastAPI()
        app.mount(
            "/",
            StaticFiles(directory=str(web_root), html=True),
            name="web",
        )
        register_health_routes(
            app,
            get_state=lambda: {"ui_ready": True, "mcp_ready": True},
        )
        resp = TestClient(app).get("/healthz")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
