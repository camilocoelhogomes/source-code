"""Store de issues locais do último sync para a Management UI (T25).

Responsabilidade deste módulo
    Porta ``CatalogIssueStore`` e implementação in-memory para expor
    ``LocalDiscoveryIssue`` à rota ``GET /api/catalog/issues`` (BDD-018).

Motivo da separação
    Desacopla ordem de boot (wire UI antes do sync) da serialização HTTP e
    do ``CatalogSync`` concreto (D-T25-001 / I-T25-001).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from github_rag.sources.local.discovery import LocalDiscoveryIssue


@runtime_checkable
class CatalogIssueStore(Protocol):
    """Porta de issues locais do último sync (BDD-018).

    Responsabilidade
        Expor e atualizar o snapshot de ``LocalDiscoveryIssue`` observável
        pela Management UI após o bootstrap/sync do catálogo.

    Motivo da separação
        O sync (T07) produz ``CatalogSyncResult.local_issues`` em momento
        distinto do wire da UI; a porta mutável desacopla essa ordem.
    """

    def replace(self, issues: Sequence[LocalDiscoveryIssue]) -> None:
        """Substitui o snapshot completo de issues."""

    def list_issues(self) -> tuple[LocalDiscoveryIssue, ...]:
        """Devolve o snapshot atual (imutável)."""


@dataclass
class InMemoryCatalogIssueStore:
    """Store default em memória para issues locais.

    Responsabilidade
        Implementar ``CatalogIssueStore`` com snapshot imutável por
        ``replace`` (tuple interna).

    Motivo da separação
        Persistência PG de issues de volume não é requisito T03; in-memory
        basta para bootstrap + UI do MVP e testes.
    """

    _issues: tuple[LocalDiscoveryIssue, ...] = field(default_factory=tuple)

    def replace(self, issues: Sequence[LocalDiscoveryIssue]) -> None:
        self._issues = tuple(issues)

    def list_issues(self) -> tuple[LocalDiscoveryIssue, ...]:
        return self._issues
