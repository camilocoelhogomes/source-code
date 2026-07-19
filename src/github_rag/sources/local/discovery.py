"""Modelos e porta de descoberta local — contratos T06."""

from __future__ import annotations

from dataclasses import dataclass

from github_rag.catalog.models import RepoOrigin
from github_rag.config.schema import AppConfig, GitConnection, GitHubConnection
from github_rag.sources.local.git_fs import GitFilesystemInspector, remap_repos_mount_path


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

    def __init__(
        self,
        inspector: GitFilesystemInspector | None = None,
        *,
        host_repos: str | None = None,
    ) -> None:
        self._inspector = inspector or GitFilesystemInspector()
        self._host_repos = host_repos

    def discover(self, config: AppConfig) -> LocalDiscoveryResult:
        """Descobre repos de todas as conexões ``type: git``."""
        repos: list[DiscoveredLocalRepo] = []
        issues: list[LocalDiscoveryIssue] = []

        for name, connection in config.connections.items():
            if isinstance(connection, GitHubConnection):
                continue
            result = self.discover_connection(name, connection)
            repos.extend(result.repos)
            issues.extend(result.issues)

        return LocalDiscoveryResult(repos=tuple(repos), issues=tuple(issues))

    def discover_connection(
        self,
        connection_name: str,
        connection: GitConnection,
    ) -> LocalDiscoveryResult:
        """Descobre repos de uma única conexão ``git``."""
        repos: list[DiscoveredLocalRepo] = []
        issues: list[LocalDiscoveryIssue] = []

        try:
            parsed = self._inspector.parse_file_url(connection.url)
        except ValueError as exc:
            issues.append(
                LocalDiscoveryIssue(
                    connection_name=connection_name,
                    path=connection.url,
                    message=str(exc),
                )
            )
            return LocalDiscoveryResult(repos=(), issues=tuple(issues))

        base = remap_repos_mount_path(parsed.base_path, self._host_repos)
        if not self._inspector.is_accessible(base):
            issues.append(
                LocalDiscoveryIssue(
                    connection_name=connection_name,
                    path=connection.url,
                    message=(
                        f"local volume path is inaccessible: {base.as_posix()}"
                    ),
                )
            )
            return LocalDiscoveryResult(repos=(), issues=tuple(issues))

        candidates = self._inspector.expand_candidates(base, parsed.glob_pattern)
        if not candidates:
            issues.append(
                LocalDiscoveryIssue(
                    connection_name=connection_name,
                    path=connection.url,
                    message="no matching directories found for local connection",
                )
            )

        for candidate in candidates:
            inspection = self._inspector.inspect_repo(candidate)
            candidate_path = candidate.resolve().as_posix()

            if inspection.is_valid_candidate:
                repos.append(
                    DiscoveredLocalRepo(
                        connection_name=connection_name,
                        local_path=candidate_path,
                        repo_identifier=candidate.name,
                    )
                )
                continue

            message = inspection.reason or "invalid local git repository"
            issues.append(
                LocalDiscoveryIssue(
                    connection_name=connection_name,
                    path=candidate_path,
                    message=message,
                )
            )

        return LocalDiscoveryResult(repos=tuple(repos), issues=tuple(issues))
