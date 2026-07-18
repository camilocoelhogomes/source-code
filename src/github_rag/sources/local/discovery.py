"""Modelos e porta de descoberta local — contratos T06."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from github_rag.catalog.models import RepoOrigin

if TYPE_CHECKING:
    from github_rag.config.schema import AppConfig, GitConnection


@dataclass(frozen=True)
class DiscoveredLocalRepo:
    """Repositório local elegível (Git válido + branch ``main``).

    Responsabilidade
        Transportar identidade de um candidato à catalogação com origem
        ``local`` e caminho montado.

    Motivo da separação
        Handoff tipado para T07 sem acoplar à porta ``CatalogRepository``.
    """

    connection_name: str
    local_path: str
    repo_identifier: str
    origin: RepoOrigin = RepoOrigin.LOCAL


@dataclass(frozen=True)
class LocalDiscoveryIssue:
    """Falha não fatal por conexão ou path (BDD-018).

    Responsabilidade
        Registrar erro operacional de volume/path sem abortar outras conexões.

    Motivo da separação
        Distinção explícita entre candidatos válidos e paths rejeitados.
    """

    connection_name: str
    path: str
    message: str


@dataclass(frozen=True)
class LocalDiscoveryResult:
    """Agregado de descoberta local.

    Responsabilidade
        Expor repos descobertos e issues da execução como snapshot imutável.

    Motivo da separação
        Resultado único consumível por bootstrap/T07.
    """

    repos: tuple[DiscoveredLocalRepo, ...]
    issues: tuple[LocalDiscoveryIssue, ...]


class LocalRepoDiscovery:
    """Porta de descoberta de repositórios locais declarados em ``AppConfig``.

    Responsabilidade
        Expandir URLs ``file://`` com glob, validar Git + ``main`` e produzir
        candidatos com origem ``local``.

    Motivo da separação
        Isola volumes montados e heurística Git de config (T02) e catálogo (T07).
    """

    def __init__(self, inspector: object | None = None) -> None:
        self._inspector = inspector

    def discover(self, config: AppConfig) -> LocalDiscoveryResult:
        """Descobre repos de todas as conexões ``type: git``."""
        raise NotImplementedError

    def discover_connection(
        self,
        connection_name: str,
        connection: GitConnection,
    ) -> LocalDiscoveryResult:
        """Descobre repos de uma única conexão ``git``."""
        raise NotImplementedError
