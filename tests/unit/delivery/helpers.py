"""Helpers compartilhados — unit delivery (T19)."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
DELIVERY_PKG = REPO_ROOT / "src" / "github_rag" / "delivery"
DOCKERFILE = REPO_ROOT / "Dockerfile"
COMPOSE = REPO_ROOT / "docker-compose.yml"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
PYPROJECT = REPO_ROOT / "pyproject.toml"
SECRET_TOKEN = "ghp_should_never_appear_in_delivery_unit_9f3a2"

DEC015_RUNTIME_PACKAGES = (
    "sqlalchemy",
    "alembic",
    "psycopg",
    "apscheduler",
    "PyGithub",
    "GitPython",
    "pathspec",
    "tree-sitter",
    "qdrant-client",
    "openai",
    "mcp",
    "fastapi",
    "uvicorn",
)

DEC015_TREE_SITTER_GRAMMARS = (
    "tree-sitter-python",
    "tree-sitter-java",
    "tree-sitter-javascript",
    "tree-sitter-typescript",
    "tree-sitter-markdown",
    "tree-sitter-yaml",
    "tree-sitter-json",
    "tree-sitter-xml",
    "tree-sitter-toml",
)

FORBIDDEN_IN_PORTS = frozenset(
    {
        "fastapi",
        "uvicorn",
        "qdrant_client",
        "openai",
        "github",
        "git",
        "httpx",
        "requests",
        "mcp",
    }
)


class RecordingSync:
    """Double de CatalogSync / alvo de run_catalog_sync."""

    def __init__(
        self,
        *,
        on_sync: Callable[[Any], None] | None = None,
        fail: BaseException | None = None,
    ) -> None:
        self.calls: list[Any] = []
        self._on_sync = on_sync
        self._fail = fail

    def sync(self, config: Any) -> Any:
        if self._on_sync is not None:
            self._on_sync(config)
        self.calls.append(config)
        if self._fail is not None:
            raise self._fail

        class _Result:
            active: tuple[Any, ...] = ()
            deactivated: tuple[Any, ...] = ()

        return _Result()


class RecordingReconcile:
    def __init__(self, *, on_run: Callable[[], None] | None = None) -> None:
        self.calls = 0
        self._on_run = on_run

    def run(self) -> None:
        self.calls += 1
        if self._on_run is not None:
            self._on_run()


class RecordingScheduler:
    def __init__(self, *, on_start: Callable[[], None] | None = None) -> None:
        self.started = 0
        self._on_start = on_start

    def start(self) -> None:
        self.started += 1
        if self._on_start is not None:
            self._on_start()


class RecordingSurfaces:
    def __init__(self, *, on_bind: Callable[[str], None] | None = None) -> None:
        self.ui_bound = False
        self.mcp_bound = False
        self.bind_order: list[str] = []
        self._on_bind = on_bind

    def bind_ui(self, *_a: Any, **_k: Any) -> None:
        self.ui_bound = True
        self.bind_order.append("ui")
        if self._on_bind is not None:
            self._on_bind("ui")

    def bind_mcp(self, *_a: Any, **_k: Any) -> None:
        self.mcp_bound = True
        self.bind_order.append("mcp")
        if self._on_bind is not None:
            self._on_bind("mcp")


class BlockingOrchestrator:
    """Orchestrator cujo run_until_idle bloqueia — bind não deve esperar."""

    def __init__(self) -> None:
        self.idle_calls = 0
        self.enqueue_calls = 0

    def enqueue(self, *_a: Any, **_k: Any) -> None:
        self.enqueue_calls += 1

    def run_until_idle(self) -> None:
        self.idle_calls += 1
        raise AssertionError(
            "run_until_idle não deve bloquear o caminho de bind do boot"
        )


def minimal_valid_config_json() -> dict[str, Any]:
    return {
        "connections": {
            "github-microservices": {
                "type": "github",
                "token": {"env": "GITHUB_TOKEN"},
                "orgs": ["my-org"],
                "repos": ["my-org/microservice-*"],
                "revisions": {"branches": ["main"]},
            },
            "local-microservices": {
                "type": "git",
                "url": "file:///repos/*",
                "revisions": {"branches": ["main"]},
            },
        }
    }


def write_valid_config(directory: Path | None = None) -> Path:
    base = Path(directory) if directory is not None else Path(tempfile.mkdtemp())
    path = base / "config.json"
    path.write_text(json.dumps(minimal_valid_config_json()), encoding="utf-8")
    return path


def base_environ(*, config_path: Path | str | None = None) -> dict[str, str]:
    env: dict[str, str] = {
        "GITHUB_TOKEN": SECRET_TOKEN,
        "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/github_rag",
        "ZOEKT_URL": "http://zoekt:6070",
        "QDRANT_URL": "http://qdrant:6333",
        "OPENAI_BASE_URL": "http://slm:11434/v1",
        "UI_HOST": "127.0.0.1",
        "UI_PORT": "8080",
        "MCP_PORT": "8001",
        "MCP_TRANSPORT": "sse",
    }
    if config_path is not None:
        env["CONFIG_PATH"] = str(config_path)
    return env


@contextmanager
def patch_infra(
    *,
    wait_side_effect: Any = None,
    alembic_side_effect: Any = None,
) -> Iterator[tuple[mock.MagicMock, mock.MagicMock]]:
    """Patch wait/alembic em wiring e runtime (import style-agnostic)."""
    wait_kwargs: dict[str, Any] = {}
    alembic_kwargs: dict[str, Any] = {}
    if wait_side_effect is not None:
        wait_kwargs["side_effect"] = wait_side_effect
    if alembic_side_effect is not None:
        alembic_kwargs["side_effect"] = alembic_side_effect

    with (
        mock.patch(
            "github_rag.delivery.wiring.wait_for_postgres", **wait_kwargs
        ) as wait_wiring,
        mock.patch(
            "github_rag.delivery.runtime.wait_for_postgres",
            create=True,
            **wait_kwargs,
        ),
        mock.patch(
            "github_rag.delivery.wiring.run_alembic_upgrade", **alembic_kwargs
        ) as alembic_wiring,
        mock.patch(
            "github_rag.delivery.runtime.run_alembic_upgrade",
            create=True,
            **alembic_kwargs,
        ),
    ):
        yield wait_wiring, alembic_wiring


def build_runtime(
    *,
    config_path: Path | None = None,
    environ: Mapping[str, str] | None = None,
    sync: RecordingSync | None = None,
    reconcile: RecordingReconcile | None = None,
    scheduler: RecordingScheduler | None = None,
    surfaces: RecordingSurfaces | None = None,
    orchestrator: Any | None = None,
    skip_infra: bool = True,
) -> tuple[Any, RecordingSync, RecordingReconcile, RecordingScheduler, RecordingSurfaces]:
    from github_rag.delivery import DefaultContainerRuntime

    sync = sync or RecordingSync()
    reconcile = reconcile or RecordingReconcile()
    scheduler = scheduler or RecordingScheduler()
    surfaces = surfaces or RecordingSurfaces()
    env = base_environ(config_path=config_path)
    if environ:
        env.update(dict(environ))

    kwargs: dict[str, Any] = {
        "environ": env,
        "sync": sync,
        "reconcile": reconcile,
        "scheduler": scheduler,
        "bind_ui": surfaces.bind_ui,
        "bind_mcp": surfaces.bind_mcp,
        "skip_infra": skip_infra,
    }
    if orchestrator is not None:
        kwargs["orchestrator"] = orchestrator

    runtime = DefaultContainerRuntime(**kwargs)
    return runtime, sync, reconcile, scheduler, surfaces


def read_text(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"artefato de delivery ausente: {path}")
    return path.read_text(encoding="utf-8")
