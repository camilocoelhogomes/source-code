"""Modelos de descoberta GitHub (T05).

Responsabilidade deste módulo
    Declarar ``DiscoveredGitHubRepo`` (saída da descoberta) e ``GitHubRepoRaw``
    (DTO interno da API). Nenhum campo de segredo.

Motivo da separação
    Isola a forma dos dados devolvida a T07 da porta HTTP e da lógica de
    wildcard; evita vazar token no modelo de saída (BDD-019).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubRepoRaw:
    """Repositório bruto retornado pela API GitHub.

    Responsabilidade
        Transportar campos mínimos necessários ao filtro de inclusão.

    Motivo da separação
        Desacopla o JSON da API REST do snapshot de domínio
        ``DiscoveredGitHubRepo`` consumido pelo catálogo.
    """

    full_name: str
    name: str
    private: bool


@dataclass(frozen=True)
class DiscoveredGitHubRepo:
    """Repositório GitHub elegível descoberto para sync (handoff T07).

    Responsabilidade
        Snapshot imutável identificando origem, org e visibilidade — sem token.

    Motivo da separação
        Contrato estável para ``CatalogSync`` independente de HTTP ou wildcards.
    """

    connection_name: str
    full_name: str
    org: str
    name: str
    private: bool
