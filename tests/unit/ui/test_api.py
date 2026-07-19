"""Unit — DefaultManagementUiApi / rotas (T18)."""

from __future__ import annotations

import unittest

from github_rag.catalog.errors import RepositoryNotFoundError
from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoState
from github_rag.query.fake import FakeQueryService
from github_rag.query.types import QueryHit, QueryHits

from tests.unit.ui.helpers import build_client, seed_repo


class TestManagementUiApi(unittest.TestCase):
    def test_list_repos_empty(self) -> None:
        client, *_ = build_client()
        resp = client.get("/api/repos")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["repos"], [])

    def test_index_empty_ids_422(self) -> None:
        client, *_ = build_client()
        resp = client.post("/api/repos/index", json={"repository_ids": []})
        self.assertEqual(resp.status_code, 422)

    def test_index_unknown_id_404(self) -> None:
        client, catalog, orch, *_ = build_client()
        resp = client.post("/api/repos/index", json={"repository_ids": [999]})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(orch.enqueued, [])

    def test_cron_invalid_keeps_previous(self) -> None:
        client, _, _, scheduler, _ = build_client()
        ok = client.put("/api/scheduler/cron", json={"cron": "15 3 * * *"})
        self.assertEqual(ok.status_code, 200)
        bad = client.put("/api/scheduler/cron", json={"cron": "not a cron"})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(scheduler.active_cron(), "15 3 * * *")

    def test_semantic_default_reformulate_false(self) -> None:
        class Spy(FakeQueryService):
            def __init__(self) -> None:
                super().__init__(
                    semantic_hits=QueryHits(
                        hits=(
                            QueryHit(
                                kind="semantic",
                                score=0.5,
                                repository="r",
                                path="p",
                                commit="c",
                                snippet="s",
                            ),
                        )
                    )
                )
                self.last = None

            def search_semantic(self, request):  # type: ignore[no-untyped-def]
                self.last = request
                return super().search_semantic(request)

        spy = Spy()
        client, *_ = build_client(query=spy)
        resp = client.post("/api/search/semantic", json={"query": "login"})
        self.assertEqual(resp.status_code, 200)
        assert spy.last is not None
        self.assertFalse(spy.last.reformulate)

    def test_exact_empty_pattern_422(self) -> None:
        client, *_ = build_client()
        resp = client.post("/api/search/exact", json={"pattern": ""})
        self.assertEqual(resp.status_code, 422)

    def test_openapi_has_no_connection_or_token_routes(self) -> None:
        client, *_ = build_client()
        paths = client.get("/openapi.json").json()["paths"]
        joined = " ".join(paths)
        self.assertNotIn("connection", joined.lower())
        self.assertNotIn("token", joined.lower())
        self.assertNotIn("/api/config", joined)

    def test_drain_flag_false_skips_idle(self) -> None:
        catalog = InMemoryCatalogRepository()
        rid = seed_repo(catalog, state=RepoState.NOT_INDEXED)
        client, _, orch, *_ = build_client(catalog=catalog, drain_on_index=False)
        resp = client.post("/api/repos/index", json={"repository_ids": [rid]})
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(orch.enqueued, [rid])
        self.assertEqual(orch.idle_calls, 0)

    def test_unknown_repo_detail_404(self) -> None:
        client, *_ = build_client()
        resp = client.get("/api/repos/404")
        self.assertEqual(resp.status_code, 404)
        self.assertNotIn("ghp_", resp.text)


if __name__ == "__main__":
    unittest.main()
