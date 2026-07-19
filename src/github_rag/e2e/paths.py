"""Paths canônicos do e2e (T21).

Responsabilidade deste módulo
    Âncora única para compose, fixtures e ROBOT_ROOT.

Motivo da separação
    Constantes testáveis sem I/O de stack; evita hardcode de cwd CI vs local.
"""

from __future__ import annotations

from pathlib import Path

COMPOSE_E2E_NAME: str = "docker-compose.e2e.yml"
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
ROBOT_ROOT: Path = _REPO_ROOT / ROBOT_SUITE_DIRNAME
E2E_CONFIG_FIXTURE: Path = _REPO_ROOT / E2E_CONFIG_FIXTURE_REL
E2E_REPOS_FIXTURE: Path = _REPO_ROOT / E2E_REPOS_FIXTURE_REL
E2E_RESULTS_DIR: Path = _REPO_ROOT / E2E_RESULTS_DIRNAME
