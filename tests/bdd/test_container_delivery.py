"""
BDD executável — T19-container-delivery.

Valida BDD-020/021/022/024/025, ENG-011/009/006 e healthchecks/compose
via runtime com doubles + asserts de manifesto (sem docker build / Robot).

Cenários: CD-01..CD-11 — ver
    spec/features/github-etl-mcp-rag/tasks/T19-container-delivery/bdd.md

Execução:
    python -m pytest tests/bdd/test_container_delivery.py -q
"""

from __future__ import annotations

import json
import re
import tempfile
import tomllib
import unittest
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO_ROOT / "Dockerfile"
COMPOSE = REPO_ROOT / "docker-compose.yml"
COMPOSE_E2E = REPO_ROOT / "docker-compose.e2e.yml"
COMPOSE_DEV = REPO_ROOT / "docker-compose.dev.yml"
COMPOSE_FILES = (COMPOSE, COMPOSE_E2E, COMPOSE_DEV)
ENV_EXAMPLE = REPO_ROOT / ".env.example"
PYPROJECT = REPO_ROOT / "pyproject.toml"
SECRET_TOKEN = "ghp_should_never_appear_in_delivery_9f3a2"

_VENV_MOUNT_RE = re.compile(
    r"(COPY|ADD)\s+[^\n]*\.venv"
    r"|-\s*\./\.venv"
    r"|/\.venv:"
    r"|:\s*\.venv\b",
    re.I,
)

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

# Grammars pinadas no pyproject (BDD-024 / DEC-015) — pelo menos este conjunto.
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


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"artefato de delivery ausente: {path}")
    return path.read_text(encoding="utf-8")


def _pyproject_deps() -> list[str]:
    data = tomllib.loads(_read(PYPROJECT))
    deps = data.get("project", {}).get("dependencies", [])
    if not isinstance(deps, list) or not deps:
        raise AssertionError("[project].dependencies ausente ou vazio")
    return [str(d) for d in deps]


def _dep_name(spec: str) -> str:
    return re.split(r"[<>=!~;\[]", spec, maxsplit=1)[0].strip()


def _import_delivery_surface() -> tuple[Any, Any, Any]:
    """Importa símbolos públicos do composition root (red até T19)."""
    from github_rag.delivery import (  # noqa: PLC0415
        ContainerRuntime,
        DefaultContainerRuntime,
        run_container_boot,
    )

    return ContainerRuntime, DefaultContainerRuntime, run_container_boot


class RecordingSync:
    """Double de CatalogSync: registra chamadas e devolve resultado vazio."""

    def __init__(self) -> None:
        self.calls: list[Any] = []

    def sync(self, config: Any) -> Any:
        self.calls.append(config)

        class _Result:
            active: tuple[Any, ...] = ()
            deactivated: tuple[Any, ...] = ()

        return _Result()


class RecordingReconcile:
    """Double de StartupIndexReconcile."""

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
    """Registra bind de UI/MCP sem abrir portas reais."""

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


def _minimal_valid_config_json() -> dict[str, Any]:
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


def _boot_with_fakes(
    *,
    config_path: Path | None = None,
    environ: Mapping[str, str] | None = None,
    sync: RecordingSync | None = None,
    reconcile: RecordingReconcile | None = None,
    scheduler: RecordingScheduler | None = None,
    surfaces: RecordingSurfaces | None = None,
    skip_infra: bool = True,
) -> tuple[Any, RecordingSync, RecordingReconcile, RecordingScheduler, RecordingSurfaces]:
    """Constrói DefaultContainerRuntime com doubles (contrato design §4.3)."""
    _, DefaultContainerRuntime, _ = _import_delivery_surface()
    sync = sync or RecordingSync()
    reconcile = reconcile or RecordingReconcile()
    scheduler = scheduler or RecordingScheduler()
    surfaces = surfaces or RecordingSurfaces()

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
    if environ:
        env.update(dict(environ))

    runtime = DefaultContainerRuntime(
        environ=env,
        sync=sync,
        reconcile=reconcile,
        scheduler=scheduler,
        bind_ui=surfaces.bind_ui,
        bind_mcp=surfaces.bind_mcp,
        skip_infra=skip_infra,
    )
    return runtime, sync, reconcile, scheduler, surfaces


