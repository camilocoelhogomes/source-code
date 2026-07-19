"""
BDD executável — T17-mcp-evidence-server.

Valida BDD-011..015 e BDD-024 na superfície MCP com fakes
(sem Cursor/Zoekt/Qdrant reais).

Execução:
    python -m pytest tests/bdd/test_mcp_evidence_server.py -q
"""

from __future__ import annotations

import ast
import asyncio
import base64
import json
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoOrigin, RepoState
from github_rag.concurrency.limiter import SemaphoreWorkerLimiter
from github_rag.query.errors import QueryError, QueryRepositoryNotFoundError
from github_rag.query.fake import FakeQueryService
from github_rag.query.types import (
    DetailFields,
    ExactSearchRequest,
    FileContent,
    ListTreeRequest,
    QueryHit,
    QueryHits,
    ReadFileRequest,
    SemanticSearchRequest,
    TreeListing,
)

# Símbolos futuros da superfície T17 — devem falhar (ImportError/AttributeError)
# até a implementação existir.
from github_rag.mcp import DefaultMcpEvidenceServer  # noqa: F401
from github_rag.mcp.errors import McpToolError  # noqa: F401

REPO = "acme/api"
COMMIT = "abc123"
SECRET_TOKEN = "ghp_should_never_appear_in_mcp_9f3a2"
MCP_PKG = Path(__file__).resolve().parents[2] / "src" / "github_rag" / "mcp"
APPROVED_TOOLS = frozenset(
    {
        "list_repos",
        "search_code",
        "semantic_search",
        "read_file",
        "list_tree",
    }
)
FORBIDDEN_IMPORTS = frozenset(
    {
        "qdrant_client",
        "openai",
        "httpx",
        "requests",
        "github",
        "git",
        "fastmcp",  # pacote Prefect standalone — proibido
        "urllib",
        "urllib3",
    }
)
NARRATIVE_KEYS = frozenset(
    {
        "answer",
        "explanation",
        "narrative",
        "summary",
        "assistant_message",
        "prose",
    }
)


class SpyQueryService:
    """Spy sobre FakeQueryService: registra requests, aplica DetailFields, bloqueio."""

    def __init__(
        self,
        *,
        exact_hits: QueryHits | None = None,
        semantic_hits: QueryHits | None = None,
        file_content: FileContent | None = None,
        tree: TreeListing | None = None,
        fail: type[QueryError] | None = None,
        fail_message: str | None = None,
        block_until: threading.Event | None = None,
        on_enter: Any = None,
    ) -> None:
        self._inner = FakeQueryService(
            exact_hits=exact_hits,
            semantic_hits=semantic_hits,
            file_content=file_content,
            tree=tree,
            fail=fail,
        )
        self._fail = fail
        self._fail_message = fail_message or (
            f"fake failure token={SECRET_TOKEN}" if fail else None
        )
        self._block_until = block_until
        self._on_enter = on_enter
        self.exact_requests: list[ExactSearchRequest] = []
        self.semantic_requests: list[SemanticSearchRequest] = []
        self.read_requests: list[ReadFileRequest] = []
        self.tree_requests: list[ListTreeRequest] = []

    def _enter(self) -> None:
        if self._on_enter is not None:
            self._on_enter()
        if self._block_until is not None:
            self._block_until.wait(timeout=5.0)

    def _maybe_fail(self) -> None:
        if self._fail is not None:
            raise self._fail(self._fail_message or "fake query service failure")

    @staticmethod
    def _project_hit(hit: QueryHit, details: DetailFields) -> QueryHit:
        return QueryHit(
            kind=hit.kind,
            score=hit.score,
            repository=hit.repository if details.repository else None,
            path=hit.path if details.path else None,
            commit=hit.commit if details.commit else None,
            snippet=hit.snippet if details.snippet else None,
            chunk_metadata_summary=hit.chunk_metadata_summary,
            line_number=hit.line_number,
        )

    def search_exact(self, request: ExactSearchRequest) -> QueryHits:
        self.exact_requests.append(request)
        self._enter()
        self._maybe_fail()
        hits = tuple(
            self._project_hit(h, request.details) for h in self._inner._exact_hits.hits
        )
        return QueryHits(hits=hits)

    def search_semantic(self, request: SemanticSearchRequest) -> QueryHits:
        self.semantic_requests.append(request)
        self._enter()
        self._maybe_fail()
        hits = tuple(
            self._project_hit(h, request.details)
            for h in self._inner._semantic_hits.hits
        )
        return QueryHits(hits=hits)

    def read_file(self, request: ReadFileRequest) -> FileContent:
        self.read_requests.append(request)
        self._enter()
        self._maybe_fail()
        fc = self._inner._file_content
        d = request.details
        return FileContent(
            content=fc.content,
            repository=fc.repository if d.repository else None,
            path=fc.path if d.path else None,
            commit=fc.commit if d.commit else None,
        )

    def list_tree(self, request: ListTreeRequest) -> TreeListing:
        self.tree_requests.append(request)
        self._enter()
        self._maybe_fail()
        tree = self._inner._tree
        d = request.details
        return TreeListing(
            paths=tree.paths,
            repository=tree.repository if d.repository else None,
            commit=tree.commit if d.commit else None,
        )


