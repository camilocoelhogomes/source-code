"""Registro das tools MCP aprovadas (T17).

Responsabilidade deste módulo
    Binding único nome MCP → handler para as 5 operações REQ-028.

Motivo da separação
    Isola decorators/SDK ``FastMCP`` do lifecycle ``build``/``run`` e da
    serialização (I-T17-003 / D-T17-003).
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from github_rag.catalog.repository import CatalogRepository
from github_rag.concurrency.limiter import WorkerLimiter
from github_rag.mcp.errors import map_query_error
from github_rag.mcp.serialize import (
    details_from_includes,
    file_to_dict,
    hit_to_dict,
    repo_entry_to_dict,
    tree_to_dict,
)
from github_rag.query.errors import QueryError
from github_rag.query.ports import QueryService
from github_rag.query.types import (
    ExactSearchRequest,
    ListTreeRequest,
    ReadFileRequest,
    SemanticSearchRequest,
)

APPROVED_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "list_repos",
        "search_code",
        "semantic_search",
        "read_file",
        "list_tree",
    }
)
"""Conjunto fechado de tools (I-T17-003).

Responsabilidade: literal de conformidade REQ-028 / MCP-08.
Motivo da separação: evita espalhar a lista nos testes e no server.
"""


def _run_query(fn: Any) -> Any:
    """Executa delegação QueryService mapeando erros tipados."""
    try:
        return fn()
    except QueryError as exc:
        raise map_query_error(exc) from None


def register_tools(
    app: FastMCP,
    *,
    catalog: CatalogRepository,
    query: QueryService,
    query_limiter: WorkerLimiter,
) -> None:
    """Registra as 5 tools aprovadas no ``FastMCP``.

    Responsabilidade
        Único ponto de binding nome MCP → handler (REQ-028). Cada handler
        adquire ``query_limiter`` antes da delegação (I-T17-006), mapeia
        ``include_*`` → ``DetailFields`` (I-T17-005) e nunca passa
        ``reformulate=True`` em semantic (I-T17-009).

    Motivo da separação
        Isola decorators/SDK do lifecycle ``build``/``run`` e da serialização.
    """
    query_svc = query

    @app.tool(name="list_repos")
    def list_repos() -> dict[str, Any]:
        """Lista repositórios ativos do catálogo (identidade e estado)."""
        with query_limiter.acquire():
            entries = catalog.list_active_catalog()
            return {"repos": [repo_entry_to_dict(entry) for entry in entries]}

    @app.tool(name="search_code")
    def search_code(
        pattern: str,
        repo_key: str | None = None,
        repository_id: int | None = None,
        path_prefix: str | None = None,
        max_matches: int | None = None,
        context_lines: int = 2,
        include_repository: bool = False,
        include_path: bool = False,
        include_commit: bool = False,
        include_snippet: bool = False,
    ) -> dict[str, Any]:
        """Busca exata de código; retorna hits de evidência estruturados."""
        details = details_from_includes(
            include_repository=include_repository,
            include_path=include_path,
            include_commit=include_commit,
            include_snippet=include_snippet,
        )
        request = ExactSearchRequest(
            pattern=pattern,
            details=details,
            repo_key=repo_key,
            repository_id=repository_id,
            path_prefix=path_prefix,
            max_matches=max_matches,
            context_lines=context_lines,
        )
        with query_limiter.acquire():
            hits = _run_query(lambda: query_svc.search_exact(request))
        return {"hits": [hit_to_dict(hit) for hit in hits.hits]}

    @app.tool(name="semantic_search")
    def semantic_search(
        query: str,
        repo_key: str | None = None,
        repository_id: int | None = None,
        limit: int = 10,
        include_repository: bool = False,
        include_path: bool = False,
        include_commit: bool = False,
        include_snippet: bool = False,
    ) -> dict[str, Any]:
        """Busca semântica; sempre sem reformulação; hits de evidência."""
        details = details_from_includes(
            include_repository=include_repository,
            include_path=include_path,
            include_commit=include_commit,
            include_snippet=include_snippet,
        )
        request = SemanticSearchRequest(
            query=query,
            details=details,
            repo_key=repo_key,
            repository_id=repository_id,
            limit=limit,
            reformulate=False,
        )
        with query_limiter.acquire():
            hits = _run_query(lambda: query_svc.search_semantic(request))
        return {"hits": [hit_to_dict(hit) for hit in hits.hits]}

    @app.tool(name="read_file")
    def read_file(
        path: str,
        repo_key: str | None = None,
        repository_id: int | None = None,
        commit_sha: str | None = None,
        include_repository: bool = False,
        include_path: bool = False,
        include_commit: bool = False,
    ) -> dict[str, Any]:
        """Lê arquivo no commit indexado (UTF-8 ou base64)."""
        details = details_from_includes(
            include_repository=include_repository,
            include_path=include_path,
            include_commit=include_commit,
            include_snippet=False,
        )
        request = ReadFileRequest(
            path=path,
            repo_key=repo_key,
            repository_id=repository_id,
            commit_sha=commit_sha,
            details=details,
        )
        with query_limiter.acquire():
            content = _run_query(lambda: query_svc.read_file(request))
        return file_to_dict(content)

    @app.tool(name="list_tree")
    def list_tree(
        repo_key: str | None = None,
        repository_id: int | None = None,
        commit_sha: str | None = None,
        path_prefix: str | None = None,
        include_repository: bool = False,
        include_commit: bool = False,
    ) -> dict[str, Any]:
        """Lista paths da árvore no commit indexado."""
        details = details_from_includes(
            include_repository=include_repository,
            include_path=False,
            include_commit=include_commit,
            include_snippet=False,
        )
        request = ListTreeRequest(
            repo_key=repo_key,
            repository_id=repository_id,
            commit_sha=commit_sha,
            path_prefix=path_prefix,
            details=details,
        )
        with query_limiter.acquire():
            tree = _run_query(lambda: query_svc.list_tree(request))
        return tree_to_dict(tree)
