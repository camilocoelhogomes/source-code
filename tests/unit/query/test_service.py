"""Unit — DefaultQueryService corners (T16 / UT-V*/E*/F*/S*)."""

from __future__ import annotations

import unittest

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoOrigin
from github_rag.index.chunk.types import SemanticChunk, SourceLanguage
from github_rag.index.vector.types import ChunkMetadata, SemanticHit
from github_rag.index.zoekt.fake import FakeExactCodeIndex
from github_rag.index.zoekt.models import FileToIndex
from github_rag.query.errors import (
    QueryReformulatorError,
    QueryRepositoryNotFoundError,
    QueryValidationError,
)
from github_rag.query.fake import (
    FakeEmbedder,
    FakeMainSnapshotProvider,
    FakeQueryReformulator,
    FakeQueryService,
    FakeSnapshotSourceResolver,
    FakeVectorStore,
)
from github_rag.query.ports import QueryService
from github_rag.query.service import DefaultQueryService
from github_rag.query.types import (
    DetailFields,
    ExactSearchRequest,
    ListTreeRequest,
    QueryHits,
    ReadFileRequest,
    SemanticSearchRequest,
)

REPO = "acme/api"
OTHER = "acme/other"
COMMIT = "abc123"


def _seed(
    catalog: InMemoryCatalogRepository,
    *,
    repo_identifier: str = REPO,
    last_processed_commit: str | None = COMMIT,
) -> int:
    entry = catalog.upsert_repository(
        connection_name="gh",
        origin=RepoOrigin.GITHUB,
        repo_identifier=repo_identifier,
        github_org="acme",
    )
    if last_processed_commit is not None:
        catalog.mark_queued(entry.id)
        catalog.mark_indexing(entry.id)
        catalog.mark_updated(entry.id, last_processed_commit)
    return entry.id


def _svc(**kwargs: object) -> DefaultQueryService:
    catalog = kwargs.pop("catalog", InMemoryCatalogRepository())  # type: ignore[arg-type]
    if isinstance(catalog, InMemoryCatalogRepository) and not catalog.list_active_catalog():
        _seed(catalog)
    return DefaultQueryService(
        exact_index=kwargs.pop("exact_index", FakeExactCodeIndex()),  # type: ignore[arg-type]
        vector_store=kwargs.pop("vector_store", FakeVectorStore()),  # type: ignore[arg-type]
        embedder=kwargs.pop("embedder", FakeEmbedder()),  # type: ignore[arg-type]
        snapshot=kwargs.pop("snapshot", FakeMainSnapshotProvider()),  # type: ignore[arg-type]
        catalog=catalog,  # type: ignore[arg-type]
        source_resolver=kwargs.pop(
            "source_resolver", FakeSnapshotSourceResolver()
        ),  # type: ignore[arg-type]
        reformulator=kwargs.pop("reformulator", None),  # type: ignore[arg-type]
    )


class TestValidation(unittest.TestCase):
    def test_browse_requires_scope(self) -> None:
        svc = _svc()
        with self.assertRaises(QueryValidationError):
            svc.read_file(ReadFileRequest(path="a.py"))
        with self.assertRaises(QueryValidationError):
            svc.list_tree(ListTreeRequest())

    def test_conflicting_repo_key_and_id(self) -> None:
        catalog = InMemoryCatalogRepository()
        id_a = _seed(catalog, repo_identifier=REPO)
        _seed(catalog, repo_identifier=OTHER)
        svc = _svc(catalog=catalog)
        with self.assertRaises(QueryValidationError):
            svc.search_exact(
                ExactSearchRequest(
                    pattern="x",
                    repository_id=id_a,
                    repo_key=OTHER,
                )
            )

    def test_empty_read_path(self) -> None:
        svc = _svc()
        with self.assertRaises(QueryValidationError):
            svc.read_file(ReadFileRequest(repo_key=REPO, path="  "))

    def test_reformulator_failure(self) -> None:
        reformulator = FakeQueryReformulator(fail=True)
        embedder = FakeEmbedder()
        svc = _svc(reformulator=reformulator, embedder=embedder)
        with self.assertRaises(QueryReformulatorError):
            svc.search_semantic(
                SemanticSearchRequest(query="q", reformulate=True)
            )
        self.assertEqual(embedder.call_count, 0)

    def test_reformulate_false_skips_port(self) -> None:
        reformulator = FakeQueryReformulator(mapping={"q": "expanded"})
        vector = (1.0,) * 8
        hit = SemanticHit(
            score=0.1,
            repo_id=REPO,
            commit_sha=COMMIT,
            chunk=SemanticChunk(
                chunk_id="c",
                path="p.py",
                language=SourceLanguage.PYTHON,
                kind="function",
                text="t",
                start_byte=0,
                end_byte=1,
                start_point=(0, 0),
                end_point=(0, 1),
            ),
            metadata=ChunkMetadata(summary="s", keywords=()),
        )
        embedder = FakeEmbedder(vectors_by_text={"q": vector})
        store = FakeVectorStore(hits_by_vector={vector: (hit,)})
        svc = _svc(
            reformulator=reformulator, embedder=embedder, vector_store=store
        )
        svc.search_semantic(
            SemanticSearchRequest(query="q", reformulate=False)
        )
        self.assertEqual(reformulator.call_count, 0)
        self.assertEqual(embedder.last_texts, ("q",))


