"""Fachada de consultas compartilhadas (T16).

Responsabilidade
    Expor QueryService, DTOs, erros e DefaultQueryService para T17/T18.

Motivo da separação
    Única porta de exact/semantic/read/tree sem client paralelo (BR-023).
"""

from github_rag.query.errors import (
    QueryCommitUnavailableError,
    QueryEmbeddingError,
    QueryError,
    QueryExactIndexError,
    QueryReformulatorError,
    QueryRepositoryNotFoundError,
    QuerySnapshotError,
    QueryValidationError,
    QueryVectorError,
)
from github_rag.query.ports import (
    QueryReformulator,
    QueryService,
    SnapshotSourceResolver,
)
from github_rag.query.service import DefaultQueryService
from github_rag.query.types import (
    DetailFields,
    ExactSearchRequest,
    FileContent,
    ListTreeRequest,
    QueryHit,
    QueryHits,
    ReadFileRequest,
    SemanticSearchRequest,
    TreeListing,
)

__all__ = [
    "DefaultQueryService",
    "DetailFields",
    "ExactSearchRequest",
    "FileContent",
    "ListTreeRequest",
    "QueryCommitUnavailableError",
    "QueryEmbeddingError",
    "QueryError",
    "QueryExactIndexError",
    "QueryHit",
    "QueryHits",
    "QueryReformulator",
    "QueryReformulatorError",
    "QueryRepositoryNotFoundError",
    "QueryService",
    "QuerySnapshotError",
    "QueryValidationError",
    "QueryVectorError",
    "ReadFileRequest",
    "SemanticSearchRequest",
    "SnapshotSourceResolver",
    "TreeListing",
]
