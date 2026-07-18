"""Sincronização do catálogo a partir das discoveries (T07) — contratos.

Responsabilidade deste módulo
    Declarar ``CatalogSync``, ``CatalogSyncResult`` e ``CatalogSyncError``:
    orquestrar config → discovery GitHub/local → upsert/soft-delete no
    ``CatalogRepository``, sem indexar nem reconciliar.

Motivo da separação
    Isola a política de bootstrap do catálogo (BR-001/016) do loader (T02),
    das discoveries (T05/T06) e da persistência (T03). Consumidores T14/T19
    dependem desta porta, não da ordem interna de I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from github_rag.catalog.models import CatalogEntry
from github_rag.catalog.repository import CatalogRepository
from github_rag.config.schema import AppConfig
from github_rag.sources.github.discovery import GitHubRepoDiscovery
from github_rag.sources.local.discovery import LocalDiscoveryIssue, LocalRepoDiscovery


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
        raise NotImplementedError("CatalogSync.sync — implementação T07 pendente")