class TestScopeAndSearch(unittest.TestCase):
    def test_multi_repo_exact(self) -> None:
        exact = FakeExactCodeIndex()
        for repo in (REPO, OTHER):
            exact.index(
                repo,
                COMMIT,
                (
                    FileToIndex(
                        repository=repo,
                        path="x.py",
                        commit=COMMIT,
                        content=b"shared_token\n",
                    ),
                ),
            )
        catalog = InMemoryCatalogRepository()
        _seed(catalog, repo_identifier=REPO)
        _seed(catalog, repo_identifier=OTHER)
        svc = _svc(exact_index=exact, catalog=catalog)
        hits = svc.search_exact(
            ExactSearchRequest(
                pattern="shared_token",
                details=DetailFields(repository=True),
            )
        )
        repos = {h.repository for h in hits.hits}
        self.assertEqual(repos, {REPO, OTHER})

    def test_semantic_filters_repo_ids(self) -> None:
        vector = (4.0,) * 8
        hits = (
            SemanticHit(
                score=0.9,
                repo_id=REPO,
                commit_sha=COMMIT,
                chunk=SemanticChunk(
                    chunk_id="c1",
                    path="a.py",
                    language=SourceLanguage.PYTHON,
                    kind="function",
                    text="a",
                    start_byte=0,
                    end_byte=1,
                    start_point=(0, 0),
                    end_point=(0, 1),
                ),
                metadata=ChunkMetadata(summary="s", keywords=()),
            ),
            SemanticHit(
                score=0.8,
                repo_id=OTHER,
                commit_sha=COMMIT,
                chunk=SemanticChunk(
                    chunk_id="c2",
                    path="b.py",
                    language=SourceLanguage.PYTHON,
                    kind="function",
                    text="b",
                    start_byte=0,
                    end_byte=1,
                    start_point=(0, 0),
                    end_point=(0, 1),
                ),
                metadata=ChunkMetadata(summary="s", keywords=()),
            ),
        )
        embedder = FakeEmbedder(vectors_by_text={"q": vector})
        store = FakeVectorStore(hits_by_vector={vector: hits})
        catalog = InMemoryCatalogRepository()
        _seed(catalog)
        svc = _svc(embedder=embedder, vector_store=store, catalog=catalog)
        result = svc.search_semantic(
            SemanticSearchRequest(
                query="q",
                repo_key=REPO,
                details=DetailFields(repository=True),
            )
        )
        self.assertEqual(store.last_repo_ids, (REPO,))
        self.assertTrue(all(h.repository == REPO for h in result.hits))

    def test_missing_repo_id(self) -> None:
        svc = _svc()
        with self.assertRaises(QueryRepositoryNotFoundError):
            svc.search_exact(
                ExactSearchRequest(pattern="x", repository_id=99999)
            )


class TestFakeQueryService(unittest.TestCase):
    def test_protocol_and_fail(self) -> None:
        fake: QueryService = FakeQueryService(
            exact_hits=QueryHits(hits=()),
            fail=QueryValidationError,
        )
        self.assertIsInstance(fake, QueryService)
        with self.assertRaises(QueryValidationError):
            fake.search_exact(ExactSearchRequest(pattern="x"))

