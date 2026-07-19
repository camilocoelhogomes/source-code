"""Erros tipados do orquestrador de indexação (T14).

Responsabilidade deste módulo
    Declarar a hierarquia de falhas do orquestrador / reconcile.

Motivo da separação
    Distinguir erros de orquestração dos erros de catálogo, snapshot e índices.
"""

from __future__ import annotations


class IndexingOrchestratorError(Exception):
    """Base das falhas do orquestrador / reconcile."""


class RepositorySourceError(IndexingOrchestratorError):
    """Origem/token/path inválidos para montar SnapshotSource."""


class IndexingPipelineError(IndexingOrchestratorError):
    """Falha em etapa do pipeline (wrap de erro de porta)."""
