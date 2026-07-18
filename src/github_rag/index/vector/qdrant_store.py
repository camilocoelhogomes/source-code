"""Adaptador Qdrant via SDK oficial ``qdrant-client`` (T13).

Responsabilidade deste módulo
    Implementar ``VectorStore`` com collection Cosine, payload §4.8 e
    reindex via ``replace_repo_commit``.

Motivo da separação
    Concentra binding Qdrant; T14/T16 dependem só da porta (DEC-015 / BR-023).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any, Sequence, TypeVar

from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from github_rag.index.chunk.types import SemanticChunk, SourceLanguage
from github_rag.index.vector.errors import (
    VectorDimensionError,
    VectorStoreError,
    VectorValidationError,
)
from github_rag.index.vector.types import (
    ChunkMetadata,
    RepoCommitScope,
    SemanticHit,
    VectorRecord,
)

_T = TypeVar("_T")

# Campos filtrados em purge/delete/search — índices KEYWORD no setup (design §4.8).
_PAYLOAD_INDEX_FIELDS: tuple[str, ...] = ("repo_id", "commit_sha", "path")

# Namespace fixo do produto para point id UUID v5 (design §4.7 / I-T13-010).
_POINT_ID_NAMESPACE = uuid.UUID("7c9e6679-7425-40de-944b-e07fc1f90ae7")


def _point_id(repo_id: str, commit_sha: str, chunk_id: str) -> str:
    name = f"{repo_id}\0{commit_sha}\0{chunk_id}"
    return str(uuid.uuid5(_POINT_ID_NAMESPACE, name))


class QdrantVectorStore:
    """Implementação ``VectorStore`` sobre ``qdrant_client.QdrantClient``."""

    def __init__(
        self,
        *,
        client: Any,
        collection_name: str = "github_rag_chunks",
        vector_size: int,
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self._vector_size = vector_size
        self._collection_ready = False

    def upsert(
        self, scope: RepoCommitScope, records: Sequence[VectorRecord]
    ) -> None:
        self._validate_scope(scope)
        if not records:
            self._ensure_collection()
            return
        points: list[PointStruct] = []
        for record in records:
            self._validate_record(record)
            points.append(self._to_point(scope, record))
        self._ensure_collection()
        self._invoke(
            "upsert",
            lambda: self._client.upsert(
                collection_name=self._collection_name,
                points=points,
            ),
        )

    def purge_other_commits(self, scope: RepoCommitScope) -> None:
        self._validate_scope(scope)
        self._ensure_collection()
        flt = Filter(
            must=[
                FieldCondition(
                    key="repo_id", match=MatchValue(value=scope.repo_id)
                )
            ],
            must_not=[
                FieldCondition(
                    key="commit_sha", match=MatchValue(value=scope.commit_sha)
                )
            ],
        )
        self._invoke(
            "purge",
            lambda: self._client.delete(
                collection_name=self._collection_name,
                points_selector=flt,
            ),
        )

    def replace_repo_commit(
        self, scope: RepoCommitScope, records: Sequence[VectorRecord]
    ) -> None:
        self.upsert(scope, records)
        self.purge_other_commits(scope)

    def delete_repo(self, repo_id: str) -> None:
        if not repo_id or not repo_id.strip():
            raise VectorValidationError("repo_id must be non-empty")
        self._ensure_collection()
        flt = Filter(
            must=[
                FieldCondition(key="repo_id", match=MatchValue(value=repo_id))
            ]
        )
        self._invoke(
            "delete_repo",
            lambda: self._client.delete(
                collection_name=self._collection_name,
                points_selector=flt,
            ),
        )

    def delete_paths(
        self, scope: RepoCommitScope, paths: Sequence[str]
    ) -> None:
        self._validate_scope(scope)
        if not paths:
            return
        self._ensure_collection()
        flt = Filter(
            must=[
                FieldCondition(
                    key="repo_id", match=MatchValue(value=scope.repo_id)
                ),
                FieldCondition(
                    key="commit_sha",
                    match=MatchValue(value=scope.commit_sha),
                ),
                FieldCondition(key="path", match=MatchAny(any=list(paths))),
            ]
        )
        self._invoke(
            "delete_paths",
            lambda: self._client.delete(
                collection_name=self._collection_name,
                points_selector=flt,
            ),
        )

    def search(
        self,
        query_vector: Sequence[float],
        *,
        limit: int,
        repo_ids: Sequence[str] | None = None,
    ) -> tuple[SemanticHit, ...]:
        self._ensure_collection()
        query_filter: Filter | None = None
        if repo_ids is not None:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="repo_id", match=MatchAny(any=list(repo_ids))
                    )
                ]
            )
        response = self._invoke(
            "search",
            lambda: self._client.query_points(
                collection_name=self._collection_name,
                query=list(query_vector),
                limit=limit,
                query_filter=query_filter,
            ),
        )
        return tuple(
            self._hit_from_payload(
                score=float(point.score),
                payload=point.payload or {},
            )
            for point in response.points
        )

    def _invoke(self, action: str, call: Callable[[], _T]) -> _T:
        """Executa chamada Qdrant mapeando exceções para ``VectorStoreError``."""
        try:
            return call()
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError(f"qdrant {action} failed: {exc}") from exc

    def _ensure_collection(self) -> None:
        if self._collection_ready:
            return
        try:
            self._client.get_collection(self._collection_name)
        except VectorStoreError:
            raise
        except Exception:
            try:
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=self._vector_size,
                        distance=Distance.COSINE,
                    ),
                )
            except VectorStoreError:
                raise
            except Exception as exc:
                try:
                    self._client.get_collection(self._collection_name)
                except Exception:
                    raise VectorStoreError(
                        f"qdrant collection setup failed: {exc}"
                    ) from exc
        self._ensure_payload_indexes()
        self._collection_ready = True

    def _ensure_payload_indexes(self) -> None:
        """Cria índices KEYWORD para filtros; falhas por campo não abortam setup.

        Responsabilidade: solicitar ``create_payload_index`` para
        ``repo_id`` / ``commit_sha`` / ``path`` após a collection existir.
        Motivo: em servidor Qdrant os índices aceleram purge/delete/search;
        em ``:memory:`` o SDK pode emitir warning sem efeito — não falhar.
        """
        for field_name in _PAYLOAD_INDEX_FIELDS:
            try:
                self._client.create_payload_index(
                    collection_name=self._collection_name,
                    field_name=field_name,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception:
                # Já existe, warning local, ou limitações do client — filtros ok.
                continue

    def _validate_scope(self, scope: RepoCommitScope) -> None:
        if not scope.repo_id or not scope.repo_id.strip():
            raise VectorValidationError("repo_id must be non-empty")
        if not scope.commit_sha or not scope.commit_sha.strip():
            raise VectorValidationError("commit_sha must be non-empty")

    def _validate_record(self, record: VectorRecord) -> None:
        chunk = record.enriched.chunk
        metadata = record.enriched.metadata
        if not metadata.summary or not metadata.summary.strip():
            raise VectorValidationError("metadata.summary must be non-empty")
        if not chunk.text:
            raise VectorValidationError("chunk.text must be non-empty")
        if not chunk.chunk_id:
            raise VectorValidationError("chunk.chunk_id must be non-empty")
        if len(record.vector) != self._vector_size:
            raise VectorDimensionError(
                f"vector length {len(record.vector)} != {self._vector_size}"
            )

    def _to_point(
        self, scope: RepoCommitScope, record: VectorRecord
    ) -> PointStruct:
        chunk = record.enriched.chunk
        metadata = record.enriched.metadata
        payload = {
            "repo_id": scope.repo_id,
            "commit_sha": scope.commit_sha,
            "chunk_id": chunk.chunk_id,
            "path": chunk.path,
            "language": chunk.language.value,
            "kind": chunk.kind,
            "text": chunk.text,
            "start_byte": chunk.start_byte,
            "end_byte": chunk.end_byte,
            "start_point": [chunk.start_point[0], chunk.start_point[1]],
            "end_point": [chunk.end_point[0], chunk.end_point[1]],
            "metadata": {
                "summary": metadata.summary,
                "keywords": list(metadata.keywords),
                "symbols": list(metadata.symbols),
            },
        }
        return PointStruct(
            id=_point_id(scope.repo_id, scope.commit_sha, chunk.chunk_id),
            vector=list(record.vector),
            payload=payload,
        )

    def _hit_from_payload(
        self, *, score: float, payload: dict[str, Any]
    ) -> SemanticHit:
        meta_raw = payload.get("metadata") or {}
        start_point = payload.get("start_point") or [0, 0]
        end_point = payload.get("end_point") or [0, 0]
        chunk = SemanticChunk(
            chunk_id=str(payload.get("chunk_id", "")),
            path=str(payload.get("path", "")),
            language=SourceLanguage(str(payload.get("language", ""))),
            kind=str(payload.get("kind", "")),
            text=str(payload.get("text", "")),
            start_byte=int(payload.get("start_byte", 0)),
            end_byte=int(payload.get("end_byte", 0)),
            start_point=(int(start_point[0]), int(start_point[1])),
            end_point=(int(end_point[0]), int(end_point[1])),
        )
        metadata = ChunkMetadata(
            summary=str(meta_raw.get("summary", "")),
            keywords=tuple(meta_raw.get("keywords") or ()),
            symbols=tuple(meta_raw.get("symbols") or ()),
        )
        return SemanticHit(
            score=score,
            repo_id=str(payload.get("repo_id", "")),
            commit_sha=str(payload.get("commit_sha", "")),
            chunk=chunk,
            metadata=metadata,
        )
