"""Rotas FastAPI da Management UI (T18).

Responsabilidade deste módulo
    Registrar endpoints ``/api/*`` e montar static ``web/``.

Motivo da separação
    Separar wiring HTTP da composition ``DefaultManagementUiApi`` (I-T18-010).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from github_rag.catalog.errors import RepositoryNotFoundError
from github_rag.catalog.repository import CatalogRepository
from github_rag.indexing.ports import IndexingOrchestrator
from github_rag.query.errors import QueryError
from github_rag.query.ports import QueryService
from github_rag.query.types import (
    DetailFields,
    ExactSearchRequest,
    SemanticSearchRequest,
)
from github_rag.schedule.errors import InvalidCronExpressionError
from github_rag.schedule.ports import DailyScheduler
from github_rag.ui.errors import http_status_for, safe_detail
from github_rag.ui.issues import CatalogIssueStore, InMemoryCatalogIssueStore
from github_rag.ui.serialize import (
    execution_to_view,
    issue_to_view,
    repo_to_detail,
    repo_to_view,
)

_UI_DETAILS = DetailFields(
    repository=True, path=True, commit=True, snippet=True
)


class IndexRequest(BaseModel):
    repository_ids: list[int] = Field(..., min_length=1)


class CronBody(BaseModel):
    cron: str = Field(..., min_length=1)


class ExactSearchBody(BaseModel):
    pattern: str = Field(..., min_length=1)
    repo_key: str | None = None
    repository_id: int | None = None
    path_prefix: str | None = None
    max_matches: int | None = None


class SemanticSearchBody(BaseModel):
    query: str = Field(..., min_length=1)
    repo_key: str | None = None
    repository_id: int | None = None
    limit: int = 10
    reformulate: bool = False


def create_app(
    *,
    catalog: CatalogRepository,
    orchestrator: IndexingOrchestrator,
    scheduler: DailyScheduler,
    query: QueryService,
    drain_on_index: bool,
    web_root: Path,
    issue_store: CatalogIssueStore | None = None,
) -> FastAPI:
    """Monta FastAPI com rotas da Management UI.

    Responsabilidade: único lugar de registro de rotas /api.
    Motivo da separação: ``DefaultManagementUiApi.build`` só compõe deps.
    """
    app = FastAPI(title="github-rag management UI", version="0.1.0")
    issues: CatalogIssueStore = (
        issue_store if issue_store is not None else InMemoryCatalogIssueStore()
    )

    def _http(exc: BaseException) -> HTTPException:
        return HTTPException(
            status_code=http_status_for(exc), detail=safe_detail(exc)
        )

    def _hits_payload(hits) -> dict:
        return {
            "hits": [
                {
                    "kind": h.kind,
                    "score": h.score,
                    "repository": h.repository,
                    "path": h.path,
                    "commit": h.commit,
                    "snippet": h.snippet,
                    "line_number": h.line_number,
                    "chunk_metadata_summary": h.chunk_metadata_summary,
                }
                for h in hits.hits
            ]
        }

    @app.get("/api/repos")
    def list_repos() -> dict:
        repos = [repo_to_view(e) for e in catalog.list_active_catalog()]
        return {"repos": repos}

    @app.get("/api/catalog/issues")
    def list_catalog_issues() -> dict:
        """Issues locais do último sync (BDD-018 / T25)."""
        return {
            "issues": [issue_to_view(i) for i in issues.list_issues()]
        }

    @app.get("/api/repos/{repository_id}")
    def get_repo(repository_id: int) -> dict:
        try:
            entry = catalog.get_repository(repository_id)
        except RepositoryNotFoundError as exc:
            raise _http(exc) from exc
        files = ()
        if entry.current_execution_id is not None:
            files = catalog.list_file_progress(entry.current_execution_id)
        return repo_to_detail(entry, files)

    @app.get("/api/repos/{repository_id}/executions")
    def list_executions(repository_id: int) -> dict:
        try:
            executions = catalog.list_executions(repository_id)
        except RepositoryNotFoundError as exc:
            raise _http(exc) from exc
        return {
            "executions": [execution_to_view(e) for e in executions]
        }

    @app.post("/api/repos/index", status_code=202)
    def index_repos(body: IndexRequest) -> dict:
        for rid in body.repository_ids:
            try:
                catalog.get_repository(rid)
            except RepositoryNotFoundError as exc:
                raise _http(exc) from exc
        orchestrator.enqueue(body.repository_ids)
        if drain_on_index:
            orchestrator.run_until_idle()
        repos = [
            repo_to_view(catalog.get_repository(rid))
            for rid in body.repository_ids
        ]
        return {"repos": repos}

    @app.get("/api/scheduler/cron")
    def get_cron() -> dict:
        return {"cron": scheduler.active_cron()}

    @app.put("/api/scheduler/cron")
    def put_cron(body: CronBody) -> dict:
        try:
            cron = scheduler.set_cron(body.cron)
        except InvalidCronExpressionError as exc:
            raise _http(exc) from exc
        return {"cron": cron}

    @app.post("/api/search/exact")
    def search_exact(body: ExactSearchBody) -> dict:
        request = ExactSearchRequest(
            pattern=body.pattern,
            details=_UI_DETAILS,
            repo_key=body.repo_key,
            repository_id=body.repository_id,
            path_prefix=body.path_prefix,
            max_matches=body.max_matches,
        )
        try:
            hits = query.search_exact(request)
        except QueryError as exc:
            raise _http(exc) from exc
        return _hits_payload(hits)

    @app.post("/api/search/semantic")
    def search_semantic(body: SemanticSearchBody) -> dict:
        request = SemanticSearchRequest(
            query=body.query,
            details=_UI_DETAILS,
            repo_key=body.repo_key,
            repository_id=body.repository_id,
            limit=body.limit,
            reformulate=body.reformulate,
        )
        try:
            hits = query.search_semantic(request)
        except QueryError as exc:
            raise _http(exc) from exc
        return _hits_payload(hits)

    @app.api_route(
        "/api/{full_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
        include_in_schema=False,
    )
    def api_not_found(full_path: str) -> None:
        """404 explícito para /api/* desconhecido (BDD-023).

        Evita que o StaticFiles montado em ``/`` responda 405 em POSTs
        inventados como ``/api/connections``.
        """
        raise HTTPException(status_code=404, detail="Not Found")

    if web_root.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=str(web_root), html=True),
            name="web",
        )

    return app