def _full_exact_hits() -> QueryHits:
    return QueryHits(
        hits=(
            QueryHit(
                kind="exact",
                score=None,
                repository=REPO,
                path="src/auth.py",
                commit=COMMIT,
                snippet="def authenticate():\n    return True\n",
                line_number=1,
            ),
        )
    )


def _full_semantic_hits() -> QueryHits:
    return QueryHits(
        hits=(
            QueryHit(
                kind="semantic",
                score=0.91,
                repository=REPO,
                path="src/auth.py",
                commit=COMMIT,
                snippet="login flow",
                chunk_metadata_summary="should-not-appear-in-mcp",
                line_number=None,
            ),
        )
    )


def _seed_catalog(
    catalog: InMemoryCatalogRepository,
    *,
    repo_identifier: str = REPO,
    origin: RepoOrigin = RepoOrigin.GITHUB,
    local_path: str | None = None,
    last_processed_commit: str | None = COMMIT,
    active: bool = True,
) -> int:
    entry = catalog.upsert_repository(
        connection_name="gh",
        origin=origin,
        repo_identifier=repo_identifier,
        github_org="acme" if origin == RepoOrigin.GITHUB else None,
        local_path=local_path,
    )
    if last_processed_commit is not None:
        entry = catalog.mark_queued(entry.id)
        entry = catalog.mark_indexing(entry.id)
        entry = catalog.mark_updated(entry.id, last_processed_commit)
    if not active:
        entry = catalog.deactivate_repository(entry.id)
    return entry.id


def _build_server(
    *,
    catalog: InMemoryCatalogRepository | None = None,
    query: SpyQueryService | None = None,
    capacity: int = 4,
) -> tuple[Any, SpyQueryService, InMemoryCatalogRepository, SemaphoreWorkerLimiter]:
    catalog = catalog or InMemoryCatalogRepository()
    query = query or SpyQueryService(
        exact_hits=_full_exact_hits(),
        semantic_hits=_full_semantic_hits(),
        file_content=FileContent(
            content=b"secret = 1\n",
            repository=REPO,
            path="src/auth.py",
            commit=COMMIT,
        ),
        tree=TreeListing(
            paths=("src/a.py", "src/b.py", "docs/readme.md"),
            repository=REPO,
            commit=COMMIT,
        ),
    )
    limiter = SemaphoreWorkerLimiter(capacity=capacity, pool="query")
    server = DefaultMcpEvidenceServer(
        catalog=catalog,
        query=query,
        query_limiter=limiter,
    )
    return server, query, catalog, limiter