class TestCD01UiAndMcpAvailable(unittest.TestCase):
    """CD-01 / BDD-020 — UI e MCP disponíveis após boot."""

    def test_boot_exposes_ui_mcp_and_healthz(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            cfg.write_text(
                json.dumps(_minimal_valid_config_json()), encoding="utf-8"
            )
            runtime, sync, reconcile, scheduler, surfaces = _boot_with_fakes(
                config_path=cfg
            )
            runtime.boot()

            self.assertGreaterEqual(len(sync.calls), 1)
            self.assertEqual(reconcile.calls, 1)
            self.assertEqual(scheduler.started, 1)
            self.assertTrue(surfaces.ui_bound)
            self.assertTrue(surfaces.mcp_bound)

            app = getattr(runtime, "ui_app", None) or getattr(
                runtime, "asgi_app", None
            )
            self.assertIsNotNone(app, "runtime deve expor ui_app/asgi_app após boot")
            from fastapi.testclient import TestClient  # noqa: PLC0415

            client = TestClient(app)
            resp = client.get("/healthz")
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(body.get("status"), "ok")
            self.assertEqual(body.get("ui"), "ready")
            self.assertEqual(body.get("mcp"), "ready")
            blob = json.dumps(body)
            self.assertNotIn(SECRET_TOKEN, blob)
            self.assertNotIn("ghp_", blob)


class TestCD02ValidConfigSync(unittest.TestCase):
    """CD-02 / BDD-021 — config válida → conexões + sync."""

    def test_valid_config_loads_all_connections_and_syncs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            payload = _minimal_valid_config_json()
            cfg.write_text(json.dumps(payload), encoding="utf-8")
            runtime, sync, reconcile, _, _ = _boot_with_fakes(config_path=cfg)
            runtime.boot()

            self.assertEqual(len(sync.calls), 1)
            loaded = sync.calls[0]
            conn_map = loaded.connections
            self.assertEqual(
                set(conn_map.keys()),
                {"github-microservices", "local-microservices"},
            )
            self.assertEqual(reconcile.calls, 1)


class TestCD03InvalidConfigFailFast(unittest.TestCase):
    """CD-03 / BDD-022 — config inválida → exit 1 sem parcial."""

    def _assert_fail_fast_no_partial(
        self,
        *,
        environ: dict[str, str],
    ) -> SystemExit:
        """Boot com doubles injetados — prova ausência de sync/reconcile/bind."""
        _, DefaultContainerRuntime, _ = _import_delivery_surface()
        sync = RecordingSync()
        reconcile = RecordingReconcile()
        surfaces = RecordingSurfaces()
        runtime = DefaultContainerRuntime(
            environ=environ,
            sync=sync,
            reconcile=reconcile,
            bind_ui=surfaces.bind_ui,
            bind_mcp=surfaces.bind_mcp,
            skip_infra=True,
        )
        with self.assertRaises(SystemExit) as ctx:
            runtime.boot()
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(sync.calls, [])
        self.assertEqual(reconcile.calls, 0)
        self.assertFalse(surfaces.ui_bound)
        self.assertFalse(surfaces.mcp_bound)
        return ctx.exception

    def test_missing_config_path_exits_without_partial(self) -> None:
        self._assert_fail_fast_no_partial(
            environ={
                "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x",
                "GITHUB_TOKEN": SECRET_TOKEN,
            }
        )

    def test_blank_config_path_exits_without_partial(self) -> None:
        self._assert_fail_fast_no_partial(
            environ={
                "CONFIG_PATH": "   ",
                "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x",
                "GITHUB_TOKEN": SECRET_TOKEN,
            }
        )

    def test_invalid_json_exits_without_sync_or_bind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "bad.json"
            cfg.write_text("{not-json", encoding="utf-8")
            self._assert_fail_fast_no_partial(
                environ={
                    "CONFIG_PATH": str(cfg),
                    "GITHUB_TOKEN": SECRET_TOKEN,
                    "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x",
                }
            )

    def test_missing_config_file_exits_without_partial(self) -> None:
        self._assert_fail_fast_no_partial(
            environ={
                "CONFIG_PATH": "/no/such/config-delivery-bdd.json",
                "GITHUB_TOKEN": SECRET_TOKEN,
                "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x",
            }
        )

    def test_run_container_boot_missing_config_exits_one(self) -> None:
        """Entrypoint de módulo também falha com SystemExit(1) (D-T19-002/004)."""
        _, _, run_container_boot = _import_delivery_surface()
        with self.assertRaises(SystemExit) as ctx:
            run_container_boot(
                {
                    "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x",
                    "GITHUB_TOKEN": SECRET_TOKEN,
                }
            )
        self.assertEqual(ctx.exception.code, 1)

    def test_failure_message_does_not_leak_token(self) -> None:
        _, DefaultContainerRuntime, _ = _import_delivery_surface()
        env = {
            "CONFIG_PATH": "/no/such/config-delivery-bdd.json",
            "GITHUB_TOKEN": SECRET_TOKEN,
            "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x",
        }
        import io
        import logging
        from contextlib import redirect_stderr, redirect_stdout

        buf_out, buf_err = io.StringIO(), io.StringIO()
        log_buf = io.StringIO()
        handler = logging.StreamHandler(log_buf)
        logging.getLogger().addHandler(handler)
        try:
            with redirect_stdout(buf_out), redirect_stderr(buf_err):
                with self.assertRaises(SystemExit):
                    DefaultContainerRuntime(environ=env, skip_infra=True).boot()
        finally:
            logging.getLogger().removeHandler(handler)
        text = buf_out.getvalue() + buf_err.getvalue() + log_buf.getvalue()
        self.assertNotIn(SECRET_TOKEN, text)
        self.assertNotIn("ghp_", text)


class TestCD04StartupReconcileOrder(unittest.TestCase):
    """CD-04 / ENG-011 — ordem D-T19-003: sync → reconcile → scheduler → bind."""

    def test_reconcile_runs_once_after_sync_before_scheduler_and_bind(self) -> None:
        order: list[str] = []
        sync = RecordingSync()
        original_sync = sync.sync

        def tracked_sync(config: Any) -> Any:
            order.append("sync")
            return original_sync(config)

        sync.sync = tracked_sync  # type: ignore[method-assign]
        reconcile = RecordingReconcile(on_run=lambda: order.append("reconcile"))
        scheduler = RecordingScheduler(on_start=lambda: order.append("scheduler"))
        surfaces = RecordingSurfaces(on_bind=lambda name: order.append(f"bind_{name}"))

        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            cfg.write_text(
                json.dumps(_minimal_valid_config_json()), encoding="utf-8"
            )
            runtime, _, _, _, _ = _boot_with_fakes(
                config_path=cfg,
                sync=sync,
                reconcile=reconcile,
                scheduler=scheduler,
                surfaces=surfaces,
            )
            runtime.boot()

        self.assertEqual(reconcile.calls, 1)
        self.assertEqual(scheduler.started, 1)
        self.assertTrue(surfaces.ui_bound)
        self.assertTrue(surfaces.mcp_bound)
        for step in ("sync", "reconcile", "scheduler", "bind_ui", "bind_mcp"):
            self.assertIn(step, order)
        self.assertLess(order.index("sync"), order.index("reconcile"))
        self.assertLess(order.index("reconcile"), order.index("scheduler"))
        self.assertLess(order.index("scheduler"), order.index("bind_ui"))
        self.assertLess(order.index("scheduler"), order.index("bind_mcp"))


class TestCD05SdkManifest(unittest.TestCase):
    """CD-05 / BDD-024 — SDKs no pyproject + instalação na imagem."""

    def test_pyproject_declares_dec015_and_uvicorn(self) -> None:
        deps = _pyproject_deps()
        names = {_dep_name(d) for d in deps}
        missing = [p for p in DEC015_RUNTIME_PACKAGES if p not in names]
        self.assertEqual(
            missing,
            [],
            f"deps runtime ausentes no pyproject.toml: {missing}",
        )
        missing_grammars = [g for g in DEC015_TREE_SITTER_GRAMMARS if g not in names]
        self.assertEqual(
            missing_grammars,
            [],
            f"grammars tree-sitter ausentes no pyproject.toml: {missing_grammars}",
        )

    def test_dockerfile_pip_installs_project_with_git(self) -> None:
        text = _read(DOCKERFILE)
        self.assertRegex(
            text,
            re.compile(r"pip\s+install\b.{0,80}\.", re.I | re.S),
            "Dockerfile deve pip install o projeto (.) no build",
        )
        self.assertNotRegex(
            text,
            re.compile(r"pip\s+install\b.{0,40}\[dev\]", re.I),
            "imagem de entrega não deve instalar extras [dev]",
        )
        self.assertRegex(
            text,
            re.compile(r"\bgit\b", re.I),
            "Dockerfile deve instalar/binário git (GitPython / discovery)",
        )


class TestCD06NoHostVenv(unittest.TestCase):
    """CD-06 / ENG-009 — sem .venv do host."""

    def test_dockerfile_and_composes_do_not_use_host_venv(self) -> None:
        dockerfile = _read(DOCKERFILE)
        self.assertNotRegex(
            dockerfile,
            _VENV_MOUNT_RE,
            "Dockerfile não deve copiar/montar .venv do host",
        )
        for path in COMPOSE_FILES:
            text = _read(path)
            self.assertNotRegex(
                text,
                _VENV_MOUNT_RE,
                f"{path.name} não deve copiar/montar .venv do host",
            )


class TestCD07Amd64Documented(unittest.TestCase):
    """CD-07 / ENG-006 — linux/amd64 documentado."""

    def test_amd64_documented_in_delivery_artifacts(self) -> None:
        chunks: list[str] = []
        for path in (
            DOCKERFILE,
            COMPOSE,
            COMPOSE_E2E,
            COMPOSE_DEV,
            REPO_ROOT / "docs" / "runbook-local.md",
            REPO_ROOT / "README.md",
        ):
            if path.is_file():
                chunks.append(path.read_text(encoding="utf-8"))
        blob = "\n".join(chunks)
        self.assertTrue(
            re.search(r"linux/amd64|\bamd64\b", blob, re.I),
            "plataforma primária linux/amd64 deve estar documentada",
        )


class TestCD08ComposeHealthAndServices(unittest.TestCase):
    """CD-08 — healthchecks + serviços ENG-002 nos três composes."""

    def test_all_composes_services_and_healthcheck(self) -> None:
        for path in COMPOSE_FILES:
            text = _read(path)
            for svc in ("app", "postgres", "qdrant", "zoekt", "slm"):
                self.assertRegex(
                    text,
                    re.compile(rf"^\s*{svc}\s*:", re.M),
                    f"{path.name}: serviço compose ausente: {svc}",
                )
            self.assertRegex(
                text,
                re.compile(r"healthcheck\s*:", re.I),
                f"{path.name}: deve declarar healthcheck",
            )
            self.assertRegex(
                text,
                re.compile(r"/healthz", re.I),
                f"{path.name}: healthcheck deve referenciar /healthz",
            )
            self.assertRegex(
                text,
                re.compile(r"8001|MCP_PORT|mcp", re.I),
                f"{path.name}: deve expor/configurar superfície MCP",
            )


class TestCD09VolumesAndEnvExample(unittest.TestCase):
    """CD-09 / ENG-005 — volumes CONFIG_PATH + /repos."""

    def test_compose_volumes_and_env_example(self) -> None:
        for path in COMPOSE_FILES:
            compose = _read(path)
            self.assertRegex(
                compose,
                re.compile(r"CONFIG_PATH", re.I),
                f"{path.name}: deve injetar/documentar CONFIG_PATH",
            )
            self.assertRegex(
                compose,
                re.compile(r"/repos"),
                f"{path.name}: deve montar /repos para file:///repos/...",
            )
        env_ex = _read(ENV_EXAMPLE)
        for name in (
            "CONFIG_PATH",
            "GITHUB_TOKEN",
            "E2E_GITHUB_TOKEN",
            "INDEX_WORKERS",
            "QUERY_WORKERS",
            "INDEX_CRON",
        ):
            self.assertIn(name, env_ex)
        self.assertNotIn("ghp_", env_ex)
        self.assertNotRegex(
            env_ex,
            re.compile(r"GITHUB_TOKEN\s*=\s*\S{8,}"),
            ".env.example não deve conter token real",
        )


class TestCD10DeliveryEntrypoint(unittest.TestCase):
    """CD-10 — entrypoint python -m github_rag.delivery."""

    def test_dockerfile_cmd_and_public_exports(self) -> None:
        text = _read(DOCKERFILE)
        self.assertRegex(
            text,
            re.compile(
                r"python\s+-m\s+github_rag\.delivery",
                re.I,
            ),
            "CMD/ENTRYPOINT deve usar python -m github_rag.delivery",
        )
        ContainerRuntime, DefaultContainerRuntime, run_container_boot = (
            _import_delivery_surface()
        )
        self.assertTrue(callable(run_container_boot))
        self.assertTrue(callable(DefaultContainerRuntime))
        # Protocol / ABC deve existir para tipagem do composition root
        self.assertIsNotNone(ContainerRuntime)


class TestCD11ThreeComposesBdd025(unittest.TestCase):
    """CD-11 / BDD-025 — três composes com papéis D-T19-020."""

    def test_delivery_artifacts_exist_without_secrets(self) -> None:
        for path in (DOCKERFILE, *COMPOSE_FILES, ENV_EXAMPLE):
            self.assertTrue(path.is_file(), f"artefato ausente: {path.name}")
        env_ex = _read(ENV_EXAMPLE)
        self.assertNotIn("ghp_", env_ex)
        self.assertNotRegex(
            env_ex,
            re.compile(r"GITHUB_TOKEN\s*=\s*\S{8,}"),
        )

    def test_e2e_compose_isolated_no_src_mount(self) -> None:
        text = _read(COMPOSE_E2E)
        self.assertRegex(
            text,
            re.compile(r"^\s*name\s*:\s*github-rag-e2e\s*$", re.M),
        )
        self.assertRegex(text, re.compile(r"e2e_", re.I))
        self.assertRegex(
            text,
            re.compile(
                r"GITHUB_TOKEN\s*:\s*\$\{E2E_GITHUB_TOKEN:-\$\{GITHUB_TOKEN:-\}\}",
            ),
            "e2e deve mapear E2E_GITHUB_TOKEN→GITHUB_TOKEN (D-T19-020)",
        )
        self.assertNotRegex(
            text,
            re.compile(r"-\s*\./src\b|:\s*\./src\b"),
        )

    def test_dev_compose_src_mount_no_venv(self) -> None:
        text = _read(COMPOSE_DEV)
        self.assertRegex(
            text,
            re.compile(r"^\s*name\s*:\s*github-rag-dev\s*$", re.M),
        )
        self.assertRegex(text, re.compile(r"\./src\b"))
        self.assertNotRegex(text, _VENV_MOUNT_RE)

    def test_user_compose_does_not_mount_src(self) -> None:
        text = _read(COMPOSE)
        self.assertNotRegex(
            text,
            re.compile(r"-\s*\./src\b|:\s*\./src\b"),
        )


if __name__ == "__main__":
    unittest.main()
