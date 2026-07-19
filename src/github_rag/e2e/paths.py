"""Paths canônicos do e2e (T21).

Responsabilidade deste módulo
    Âncora única para compose, fixtures e ROBOT_ROOT.

Motivo da separação
    Constantes testáveis sem I/O de stack; evita hardcode de cwd CI vs local.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

COMPOSE_E2E_NAME: str = "docker-compose.e2e.yml"
COMPOSE_DEV_NAME: str = "docker-compose.dev.yml"
ROBOT_SUITE_DIRNAME: str = "e2e/robot"
E2E_CONFIG_FIXTURE_REL: str = "e2e/fixtures/config.e2e.json"
E2E_REPOS_FIXTURE_REL: str = "e2e/fixtures/repos"
E2E_RESULTS_DIRNAME: str = "e2e/results"


def resolve_repo_root(start: Path | None = None) -> Path:
    """Localiza a raiz do repo (presença de docker-compose.e2e.yml + pyproject).

    Responsabilidade
        Fornecer âncora única para COMPOSE_E2E / fixtures / ROBOT_ROOT.

    Motivo da separação
        Evita hardcode de cwd do processo CI vs operador local.
    """
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / COMPOSE_E2E_NAME).is_file() and (
            candidate / "pyproject.toml"
        ).is_file():
            return candidate
    raise FileNotFoundError(
        f"repo root with {COMPOSE_E2E_NAME} and pyproject.toml not found "
        f"from {current}"
    )


_REPO_ROOT = resolve_repo_root(Path(__file__).resolve())

COMPOSE_E2E: Path = _REPO_ROOT / COMPOSE_E2E_NAME
COMPOSE_DEV: Path = _REPO_ROOT / COMPOSE_DEV_NAME
ROBOT_ROOT: Path = _REPO_ROOT / ROBOT_SUITE_DIRNAME
E2E_CONFIG_FIXTURE: Path = _REPO_ROOT / E2E_CONFIG_FIXTURE_REL
E2E_REPOS_FIXTURE: Path = _REPO_ROOT / E2E_REPOS_FIXTURE_REL
E2E_RESULTS_DIR: Path = _REPO_ROOT / E2E_RESULTS_DIRNAME


def resolve_robot_executable() -> str:
    """Resolve o CLI ``robot`` co-localizado ao Python ativo (``.venv/bin``).

    Responsabilidade
        Garantir que ``python -m github_rag.e2e`` invoque Robot do extra
        ``[e2e]`` sem depender de ``PATH`` do shell.

    Motivo da separação
        Launcher e suite compartilham a mesma regra; testável sem subprocess
        real.
    """
    venv_robot = Path(sys.executable).parent / "robot"
    if venv_robot.is_file():
        return str(venv_robot)
    prefix_robot = Path(sys.prefix) / "bin" / "robot"
    if prefix_robot.is_file():
        return str(prefix_robot)
    found = shutil.which("robot")
    if found:
        return found
    return "robot"