def _parse_tool_payload(result: Any) -> Any:
    """Normaliza retorno FastMCP (TextContent JSON / dict / str) → objeto Python."""
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        return json.loads(result)
    if isinstance(result, list):
        texts: list[str] = []
        for block in result:
            text = getattr(block, "text", None)
            if text is None and isinstance(block, dict):
                text = block.get("text")
            if text is not None:
                texts.append(text)
        if len(texts) == 1:
            try:
                return json.loads(texts[0])
            except json.JSONDecodeError:
                return texts[0]
        return texts
    text = getattr(result, "text", None)
    if text is not None:
        return json.loads(text)
    raise AssertionError(f"payload de tool não reconhecido: {type(result)!r}")


def _invoke_tool(app: Any, name: str, arguments: dict[str, Any] | None = None) -> Any:
    """Invoca tool registrada no FastMCP (bridge sync)."""
    arguments = arguments or {}
    call = getattr(app, "call_tool", None)
    if call is None and hasattr(app, "_tool_manager"):
        call = app._tool_manager.call_tool
    if call is None:
        raise AssertionError("FastMCP sem call_tool — implementação T17 incompleta")
    result = call(name, arguments)
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    # Algumas versões devolvem (content, meta) ou CallToolResult
    if isinstance(result, tuple) and result:
        result = result[0]
    content = getattr(result, "content", result)
    return _parse_tool_payload(content)


def _list_tool_names(app: Any) -> set[str]:
    list_fn = getattr(app, "list_tools", None)
    if list_fn is None and hasattr(app, "_tool_manager"):
        list_fn = app._tool_manager.list_tools
    if list_fn is None:
        raise AssertionError("FastMCP sem list_tools")
    tools = list_fn()
    if asyncio.iscoroutine(tools):
        tools = asyncio.run(tools)
    names: set[str] = set()
    for tool in tools:
        name = getattr(tool, "name", None)
        if name is None and isinstance(tool, dict):
            name = tool.get("name")
        if name is not None:
            names.add(name)
    return names


def _collect_imports(package_dir: Path) -> set[str]:
    found: set[str] = set()
    if not package_dir.is_dir():
        return found
    for path in package_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module.split(".")[0])
    return found