class TestCoverageCorners(unittest.TestCase):
    def test_matching_repo_key_and_id(self) -> None:
        catalog = InMemoryCatalogRepository()
        repo_id = _seed(catalog, repo_identifier=REPO)
        svc = _svc(catalog=catalog)
        hits = svc.search_exact(
            ExactSearchRequest(
                pattern="zzz_absent",
                repository_id=repo_id,
                repo_key=REPO,
            )
        )
        self.assertEqual(hits.hits, ())

    def test_reformulator_error_passthrough(self) -> None:
        class Boom:
            def reformulate(self, query: str) -> str:
                raise QueryReformulatorError("direct")

        embedder = FakeEmbedder()
        svc = _svc(reformulator=Boom(), embedder=embedder)
        with self.assertRaises(QueryReformulatorError):
            svc.search_semantic(
                SemanticSearchRequest(query="q", reformulate=True)
            )

    def test_empty_embed_vectors(self) -> None:
        class EmptyEmbedder:
            dimensions = 8

            def embed(self, texts):
                return ()

        catalog = InMemoryCatalogRepository()
        _seed(catalog)
        svc = DefaultQueryService(
            exact_index=FakeExactCodeIndex(),
            vector_store=FakeVectorStore(),
            embedder=EmptyEmbedder(),
            snapshot=FakeMainSnapshotProvider(),
            catalog=catalog,
            source_resolver=FakeSnapshotSourceResolver(),
        )
        from github_rag.query.errors import QueryEmbeddingError

        with self.assertRaises(QueryEmbeddingError):
            svc.search_semantic(SemanticSearchRequest(query="q"))

    def test_list_tree_snapshot_error(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed(catalog)
        snapshot = FakeMainSnapshotProvider(fail=True)
        svc = _svc(catalog=catalog, snapshot=snapshot)
        from github_rag.query.errors import QuerySnapshotError

        with self.assertRaises(QuerySnapshotError):
            svc.list_tree(ListTreeRequest(repo_key=REPO))

    def test_fake_methods_coverage(self) -> None:
        from github_rag.index.vector.types import RepoCommitScope, VectorRecord
        from github_rag.index.chunk.types import SemanticChunk, SourceLanguage
        from github_rag.index.vector.types import ChunkMetadata, EnrichedChunk
        from github_rag.query.types import FileContent, TreeListing
        from github_rag.snapshot.models import LocalSnapshotSource

        store = FakeVectorStore()
        scope = RepoCommitScope(repo_id=REPO, commit_sha=COMMIT)
        store.upsert(scope, ())
        store.purge_other_commits(scope)
        store.replace_repo_commit(scope, ())
        store.delete_repo(REPO)
        store.delete_paths(scope, ("a.py",))

        snap = FakeMainSnapshotProvider(
            files={(COMMIT, "a.py"): b"x"},
            trees={COMMIT: ("a.py",)},
        )
        src = LocalSnapshotSource(local_path="/x")
        with self.assertRaises(Exception):
            snap.get_main_tip(src)
        with self.assertRaises(Exception):
            snap.diff_files(src, from_commit=None, to_commit=COMMIT)

        embedder = FakeEmbedder(dimensions=4)
        self.assertEqual(embedder.dimensions, 4)
        vectors = embedder.embed(("unknown text",))
        self.assertEqual(len(vectors[0]), 4)

        snap2 = FakeMainSnapshotProvider(fail=True)
        with self.assertRaises(Exception):
            snap2.read_file(src, commit_sha=COMMIT, path="a.py")
        with self.assertRaises(Exception):
            snap2.list_tree(src, commit_sha=COMMIT)

        resolver = FakeSnapshotSourceResolver(fail=True)
        catalog = InMemoryCatalogRepository()
        entry = catalog.upsert_repository(
            connection_name="gh",
            origin=RepoOrigin.GITHUB,
            repo_identifier=REPO,
            github_org="acme",
        )
        with self.assertRaises(Exception):
            resolver.resolve(entry)

        fake = FakeQueryService(
            file_content=FileContent(content=b"z"),
            tree=TreeListing(paths=("p.py",)),
            semantic_hits=QueryHits(hits=()),
        )
        self.assertEqual(
            fake.read_file(ReadFileRequest(repo_key=REPO, path="p.py")).content,
            b"z",
        )
        self.assertEqual(
            fake.list_tree(ListTreeRequest(repo_key=REPO)).paths, ("p.py",)
        )
        self.assertEqual(
            fake.search_semantic(SemanticSearchRequest(query="q")).hits, ()
        )

if __name__ == "__main__":
    unittest.main()


