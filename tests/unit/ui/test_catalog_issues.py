"""Unit — CatalogIssueStore + GET /api/catalog/issues (T25 / UT-I*)."""

from __future__ import annotations

import unittest

from github_rag.sources.local.discovery import LocalDiscoveryIssue
from github_rag.ui.issues import InMemoryCatalogIssueStore
from tests.unit.ui.helpers import build_client

# Sentinel that must never appear in API JSON from env/product leaks.
_ENV_TOKEN_SENTINEL = "ghp_t25_unit_must_not_leak_9f3a2"


class TestCatalogIssueStore(unittest.TestCase):
    def test_ut_i01_empty_store_lists_empty(self) -> None:
        store = InMemoryCatalogIssueStore()
        self.assertEqual(store.list_issues(), ())

    def test_ut_i02_replace_round_trip(self) -> None:
        store = InMemoryCatalogIssueStore()
        issue = LocalDiscoveryIssue(
            connection_name="local-missing",
            path="/repos/__missing__",
            message="path inaccessible: missing",
        )
        store.replace([issue])
        listed = store.list_issues()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].connection_name, "local-missing")
        self.assertEqual(listed[0].path, "/repos/__missing__")
        self.assertIn("inaccessible", listed[0].message.lower())

    def test_ut_i03_replace_overwrites_not_appends(self) -> None:
        store = InMemoryCatalogIssueStore()
        store.replace(
            [
                LocalDiscoveryIssue("a", "/a", "first"),
                LocalDiscoveryIssue("b", "/b", "second"),
            ]
        )
        store.replace([LocalDiscoveryIssue("c", "/c", "only")])
        listed = store.list_issues()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].connection_name, "c")


class TestCatalogIssuesRoute(unittest.TestCase):
    def test_ut_i04_get_catalog_issues_serializes(self) -> None:
        store = InMemoryCatalogIssueStore()
        store.replace(
            [
                LocalDiscoveryIssue(
                    connection_name="local-missing",
                    path="/repos/__missing_e2e_volume__",
                    message="volume inaccessible",
                )
            ]
        )
        client, *_ = build_client(issue_store=store)
        resp = client.get("/api/catalog/issues")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("issues", body)
        self.assertEqual(len(body["issues"]), 1)
        issue = body["issues"][0]
        self.assertEqual(issue["connection_name"], "local-missing")
        self.assertEqual(issue["path"], "/repos/__missing_e2e_volume__")
        self.assertIn("inaccessible", issue["message"].lower())

    def test_ut_i05_issues_response_never_contains_token(self) -> None:
        import os

        store = InMemoryCatalogIssueStore()
        store.replace(
            [
                LocalDiscoveryIssue(
                    connection_name="local",
                    path="/repos/x",
                    message="volume inaccessible",
                )
            ]
        )
        previous = os.environ.get("GITHUB_TOKEN")
        os.environ["GITHUB_TOKEN"] = _ENV_TOKEN_SENTINEL
        try:
            client, *_ = build_client(issue_store=store)
            resp = client.get("/api/catalog/issues")
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(_ENV_TOKEN_SENTINEL, resp.text)
        finally:
            if previous is None:
                os.environ.pop("GITHUB_TOKEN", None)
            else:
                os.environ["GITHUB_TOKEN"] = previous

    def test_ut_i06_default_without_store_returns_empty(self) -> None:
        client, *_ = build_client()
        resp = client.get("/api/catalog/issues")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["issues"], [])


if __name__ == "__main__":
    unittest.main()
