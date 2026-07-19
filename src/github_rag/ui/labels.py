"""Rótulos PT de estados REQ-020 para a UI (T18).

Responsabilidade deste módulo
    Mapear ``RepoState`` (slug ASCII) para o rótulo em português da UI.

Motivo da separação
    Domínio T03 mantém slugs estáveis; apresentação PT fica na superfície UI.
"""

from __future__ import annotations

from typing import Final, Mapping

from github_rag.catalog.models import RepoState

STATE_LABELS: Final[Mapping[RepoState, str]] = {
    RepoState.NOT_INDEXED: "não indexado",
    RepoState.QUEUED: "na fila",
    RepoState.INDEXING: "indexando",
    RepoState.UP_TO_DATE: "atualizado",
    RepoState.ERROR: "erro",
}


def state_label(state: RepoState) -> str:
    """Traduz slug REQ-020 para rótulo PT de UI.

    Responsabilidade: apresentação; não altera o domínio.
    Motivo da separação: enums ASCII estáveis (T03) vs copy PT (REQ-020).
    """
    return STATE_LABELS[state]
