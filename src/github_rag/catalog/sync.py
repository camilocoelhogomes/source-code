"""Sincronização do catálogo a partir das discoveries (T07).

Responsabilidade deste módulo
    ``CatalogSync`` orquestra config → discovery GitHub/local → upsert e
    soft-delete no ``CatalogRepository``, sem indexar nem reconciliar.

Motivo da separação
    Isola a política de bootstrap do catálogo (BR-001/016) do loader (T02),
    das discoveries (T05/T06) e da persistência (T03). Consumidores T14/T19
    dependem desta porta, não da ordem interna de I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from github_rag.catalog.models import CatalogEntry, RepoOrigin
from github_rag.catalog.repository import CatalogRepository
from github_rag.config.schema import AppConfig, GitHubConnection
from github_rag.sources.github.discovery import GitHubRepoDiscovery
from github_rag.sources.github.errors import GitHubDiscoveryError
from github_rag.sources.github.models import DiscoveredGitHubRepo
from github_rag.sources.local.discovery import (
    DiscoveredLocalRepo,
    LocalDiscoveryIssue,
    LocalRepoDiscovery,
)


class CatalogSyncError(Exception):
    """Falha fatal na sincronização do catálogo.

    Responsabilidade
        Sinalizar aborto do sync (tipicamente discovery GitHub) sem aplicar
        desativações; mensagem sem valor de token.

    Motivo da separação
        Distingue orquestração T07 de ``GitHubDiscoveryError`` (T05) e de
        erros de persistência T03, preservando redaction (BDD-014).
    """


@dataclass(frozen=True)
class CatalogSyncResult:
    """Snapshot imutável do efeito de um ``CatalogSync.sync``.

    Responsabilidade
        Expor ativos, upserts, desativações e issues locais da execução.

    Motivo da separação
        Congela o handoff observável para bootstrap/T14/T18 sem acoplar à
        ordem interna de mutações.
    """

    active: tuple[CatalogEntry, ...]
    upserted: tuple[CatalogEntry, ...]
    deactivated: tuple[CatalogEntry, ...]
    local_issues: tuple[LocalDiscoveryIssue, ...]


@dataclass(frozen=True)
class _UpsertCandidate:
    """Candidato interno ao upsert (após discovery completo)."""

    connection_name: str
    origin: RepoOrigin
    repo_identifier: str
    github_org: str | None
    local_path: str | None


class CatalogSync:
    """Orquestra discovery → upsert → soft-delete do catálogo ativo.

    Responsabilidade
        Sincronizar o SoT com repositórios descobertos a partir de
        ``AppConfig`` válido; preservar estados/commits via upsert T03;
        remover do catálogo ativo os ausentes (sem estado extra).

    Motivo da separação
        Concentra a política de sync (D-T07-*) fora do loader, discoveries e
        indexação — T14 só consome o resultado antes do reconcile.
    """

    def __init__(
        self,
        *,
        catalog: CatalogRepository,
        github_discovery: GitHubRepoDiscovery,
        local_discovery: LocalRepoDiscovery,
    ) -> None:
        self._catalog = catalog
        self._github_discovery = github_discovery
        self._local_discovery = local_discovery

    def sync(self, config: AppConfig) -> CatalogSyncResult:
        """Sincroniza o catálogo com a discovery da config atual.

        Algoritmo: discovery GitHub (abort sem mutação se falhar) → discovery
        local → upserts → desativa ausentes → ``CatalogSyncResult``.
        """
        github_repos = self._discover_github(config)
        local_result = self._local_discovery.discover(config)

        candidates = (
            *(_from_github(repo) for repo in github_repos),
            *(_from_local(repo) for repo in local_result.repos),
        )
        discovered_keys = {
            (c.connection_name, c.repo_identifier) for c in candidates
        }

        upserted: list[CatalogEntry] = []
        for candidate in candidates:
            entry = self._catalog.upsert_repository(
                connection_name=candidate.connection_name,
                origin=candidate.origin,
                repo_identifier=candidate.repo_identifier,
                github_org=candidate.github_org,
                local_path=candidate.local_path,
            )
            upserted.append(entry)

        deactivated: list[CatalogEntry] = []
        for entry in list(self._catalog.list_active_catalog()):
            key = (entry.connection_name, entry.repo_identifier)
            if key not in discovered_keys:
                deactivated.append(self._catalog.deactivate_repository(entry.id))

        active = tuple(self._catalog.list_active_catalog())
        return CatalogSyncResult(
            active=active,
            upserted=tuple(upserted),
            deactivated=tuple(deactivated),
            local_issues=tuple(local_result.issues),
        )

    def _discover_github(
        self, config: AppConfig
    ) -> tuple[DiscoveredGitHubRepo, ...]:
        discovered: list[DiscoveredGitHubRepo] = []
        for name, connection in config.connections.items():
            if getattr(connection, "type", None) != "github":
                continue
            github_conn: GitHubConnection = connection  # type: ignore[assignment]
            try:
                discovered.extend(
                    self._github_discovery.discover(name, github_conn)
                )
            except GitHubDiscoveryError as exc:
                raise CatalogSyncError(
                    "falha na descoberta GitHub durante sync do catálogo; "
                    "nenhuma mutação aplicada nesta execução"
                ) from exc
        discovered.sort(
            key=lambda item: (item.connection_name, item.full_name)
        )
        return tuple(discovered)


def _from_github(repo: DiscoveredGitHubRepo) -> _UpsertCandidate:
    return _UpsertCandidate(
        connection_name=repo.connection_name,
        origin=RepoOrigin.GITHUB,
        repo_identifier=repo.full_name,
        github_org=repo.org,
        local_path=None,
    )


def _from_local(repo: DiscoveredLocalRepo) -> _UpsertCandidate:
    return _UpsertCandidate(
        connection_name=repo.connection_name,
        origin=repo.origin,
        repo_identifier=repo.repo_identifier,
        github_org=None,
        local_path=repo.local_path,
    )
