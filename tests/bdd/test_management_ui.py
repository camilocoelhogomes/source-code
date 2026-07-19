"""BDD — ManagementUiApi / UI (T18).

Cenários: UI-01..UI-10 (BDD-002/003/007/009/010/016/023/024 + REQ-023).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoOrigin, RepoState

from tests.unit.ui.helpers import (
    WEB_ROOT,
    build_client,
    put_progress,
    seed_error_history,
    seed_repo,
)


class TestManagementUiBdd(unittest.TestCase):
    def test_ui01_list_repos_origin_and_state(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_repo(catalog, origin=RepoOrigin.GITHUB, identifier="acme/api")
        seed_repo(
            catalog,
            origin=RepoOrigin.LOCAL,
            identifier="local-api",
            connection_name="local",
        )
        client, *_ = build_client(catalog=catalog)
        resp = client.get("/api/repos")
        self.assertEqual(resp.status_code, 200)
        repos = resp.json()["repos"]
        self.assertEqual(len(repos), 2)
        by_origin = {r["origin"]: r for r in repos}
        self.assertIn("github", by_origin)
        self.assertIn("local", by_origin)
        self.assertEqual(by_origin["local"]["state"], "not_indexed")
        self.assertEqual(by_origin["local"]["state_label"], "não indexado")
        for r in repos:
            self.assertIn(
                r["state"],
                {"not_indexed", "queued", "indexing", "up_to_date", "error"},
            )

    def test_ui02_index_selected_repos(self) -> None:
        catalog = InMemoryCatalogRepository()
        r1 = seed_repo(catalog, identifier="acme/a")
        r2 = seed_repo(catalog, identifier="acme/b", connection_name="gh2")
        client, _, orch, *_ = build_client(catalog=catalog)
        resp = client.post("/api/repos/index", json={"repository_ids": [r1, r2]})
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(sorted(orch.enqueued), sorted([r1, r2]))
        self.assertGreaterEqual(orch.idle_calls, 1)
        states = {e.state for e in catalog.list_active_catalog()}
        self.assertEqual(states, {RepoState.UP_TO_DATE})

    def test_ui03_progress_detail(self) -> None:
        catalog = InMemoryCatalogRepository()
        rid = seed_repo(catalog)
        put_progress(catalog, rid)
        client, *_ = build_client(catalog=catalog)
        resp = client.get(f"/api/repos/{rid}")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["progress"]["percent"], 40)
        self.assertEqual(body["progress"]["files_processed"], 2)
        self.assertEqual(body["progress"]["files_total"], 5)
        self.assertEqual(body["progress"]["current_stage"], "tree_sitter")
        files = {f["path"]: f for f in body["files"]}
        self.assertTrue(files["src/a.py"]["zoekt"])
        self.assertTrue(files["src/a.py"]["tree_sitter"])
        self.assertFalse(files["src/a.py"]["metadata_persisted"])

    def test_ui04_error_message_time_history(self) -> None:
        catalog = InMemoryCatalogRepository()
        rid = seed_repo(catalog)
        seed_error_history(catalog, rid)
        client, *_ = build_client(catalog=catalog)
        resp = client.get(f"/api/repos/{rid}/executions")
        self.assertEqual(resp.status_code, 200)
        executions = resp.json()["executions"]
        self.assertGreaterEqual(len(executions), 2)
        failed = [e for e in executions if e.get("error_message")]
        self.assertTrue(failed)
        self.assertTrue(any(e.get("error_at") for e in failed))
        self.assertTrue(
            any("fail" in (e.get("error_message") or "") for e in failed)
        )

    def test_ui05_configure_cron(self) -> None:
        client, _, _, scheduler, _ = build_client()
        get0 = client.get("/api/scheduler/cron")
        self.assertEqual(get0.status_code, 200)
        self.assertEqual(get0.json()["cron"], "0 2 * * *")
        put = client.put("/api/scheduler/cron", json={"cron": "30 4 * * *"})
        self.assertEqual(put.status_code, 200)
        self.assertEqual(put.json()["cron"], "30 4 * * *")
        self.assertEqual(scheduler.active_cron(), "30 4 * * *")
        self.assertEqual(client.get("/api/scheduler/cron").json()["cron"], "30 4 * * *")
        bad = client.put("/api/scheduler/cron", json={"cron": "99 99 * * *"})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(scheduler.active_cron(), "30 4 * * *")

    def test_ui06_exact_search(self) -> None:
        client, *_ = build_client()
        resp = client.post(
            "/api/search/exact", json={"pattern": "authenticate"}
        )
        self.assertEqual(resp.status_code, 200)
        hits = resp.json()["hits"]
        self.assertTrue(hits)
        self.assertEqual(hits[0]["kind"], "exact")
        self.assertIn("auth", hits[0]["path"])

    def test_ui07_semantic_search(self) -> None:
        client, *_ = build_client()
        resp = client.post(
            "/api/search/semantic",
            json={"query": "login flow", "reformulate": False},
        )
        self.assertEqual(resp.status_code, 200)
        hits = resp.json()["hits"]
        self.assertTrue(hits)
        self.assertEqual(hits[0]["kind"], "semantic")

    def test_ui08_no_crud_connections_or_token(self) -> None:
        client, *_ = build_client()
        self.assertEqual(client.post("/api/connections").status_code, 404)
        self.assertEqual(client.post("/api/connections/x").status_code, 404)
        self.assertEqual(client.put("/api/token").status_code, 404)
        paths = " ".join(client.get("/openapi.json").json()["paths"])
        self.assertNotIn("connection", paths.lower())
        html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
        js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
        blob = (html + js).lower()
        self.assertNotIn('type="password"', blob)
        self.assertNotIn("github token", blob)
        self.assertNotIn("personal access token", blob)

    def test_ui09_fastapi_surface(self) -> None:
        from github_rag.ui.api import DefaultManagementUiApi
        from github_rag.ui.ports import ManagementUiApi

        self.assertTrue(issubclass(DefaultManagementUiApi, object))
        import fastapi

        client, *_ = build_client()
        app = client.app
        self.assertIsInstance(app, fastapi.FastAPI)
        self.assertTrue(isinstance(DefaultManagementUiApi, type))
        # Protocol runtime
        from github_rag.catalog.memory import InMemoryCatalogRepository
        from tests.unit.ui.helpers import NoopReconcile, SpyOrchestrator
        from github_rag.schedule.memory import InMemoryCronPreferenceStore
        from github_rag.schedule.scheduler import DefaultDailyScheduler
        from github_rag.query.fake import FakeQueryService

        catalog = InMemoryCatalogRepository()
        orch = SpyOrchestrator(catalog)
        api = DefaultManagementUiApi(
            catalog=catalog,
            orchestrator=orch,
            scheduler=DefaultDailyScheduler(
                preference_store=InMemoryCronPreferenceStore(),
                reconcile=NoopReconcile(),
                orchestrator=orch,
                default_cron="0 2 * * *",
            ),
            query=FakeQueryService(),
            web_root=WEB_ROOT,
        )
        self.assertIsInstance(api, ManagementUiApi)

    def test_ui10_no_token_leak_in_errors(self) -> None:
        client, *_ = build_client()
        resp = client.get("/api/repos/99999")
        self.assertEqual(resp.status_code, 404)
        self.assertNotIn("ghp_", resp.text)
        self.assertNotIn("github_pat_", resp.text)


if __name__ == "__main__":
    unittest.main()
