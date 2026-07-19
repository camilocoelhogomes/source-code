"""Unit — healthz payload / rotas (T19 / UT-H*)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.unit.delivery.helpers import (
    SECRET_TOKEN,
    build_runtime,
    write_valid_config,
)


class TestHealthzPayload(unittest.TestCase):
    """UT-H01 / UT-H02 / UT-H05."""

    def test_ut_h01_payload_ready_canonical(self) -> None:
        from github_rag.delivery.health import healthz_payload

        body = healthz_payload(ui_ready=True, mcp_ready=True)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["ui"], "ready")
        self.assertEqual(body["mcp"], "ready")

    def test_ut_h02_payload_not_ready(self) -> None:
        from github_rag.delivery.health import healthz_payload

        body = healthz_payload(ui_ready=False, mcp_ready=False)
        self.assertNotEqual(
            (body.get("status"), body.get("ui"), body.get("mcp")),
            ("ok", "ready", "ready"),
            "antes do boot completo não deve reportar ready canônico",
        )
        # Nenhum lado ready quando ambos False
        self.assertNotEqual(body.get("ui"), "ready")
        self.assertNotEqual(body.get("mcp"), "ready")

    def test_ut_h05_payload_keys_exactly(self) -> None:
        from github_rag.delivery.health import healthz_payload

        body = healthz_payload(ui_ready=True, mcp_ready=True)
        self.assertEqual(set(body.keys()), {"status", "ui", "mcp"})

    def test_healthz_route_503_when_not_ready_and_object_state(self) -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from github_rag.delivery.health import register_health_routes

        class _State:
            ui_ready = False
            mcp_ready = False

        app = FastAPI()
        register_health_routes(app, get_state=lambda: _State())
        resp = TestClient(app).get("/healthz")
        self.assertEqual(resp.status_code, 503)
        body = resp.json()
        self.assertNotEqual(body.get("status"), "ok")
        self.assertNotEqual(body.get("ui"), "ready")


class TestHealthzAfterBoot(unittest.TestCase):
    """UT-H03 / UT-H04 — health só após boot; sem segredos."""

    def test_ut_h03_healthz_200_only_after_full_boot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            runtime, _, _, _, surfaces = build_runtime(config_path=cfg)

            pre_app = getattr(runtime, "ui_app", None) or getattr(
                runtime, "asgi_app", None
            )
            self.assertIsNone(
                pre_app,
                "antes do boot não deve expor app ASGI com /healthz ready",
            )

            runtime.boot()
            self.assertTrue(surfaces.ui_bound)
            self.assertTrue(surfaces.mcp_bound)

            app = getattr(runtime, "ui_app", None) or getattr(
                runtime, "asgi_app", None
            )
            self.assertIsNotNone(app, "runtime deve expor ui_app/asgi_app após boot")
            from fastapi.testclient import TestClient

            client = TestClient(app)
            resp = client.get("/healthz")
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(body.get("status"), "ok")
            self.assertEqual(body.get("ui"), "ready")
            self.assertEqual(body.get("mcp"), "ready")

    def test_ut_h04_healthz_body_has_no_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_valid_config(Path(tmp))
            runtime, _, _, _, _ = build_runtime(config_path=cfg)
            runtime.boot()
            app = getattr(runtime, "ui_app", None) or getattr(
                runtime, "asgi_app", None
            )
            from fastapi.testclient import TestClient

            body = TestClient(app).get("/healthz").json()
            blob = json.dumps(body)
            self.assertNotIn(SECRET_TOKEN, blob)
            self.assertNotIn("ghp_", blob)
            self.assertNotIn("DATABASE_URL", blob)
            self.assertNotIn("secret_pass", blob)


if __name__ == "__main__":
    unittest.main()
