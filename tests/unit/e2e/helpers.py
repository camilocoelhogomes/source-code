"""Helpers compartilhados — unit e2e (T21)."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SECRET_TOKEN = "ghp_should_never_appear_in_e2e_unit_9f3a2"
GREEN_PATH_SUITE_MARKERS = (
    "health",
    "catalog_indexing",
    "ui",
    "ui_browser",
    "mcp",
    "negative",
)
E2E_CONFIG_FIXTURE = REPO_ROOT / "e2e" / "fixtures" / "config.e2e.json"
E2E_REPOS_FIXTURE = REPO_ROOT / "e2e" / "fixtures" / "repos"


class RecordingLauncher:
    """Double de E2eStackLauncher — registra up/down/wait_healthy."""

    def __init__(
        self,
        *,
        up_error: BaseException | None = None,
        healthy_error: BaseException | None = None,
        inject_host_env: bool = True,
    ) -> None:
        self.up_calls: list[Mapping[str, str]] = []
        self.down_calls = 0
        self.healthy_calls = 0
        self._up_error = up_error
        self._healthy_error = healthy_error
        self._inject_host_env = inject_host_env
        self.order: list[str] = []

    def up(self, env: Mapping[str, str] | None = None, **_kwargs: Any) -> None:
        self.order.append("up")
        merged = dict(env or {})
        if self._inject_host_env:
            merged.setdefault("HOST_CONFIG", str(E2E_CONFIG_FIXTURE))
            merged.setdefault("HOST_REPOS", str(E2E_REPOS_FIXTURE))
        self.up_calls.append(merged)
        if self._up_error is not None:
            raise self._up_error

    def wait_healthy(self, *_a: Any, **_k: Any) -> None:
        self.order.append("wait_healthy")
        self.healthy_calls += 1
        if self._healthy_error is not None:
            raise self._healthy_error

    def down(self, *_a: Any, **_k: Any) -> None:
        self.order.append("down")
        self.down_calls += 1


class RecordingRobotRunner:
    """Double do CLI robot — registra invocações; retorna exit code."""

    def __init__(
        self,
        *,
        exit_code: int = 0,
        raise_on_call: BaseException | None = None,
    ) -> None:
        self.exit_code = exit_code
        self.raise_on_call = raise_on_call
        self.calls: list[dict[str, Any]] = []
        self.order_hook: list[str] | None = None

    def __call__(self, *args: Any, **kwargs: Any) -> int:
        if self.order_hook is not None:
            self.order_hook.append("robot")
        self.calls.append({"args": args, "kwargs": dict(kwargs)})
        if self.raise_on_call is not None:
            raise self.raise_on_call
        return self.exit_code


def import_e2e() -> Any:
    """Importa superfície pública github_rag.e2e (RED até implementação)."""
    import github_rag.e2e as e2e_pkg  # noqa: PLC0415

    return e2e_pkg


def suite_run(
    *,
    environ: MutableMapping[str, str],
    launcher: RecordingLauncher,
    robot_runner: RecordingRobotRunner | None = None,
    e2e_pkg: Any | None = None,
) -> int:
    """Constrói DefaultRobotMvpSuite com doubles e executa run()."""
    e2e_pkg = e2e_pkg or import_e2e()
    DefaultRobotMvpSuite = e2e_pkg.DefaultRobotMvpSuite
    robot_runner = robot_runner or RecordingRobotRunner(exit_code=0)
    robot_runner.order_hook = launcher.order
    suite = DefaultRobotMvpSuite(
        launcher=launcher,
        robot_runner=robot_runner,
        environ=environ,
        repo_root=REPO_ROOT,
    )
    return int(suite.run())


def hitl_env_with_token(token: str = SECRET_TOKEN) -> dict[str, str]:
    return {
        "GITHUB_ACTIONS": "false",
        "E2E_GITHUB_TOKEN": token,
    }


def robot_call_blob(call: dict[str, Any]) -> str:
    blob = " ".join(str(a) for a in call["args"])
    blob += " " + " ".join(f"{k}={v}" for k, v in call["kwargs"].items())
    exclude = call["kwargs"].get("exclude") or call["kwargs"].get("excludes")
    if exclude is not None:
        if isinstance(exclude, str):
            blob += " " + exclude
        else:
            blob += " " + " ".join(str(x) for x in exclude)
    return blob
