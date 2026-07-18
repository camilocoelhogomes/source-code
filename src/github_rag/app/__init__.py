"""Bootstrap da aplicação — helpers de inicialização (T07+).

Responsabilidade deste pacote
    Expor pontos de wire estáveis do boot (ex.: sync de catálogo) sem
    acoplar entrypoints à orquestração interna.

Motivo da separação
    T14/T19 montam a ordem sync → reconcile; este pacote oferece o helper
    de sync sem embutir indexação.
"""

from github_rag.app.bootstrap import run_catalog_sync

__all__ = ["run_catalog_sync"]
