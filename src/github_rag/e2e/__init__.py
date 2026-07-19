"""Pacote e2e — prova MVP Robot/Podman (T21).

Responsabilidade
    Orquestrar credenciais, stack Podman e suíte Robot sem domínio de produto.

Motivo da separação
    Handoff consumível por docs-cicd sem ownership dos composes T19.
"""

from __future__ import annotations

from github_rag.e2e import timeouts
from github_rag.e2e.credentials import E2eCredentialResolver, ResolvedE2eCredential
from github_rag.e2e.errors import E2eCredentialError, E2eStackError
from github_rag.e2e.launcher import PodmanE2eStackLauncher
from github_rag.e2e.paths import (
    COMPOSE_DEV,
    COMPOSE_E2E,
    E2E_CONFIG_FIXTURE,
    E2E_REPOS_FIXTURE,
    ROBOT_ROOT,
)
from github_rag.e2e.ports import E2eStackLauncher, RobotCliRunner, RobotMvpSuite
from github_rag.e2e.suite import DefaultRobotMvpSuite, run_mvp_e2e

__all__ = [
    "E2eStackLauncher",
    "RobotMvpSuite",
    "PodmanE2eStackLauncher",
    "DefaultRobotMvpSuite",
    "RobotCliRunner",
    "E2eCredentialResolver",
    "ResolvedE2eCredential",
    "E2eCredentialError",
    "E2eStackError",
    "run_mvp_e2e",
    "COMPOSE_DEV",
    "COMPOSE_E2E",
    "ROBOT_ROOT",
    "E2E_CONFIG_FIXTURE",
    "E2E_REPOS_FIXTURE",
    "timeouts",
]
