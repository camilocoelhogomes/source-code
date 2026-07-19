"""Orquestração canônica da prova MVP Robot (T21).

Responsabilidade deste módulo
    Coordenar resolve → up → healthy → robot → down com exit codes estáveis.

Motivo da separação
    Entry único para operador/CI/docs-cicd; deps injetáveis nos testes.
"""

from __future__ import annotations

import logging
import os
import subprocess
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any

from github_rag.e2e.credentials import E2eCredentialResolver
from github_rag.e2e.errors import E2eCredentialError, E2eStackError
from github_rag.e2e.launcher import PodmanE2eStackLauncher
from github_rag.e2e.paths import (
    E2E_CONFIG_FIXTURE,
    E2E_REPOS_FIXTURE,
    E2E_RESULTS_DIR,
    ROBOT_ROOT,
    resolve_repo_root,
)
from github_rag.e2e.ports import E2eStackLauncher, RobotCliRunner

logger = logging.getLogger(__name__)

GREEN_PATH_SUITES: tuple[str, ...] = (
    "health",
    "catalog_indexing",
    "ui",
    "ui_browser",
    "mcp",
    "negative",
)


def _default_robot_runner(
    *,
    robot_root: Path,
    output_dir: Path,
) -> RobotCliRunner:
    def _run(*args: Any, **kwargs: Any) -> int:
        # Prefer explicit kwargs from suite; fall back to args for suite names
        exclude = kwargs.get("exclude") or kwargs.get("excludes") or "bdd015"
        if isinstance(exclude, (list, tuple)):
            exclude_tag = next(
                (str(x) for x in exclude if str(x).strip()), "bdd015"
            )
        else:
            exclude_tag = str(exclude).strip() or "bdd015"
        suites = kwargs.get("suites")
        if not suites:
            # Positional args may carry suite markers (not CLI flags)
            named = [str(a) for a in args if not str(a).startswith("-")]
            suites = named or list(GREEN_PATH_SUITES)
        output = Path(kwargs.get("outputdir") or output_dir)
        output.mkdir(parents=True, exist_ok=True)
        suite_paths = [str(robot_root / f"{name}.robot") for name in suites]
        cmd = [
            "robot",
            "--exclude",
            exclude_tag,
            "--outputdir",
            str(output),
            *suite_paths,
        ]
        # Only forward explicit CLI flags from args (never bare suite names —
        # those are already encoded as suite_paths; duplicating breaks Robot).
        for arg in args:
            text = str(arg)
            if text.startswith("-"):
                cmd.append(text)
        completed = subprocess.run(cmd, check=False)
        return int(completed.returncode)

    return _run


class DefaultRobotMvpSuite:
    """Implementação canônica de ``RobotMvpSuite`` (I-T21-003/009/013).

    Responsabilidade
        Orquestrar resolve → up → wait_healthy → robot → down (finally).

    Motivo da separação
        Entry estável; launcher e robot_runner substituíveis.
    """

    def __init__(
        self,
        *,
        launcher: E2eStackLauncher,
        robot_runner: RobotCliRunner | None = None,
        credential_resolver: E2eCredentialResolver | None = None,
        environ: Mapping[str, str] | MutableMapping[str, str] | None = None,
        repo_root: Path | None = None,
        output_dir: Path | None = None,
    ) -> None:
        self._launcher = launcher
        self._resolver = credential_resolver or E2eCredentialResolver()
        self._environ = environ
        self._repo_root = (
            repo_root.resolve()
            if repo_root is not None
            else resolve_repo_root()
        )
        self._robot_root = self._repo_root / "e2e" / "robot"
        if not self._robot_root.is_dir() and ROBOT_ROOT.is_dir():
            self._robot_root = ROBOT_ROOT
        self._output_dir = (
            output_dir
            if output_dir is not None
            else (self._repo_root / "e2e" / "results")
        )
        if output_dir is None and E2E_RESULTS_DIR.parent == self._repo_root / "e2e":
            self._output_dir = E2E_RESULTS_DIR
        self._robot_runner = robot_runner or _default_robot_runner(
            robot_root=self._robot_root,
            output_dir=self._output_dir,
        )

    def _env_map(self) -> Mapping[str, str]:
        if self._environ is not None:
            return self._environ
        return os.environ

    def run(self) -> int:
        attempted_up = False
        try:
            credential = self._resolver.resolve(environ=self._env_map())
            host_config = self._repo_root / "e2e" / "fixtures" / "config.e2e.json"
            host_repos = self._repo_root / "e2e" / "fixtures" / "repos"
            if not host_config.is_file() and E2E_CONFIG_FIXTURE.is_file():
                host_config = E2E_CONFIG_FIXTURE
                host_repos = E2E_REPOS_FIXTURE

            up_env: dict[str, str] = {
                "HOST_CONFIG": str(host_config.resolve()),
                "HOST_REPOS": str(host_repos.resolve()),
            }
            if credential.source == "E2E_GITHUB_TOKEN":
                up_env["E2E_GITHUB_TOKEN"] = credential.token
            else:
                up_env["GITHUB_TOKEN"] = credential.token

            attempted_up = True
            self._launcher.up(up_env)
            self._launcher.wait_healthy()
            code = int(
                self._robot_runner(
                    exclude="bdd015",
                    excludes=["bdd015"],
                    suites=list(GREEN_PATH_SUITES),
                    outputdir=str(self._output_dir),
                )
            )
            return code
        except E2eCredentialError as exc:
            logger.error("e2e credential failure: %s", exc)
            return 2
        except E2eStackError as exc:
            logger.error("e2e stack failure: %s", exc)
            return 3
        except Exception as exc:  # noqa: BLE001 — map unexpected to ≠0
            logger.error("e2e unexpected failure: %s", type(exc).__name__)
            return 1
        finally:
            if attempted_up:
                try:
                    self._launcher.down()
                except Exception:  # noqa: BLE001 — never mask suite exit
                    logger.exception("e2e stack down failed (best-effort)")


def run_mvp_e2e(
    *,
    launcher: E2eStackLauncher | None = None,
    environ: Mapping[str, str] | None = None,
) -> int:
    """Helper de módulo / entrypoint.

    Responsabilidade
        Atalho ``DefaultRobotMvpSuite(...).run()``.

    Motivo da separação
        ``__main__`` e scripts CI não duplicam wiring.
    """
    return DefaultRobotMvpSuite(
        launcher=launcher or PodmanE2eStackLauncher(),
        environ=environ,
    ).run()
