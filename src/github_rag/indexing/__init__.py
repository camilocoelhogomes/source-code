"""Orquestração de indexação (T14).

Responsabilidade deste pacote
    Expor ``IndexingOrchestrator``, ``StartupIndexReconcile`` e helpers
    do pipeline RAG — somente via portas (ENG-013).

Motivo da separação
    Isola fila/estados/reconcile dos adaptadores SDK (T08–T13).
"""

from github_rag.indexing.errors import (
    IndexingOrchestratorError,
    IndexingPipelineError,
    RepositorySourceError,
)
from github_rag.indexing.orchestrator import DefaultIndexingOrchestrator
from github_rag.indexing.pipeline import DefaultFileRagPipeline, FileRagPipeline
from github_rag.indexing.ports import IndexingOrchestrator, StartupIndexReconcile
from github_rag.indexing.progress import compute_progress_percent
from github_rag.indexing.startup_reconcile import DefaultStartupIndexReconcile
from github_rag.indexing.types import to_vector_metadata

__all__ = [
    "DefaultFileRagPipeline",
    "DefaultIndexingOrchestrator",
    "DefaultStartupIndexReconcile",
    "FileRagPipeline",
    "IndexingOrchestrator",
    "IndexingOrchestratorError",
    "IndexingPipelineError",
    "RepositorySourceError",
    "StartupIndexReconcile",
    "compute_progress_percent",
    "to_vector_metadata",
]
