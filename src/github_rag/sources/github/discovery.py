"""Orquestração de descoberta de repositórios GitHub (T05).

Responsabilidade deste módulo
    ``GitHubRepoDiscovery``: listar repos por org via ``GitHubApiClient``,
    filtrar por wildcards de inclusão e produzir ``DiscoveredGitHubRepo``.

Motivo da separação
    Porta de domínio consumida por T07; não acopla HTTP nem persistência.
"""

from __future__ import annotations

from github_rag.config.schema import GitHubConnection
from github_rag.sources.github.client import GitHubApiClient, PyGithubApiClient
from github_rag.sources.github.errors import GitHubDiscoveryError
from github_rag.sources.github.models import DiscoveredGitHubRepo, GitHubRepoRaw
from github_rag.sources.github.wildcard import matches_any_inclusion_pattern


class GitHubRepoDiscovery:
    """Descobre repositórios GitHub elegíveis para uma conexão validada.

    Responsabilidade
        Orquestrar listagem por org + filtro BR-022 usando ``connection.secret``.

    Motivo da separação
        Consumidor T07 depende desta porta, não de PyGithub ou REST.
    """

    def __init__(self, client: GitHubApiClient | None = None) -> None:
        self._client = client if client is not None else PyGithubApiClient()

    def discover(
        self,
        connection_name: str,
        connection: GitHubConnection,
    ) -> tuple[DiscoveredGitHubRepo, ...]:
        """Descobre repos que casam os wildcards de inclusão da conexão."""
        patterns = tuple(connection.repos)
        if not patterns:
            return ()

        token = connection.secret.get_value()
        raw_by_name: dict[str, GitHubRepoRaw] = {}

        for org in connection.orgs:
            repos = self._client.list_org_repos(org, token=token)
            for repo in repos:
                raw_by_name.setdefault(repo.full_name, repo)

        discovered: list[DiscoveredGitHubRepo] = []
        for full_name, raw in raw_by_name.items():
            if not matches_any_inclusion_pattern(full_name, patterns):
                continue
            org, name = full_name.split("/", 1)
            discovered.append(
                DiscoveredGitHubRepo(
                    connection_name=connection_name,
                    full_name=full_name,
                    org=org,
                    name=name,
                    private=raw.private,
                )
            )

        discovered.sort(key=lambda item: item.full_name)
        return tuple(discovered)
