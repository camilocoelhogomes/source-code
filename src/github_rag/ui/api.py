"""Implementação ``DefaultManagementUiApi`` (T18).

Responsabilidade deste módulo
    Compor catálogo + orquestrador + scheduler + QueryService e montar FastAPI.

Motivo da separação
    Composition root da superfície UI; T19 só chama ``build()``.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from github_rag.catalog.repository import CatalogRepository
from github_rag.indexing.ports import IndexingOrchestrator
from github_rag.query.ports import QueryService
from github_rag.schedule.ports import DailyScheduler
from github_rag.ui.app import create_app


def default_web_root() -> Path:
    """Resolve ``web/`` na raiz do repositório.

    Responsabilidade: path default do frontend estático.
    Motivo da separação: evita string mágica no construtor.
    """
    # src/github_rag/ui/api.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3] / "web"


class DefaultManagementUiApi:
    """Composition default da Management UI (FastAPI + static).

    Responsabilidade
        Guardar deps injetáveis e expor ``build()`` → ``FastAPI``.

    Motivo da separação
        Testável com fakes; sem CRUD de conexões/token (I-T18-006).
    """

    def __init__(
        self,
        *,
        catalog: CatalogRepository,
        orchestrator: IndexingOrchestrator,
        scheduler: DailyScheduler,
        query: QueryService,
        drain_on_index: bool = True,
        web_root: Path | None = None,
    ) -> None:
        self._catalog = catalog
        self._orchestrator = orchestrator
        self._scheduler = scheduler
        self._query = query
        self._drain_on_index = drain_on_index
        self._web_root = web_root if web_root is not None else default_web_root()

    def build(self) -> FastAPI:
        """Monta a aplicação ASGI (I-T18-001).

        Responsabilidade: delegar a ``create_app`` com deps capturadas.
        Motivo da separação: composition ≠ registro de rotas.
        """
        return create_app(
            catalog=self._catalog,
            orchestrator=self._orchestrator,
            scheduler=self._scheduler,
            query=self._query,
            drain_on_index=self._drain_on_index,
            web_root=self._web_root,
        )
