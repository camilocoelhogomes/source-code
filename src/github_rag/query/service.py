"""Implementação default da fachada QueryService (T16).

Responsabilidade deste módulo
    Orquestrar ExactCodeIndex, Embedder, VectorStore, MainSnapshotProvider e
    CatalogRepository com projeção BDD-012 — sem client paralelo.

Motivo da separação
    Composição injetável para T17/T18 e testes (I-T16-002 / BR-023).
"""

from __future__ import annotations

from github_rag.catalog.repository import CatalogRepository
from github_rag.index.vector.errors import EmbeddingError, VectorStoreError
from github_rag.index.vector.ports import Embedder, VectorStore
from github_rag.index.zoekt.errors import ExactCodeIndexError
from github_rag.index.zoekt.models import ExactSearchQuery
from github_rag.index.zoekt.port import ExactCodeIndex
from github_rag.query.errors import (
    QueryEmbeddingError,
    QueryExactIndexError,
    QueryReformulatorError,
    QuerySnapshotError,
    QueryValidationError,
    QueryVectorError,
)
from github_rag.query.ports import QueryReformulator, SnapshotSourceResolver
from github_rag.query.projection import project_exact, project_semantic
from github_rag.query.resolve import resolve_browse_commit, resolve_catalog_entry
from github_rag.query.types import (
    DetailFields,
    ExactSearchRequest,
    FileContent,
    ListTreeRequest,
    QueryHits,
    ReadFileRequest,
    SemanticSearchRequest,
    TreeListing,
)
from github_rag.snapshot.errors import SnapshotError
from github_rag.snapshot.provider import MainSnapshotProvider


def _is_blank(value: str) -> bool:
    return value.strip() == ""


class DefaultQueryService:
    """Orquestra portas T07/T08/T10/T13 (+ reformulador opcional)."""

    def __init__(
        self,
        *,
        exact_index: ExactCodeIndex,
        vector_store: VectorStore,
        embedder: Embedder,
        snapshot: MainSnapshotProvider,
        catalog: CatalogRepository,
        source_resolver: SnapshotSourceResolver,
        reformulator: QueryReformulator | None = None,
    ) -> None:
        self._exact_index = exact_index
        self._vector_store = vector_store
        self._embedder = embedder
        self._snapshot = snapshot
        self._catalog = catalog
        self._source_resolver = source_resolver
        self._reformulator = reformulator

    def search_exact(self, request: ExactSearchRequest) -> QueryHits:
        if _is_blank(request.pattern):
            return QueryHits(hits=())

        entry = resolve_catalog_entry(
            self._catalog,
            repo_key=request.repo_key,
            repository_id=request.repository_id,
            require_scope=False,
        )
        repo_filter = entry.repo_identifier if entry is not None else None

        query = ExactSearchQuery(
            pattern=request.pattern,
            repository=repo_filter,
            path_prefix=request.path_prefix,
            max_matches=request.max_matches,
            context_lines=request.context_lines,
        )
        try:
            matches = self._exact_index.search(query)
        except ExactCodeIndexError as exc:
            raise QueryExactIndexError("falha na busca exata") from exc

        hits = tuple(project_exact(m, request.details) for m in matches)
        return QueryHits(hits=hits)

    def search_semantic(self, request: SemanticSearchRequest) -> QueryHits:
        if _is_blank(request.query):
            raise QueryValidationError("query semântica vazia")

        entry = resolve_catalog_entry(
            self._catalog,
            repo_key=request.repo_key,
            repository_id=request.repository_id,
            require_scope=False,
        )
        repo_ids = (entry.repo_identifier,) if entry is not None else None

        text = request.query
        if request.reformulate and self._reformulator is not None:
            try:
                text = self._reformulator.reformulate(request.query)
            except QueryReformulatorError:
                raise
            except Exception as exc:
                raise QueryReformulatorError(
                    "falha na reformulação da query"
                ) from exc

        try:
            vectors = self._embedder.embed((text,))
        except EmbeddingError as exc:
            raise QueryEmbeddingError("falha ao gerar embedding") from exc

        if not vectors:
            raise QueryEmbeddingError("embedder retornou sequência vazia")

        try:
            semantic_hits = self._vector_store.search(
                vectors[0],
                limit=request.limit,
                repo_ids=repo_ids,
            )
        except VectorStoreError as exc:
            raise QueryVectorError("falha na busca vetorial") from exc

        hits = tuple(
            project_semantic(h, request.details) for h in semantic_hits
        )
        return QueryHits(hits=hits)

    def read_file(self, request: ReadFileRequest) -> FileContent:
        if _is_blank(request.path):
            raise QueryValidationError("path de arquivo vazio")

        entry = resolve_catalog_entry(
            self._catalog,
            repo_key=request.repo_key,
            repository_id=request.repository_id,
            require_scope=True,
        )
        assert entry is not None
        commit = resolve_browse_commit(entry, commit_sha=request.commit_sha)

        try:
            source = self._source_resolver.resolve(entry)
            content = self._snapshot.read_file(
                source, commit_sha=commit, path=request.path
            )
        except SnapshotError as exc:
            raise QuerySnapshotError("falha ao ler arquivo do snapshot") from exc

        return self._project_file_content(
            content=content,
            repo_key=entry.repo_identifier,
            path=request.path,
            commit=commit,
            details=request.details,
        )

    def list_tree(self, request: ListTreeRequest) -> TreeListing:
        entry = resolve_catalog_entry(
            self._catalog,
            repo_key=request.repo_key,
            repository_id=request.repository_id,
            require_scope=True,
        )
        assert entry is not None
        commit = resolve_browse_commit(entry, commit_sha=request.commit_sha)

        try:
            source = self._source_resolver.resolve(entry)
            paths = self._snapshot.list_tree(source, commit_sha=commit)
        except SnapshotError as exc:
            raise QuerySnapshotError(
                "falha ao listar árvore do snapshot"
            ) from exc

        if request.path_prefix is not None:
            prefix = request.path_prefix
            paths = tuple(p for p in paths if p.startswith(prefix))

        return TreeListing(
            paths=paths,
            repository=(
                entry.repo_identifier if request.details.repository else None
            ),
            commit=commit if request.details.commit else None,
        )

    @staticmethod
    def _project_file_content(
        *,
        content: bytes,
        repo_key: str,
        path: str,
        commit: str,
        details: DetailFields,
    ) -> FileContent:
        return FileContent(
            content=content,
            repository=repo_key if details.repository else None,
            path=path if details.path else None,
            commit=commit if details.commit else None,
        )
