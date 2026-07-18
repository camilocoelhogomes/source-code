"""Helpers de bootstrap — sync de catálogo (T07).

Responsabilidade deste módulo
    Oferecer ``run_catalog_sync`` como ponto de wire que executa apenas o
    sync do catálogo.

Motivo da separação
    Estabiliza o handoff para T14/T19 (sync → reconcile ENG-011) sem
    espalhar a chamada nem embutir indexação em T07.
"""

from __future__ import annotations

from github_rag.catalog.sync import CatalogSync, CatalogSyncResult
from github_rag.config.schema import AppConfig


def run_catalog_sync(config: AppConfig, sync: CatalogSync) -> CatalogSyncResult:
    """Executa o sync de catálogo no boot; não reconcilia nem indexa.

    Responsabilidade
        Delegar a ``sync.sync(config)``.

    Motivo da separação
        Ponto único de wire; ENG-011 permanece em T14 (CS-10 / D-T07-003).
    """
    return sync.sync(config)
