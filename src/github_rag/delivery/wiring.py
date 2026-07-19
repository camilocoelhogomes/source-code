"""Helpers de composition da entrega (T19).

Responsabilidade deste módulo
    Factories de adaptadores, wait PG, alembic e binds UI/MCP — sem domínio novo.

Motivo da separação
    Isola I/O de infra e wiring do orquestrador ``boot()`` (I-T19-008).
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

_LOG = logging.getLogger(__name__)

_ENV_DATABASE_URL = "DATABASE_URL"
_ENV_ZOEKT_URL = "ZOEKT_URL"
_ENV_QDRANT_URL = "QDRANT_URL"
_ENV_OPENAI_BASE_URL = "OPENAI_BASE_URL"
_DEFAULT_EMBED_MODEL = "nomic-embed-text"
_DEFAULT_EMBED_DIMS = 768


class DeliveryWiringError(Exception):
    """Falha tipada de wiring/infra de entrega sem vazar segredos."""


_ENV_APP_ROOT = "GITHUB_RAG_APP_ROOT"


def _resolve_delivery_root() -> Path:
    """Localiza a raiz de entrega (``alembic.ini`` + ``migrations/``).

    Responsabilidade
        Resolver o diretório de runtime da imagem/container ou checkout dev.

    Motivo da separação
        Com ``pip install .``, ``__file__`` fica em ``site-packages`` e
        ``parents[3]`` não aponta para ``/app``; override via env ou walk-up
        a partir de árvore de desenvolvimento.
    """
    override = os.environ.get(_ENV_APP_ROOT, "").strip()
    if override:
        root = Path(override).resolve()
        if (root / "alembic.ini").is_file() and (root / "migrations").is_dir():
            return root
        raise DeliveryWiringError("alembic.ini ausente no contexto de entrega")

    start = Path(__file__).resolve()
    for candidate in start.parents:
        if (candidate / "alembic.ini").is_file() and (
            candidate / "migrations"
        ).is_dir():
            return candidate
    raise DeliveryWiringError("alembic.ini ausente no contexto de entrega")


def _require_env(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name, "")
    if not isinstance(value, str) or not value.strip():
        raise DeliveryWiringError(f"{name} ausente ou vazia")
    return value.strip()


def wait_for_postgres(
    environ: Mapping[str, str],
    *,
    timeout_seconds: float = 60.0,
    interval_seconds: float = 1.0,
) -> None:
    """Aguarda PostgreSQL aceitar conexões (retry/backoff).

    Responsabilidade
        Bloquear o boot até PG ready ou timeout → falha tipada/segura.

    Motivo da separação
        Isola I/O de readiness do orquestrador ``boot()``; omitido quando
        ``skip_infra=True`` (I-T19-011). Não vaza ``DATABASE_URL`` completa.
    """
    database_url = _require_env(environ, _ENV_DATABASE_URL)
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            engine = create_engine(database_url, future=True, pool_pre_ping=True)
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
            finally:
                engine.dispose()
            return
        except DeliveryWiringError:
            raise
        except Exception:  # noqa: BLE001 — retry até timeout; sem URL na mensagem
            if time.monotonic() >= deadline:
                raise TimeoutError("postgres not ready") from None
            time.sleep(interval_seconds)


def run_alembic_upgrade(environ: Mapping[str, str]) -> None:
    """Executa ``alembic upgrade head`` com URL do ambiente.

    Responsabilidade
        Migrar schema do catálogo antes do wire de repositório.

    Motivo da separação
        Migração é preocupação de entrega/processo, não de domínio T03 runtime.
        Mensagens sem credenciais (design §7).
    """
    database_url = _require_env(environ, _ENV_DATABASE_URL)
    from alembic import command
    from alembic.config import Config

    repo_root = _resolve_delivery_root()
    ini_path = repo_root / "alembic.ini"

    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", database_url)
    previous = os.environ.get(_ENV_DATABASE_URL)
    try:
        os.environ[_ENV_DATABASE_URL] = database_url
        command.upgrade(cfg, "head")
    except DeliveryWiringError:
        raise
    except Exception as exc:  # noqa: BLE001 — normaliza sem credenciais
        raise DeliveryWiringError("falha ao executar alembic upgrade head") from exc
    finally:
        if previous is None:
            os.environ.pop(_ENV_DATABASE_URL, None)
        else:
            os.environ[_ENV_DATABASE_URL] = previous


def wire_catalog(environ: Mapping[str, str]) -> Any:
    """Constrói ``CatalogRepository`` (factory PG existente)."""
    from github_rag.catalog.postgres import create_postgres_catalog_repository

    return create_postgres_catalog_repository(environ)


def wire_catalog_sync(environ: Mapping[str, str], *, catalog: Any) -> Any:
    """Constrói ``CatalogSync`` + discoveries (GitHub/local)."""
    from github_rag.catalog.sync import CatalogSync
    from github_rag.sources.github.discovery import GitHubRepoDiscovery
    from github_rag.sources.local.discovery import LocalRepoDiscovery

    _ = environ  # frontier env reservada para clients futuros
    return CatalogSync(
        catalog=catalog,
        github_discovery=GitHubRepoDiscovery(),
        local_discovery=LocalRepoDiscovery(),
    )


def wire_indexing_stack(
    environ: Mapping[str, str],
    *,
    catalog: Any,
    settings: Any,
) -> tuple[Any, Any]:
    """Constrói ``(IndexingOrchestrator, StartupIndexReconcile)``."""
    from openai import OpenAI
    from qdrant_client import QdrantClient

    from github_rag.concurrency import create_index_limiter
    from github_rag.eligibility import PathspecFileEligibilityFilter
    from github_rag.index.chunk import TreeSitterContextualChunker
    from github_rag.index.metadata.config import SlmClientSettings
    from github_rag.index.metadata.openai_slm import OpenAICompatibleMetadataGenerator
    from github_rag.index.vector.embedder import OpenAICompatibleEmbedder
    from github_rag.index.vector.qdrant_store import QdrantVectorStore
    from github_rag.index.zoekt.index import ZoektExactCodeIndex
    from github_rag.indexing import DefaultFileRagPipeline, DefaultIndexingOrchestrator
    from github_rag.indexing.startup_reconcile import DefaultStartupIndexReconcile
    from github_rag.snapshot import DefaultMainSnapshotProvider

    zoekt_url = _require_env(environ, _ENV_ZOEKT_URL)
    qdrant_url = _require_env(environ, _ENV_QDRANT_URL)
    openai_base = _require_env(environ, _ENV_OPENAI_BASE_URL)
    _ = zoekt_url  # validado; ZoektExactCodeIndex.from_environ lê ZOEKT_*

    api_key = environ.get("OPENAI_API_KEY", "local").strip() or "local"
    slm_model = environ.get("SLM_MODEL", "qwen2.5-coder:3b").strip() or "qwen2.5-coder:3b"
    embed_model = (
        environ.get("EMBEDDING_MODEL", _DEFAULT_EMBED_MODEL).strip()
        or _DEFAULT_EMBED_MODEL
    )
    raw_dims = environ.get("EMBEDDING_DIMENSIONS", str(_DEFAULT_EMBED_DIMS)).strip()
    try:
        embed_dims = int(raw_dims) if raw_dims else _DEFAULT_EMBED_DIMS
    except ValueError as exc:
        raise DeliveryWiringError("EMBEDDING_DIMENSIONS inválido") from exc

    github_token = environ.get("GITHUB_TOKEN")
    if isinstance(github_token, str):
        github_token = github_token.strip() or None
    else:
        github_token = None

    openai_client = OpenAI(base_url=openai_base, api_key=api_key)
    slm_settings = SlmClientSettings(
        base_url=openai_base, api_key=api_key, model=slm_model
    )
    metadata = OpenAICompatibleMetadataGenerator(
        client=openai_client, settings=slm_settings
    )
    embedder = OpenAICompatibleEmbedder(
        client=openai_client, model=embed_model, dimensions=embed_dims
    )
    vector_store = QdrantVectorStore(
        client=QdrantClient(url=qdrant_url),
        vector_size=embed_dims,
    )
    exact_index = ZoektExactCodeIndex.from_environ(environ)
    snapshot = DefaultMainSnapshotProvider()
    rag = DefaultFileRagPipeline(
        chunker=TreeSitterContextualChunker(),
        metadata_generator=metadata,
        embedder=embedder,
    )
    orchestrator = DefaultIndexingOrchestrator(
        catalog=catalog,
        snapshot=snapshot,
        eligibility=PathspecFileEligibilityFilter(),
        exact_index=exact_index,
        rag_pipeline=rag,
        vector_store=vector_store,
        limiter=create_index_limiter(settings),
        github_token=github_token,
    )
    reconcile = DefaultStartupIndexReconcile(
        catalog=catalog,
        snapshot=snapshot,
        orchestrator=orchestrator,
        github_token=github_token,
    )
    return orchestrator, reconcile


def wire_scheduler(
    environ: Mapping[str, str],
    *,
    catalog: Any,
    orchestrator: Any,
    settings: Any,
    reconcile: Any,
) -> Any:
    """Constrói ``DailyScheduler`` com preferência PG (ENG-004)."""
    from sqlalchemy.orm import sessionmaker

    from github_rag.schedule import DefaultDailyScheduler
    from github_rag.schedule.postgres import SqlAlchemyCronPreferenceStore

    _ = catalog
    database_url = _require_env(environ, _ENV_DATABASE_URL)
    engine = create_engine(database_url, future=True)
    session_factory = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    store = SqlAlchemyCronPreferenceStore(session_factory)
    return DefaultDailyScheduler(
        preference_store=store,
        reconcile=reconcile,
        orchestrator=orchestrator,
        default_cron=settings.index_cron,
    )


def wire_query_service(
    environ: Mapping[str, str],
    *,
    catalog: Any,
    settings: Any,
) -> Any:
    """Constrói ``QueryService`` + dependências de busca."""
    from openai import OpenAI
    from qdrant_client import QdrantClient

    from github_rag.index.vector.embedder import OpenAICompatibleEmbedder
    from github_rag.index.vector.qdrant_store import QdrantVectorStore
    from github_rag.index.zoekt.index import ZoektExactCodeIndex
    from github_rag.indexing.orchestrator import snapshot_source_for
    from github_rag.query.service import DefaultQueryService
    from github_rag.snapshot import DefaultMainSnapshotProvider

    _ = settings
    qdrant_url = _require_env(environ, _ENV_QDRANT_URL)
    openai_base = _require_env(environ, _ENV_OPENAI_BASE_URL)
    api_key = environ.get("OPENAI_API_KEY", "local").strip() or "local"
    embed_model = (
        environ.get("EMBEDDING_MODEL", _DEFAULT_EMBED_MODEL).strip()
        or _DEFAULT_EMBED_MODEL
    )
    raw_dims = environ.get("EMBEDDING_DIMENSIONS", str(_DEFAULT_EMBED_DIMS)).strip()
    try:
        embed_dims = int(raw_dims) if raw_dims else _DEFAULT_EMBED_DIMS
    except ValueError as exc:
        raise DeliveryWiringError("EMBEDDING_DIMENSIONS inválido") from exc

    github_token = environ.get("GITHUB_TOKEN")
    if isinstance(github_token, str):
        github_token = github_token.strip() or None
    else:
        github_token = None

    class _Resolver:
        def resolve(self, entry: Any) -> Any:
            return snapshot_source_for(entry, github_token=github_token)

    openai_client = OpenAI(base_url=openai_base, api_key=api_key)
    return DefaultQueryService(
        exact_index=ZoektExactCodeIndex.from_environ(environ),
        vector_store=QdrantVectorStore(
            client=QdrantClient(url=qdrant_url),
            vector_size=embed_dims,
        ),
        embedder=OpenAICompatibleEmbedder(
            client=openai_client, model=embed_model, dimensions=embed_dims
        ),
        snapshot=DefaultMainSnapshotProvider(),
        catalog=catalog,
        source_resolver=_Resolver(),
    )


def wire_ui_app(
    *,
    catalog: Any,
    orchestrator: Any,
    scheduler: Any,
    query: Any,
    issue_store: Any | None = None,
) -> Any:
    """``DefaultManagementUiApi(...).build()`` → FastAPI."""
    from github_rag.ui import DefaultManagementUiApi

    return DefaultManagementUiApi(
        catalog=catalog,
        orchestrator=orchestrator,
        scheduler=scheduler,
        query=query,
        drain_on_index=True,
        issue_store=issue_store,
    ).build()


def wire_mcp_server(
    *,
    catalog: Any,
    query: Any,
    query_limiter: Any,
) -> Any:
    """``DefaultMcpEvidenceServer(...).build()`` → FastMCP."""
    from github_rag.mcp import DefaultMcpEvidenceServer

    return DefaultMcpEvidenceServer(
        catalog=catalog,
        query=query,
        query_limiter=query_limiter,
    ).build()


def default_bind_ui(app: Any, environ: Mapping[str, str]) -> None:
    """Serve UI via uvicorn (``UI_HOST``/``UI_PORT``)."""
    import uvicorn

    host = environ.get("UI_HOST", "0.0.0.0").strip() or "0.0.0.0"
    raw_port = environ.get("UI_PORT", "8080").strip() or "8080"
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise DeliveryWiringError("UI_PORT inválido") from exc
    _LOG.info("delivery_surfaces_up ui_host=%s ui_port=%s", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")


def default_bind_mcp(mcp_app: Any, environ: Mapping[str, str]) -> None:
    """Inicia transporte MCP container (SSE/streamable HTTP)."""
    transport = environ.get("MCP_TRANSPORT", "sse").strip() or "sse"
    raw_port = environ.get("MCP_PORT", "8001").strip() or "8001"
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise DeliveryWiringError("MCP_PORT inválido") from exc
    settings = getattr(mcp_app, "settings", None)
    if settings is not None:
        if hasattr(settings, "port"):
            settings.port = port
        if hasattr(settings, "host"):
            settings.host = environ.get("MCP_HOST", "0.0.0.0")
    _LOG.info("delivery_surfaces_up mcp_transport=%s mcp_port=%s", transport, port)
    mcp_app.run(transport=transport)
