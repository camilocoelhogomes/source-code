"""Composition root e entrypoint de boot do container (T19).

Responsabilidade deste módulo
    ``DefaultContainerRuntime`` + ``run_container_boot`` — orquestração I-T19-005/006.

Motivo da separação
    Mantém ``ContainerRuntime`` como Protocol estável e concentra lifecycle
    (não domínio) numa classe testável (CD-01..04).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Mapping
from typing import Any

from github_rag.app.bootstrap import run_catalog_sync
from github_rag.concurrency import create_query_limiter
from github_rag.config import ConfigLoader
from github_rag.config.secrets import EnvironSecretResolver
from github_rag.delivery.health import register_health_routes
from github_rag.delivery.wiring import (
    default_bind_mcp,
    default_bind_ui,
    run_alembic_upgrade,
    wait_for_postgres,
    wire_catalog,
    wire_catalog_sync,
    wire_indexing_stack,
    wire_mcp_server,
    wire_query_service,
    wire_scheduler,
    wire_ui_app,
)
from github_rag.settings import load_settings

_LOG = logging.getLogger(__name__)


class DefaultContainerRuntime:
    """Implementação default do composition root de entrega.

    Responsabilidade
        Materializar I-T19-005/006 com deps keyword-only injetáveis; em
        produção compor adaptadores via ``wiring``; em testes aceitar doubles.

    Motivo da separação
        Mantém ``ContainerRuntime`` como Protocol estável e concentra a
        orquestração (não domínio) numa classe testável (CD-01..04).
    """

    def __init__(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        settings: Any | None = None,
        config: Any | None = None,
        config_loader: Any | None = None,
        catalog: Any | None = None,
        sync: Any | None = None,
        reconcile: Any | None = None,
        orchestrator: Any | None = None,
        scheduler: Any | None = None,
        ui: Any | None = None,
        mcp: Any | None = None,
        bind_ui: Callable[..., None] | None = None,
        bind_mcp: Callable[..., None] | None = None,
        skip_infra: bool = False,
    ) -> None:
        self._environ: Mapping[str, str] = os.environ if environ is None else environ
        self._settings = settings
        self._config = config
        self._config_loader = config_loader
        self._catalog = catalog
        self._sync = sync
        self._reconcile = reconcile
        self._orchestrator = orchestrator
        self._scheduler = scheduler
        self._ui = ui
        self._mcp = mcp
        self._bind_ui = bind_ui
        self._bind_mcp = bind_mcp
        self._skip_infra = skip_infra
        self._booted = False
        self._ui_ready = False
        self._mcp_ready = False
        self.ui_app: Any | None = None
        self.asgi_app: Any | None = None
        self._mcp_app: Any | None = None

    def boot(self) -> None:
        """Executa o boot ordenado até superfícies prontas ou falha fatal."""
        if self._booted:
            return

        stage = "start"
        try:
            _LOG.info("delivery_boot_start")

            stage = "settings"
            settings = (
                self._settings
                if self._settings is not None
                else load_settings(self._environ)
            )

            stage = "config"
            if self._config is not None:
                config = self._config
            else:
                loader = self._config_loader
                if loader is None:
                    loader = ConfigLoader(
                        secret_resolver=EnvironSecretResolver(self._environ)
                    )
                config = loader.load(settings.config_path)
            connection_count = len(getattr(config, "connections", {}) or {})
            _LOG.info(
                "delivery_config_loaded connection_count=%s", connection_count
            )

            if not self._skip_infra:
                stage = "migrate_wait"
                wait_for_postgres(self._environ)
                stage = "migrate_alembic"
                run_alembic_upgrade(self._environ)
                _LOG.info("delivery_migrations_ok")

            stage = "wire"
            self._ensure_wired(settings)

            stage = "sync"
            assert self._sync is not None
            run_catalog_sync(config, self._sync)
            _LOG.info("delivery_catalog_sync_ok")

            stage = "reconcile"
            assert self._reconcile is not None
            self._reconcile.run()
            _LOG.info("delivery_startup_reconcile_ok")

            stage = "scheduler"
            assert self._scheduler is not None
            self._scheduler.start()

            stage = "surfaces"
            self._materialize_surfaces()
            bind_ui = (
                self._bind_ui if self._bind_ui is not None else default_bind_ui
            )
            bind_mcp = (
                self._bind_mcp if self._bind_mcp is not None else default_bind_mcp
            )
            bind_ui(self.ui_app, self._environ)
            bind_mcp(self._mcp_app, self._environ)
            self._ui_ready = True
            self._mcp_ready = True
            _LOG.info("delivery_surfaces_up")

            self._booted = True
        except SystemExit:
            raise
        except BaseException as exc:
            _LOG.error(
                "delivery_boot_failed stage=%s error_type=%s",
                stage,
                type(exc).__name__,
            )
            raise SystemExit(1) from exc

    def _ensure_wired(self, settings: Any) -> None:
        """Materializa deps de produção apenas quando não injetadas."""

        def _catalog() -> Any:
            if self._catalog is None:
                self._catalog = wire_catalog(self._environ)
            return self._catalog

        if self._sync is None:
            self._sync = wire_catalog_sync(self._environ, catalog=_catalog())

        if self._orchestrator is None or self._reconcile is None:
            orchestrator, reconcile = wire_indexing_stack(
                self._environ, catalog=_catalog(), settings=settings
            )
            if self._orchestrator is None:
                self._orchestrator = orchestrator
            if self._reconcile is None:
                self._reconcile = reconcile

        if self._scheduler is None:
            assert self._orchestrator is not None
            assert self._reconcile is not None
            self._scheduler = wire_scheduler(
                self._environ,
                catalog=_catalog(),
                orchestrator=self._orchestrator,
                settings=settings,
                reconcile=self._reconcile,
            )

        # Superfícies de produção só quando binds default serão usados.
        if self._bind_ui is None or self._bind_mcp is None:
            query = wire_query_service(
                self._environ, catalog=_catalog(), settings=settings
            )
            assert self._orchestrator is not None
            assert self._scheduler is not None
            if self._ui is None:
                self._ui = wire_ui_app(
                    catalog=self._catalog,
                    orchestrator=self._orchestrator,
                    scheduler=self._scheduler,
                    query=query,
                )
            if self._mcp is None:
                self._mcp = wire_mcp_server(
                    catalog=self._catalog,
                    query=query,
                    query_limiter=create_query_limiter(settings),
                )

    def _materialize_surfaces(self) -> None:
        """Expõe ASGI com ``/healthz`` e prepara app MCP (I-T19-013)."""
        from fastapi import FastAPI

        if self._ui is not None:
            app = self._ui.build() if hasattr(self._ui, "build") else self._ui
        else:
            app = FastAPI()

        register_health_routes(
            app,
            get_state=lambda: {
                "ui_ready": self._ui_ready,
                "mcp_ready": self._mcp_ready,
            },
        )
        self.ui_app = app
        self.asgi_app = app

        if self._mcp is not None:
            self._mcp_app = (
                self._mcp.build() if hasattr(self._mcp, "build") else self._mcp
            )
        else:
            self._mcp_app = None


def run_container_boot(environ: Mapping[str, str] | None = None) -> None:
    """Entrypoint de módulo do container.

    Responsabilidade
        Instanciar ``DefaultContainerRuntime(environ=environ)`` (wiring de
        produção) e chamar ``boot()``.

    Motivo da separação
        ``__main__`` e operadores chamam uma função estável sem conhecer a
        classe; testes CD-03 exercitam fail-fast do entrypoint (I-T19-003).

    Erros
        Propaga ``SystemExit(1)`` de ``boot()`` (I-T19-006).
    """
    DefaultContainerRuntime(environ=environ).boot()
