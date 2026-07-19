"""Helpers compartilhados — unit mcp (T17)."""

from __future__ import annotations

import asyncio
import ast
import json
import threading
from pathlib import Path
from typing import Any

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import CatalogEntry, RepoOrigin, RepoState
from github_rag.concurrency.limiter import SemaphoreWorkerLimiter
from github_rag.query.errors import QueryError
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

REPO = "acme/api"
COMMIT = "abc123"
SECRET_TOKEN = "ghp_should_never_appear_in_mcp_9f3a2"
MCP_PKG = Path(__file__).resolve().parents[3] / "src" / "github_rag" / "mcp"
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
        "fastmcp",
        "urllib",
        "urllib3",
    }
)


class SpyQueryService:
    """Spy sobre FakeQueryService: registra requests e aplica DetailFields."""

    def __init__(
        self,
        *,
        exact_hits: QueryHits | None = None,
        semantic_hits: QueryHits | None = None,
        file_content: FileContent | None = None,
        tree: TreeListing | None = None,
        fail: type[QueryError] | None = None,
        fail_message: str | None = None,
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
        self._on_enter = on_enter
        self.exact_requests: list[ExactSearchRequest] = []
        self.semantic_requests: list[SemanticSearchRequest] = []
        self.read_requests: list[ReadFileRequest] = []
        self.tree_requests: list[ListTreeRequest] = []
        self.call_count = 0

    def _enter(self) -> None:
        self.call_count += 1
        if self._on_enter is not None:
            self._on_enter()

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


class CountingLimiter:
    """WorkerLimiter instrumentado: conta acquires (pool query).

    ``SemaphoreWorkerLimiter`` não expõe atributo público ``pool`` — o label
    é passado explicitamente aqui para UT-L01/L04.
    """

    def __init__(
        self, inner: SemaphoreWorkerLimiter, *, pool: str = "query"
    ) -> None:
        self._inner = inner
        self.acquire_count = 0
        self.pool = pool

    @property
    def capacity(self) -> int:
        return self._inner.capacity

    def acquire(self) -> Any:
        self.acquire_count += 1
        return self._inner.acquire()


def full_exact_hits() -> QueryHits:
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


def full_semantic_hits() -> QueryHits:
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


def seed_catalog(
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


def make_catalog_entry(
    *,
    repo_identifier: str = REPO,
    origin: RepoOrigin = RepoOrigin.GITHUB,
    state: RepoState = RepoState.UP_TO_DATE,
    local_path: str | None = None,
    last_processed_commit: str | None = COMMIT,
    current_main_commit: str | None = COMMIT,
) -> CatalogEntry:
    return CatalogEntry(
        id=42,
        connection_name="gh",
        origin=origin,
        repo_identifier=repo_identifier,
        state=state,
        active=True,
        row_version=1,
        github_org="acme" if origin == RepoOrigin.GITHUB else None,
        local_path=local_path,
        last_processed_commit=last_processed_commit,
        current_main_commit=current_main_commit,
    )


def parse_tool_payload(result: Any) -> Any:
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


def invoke_tool(app: Any, name: str, arguments: dict[str, Any] | None = None) -> Any:
    arguments = arguments or {}
    call = getattr(app, "call_tool", None)
    if call is None and hasattr(app, "_tool_manager"):
        call = app._tool_manager.call_tool
    if call is None:
        raise AssertionError("FastMCP sem call_tool — implementação T17 incompleta")
    result = call(name, arguments)
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    if isinstance(result, tuple) and result:
        result = result[0]
    content = getattr(result, "content", result)
    return parse_tool_payload(content)


def list_tool_names(app: Any) -> set[str]:
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


def collect_imports(package_dir: Path) -> set[str]:
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


def build_server(
    *,
    catalog: Any | None = None,
    query: SpyQueryService | None = None,
    capacity: int = 4,
    query_limiter: Any | None = None,
):
    from github_rag.mcp import DefaultMcpEvidenceServer

    catalog = catalog or InMemoryCatalogRepository()
    query = query or SpyQueryService(
        exact_hits=full_exact_hits(),
        semantic_hits=full_semantic_hits(),
        file_content=FileContent(
            content=b"secret = 1\n",
            repository=REPO,
            path="src/auth.py",
            commit=COMMIT,
        ),
        tree=TreeListing(
            paths=("src/a.py", "src/b.py"),
            repository=REPO,
            commit=COMMIT,
        ),
    )
    limiter = query_limiter or SemaphoreWorkerLimiter(capacity=capacity, pool="query")
    server = DefaultMcpEvidenceServer(
        catalog=catalog,
        query=query,
        query_limiter=limiter,
    )
    return server, query, catalog, limiter
