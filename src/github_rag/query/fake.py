"""Doubles injetáveis para BDD/unit da fachada QueryService (T16).

Responsabilidade deste módulo
    Fakes de Embedder, VectorStore (search), MainSnapshotProvider,
    SnapshotSourceResolver, QueryReformulator e QueryService.

Motivo da separação
    Valida contratos sem Zoekt/Qdrant/Git reais (I-T16-015 / BDD-024).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from github_rag.catalog.models import CatalogEntry, RepoOrigin
from github_rag.index.vector.errors import EmbeddingError, VectorStoreError
from github_rag.index.vector.types import (
    RepoCommitScope,
    SemanticHit,
    VectorRecord,
)
from github_rag.query.errors import QueryError
from github_rag.query.types import (
    ExactSearchRequest,
    FileContent,
    ListTreeRequest,
    QueryHits,
    ReadFileRequest,
    SemanticSearchRequest,
    TreeListing,
)
from github_rag.snapshot.diff import FileDiffSet
from github_rag.snapshot.errors import FileNotFoundInCommitError, SnapshotError
from github_rag.snapshot.models import (
    FirstIndexSignal,
    LocalSnapshotSource,
    MainSnapshot,
    SnapshotSource,
)


class FakeEmbedder:
    """Double de Embedder com vetores controlados e instrumentação."""

    def __init__(
        self,
        *,
        vectors_by_text: Mapping[str, tuple[float, ...]] | None = None,
        dimensions: int = 8,
        fail: bool = False,
    ) -> None:
        self._vectors_by_text = dict(vectors_by_text or {})
        self._dimensions = dimensions
        self._fail = fail
        self.call_count = 0
        self.last_texts: tuple[str, ...] | None = None

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        self.call_count += 1
        self.last_texts = tuple(texts)
        if self._fail:
            raise EmbeddingError("fake embed failure")
        out: list[tuple[float, ...]] = []
        for text in texts:
            if text in self._vectors_by_text:
                out.append(self._vectors_by_text[text])
            else:
                out.append(tuple(float(i % 7) for i in range(self._dimensions)))
        return tuple(out)


class FakeVectorStore:
    """Double de VectorStore focado em search; demais métodos no-op."""

    def __init__(
        self,
        *,
        hits_by_vector: Mapping[tuple[float, ...], tuple[SemanticHit, ...]]
        | None = None,
        fail_search: bool = False,
    ) -> None:
        self._hits_by_vector = dict(hits_by_vector or {})
        self._fail_search = fail_search
        self.search_call_count = 0
        self.last_repo_ids: Sequence[str] | None = None
        self.last_limit: int | None = None

    def upsert(
        self,
        scope: RepoCommitScope,
        records: Sequence[VectorRecord],
    ) -> None:
        return None

    def purge_other_commits(self, scope: RepoCommitScope) -> None:
        return None

    def replace_repo_commit(
        self,
        scope: RepoCommitScope,
        records: Sequence[VectorRecord],
    ) -> None:
        return None

    def delete_repo(self, repo_id: str) -> None:
        return None

    def delete_paths(
        self,
        scope: RepoCommitScope,
        paths: Sequence[str],
    ) -> None:
        return None

    def search(
        self,
        query_vector: Sequence[float],
        *,
        limit: int,
        repo_ids: Sequence[str] | None = None,
    ) -> tuple[SemanticHit, ...]:
        self.search_call_count += 1
        self.last_repo_ids = repo_ids
        self.last_limit = limit
        if self._fail_search:
            raise VectorStoreError("fake vector search failure")
        key = tuple(float(x) for x in query_vector)
        hits = self._hits_by_vector.get(key, ())
        if repo_ids is not None:
            allowed = set(repo_ids)
            hits = tuple(h for h in hits if h.repo_id in allowed)
        return hits[:limit]


class FakeMainSnapshotProvider:
    """Double de MainSnapshotProvider para read_file/list_tree sem Git."""

    def __init__(
        self,
        *,
        files: Mapping[tuple[str, str], bytes] | None = None,
        trees: Mapping[str, tuple[str, ...]] | None = None,
        fail: bool = False,
        fail_file_not_found: bool = False,
    ) -> None:
        self._files = dict(files or {})
        self._trees = dict(trees or {})
        self._fail = fail
        self._fail_file_not_found = fail_file_not_found
        self.read_file_calls: list[tuple[str, str]] = []
        self.list_tree_calls: list[str] = []
        self.call_count = 0

    def get_main_tip(self, source: SnapshotSource) -> MainSnapshot:
        raise SnapshotError("get_main_tip não usado em T16 tests")

    def list_tree(
        self, source: SnapshotSource, *, commit_sha: str
    ) -> tuple[str, ...]:
        self.call_count += 1
        self.list_tree_calls.append(commit_sha)
        if self._fail:
            raise SnapshotError("fake list_tree failure")
        return self._trees.get(commit_sha, ())

    def read_file(
        self, source: SnapshotSource, *, commit_sha: str, path: str
    ) -> bytes:
        self.call_count += 1
        self.read_file_calls.append((commit_sha, path))
        if self._fail:
            raise SnapshotError("fake read_file failure")
        if self._fail_file_not_found:
            raise FileNotFoundInCommitError(
                f"path ausente: {path} @ {commit_sha}"
            )
        key = (commit_sha, path)
        if key not in self._files:
            raise FileNotFoundInCommitError(
                f"path ausente: {path} @ {commit_sha}"
            )
        return self._files[key]

    def diff_files(
        self,
        source: SnapshotSource,
        *,
        from_commit: str | None,
        to_commit: str,
    ) -> FileDiffSet | FirstIndexSignal:
        raise SnapshotError("diff_files não usado em T16 tests")


class FakeSnapshotSourceResolver:
    """Double: CatalogEntry → LocalSnapshotSource sintético."""

    def __init__(self, *, fail: bool = False) -> None:
        self._fail = fail
        self.resolve_calls: list[int] = []

    def resolve(self, entry: CatalogEntry) -> SnapshotSource:
        self.resolve_calls.append(entry.id)
        if self._fail:
            raise SnapshotError("fake source resolve failure")
        if entry.origin == RepoOrigin.LOCAL and entry.local_path:
            return LocalSnapshotSource(local_path=entry.local_path)
        return LocalSnapshotSource(local_path=f"/fake/{entry.repo_identifier}")


class FakeQueryReformulator:
    """Double: mapping query → reformulated; nunca produz hits."""

    def __init__(
        self,
        *,
        mapping: Mapping[str, str] | None = None,
        fail: bool = False,
    ) -> None:
        self._mapping = dict(mapping or {})
        self._fail = fail
        self.call_count = 0
        self.last_query: str | None = None

    def reformulate(self, query: str) -> str:
        self.call_count += 1
        self.last_query = query
        if self._fail:
            raise RuntimeError("fake reformulator failure")
        return self._mapping.get(query, query)


class FakeQueryService:
    """Double completo de QueryService para T17/T18 sem DefaultQueryService."""

    def __init__(
        self,
        *,
        exact_hits: QueryHits | None = None,
        semantic_hits: QueryHits | None = None,
        file_content: FileContent | None = None,
        tree: TreeListing | None = None,
        fail: type[QueryError] | None = None,
    ) -> None:
        self._exact_hits = exact_hits or QueryHits(hits=())
        self._semantic_hits = semantic_hits or QueryHits(hits=())
        self._file_content = file_content or FileContent(content=b"")
        self._tree = tree or TreeListing(paths=())
        self._fail = fail

    def _maybe_fail(self) -> None:
        if self._fail is not None:
            raise self._fail("fake query service failure")

    def search_exact(self, request: ExactSearchRequest) -> QueryHits:
        self._maybe_fail()
        return self._exact_hits

    def search_semantic(self, request: SemanticSearchRequest) -> QueryHits:
        self._maybe_fail()
        return self._semantic_hits

    def read_file(self, request: ReadFileRequest) -> FileContent:
        self._maybe_fail()
        return self._file_content

    def list_tree(self, request: ListTreeRequest) -> TreeListing:
        self._maybe_fail()
        return self._tree
