"""
BDD executável — T16-query-services.

Valida BDD-009/010/012/024 na camada QueryService com fakes
(sem Zoekt/Qdrant/Git reais).

Execução:
    python -m pytest tests/bdd/test_query_services.py -q
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoOrigin
from github_rag.index.chunk.types import SemanticChunk, SourceLanguage
from github_rag.index.vector.errors import EmbeddingError, VectorStoreError
from github_rag.index.vector.types import ChunkMetadata, SemanticHit
from github_rag.index.zoekt.errors import ExactCodeIndexError
from github_rag.index.zoekt.fake import FakeExactCodeIndex
from github_rag.index.zoekt.models import FileToIndex
from github_rag.query.errors import (
    QueryCommitUnavailableError,
    QueryEmbeddingError,
    QueryError,
    QueryExactIndexError,
    QueryRepositoryNotFoundError,
    QuerySnapshotError,
    QueryValidationError,
    QueryVectorError,
)
from github_rag.query.fake import (
    FakeEmbedder,
    FakeMainSnapshotProvider,
    FakeQueryReformulator,
    FakeSnapshotSourceResolver,
    FakeVectorStore,
)
from github_rag.query.service import DefaultQueryService
from github_rag.query.types import (
    DetailFields,
    ExactSearchRequest,
    ListTreeRequest,
    ReadFileRequest,
    SemanticSearchRequest,
)
from github_rag.snapshot.errors import FileNotFoundInCommitError

REPO = "acme/api"
COMMIT = "abc123"
SECRET_TOKEN = "ghp_should_never_appear_in_errors_9f3a2"
QUERY_PKG = Path(__file__).resolve().parents[2] / "src" / "github_rag" / "query"
FORBIDDEN_IMPORTS = frozenset(
    {
        "qdrant_client",
        "openai",
        "httpx",
        "requests",
        "github",
        "git",
        "urllib",
        "urllib3",
    }
)


def _chunk(
    *,
    path: str = "src/auth.py",
    text: str = "login flow",
) -> SemanticChunk:
    return SemanticChunk(
        chunk_id="c1",
        path=path,
        language=SourceLanguage.PYTHON,
        kind="function",
        text=text,
        start_byte=0,
        end_byte=len(text),
        start_point=(0, 0),
        end_point=(0, len(text)),
    )


def _semantic_hit(
    *,
    repo_id: str = REPO,
    commit_sha: str = COMMIT,
    text: str = "login flow",
    score: float = 0.91,
) -> SemanticHit:
    return SemanticHit(
        score=score,
        repo_id=repo_id,
        commit_sha=commit_sha,
        chunk=_chunk(text=text),
        metadata=ChunkMetadata(summary="auth", keywords=("login",)),
    )


def _seed_catalog(
    catalog: InMemoryCatalogRepository,
    *,
    repo_identifier: str = REPO,
    last_processed_commit: str | None = COMMIT,
    active: bool = True,
) -> int:
    entry = catalog.upsert_repository(
        connection_name="gh",
        origin=RepoOrigin.GITHUB,
        repo_identifier=repo_identifier,
        github_org="acme",
    )
    if last_processed_commit is not None:
        entry = catalog.mark_queued(entry.id)
        entry = catalog.mark_indexing(entry.id)
        entry = catalog.mark_updated(entry.id, last_processed_commit)
    if not active:
        entry = catalog.deactivate_repository(entry.id)
    return entry.id


def _build_service(
    *,
    exact: FakeExactCodeIndex | None = None,
    embedder: FakeEmbedder | None = None,
    vector: FakeVectorStore | None = None,
    snapshot: FakeMainSnapshotProvider | None = None,
    catalog: InMemoryCatalogRepository | None = None,
    reformulator: FakeQueryReformulator | None = None,
) -> tuple[DefaultQueryService, dict]:
    exact = exact or FakeExactCodeIndex()
    embedder = embedder or FakeEmbedder()
    vector = vector or FakeVectorStore()
    snapshot = snapshot or FakeMainSnapshotProvider()
    catalog = catalog or InMemoryCatalogRepository()
    resolver = FakeSnapshotSourceResolver()
    svc = DefaultQueryService(
        exact_index=exact,
        vector_store=vector,
        embedder=embedder,
        snapshot=snapshot,
        catalog=catalog,
        source_resolver=resolver,
        reformulator=reformulator,
    )
    return svc, {
        "exact": exact,
        "embedder": embedder,
        "vector": vector,
        "snapshot": snapshot,
        "catalog": catalog,
        "resolver": resolver,
        "reformulator": reformulator,
    }


class TestQS01SearchExact(unittest.TestCase):
    """QS-01 / BDD-009."""

    def test_exact_matches_from_index(self) -> None:
        exact = FakeExactCodeIndex()
        exact.index(
            REPO,
            COMMIT,
            (
                FileToIndex(
                    repository=REPO,
                    path="src/auth.py",
                    commit=COMMIT,
                    content=b"def authenticate():\n    return True\n",
                ),
            ),
        )
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        svc, _ = _build_service(exact=exact, catalog=catalog)
        details = DetailFields(
            repository=True, path=True, commit=True, snippet=True
        )
        result = svc.search_exact(
            ExactSearchRequest(
                pattern="def authenticate",
                details=details,
                repo_key=REPO,
            )
        )
        self.assertGreaterEqual(len(result.hits), 1)
        self.assertTrue(all(h.kind == "exact" for h in result.hits))
        self.assertTrue(
            any(
                h.repository == REPO
                and h.path == "src/auth.py"
                and h.commit == COMMIT
                and h.snippet is not None
                and "def authenticate" in h.snippet
                and h.score is None
                for h in result.hits
            )
        )


class TestQS02SearchSemantic(unittest.TestCase):
    """QS-02 / BDD-010 / BR-011."""

    def test_semantic_via_embedder_and_store(self) -> None:
        query = "how does login work"
        vector = (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        hit = _semantic_hit()
        embedder = FakeEmbedder(vectors_by_text={query: vector})
        store = FakeVectorStore(hits_by_vector={vector: (hit,)})
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        svc, deps = _build_service(
            embedder=embedder, vector=store, catalog=catalog
        )
        details = DetailFields(
            repository=True, path=True, commit=True, snippet=True
        )
        result = svc.search_semantic(
            SemanticSearchRequest(
                query=query,
                details=details,
                repo_key=REPO,
                reformulate=False,
            )
        )
        self.assertGreaterEqual(len(result.hits), 1)
        h = result.hits[0]
        self.assertEqual(h.kind, "semantic")
        self.assertIsInstance(h.score, float)
        self.assertEqual(h.repository, REPO)
        self.assertEqual(h.path, "src/auth.py")
        self.assertEqual(h.commit, COMMIT)
        self.assertEqual(h.snippet, "login flow")
        self.assertEqual(deps["embedder"].call_count, 1)
        self.assertEqual(deps["vector"].search_call_count, 1)
        self.assertIsNone(deps["reformulator"])


class TestQS03DetailsOmitted(unittest.TestCase):
    """QS-03 / BDD-012."""

    def test_default_details_omit_optional_fields(self) -> None:
        exact = FakeExactCodeIndex()
        exact.index(
            REPO,
            COMMIT,
            (
                FileToIndex(
                    repository=REPO,
                    path="src/auth.py",
                    commit=COMMIT,
                    content=b"authenticate\n",
                ),
            ),
        )
        query = "login"
        vector = (0.5,) * 8
        embedder = FakeEmbedder(vectors_by_text={query: vector})
        store = FakeVectorStore(
            hits_by_vector={vector: (_semantic_hit(),)}
        )
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        svc, _ = _build_service(
            exact=exact, embedder=embedder, vector=store, catalog=catalog
        )
        exact_hits = svc.search_exact(
            ExactSearchRequest(pattern="authenticate", details=DetailFields())
        )
        semantic_hits = svc.search_semantic(
            SemanticSearchRequest(query=query, details=DetailFields())
        )
        for hit in (*exact_hits.hits, *semantic_hits.hits):
            self.assertIsNone(hit.repository)
            self.assertIsNone(hit.path)
            self.assertIsNone(hit.commit)
            self.assertIsNone(hit.snippet)
            self.assertIn(hit.kind, {"exact", "semantic"})
        self.assertIsInstance(semantic_hits.hits[0].score, float)


class TestQS04DetailsIncluded(unittest.TestCase):
    """QS-04 / BDD-012."""

    def test_requested_details_and_partial_matrix(self) -> None:
        exact = FakeExactCodeIndex()
        exact.index(
            REPO,
            COMMIT,
            (
                FileToIndex(
                    repository=REPO,
                    path="src/auth.py",
                    commit=COMMIT,
                    content=b"authenticate\n",
                ),
            ),
        )
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        svc, _ = _build_service(exact=exact, catalog=catalog)
        full = DetailFields(
            repository=True, path=True, commit=True, snippet=True
        )
        hits = svc.search_exact(
            ExactSearchRequest(pattern="authenticate", details=full)
        )
        self.assertGreaterEqual(len(hits.hits), 1)
        h = hits.hits[0]
        self.assertEqual(h.repository, REPO)
        self.assertEqual(h.path, "src/auth.py")
        self.assertEqual(h.commit, COMMIT)
        self.assertIsNotNone(h.snippet)

        path_only = DetailFields(path=True)
        hits2 = svc.search_exact(
            ExactSearchRequest(pattern="authenticate", details=path_only)
        )
        h2 = hits2.hits[0]
        self.assertEqual(h2.path, "src/auth.py")
        self.assertIsNone(h2.repository)
        self.assertIsNone(h2.commit)
        self.assertIsNone(h2.snippet)


class TestQS05NoParallelClients(unittest.TestCase):
    """QS-05 / BDD-024."""

    def test_query_package_has_no_forbidden_imports(self) -> None:
        for path in QUERY_PKG.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".", 1)[0]
                        self.assertNotIn(root, FORBIDDEN_IMPORTS, path.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    root = node.module.split(".", 1)[0]
                    self.assertNotIn(root, FORBIDDEN_IMPORTS, path.name)


class TestQS06ReadFile(unittest.TestCase):
    """QS-06."""

    def test_read_file_uses_last_processed_commit(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        snapshot = FakeMainSnapshotProvider(
            files={(COMMIT, "src/auth.py"): b"secret = 1\n"}
        )
        svc, _ = _build_service(catalog=catalog, snapshot=snapshot)
        details = DetailFields(repository=True, path=True, commit=True)
        result = svc.read_file(
            ReadFileRequest(
                repo_key=REPO,
                path="src/auth.py",
                commit_sha=None,
                details=details,
            )
        )
        self.assertEqual(result.content, b"secret = 1\n")
        self.assertEqual(snapshot.read_file_calls[-1], (COMMIT, "src/auth.py"))
        self.assertEqual(result.repository, REPO)
        self.assertEqual(result.path, "src/auth.py")
        self.assertEqual(result.commit, COMMIT)

        omitted = svc.read_file(
            ReadFileRequest(
                repo_key=REPO,
                path="src/auth.py",
                details=DetailFields(),
            )
        )
        self.assertEqual(omitted.content, b"secret = 1\n")
        self.assertIsNone(omitted.repository)
        self.assertIsNone(omitted.path)
        self.assertIsNone(omitted.commit)


class TestQS07ListTree(unittest.TestCase):
    """QS-07."""

    def test_list_tree_path_prefix(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        snapshot = FakeMainSnapshotProvider(
            trees={
                COMMIT: ("src/a.py", "src/b.py", "docs/readme.md"),
            }
        )
        svc, _ = _build_service(catalog=catalog, snapshot=snapshot)
        filtered = svc.list_tree(
            ListTreeRequest(repo_key=REPO, path_prefix="src/")
        )
        self.assertEqual(set(filtered.paths), {"src/a.py", "src/b.py"})
        self.assertEqual(snapshot.list_tree_calls[-1], COMMIT)

        full = svc.list_tree(ListTreeRequest(repo_key=REPO, path_prefix=None))
        self.assertEqual(
            set(full.paths), {"src/a.py", "src/b.py", "docs/readme.md"}
        )


class TestQS08TypedBackendErrors(unittest.TestCase):
    """QS-08."""

    def test_backend_errors_are_typed(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)

        exact = FakeExactCodeIndex(fail_operations={"search"})
        exact.index(
            REPO,
            COMMIT,
            (
                FileToIndex(
                    repository=REPO,
                    path="a.py",
                    commit=COMMIT,
                    content=b"x",
                ),
            ),
        )
        svc, _ = _build_service(exact=exact, catalog=catalog)
        with self.assertRaises(QueryExactIndexError) as ctx:
            svc.search_exact(ExactSearchRequest(pattern="x"))
        self.assertIsInstance(ctx.exception.__cause__, ExactCodeIndexError)
        self.assertNotIn(SECRET_TOKEN, str(ctx.exception))

        embedder = FakeEmbedder(fail=True)
        svc2, _ = _build_service(embedder=embedder, catalog=catalog)
        with self.assertRaises(QueryEmbeddingError) as ctx2:
            svc2.search_semantic(SemanticSearchRequest(query="login"))
        self.assertIsInstance(ctx2.exception.__cause__, EmbeddingError)

        store = FakeVectorStore(fail_search=True)
        embedder_ok = FakeEmbedder(
            vectors_by_text={"login": (1.0,) * 8}
        )
        svc3, _ = _build_service(
            embedder=embedder_ok, vector=store, catalog=catalog
        )
        with self.assertRaises(QueryVectorError) as ctx3:
            svc3.search_semantic(SemanticSearchRequest(query="login"))
        self.assertIsInstance(ctx3.exception.__cause__, VectorStoreError)

        snapshot = FakeMainSnapshotProvider(fail_file_not_found=True)
        svc4, _ = _build_service(catalog=catalog, snapshot=snapshot)
        with self.assertRaises(QuerySnapshotError) as ctx4:
            svc4.read_file(
                ReadFileRequest(repo_key=REPO, path="missing.py")
            )
        self.assertIsInstance(ctx4.exception.__cause__, FileNotFoundInCommitError)
        self.assertIsInstance(ctx4.exception, QueryError)


class TestQS09Reformulator(unittest.TestCase):
    """QS-09 / BR-011."""

    def test_reformulate_noop_without_port(self) -> None:
        query = "original query"
        vector = (2.0,) * 8
        hit = _semantic_hit(text="evidence from store")
        embedder = FakeEmbedder(vectors_by_text={query: vector})
        store = FakeVectorStore(hits_by_vector={vector: (hit,)})
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        svc, deps = _build_service(
            embedder=embedder, vector=store, catalog=catalog, reformulator=None
        )
        result = svc.search_semantic(
            SemanticSearchRequest(
                query=query,
                reformulate=True,
                details=DetailFields(snippet=True),
            )
        )
        self.assertEqual(deps["embedder"].last_texts, (query,))
        self.assertEqual(result.hits[0].snippet, "evidence from store")

    def test_reformulate_changes_embed_text_only(self) -> None:
        original = "short"
        reformed = "expanded auth login"
        vector = (3.0,) * 8
        hit = _semantic_hit(text="store evidence")
        embedder = FakeEmbedder(vectors_by_text={reformed: vector})
        store = FakeVectorStore(hits_by_vector={vector: (hit,)})
        reformulator = FakeQueryReformulator(mapping={original: reformed})
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        svc, deps = _build_service(
            embedder=embedder,
            vector=store,
            catalog=catalog,
            reformulator=reformulator,
        )
        result = svc.search_semantic(
            SemanticSearchRequest(
                query=original,
                reformulate=True,
                details=DetailFields(snippet=True),
            )
        )
        self.assertEqual(reformulator.call_count, 1)
        self.assertEqual(deps["embedder"].last_texts, (reformed,))
        self.assertEqual(result.hits[0].snippet, "store evidence")
        self.assertNotEqual(result.hits[0].snippet, reformed)


class TestQS10RepoNotFound(unittest.TestCase):
    """QS-10."""

    def test_missing_and_inactive(self) -> None:
        catalog = InMemoryCatalogRepository()
        repo_id = _seed_catalog(catalog, active=False)
        svc, _ = _build_service(catalog=catalog)
        with self.assertRaises(QueryRepositoryNotFoundError):
            svc.search_exact(
                ExactSearchRequest(pattern="x", repository_id=repo_id)
            )
        with self.assertRaises(QueryRepositoryNotFoundError):
            svc.search_exact(
                ExactSearchRequest(pattern="x", repo_key="missing/repo")
            )


class TestQS11CommitUnavailable(unittest.TestCase):
    """QS-11."""

    def test_browse_without_commit(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog, last_processed_commit=None)
        snapshot = FakeMainSnapshotProvider(
            files={("deadbeef", "a.py"): b"ok"}
        )
        svc, _ = _build_service(catalog=catalog, snapshot=snapshot)
        with self.assertRaises(QueryCommitUnavailableError):
            svc.read_file(ReadFileRequest(repo_key=REPO, path="a.py"))
        self.assertEqual(snapshot.call_count, 0)

        ok = svc.read_file(
            ReadFileRequest(
                repo_key=REPO, path="a.py", commit_sha="deadbeef"
            )
        )
        self.assertEqual(ok.content, b"ok")


class TestQS12EmptyQueries(unittest.TestCase):
    """QS-12."""

    def test_empty_pattern_and_query(self) -> None:
        exact = FakeExactCodeIndex()
        embedder = FakeEmbedder()
        store = FakeVectorStore()
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        svc, deps = _build_service(
            exact=exact, embedder=embedder, vector=store, catalog=catalog
        )
        empty = svc.search_exact(ExactSearchRequest(pattern="  \t"))
        self.assertEqual(empty.hits, ())

        with self.assertRaises(QueryValidationError):
            svc.search_semantic(SemanticSearchRequest(query="   "))
        self.assertEqual(deps["embedder"].call_count, 0)
        self.assertEqual(deps["vector"].search_call_count, 0)


if __name__ == "__main__":
    unittest.main()