class TestMCP01FiveToolsEvidenceNoNarrative(unittest.TestCase):
    """MCP-01 / BDD-011."""

    def test_five_tools_return_evidence_without_slm(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        server, query, _, _ = _build_server(catalog=catalog)
        app = server.build()
        names = _list_tool_names(app)
        self.assertEqual(names, set(APPROVED_TOOLS))
        self.assertNotIn("ask_codebase", names)

        list_payload = _invoke_tool(app, "list_repos")
        self.assertIn("repos", list_payload)
        self.assertGreaterEqual(len(list_payload["repos"]), 1)

        exact_payload = _invoke_tool(
            app, "search_code", {"pattern": "authenticate", "repo_key": REPO}
        )
        self.assertIn("hits", exact_payload)
        self.assertGreaterEqual(len(exact_payload["hits"]), 1)

        semantic_payload = _invoke_tool(
            app, "semantic_search", {"query": "login", "repo_key": REPO}
        )
        self.assertIn("hits", semantic_payload)
        self.assertGreaterEqual(len(semantic_payload["hits"]), 1)

        file_payload = _invoke_tool(
            app, "read_file", {"path": "src/auth.py", "repo_key": REPO}
        )
        self.assertTrue(
            "content" in file_payload or "content_base64" in file_payload
        )

        tree_payload = _invoke_tool(app, "list_tree", {"repo_key": REPO})
        self.assertIn("paths", tree_payload)

        for payload in (
            list_payload,
            exact_payload,
            semantic_payload,
            file_payload,
            tree_payload,
        ):
            blob = json.dumps(payload)
            for key in NARRATIVE_KEYS:
                self.assertNotIn(f'"{key}"', blob)

        imports = _collect_imports(MCP_PKG)
        self.assertNotIn("openai", imports)
        src = "\n".join(
            p.read_text(encoding="utf-8") for p in MCP_PKG.rglob("*.py")
        )
        self.assertNotIn("MetadataGenerator", src)
        self.assertNotIn("QueryReformulator", src)
        self.assertEqual(len(query.semantic_requests), 1)


class TestMCP02DetailsOmitted(unittest.TestCase):
    """MCP-02 / BDD-012."""

    def test_optional_detail_keys_omitted_when_not_requested(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        server, query, _, _ = _build_server(catalog=catalog)
        app = server.build()

        exact_payload = _invoke_tool(
            app, "search_code", {"pattern": "authenticate", "repo_key": REPO}
        )
        semantic_payload = _invoke_tool(
            app, "semantic_search", {"query": "login", "repo_key": REPO}
        )
        for payload in (exact_payload, semantic_payload):
            for hit in payload["hits"]:
                self.assertIn(hit["kind"], {"exact", "semantic"})
                for key in ("repository", "path", "commit", "snippet"):
                    self.assertNotIn(key, hit)
                self.assertNotIn("repository", json.dumps(hit))

        self.assertEqual(query.exact_requests[-1].details, DetailFields())
        self.assertEqual(query.semantic_requests[-1].details, DetailFields())
        if exact_payload["hits"][0]["kind"] == "semantic":
            self.fail("exact tool should return exact hits")
        if "score" in semantic_payload["hits"][0]:
            self.assertIsInstance(semantic_payload["hits"][0]["score"], float)


class TestMCP03DetailsIncluded(unittest.TestCase):
    """MCP-03 / BDD-012."""

    def test_details_included_when_requested(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        server, query, _, _ = _build_server(catalog=catalog)
        app = server.build()
        flags = {
            "include_repository": True,
            "include_path": True,
            "include_commit": True,
            "include_snippet": True,
        }
        expected_details = DetailFields(
            repository=True, path=True, commit=True, snippet=True
        )
        exact_payload = _invoke_tool(
            app,
            "search_code",
            {"pattern": "authenticate", "repo_key": REPO, **flags},
        )
        hit = exact_payload["hits"][0]
        self.assertEqual(hit["repository"], REPO)
        self.assertEqual(hit["path"], "src/auth.py")
        self.assertEqual(hit["commit"], COMMIT)
        self.assertIn("authenticate", hit["snippet"])
        self.assertEqual(query.exact_requests[-1].details, expected_details)

        semantic_payload = _invoke_tool(
            app,
            "semantic_search",
            {"query": "login", "repo_key": REPO, **flags},
        )
        sem = semantic_payload["hits"][0]
        self.assertEqual(sem["kind"], "semantic")
        self.assertEqual(sem["repository"], REPO)
        self.assertEqual(sem["path"], "src/auth.py")
        self.assertEqual(sem["commit"], COMMIT)
        self.assertEqual(sem["snippet"], "login flow")
        self.assertEqual(query.semantic_requests[-1].details, expected_details)

        path_only = _invoke_tool(
            app,
            "search_code",
            {
                "pattern": "authenticate",
                "repo_key": REPO,
                "include_path": True,
            },
        )
        hit2 = path_only["hits"][0]
        self.assertEqual(hit2["path"], "src/auth.py")
        self.assertNotIn("repository", hit2)
        self.assertNotIn("commit", hit2)
        self.assertNotIn("snippet", hit2)


class TestMCP04Parallelism(unittest.TestCase):
    """MCP-04 / BDD-013."""

    def test_peak_never_exceeds_query_workers(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
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

        query = SpyQueryService(
            exact_hits=_full_exact_hits(),
            block_until=None,
            on_enter=on_enter,
        )
        # on_enter already blocks via release; avoid double-wait
        query._block_until = None
        server, _, _, limiter = _build_server(
            catalog=catalog, query=query, capacity=2
        )
        self.assertEqual(limiter.capacity, 2)
        self.assertIsInstance(limiter, SemaphoreWorkerLimiter)
        app = server.build()

        def work() -> None:
            _invoke_tool(
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

    def test_excess_waits_for_capacity(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
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

        query = SpyQueryService(exact_hits=_full_exact_hits(), on_enter=on_enter)
        server, _, _, _ = _build_server(catalog=catalog, query=query, capacity=1)
        app = server.build()

        def call() -> None:
            _invoke_tool(
                app, "search_code", {"pattern": "x", "repo_key": REPO}
            )

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

    def test_list_repos_also_respects_query_limiter(self) -> None:
        """D-T17-006: list_repos também consome slot do pool query."""
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        release_first = threading.Event()
        first_entered = threading.Event()
        second_entered = threading.Event()
        entered = 0
        lock = threading.Lock()

        class _BlockingCatalog:
            def __init__(self, inner: InMemoryCatalogRepository) -> None:
                self._inner = inner

            def list_active_catalog(self) -> Any:
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

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

        server, _, _, _ = _build_server(
            catalog=_BlockingCatalog(catalog),  # type: ignore[arg-type]
            capacity=1,
        )
        app = server.build()

        def call() -> None:
            _invoke_tool(app, "list_repos")

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


class TestMCP05TokenAbsent(unittest.TestCase):
    """MCP-05 / BDD-014."""

    def test_token_absent_from_success_and_errors(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        server, _, _, _ = _build_server(catalog=catalog)
        app = server.build()
        ok = _invoke_tool(app, "list_repos")
        self.assertNotIn(SECRET_TOKEN, json.dumps(ok))

        failing = SpyQueryService(
            fail=QueryRepositoryNotFoundError,
            fail_message=f"missing repo token={SECRET_TOKEN}",
        )
        server2, _, _, _ = _build_server(catalog=catalog, query=failing)
        app2 = server2.build()
        with self.assertRaises(Exception) as ctx:
            _invoke_tool(
                app2, "search_code", {"pattern": "x", "repo_key": "missing/repo"}
            )
        exc = ctx.exception
        self.assertNotIn(SECRET_TOKEN, str(exc))
        self.assertNotIn(SECRET_TOKEN, repr(exc))
        if isinstance(exc, McpToolError):
            self.assertNotIn(SECRET_TOKEN, getattr(exc, "message", str(exc)))


class TestMCP06ToolsListableAndUsable(unittest.TestCase):
    """MCP-06 / BDD-015."""

    def test_tools_listable_and_callable(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        server, _, _, _ = _build_server(catalog=catalog)
        self.assertTrue(callable(server.run))
        app = server.build()
        names = _list_tool_names(app)
        self.assertEqual(names, set(APPROVED_TOOLS))
        for name, args in (
            ("list_repos", {}),
            ("search_code", {"pattern": "authenticate", "repo_key": REPO}),
            ("semantic_search", {"query": "login", "repo_key": REPO}),
            ("read_file", {"path": "src/auth.py", "repo_key": REPO}),
            ("list_tree", {"repo_key": REPO}),
        ):
            payload = _invoke_tool(app, name, args)
            self.assertIsInstance(payload, dict)


class TestMCP07OfficialMcpSdk(unittest.TestCase):
    """MCP-07 / BDD-024."""

    def test_uses_official_mcp_fastmcp(self) -> None:
        import mcp
        from mcp.server.fastmcp import FastMCP

        self.assertIsNotNone(mcp)
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        server, _, _, _ = _build_server(catalog=catalog)
        app = server.build()
        self.assertIsInstance(app, FastMCP)
        imports = _collect_imports(MCP_PKG)
        self.assertIn("mcp", imports)
        self.assertNotIn("fastmcp", imports)
        for forbidden in FORBIDDEN_IMPORTS - {"fastmcp"}:
            self.assertNotIn(forbidden, imports)


class TestMCP08NoAskCodebase(unittest.TestCase):
    """MCP-08."""

    def test_closed_tool_set(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        server, _, _, _ = _build_server(catalog=catalog)
        names = _list_tool_names(server.build())
        self.assertEqual(len(names), 5)
        self.assertNotIn("ask_codebase", names)
        self.assertEqual(names, set(APPROVED_TOOLS))


class TestMCP09SemanticReformulateFalse(unittest.TestCase):
    """MCP-09 / BR-011 / D-T17-009."""

    def test_semantic_always_reformulate_false_and_no_chunk_summary(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        server, query, _, _ = _build_server(catalog=catalog)
        app = server.build()
        payload = _invoke_tool(
            app,
            "semantic_search",
            {
                "query": "login",
                "repo_key": REPO,
                "include_snippet": True,
            },
        )
        self.assertEqual(len(query.semantic_requests), 1)
        self.assertIs(query.semantic_requests[0].reformulate, False)
        for hit in payload["hits"]:
            self.assertNotIn("chunk_metadata_summary", hit)


class TestMCP10ListReposNoLocalPathOrToken(unittest.TestCase):
    """MCP-10 / D-T17-008."""

    def test_list_repos_omits_local_path_and_inactive(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog, repo_identifier=REPO)
        _seed_catalog(
            catalog,
            repo_identifier="local/demo",
            origin=RepoOrigin.LOCAL,
            local_path="/secret/mount/repo",
            last_processed_commit=None,
        )
        inactive_id = _seed_catalog(
            catalog,
            repo_identifier="gone/repo",
            last_processed_commit=None,
            active=False,
        )
        self.assertIsNotNone(inactive_id)
        server, _, _, _ = _build_server(catalog=catalog)
        payload = _invoke_tool(server.build(), "list_repos")
        self.assertNotIn(SECRET_TOKEN, json.dumps(payload))
        keys = {r["repo_key"] for r in payload["repos"]}
        self.assertIn(REPO, keys)
        self.assertIn("local/demo", keys)
        self.assertNotIn("gone/repo", keys)
        for repo in payload["repos"]:
            self.assertNotIn("local_path", repo)
            self.assertNotIn("token", repo)
            self.assertIn(
                repo["state"],
                {s.value for s in RepoState},
            )
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


class TestMCP11ReadFileEncoding(unittest.TestCase):
    """MCP-11 / D-T17-007."""

    def test_utf8_and_base64_content(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        utf = SpyQueryService(
            file_content=FileContent(content=b"hello\n"),
        )
        server, _, _, _ = _build_server(catalog=catalog, query=utf)
        payload = _invoke_tool(
            server.build(),
            "read_file",
            {"path": "a.txt", "repo_key": REPO},
        )
        self.assertEqual(payload["content"], "hello\n")
        self.assertEqual(payload["content_encoding"], "utf-8")

        binary = SpyQueryService(
            file_content=FileContent(content=b"\xff\xfe"),
        )
        server2, _, _, _ = _build_server(catalog=catalog, query=binary)
        payload2 = _invoke_tool(
            server2.build(),
            "read_file",
            {"path": "b.bin", "repo_key": REPO},
        )
        self.assertEqual(payload2["content_encoding"], "base64")
        self.assertNotIn("content", payload2)
        self.assertEqual(
            payload2["content_base64"],
            base64.b64encode(b"\xff\xfe").decode("ascii"),
        )


class TestMCP12ErrorsAndEmptyList(unittest.TestCase):
    """MCP-12."""

    def test_empty_catalog_is_success(self) -> None:
        catalog = InMemoryCatalogRepository()
        server, _, _, _ = _build_server(catalog=catalog)
        payload = _invoke_tool(server.build(), "list_repos")
        self.assertEqual(payload.get("repos"), [])

    def test_query_failure_is_typed_without_empty_hits_fallback(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        failing = SpyQueryService(
            fail=QueryRepositoryNotFoundError,
            fail_message=f"not found token={SECRET_TOKEN}",
        )
        server, _, _, _ = _build_server(catalog=catalog, query=failing)
        with self.assertRaises(Exception) as ctx:
            _invoke_tool(
                server.build(),
                "search_code",
                {"pattern": "x", "repo_key": REPO},
            )
        exc = ctx.exception
        self.assertNotIn(SECRET_TOKEN, str(exc))
        # Falha tipada: McpToolError (quando implementação existir) ou não é dict de hits
        if not isinstance(exc, McpToolError):
            self.assertFalse(isinstance(exc, dict))


if __name__ == "__main__":
    unittest.main()
