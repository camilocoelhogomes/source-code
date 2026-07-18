"""Fronteira de catálogo (T03) — reexporta os contratos públicos.

Responsabilidade deste pacote
    Expor a superfície pública estável do catálogo: enums de domínio, modelos de
    leitura imutáveis, hierarquia de erros, a porta ``CatalogRepository`` e os
    contratos da máquina de estados. É o ponto único de import para consumidores
    (T07/T14/T17/T18) e para os testes BDD (``from github_rag import catalog``).

Motivo da separação
    Centralizar os reexports evita que consumidores dependam de caminhos internos
    de módulo (`catalog.models`, `catalog.repository`), permitindo reorganização
    interna sem quebrar o handoff.

Nota de etapa (gate de implementação)
    ``InMemoryCatalogRepository`` (fake de domínio) já é exportado aqui, tornando
    o BDD/unit verdes. ``PostgresCatalogRepository`` (adaptador) vive em
    ``catalog.postgres`` e depende de SQLAlchemy/psycopg — importado sob demanda
    para não exigir o driver no run de domínio.
"""

from .errors import (
    CatalogError,
    CatalogPersistenceError,
    ConcurrencyConflictError,
    InvalidStateTransitionError,
    RepositoryNotFoundError,
)
from .models import (
    CatalogEntry,
    ExecutionStatus,
    FileProgress,
    FileStage,
    IndexingExecution,
    Progress,
    RepoOrigin,
    RepoState,
)
from .memory import InMemoryCatalogRepository
from .repository import CatalogRepository
from .sync import CatalogSync, CatalogSyncError, CatalogSyncResult
from .transitions import (
    ALLOWED_TRANSITIONS,
    IDEMPOTENT_SELF_STATES,
    ensure_transition_allowed,
    is_transition_allowed,
    is_up_to_date,
)

__all__ = [
    "ALLOWED_TRANSITIONS",
    "IDEMPOTENT_SELF_STATES",
    "CatalogEntry",
    "CatalogError",
    "CatalogPersistenceError",
    "CatalogRepository",
    "CatalogSync",
    "CatalogSyncError",
    "CatalogSyncResult",
    "ConcurrencyConflictError",
    "ExecutionStatus",
    "FileProgress",
    "FileStage",
    "IndexingExecution",
    "InMemoryCatalogRepository",
    "InvalidStateTransitionError",
    "Progress",
    "RepoOrigin",
    "RepoState",
    "RepositoryNotFoundError",
    "ensure_transition_allowed",
    "is_transition_allowed",
    "is_up_to_date",
]
