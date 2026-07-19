"""Portas Protocol do pacote e2e (T21).

Responsabilidade deste módulo
    Congelar contratos ``E2eStackLauncher`` / ``RobotMvpSuite`` / ``RobotCliRunner``.

Motivo da separação
    Handoff docs-cicd e doubles BDD sem Podman/Robot real.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class E2eStackLauncher(Protocol):
    """Lifecycle da stack e2e (Podman + docker-compose.e2e.yml).

    Responsabilidade
        Subir, aguardar healthy e derrubar a stack isolada T19.

    Motivo da separação
        Runtime ≠ asserções Robot; reutilizável pela esteira docs-cicd.
    """

    def up(self, env: Mapping[str, str] | None = None, **kwargs: Any) -> None:
        """Sobe a stack compose e2e."""
        ...

    def wait_healthy(self, *, timeout_seconds: float | None = None) -> None:
        """Aguarda GET /healthz = 200 com UI+MCP ready."""
        ...

    def down(self) -> None:
        """Derruba a stack (melhor esforço; idempotente)."""
        ...


@runtime_checkable
class RobotCliRunner(Protocol):
    """Invocação testável do CLI Robot Framework.

    Responsabilidade
        Executar suites green path e retornar exit code do ``robot``.

    Motivo da separação
        Isola subprocess ``robot`` do orquestrador.
    """

    def __call__(self, *args: Any, **kwargs: Any) -> int:
        """Retorna exit code do Robot (0 = green)."""
        ...


@runtime_checkable
class RobotMvpSuite(Protocol):
    """Orquestração canônica da prova MVP (BDD-026).

    Responsabilidade
        Coordenar credenciais → launcher → robot → down; exit code estável.

    Motivo da separação
        Suíte consumível por docs-cicd sem transferir ownership.
    """

    def run(self) -> int:
        """Executa a prova MVP; 0 = green; ≠0 = MVP não entregue."""
        ...
