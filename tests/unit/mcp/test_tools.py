"""Unit — contracts das 5 tools / limiter / redaction (T17 / UT-T* / UT-L* / UT-V* / UT-C*)."""

from __future__ import annotations

import base64
import json
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, wait

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoOrigin, RepoState
from github_rag.concurrency.limiter import SemaphoreWorkerLimiter
from github_rag.mcp import DefaultMcpEvidenceServer
from github_rag.mcp.errors import McpToolError
from github_rag.mcp.tools import APPROVED_TOOL_NAMES, register_tools
from github_rag.query.errors import (
    QueryRepositoryNotFoundError,
    QueryValidationError,
)
from github_rag.query.types import DetailFields, FileContent, QueryHits
from mcp.server.fastmcp import FastMCP

from .helpers import (
    APPROVED_TOOLS,
    COMMIT,
    REPO,
    SECRET_TOKEN,
    CountingLimiter,
    SpyQueryService,
    build_server,
    full_exact_hits,
    invoke_tool,
    list_tool_names,
    seed_catalog,
)


class TestRegisterToolsContract(unittest.TestCase):
    """UT-T01 / UT-T02."""

    def test_ut_t01_register_tools_exactly_five(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        query = SpyQueryService(exact_hits=full_exact_hits())
        limiter = SemaphoreWorkerLimiter(capacity=2, pool="query")
        app = FastMCP("unit-mcp")
        register_tools(app, catalog=catalog, query=query, query_limiter=limiter)
        names = list_tool_names(app)
        self.assertEqual(names, set(APPROVED_TOOLS))
        self.assertEqual(names, set(APPROVED_TOOL_NAMES))

    def test_ut_t02_no_ask_codebase(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        server, _, _, _ = build_server(catalog=catalog)
        names = list_tool_names(server.build())
        self.assertNotIn("ask_codebase", names)
        self.assertEqual(len(names), 5)


class TestToolDelegation(unittest.TestCase):
    """UT-T03..T10."""

    def test_ut_t03_search_code_maps_detail_fields(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        server, query, _, _ = build_server(catalog=catalog)
        app = server.build()
        invoke_tool(
            app,
            "search_code",
            {
                "pattern": "authenticate",
                "repo_key": REPO,
                "include_path": True,
            },
        )
        self.assertEqual(len(query.exact_requests), 1)
        self.assertEqual(
            query.exact_requests[0].details,
            DetailFields(path=True),
        )

    def test_ut_t04_semantic_always_reformulate_false(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        server, query, _, _ = build_server(catalog=catalog)
        app = server.build()
        payload = invoke_tool(
            app,
            "semantic_search",
            {"query": "login", "repo_key": REPO, "include_snippet": True},
        )
        self.assertEqual(len(query.semantic_requests), 1)
        self.assertIs(query.semantic_requests[0].reformulate, False)
        for hit in payload["hits"]:
            self.assertNotIn("chunk_metadata_summary", hit)

    def test_ut_t05_list_repos_uses_catalog_not_query(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        server, query, _, _ = build_server(catalog=catalog)
        payload = invoke_tool(server.build(), "list_repos")
        self.assertGreaterEqual(len(payload["repos"]), 1)
        self.assertEqual(query.call_count, 0)
        self.assertEqual(query.exact_requests, [])
        self.assertEqual(query.semantic_requests, [])

    def test_ut_t06_empty_catalog_success(self) -> None:
        catalog = InMemoryCatalogRepository()
        server, _, _, _ = build_server(catalog=catalog)
        payload = invoke_tool(server.build(), "list_repos")
        self.assertEqual(payload, {"repos": []})

    def test_ut_t07_list_repos_omits_secrets_and_inactive(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog, repo_identifier=REPO)
        seed_catalog(
            catalog,
            repo_identifier="local/demo",
            origin=RepoOrigin.LOCAL,
            local_path="/secret/mount/repo",
            last_processed_commit=None,
        )
        seed_catalog(
            catalog,
            repo_identifier="gone/repo",
            last_processed_commit=None,
            active=False,
        )
        server, _, _, _ = build_server(catalog=catalog)
        payload = invoke_tool(server.build(), "list_repos")
        blob = json.dumps(payload)
        self.assertNotIn(SECRET_TOKEN, blob)
        keys = {r["repo_key"] for r in payload["repos"]}
        self.assertIn(REPO, keys)
        self.assertIn("local/demo", keys)
        self.assertNotIn("gone/repo", keys)
        for repo in payload["repos"]:
            self.assertNotIn("local_path", repo)
            self.assertNotIn("token", repo)
            self.assertIn(repo["state"], {s.value for s in RepoState})
            for required in (
                "repo_key",
                "repository_id",
                "origin",
                "connection_name",
                "state",
                "last_processed_commit",
                "current_main_commit",
            ):
                self.assertIn(required, repo)

    def test_ut_t08_read_file_utf8_and_base64(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        utf = SpyQueryService(file_content=FileContent(content=b"hello\n"))
        server, _, _, _ = build_server(catalog=catalog, query=utf)
        payload = invoke_tool(
            server.build(), "read_file", {"path": "a.txt", "repo_key": REPO}
        )
        self.assertEqual(payload["content"], "hello\n")
        self.assertEqual(payload["content_encoding"], "utf-8")

        binary = SpyQueryService(file_content=FileContent(content=b"\xff\xfe"))
        server2, _, _, _ = build_server(catalog=catalog, query=binary)
        payload2 = invoke_tool(
            server2.build(), "read_file", {"path": "b.bin", "repo_key": REPO}
        )
        self.assertEqual(payload2["content_encoding"], "base64")
        self.assertNotIn("content", payload2)
        self.assertEqual(
            payload2["content_base64"],
            base64.b64encode(b"\xff\xfe").decode("ascii"),
        )

    def test_ut_t09_query_failure_typed_no_empty_hits_fallback(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        failing = SpyQueryService(
            fail=QueryRepositoryNotFoundError,
            fail_message=f"not found token={SECRET_TOKEN}",
        )
        server, _, _, _ = build_server(catalog=catalog, query=failing)
        with self.assertRaises(Exception) as ctx:
            invoke_tool(
                server.build(),
                "search_code",
                {"pattern": "x", "repo_key": REPO},
            )
        exc = ctx.exception
        self.assertIsInstance(exc, McpToolError)
        self.assertNotIn(SECRET_TOKEN, str(exc))
        self.assertNotEqual(getattr(exc, "kind", None), None)
        # não é sucesso silencioso com hits vazios
        self.assertFalse(isinstance(exc, dict))

    def test_ut_t10_token_absent_from_success_and_error(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        server, _, _, _ = build_server(catalog=catalog)
        ok = invoke_tool(server.build(), "list_repos")
        self.assertNotIn(SECRET_TOKEN, json.dumps(ok))

        failing = SpyQueryService(
            fail=QueryRepositoryNotFoundError,
            fail_message=f"missing repo token={SECRET_TOKEN}",
        )
        server2, _, _, _ = build_server(catalog=catalog, query=failing)
        with self.assertRaises(Exception) as ctx:
            invoke_tool(
                server2.build(),
                "search_code",
                {"pattern": "x", "repo_key": "missing/repo"},
            )
        exc = ctx.exception
        self.assertNotIn(SECRET_TOKEN, str(exc))
        self.assertNotIn(SECRET_TOKEN, repr(exc))
        if isinstance(exc, McpToolError):
            self.assertNotIn(SECRET_TOKEN, exc.message)


class TestLimiterAcquire(unittest.TestCase):
    """UT-L01..L04 / UT-C01."""

    def test_ut_l01_acquire_on_every_tool(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        inner = SemaphoreWorkerLimiter(capacity=4, pool="query")
        limiter = CountingLimiter(inner)
        server, _, _, _ = build_server(
            catalog=catalog, capacity=4, query_limiter=limiter
        )
        app = server.build()
        invoke_tool(app, "list_repos")
        invoke_tool(app, "search_code", {"pattern": "x", "repo_key": REPO})
        invoke_tool(app, "semantic_search", {"query": "q", "repo_key": REPO})
        invoke_tool(app, "read_file", {"path": "a.py", "repo_key": REPO})
        invoke_tool(app, "list_tree", {"repo_key": REPO})
        self.assertEqual(limiter.acquire_count, 5)
        self.assertEqual(limiter.pool, "query")

    def test_ut_l02_capacity_one_search_waits(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        release_first = threading.Event()
        first_entered = threading.Event()
        second_entered = threading.Event()
        entered = 0
        lock = threading.Lock()

        def on_enter() -> None:
            nonlocal entered
            with lock:
                entered += 1
                n = entered
            if n == 1:
                first_entered.set()
                release_first.wait(timeout=5.0)
            else:
                second_entered.set()

        query = SpyQueryService(exact_hits=full_exact_hits(), on_enter=on_enter)
        server, _, _, _ = build_server(catalog=catalog, query=query, capacity=1)
        app = server.build()

        def call() -> None:
            invoke_tool(app, "search_code", {"pattern": "x", "repo_key": REPO})

        t1 = threading.Thread(target=call)
        t2 = threading.Thread(target=call)
        t1.start()
        self.assertTrue(first_entered.wait(timeout=2.0))
        t2.start()
        time.sleep(0.05)
        self.assertFalse(second_entered.is_set())
        release_first.set()
        t1.join(timeout=2.0)
        t2.join(timeout=2.0)
        self.assertTrue(second_entered.is_set())

    def test_ut_l03_capacity_one_list_repos_waits(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        release_first = threading.Event()
        first_entered = threading.Event()
        second_entered = threading.Event()
        entered = 0
        lock = threading.Lock()

        class _BlockingCatalog:
            def __init__(self, inner: InMemoryCatalogRepository) -> None:
                self._inner = inner

            def list_active_catalog(self):
                nonlocal entered
                with lock:
                    entered += 1
                    n = entered
                if n == 1:
                    first_entered.set()
                    release_first.wait(timeout=5.0)
                else:
                    second_entered.set()
                return self._inner.list_active_catalog()

            def __getattr__(self, name: str):
                return getattr(self._inner, name)

        server, _, _, _ = build_server(
            catalog=_BlockingCatalog(catalog),  # type: ignore[arg-type]
            capacity=1,
        )
        app = server.build()

        def call() -> None:
            invoke_tool(app, "list_repos")

        t1 = threading.Thread(target=call)
        t2 = threading.Thread(target=call)
        t1.start()
        self.assertTrue(first_entered.wait(timeout=2.0))
        t2.start()
        time.sleep(0.05)
        self.assertFalse(second_entered.is_set())
        release_first.set()
        t1.join(timeout=2.0)
        t2.join(timeout=2.0)
        self.assertTrue(second_entered.is_set())

    def test_ut_l04_query_pool_not_index(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        inner = SemaphoreWorkerLimiter(capacity=2, pool="query")
        limiter = CountingLimiter(inner, pool="query")
        server = DefaultMcpEvidenceServer(
            catalog=catalog,
            query=SpyQueryService(exact_hits=full_exact_hits()),
            query_limiter=limiter,
        )
        self.assertIs(server._query_limiter, limiter)
        self.assertEqual(limiter.pool, "query")
        self.assertNotEqual(limiter.pool, "index")
        app = server.build()
        invoke_tool(app, "search_code", {"pattern": "x", "repo_key": REPO})
        self.assertGreaterEqual(limiter.acquire_count, 1)
        self.assertEqual(limiter.pool, "query")

    def test_ut_c01_peak_never_exceeds_capacity(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        release = threading.Event()
        active = 0
        peak = 0
        lock = threading.Lock()

        def on_enter() -> None:
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            release.wait(timeout=5.0)
            with lock:
                active -= 1

        query = SpyQueryService(exact_hits=full_exact_hits(), on_enter=on_enter)
        server, _, _, _ = build_server(catalog=catalog, query=query, capacity=2)
        app = server.build()

        def work() -> None:
            invoke_tool(
                app, "search_code", {"pattern": "authenticate", "repo_key": REPO}
            )

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(work) for _ in range(4)]
            time.sleep(0.1)
            self.assertLessEqual(peak, 2)
            release.set()
            wait(futures)
            for future in futures:
                future.result()
        self.assertLessEqual(peak, 2)
        self.assertGreaterEqual(peak, 1)

    def test_ut_c02_identical_calls_idempotent_results(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        server, _, _, _ = build_server(catalog=catalog)
        app = server.build()
        args = {"pattern": "authenticate", "repo_key": REPO, "include_path": True}
        a = invoke_tool(app, "search_code", args)
        b = invoke_tool(app, "search_code", args)
        self.assertEqual(a, b)


class TestInvalidInputs(unittest.TestCase):
    """UT-V01 / UT-V02 — alinhado a I-T16-009 / I-T16-012."""

    def test_ut_v01_empty_pattern_returns_empty_hits(self) -> None:
        """Paridade T16: pattern vazio/whitespace → hits vazios (não erro)."""
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)

        class _EmptyAwareSpy(SpyQueryService):
            def search_exact(self, request):  # type: ignore[no-untyped-def]
                self.exact_requests.append(request)
                self._enter()
                self._maybe_fail()
                if not request.pattern.strip():
                    return QueryHits(hits=())
                hits = tuple(
                    self._project_hit(h, request.details)
                    for h in self._inner._exact_hits.hits
                )
                return QueryHits(hits=hits)

        query = _EmptyAwareSpy(exact_hits=full_exact_hits())
        server, _, _, _ = build_server(catalog=catalog, query=query)
        payload = invoke_tool(
            server.build(),
            "search_code",
            {"pattern": "   ", "repo_key": REPO},
        )
        self.assertEqual(payload, {"hits": []})

    def test_ut_v01b_empty_semantic_query_is_typed_error(self) -> None:
        """Paridade T16: query semântica vazia → validation (via map_query_error)."""
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)

        class _ValidatingSpy(SpyQueryService):
            def search_semantic(self, request):  # type: ignore[no-untyped-def]
                if not request.query.strip():
                    raise QueryValidationError("query empty")
                return super().search_semantic(request)

        query = _ValidatingSpy()
        server, _, _, _ = build_server(catalog=catalog, query=query)
        with self.assertRaises(McpToolError) as ctx:
            invoke_tool(
                server.build(),
                "semantic_search",
                {"query": "  ", "repo_key": REPO},
            )
        self.assertEqual(ctx.exception.kind, "validation")
        self.assertNotIn(SECRET_TOKEN, ctx.exception.message)

    def test_ut_v02_browse_without_scope_is_typed_error(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)

        class _ValidatingSpy(SpyQueryService):
            def read_file(self, request):  # type: ignore[no-untyped-def]
                if request.repo_key is None and request.repository_id is None:
                    raise QueryValidationError("scope required")
                return super().read_file(request)

            def list_tree(self, request):  # type: ignore[no-untyped-def]
                if request.repo_key is None and request.repository_id is None:
                    raise QueryValidationError("scope required")
                return super().list_tree(request)

        query = _ValidatingSpy(file_content=FileContent(content=b"x"))
        server, _, _, _ = build_server(catalog=catalog, query=query)
        app = server.build()
        with self.assertRaises(McpToolError) as ctx:
            invoke_tool(app, "read_file", {"path": "a.py"})
        self.assertEqual(ctx.exception.kind, "validation")
        with self.assertRaises(McpToolError) as ctx2:
            invoke_tool(app, "list_tree", {})
        self.assertEqual(ctx2.exception.kind, "validation")


if __name__ == "__main__":
    unittest.main()
