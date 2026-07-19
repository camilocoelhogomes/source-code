"""Projeção pura DetailFields → QueryHit (T16 / BDD-012).

Responsabilidade deste módulo
    Aplicar flags de detalhes opcionais sobre ExactMatch e SemanticHit.

Motivo da separação
    Política BDD-012 testável sem I/O nem backends (I-T16-011).
"""

from __future__ import annotations

from github_rag.index.vector.types import SemanticHit
from github_rag.index.zoekt.models import ExactMatch
from github_rag.query.types import DetailFields, QueryHit


def project_exact(match: ExactMatch, details: DetailFields) -> QueryHit:
    """Mapeia ExactMatch → QueryHit com campos não solicitados em None."""
    return QueryHit(
        kind="exact",
        score=None,
        repository=match.repository if details.repository else None,
        path=match.path if details.path else None,
        commit=match.commit if details.commit else None,
        snippet=match.snippet if details.snippet else None,
        line_number=None,
    )


def project_semantic(hit: SemanticHit, details: DetailFields) -> QueryHit:
    """Mapeia SemanticHit → QueryHit com campos não solicitados em None."""
    return QueryHit(
        kind="semantic",
        score=hit.score,
        repository=hit.repo_id if details.repository else None,
        path=hit.chunk.path if details.path else None,
        commit=hit.commit_sha if details.commit else None,
        snippet=hit.chunk.text if details.snippet else None,
        chunk_metadata_summary=None,
        line_number=None,
    )
