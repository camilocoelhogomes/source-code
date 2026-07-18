"""Testes unitários — QdrantVectorStore (T13)."""

from __future__ import annotations

import inspect
import unittest
from unittest.mock import MagicMock

from qdrant_client.models import PayloadSchemaType

from github_rag.index.chunk.types import SemanticChunk, SourceLanguage
from github_rag.index.vector.errors import (
    VectorDimensionError,
    VectorStoreError,
    VectorValidationError,
)
from github_rag.index.vector.qdrant_store import QdrantVectorStore
from github_rag.index.vector.types import RepoCommitScope, SemanticHit
from tests.unit.index.vector.fixtures import (
    VECTOR_SIZE,
    assert_no_chunking_params,
    make_chunk,
    make_enriched,
    make_record,
    make_store,
    normalize,
)

_PAYLOAD_INDEX_FIELDS = frozenset({"repo_id", "commit_sha", "path"})


def _index_field_names(client: MagicMock) -> set[str]:
    fields: set[str] = set()
    for c in client.create_payload_index.call_args_list:
        name = c.kwargs.get("field_name")
        if name is None and len(c.args) >= 2:
            name = c.args[1]
        if name is not None:
            fields.add(name)
    return fields


def _index_schemas(client: MagicMock) -> list[object]:
    schemas: list[object] = []
    for c in client.create_payload_index.call_args_list:
        schema = c.kwargs.get("field_schema")
        if schema is None:
            schema = c.kwargs.get("field_type")
        schemas.append(schema)
    return schemas


class TestUpsertAndSearch(unittest.TestCase):
    """UT-Q01, UT-Q02, UT-Q14, UT-Q15, UT-Q19."""

    def test_ut_q01_upsert_rehydrates_full_payload(self) -> None:
        store = make_store()
        scope = RepoCommitScope(repo_id="repo-a", commit_sha="aaa111")
        chunk = make_chunk(
            chunk_id="chunk-1",
            start_byte=10,
            end_byte=42,
            start_point=(2, 0),
            end_point=(5, 4),
        )
        enriched = make_enriched(
            chunk, summary="saudação hello", keywords=("greet",), symbols=("hello",)
        )
        vector = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(scope, [make_record(enriched, vector)])

        hits = store.search(vector, limit=5)
        self.assertGreaterEqual(len(hits), 1)
        hit = hits[0]
        self.assertIsInstance(hit, SemanticHit)
        self.assertEqual(hit.repo_id, "repo-a")
        self.assertEqual(hit.commit_sha, "aaa111")
        self.assertEqual(hit.chunk.chunk_id, "chunk-1")
        self.assertEqual(hit.chunk.path, "src/app.py")
        self.assertEqual(hit.chunk.language, SourceLanguage.PYTHON)
        self.assertEqual(hit.chunk.kind, "function")
        self.assertEqual(hit.chunk.text, chunk.text)
        self.assertEqual(hit.chunk.start_byte, 10)
        self.assertEqual(hit.chunk.end_byte, 42)
        self.assertEqual(hit.chunk.start_point, (2, 0))
        self.assertEqual(hit.chunk.end_point, (5, 4))
        self.assertEqual(hit.metadata.summary, "saudação hello")
        self.assertEqual(hit.metadata.keywords, ("greet",))
        self.assertEqual(hit.metadata.symbols, ("hello",))

    def test_ut_q02_closer_vector_ranks_first(self) -> None:
        store = make_store()
        scope = RepoCommitScope(repo_id="repo-a", commit_sha="c1")
        vec_a = normalize((1.0, 0.0, 0.0, 0.0))
        vec_b = normalize((0.0, 1.0, 0.0, 0.0))
        query = normalize((0.95, 0.05, 0.0, 0.0))
        store.upsert(
            scope,
            [
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="a", text="def auth():\n    pass\n"),
                        summary="auth",
                    ),
                    vec_a,
                ),
                make_record(
                    make_enriched(
                        make_chunk(
                            chunk_id="b",
                            path="src/other.py",
                            text="def paint():\n    pass\n",
                        ),
                        summary="paint",
                    ),
                    vec_b,
                ),
            ],
        )
        hits = store.search(query, limit=2)
        self.assertGreaterEqual(len(hits), 1)
        self.assertEqual(hits[0].chunk.chunk_id, "a")
        self.assertEqual(hits[0].metadata.summary, "auth")
        if len(hits) >= 2:
            self.assertGreater(hits[0].score, hits[1].score)

    def test_ut_q14_empty_keywords_symbols_ok(self) -> None:
        store = make_store()
        scope = RepoCommitScope("repo-a", "c1")
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            scope,
            [
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="empty-meta"),
                        summary="ok",
                        keywords=(),
                        symbols=(),
                    ),
                    vec,
                )
            ],
        )
        hits = store.search(vec, limit=5, repo_ids=["repo-a"])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].metadata.keywords, ())
        self.assertEqual(hits[0].metadata.symbols, ())

    def test_ut_q15_search_empty_collection(self) -> None:
        store = make_store()
        hits = store.search(normalize((1.0, 0.0, 0.0, 0.0)), limit=5)
        self.assertEqual(hits, ())

    def test_ut_q19_distinct_chunk_ids_yield_two_hits(self) -> None:
        store = make_store()
        scope = RepoCommitScope("repo-a", "c1")
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            scope,
            [
                make_record(
                    make_enriched(make_chunk(chunk_id="c-a"), summary="a"), vec
                ),
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="c-b", path="src/b.py"), summary="b"
                    ),
                    vec,
                ),
            ],
        )
        hits = store.search(vec, limit=10, repo_ids=["repo-a"])
        ids = {h.chunk.chunk_id for h in hits}
        self.assertEqual(ids, {"c-a", "c-b"})


class TestReplacePurgeDelete(unittest.TestCase):
    """UT-Q03, UT-Q07, UT-Q08, UT-Q09, UT-Q10, UT-Q13."""

    def test_ut_q03_replace_purges_old_commit(self) -> None:
        store = make_store()
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            RepoCommitScope("repo-a", "oldsha"),
            [
                make_record(
                    make_enriched(make_chunk(chunk_id="old-1"), summary="old"),
                    vec,
                )
            ],
        )
        store.replace_repo_commit(
            RepoCommitScope("repo-a", "newsha"),
            [
                make_record(
                    make_enriched(make_chunk(chunk_id="new-1"), summary="new"),
                    vec,
                )
            ],
        )
        hits = store.search(vec, limit=10, repo_ids=["repo-a"])
        self.assertTrue(hits)
        self.assertTrue(all(h.commit_sha == "newsha" for h in hits))
        self.assertFalse(any(h.commit_sha == "oldsha" for h in hits))
        self.assertEqual(hits[0].metadata.summary, "new")

    def test_ut_q07_purge_scoped_to_repo(self) -> None:
        store = make_store()
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            RepoCommitScope("repo-a", "oldsha"),
            [
                make_record(
                    make_enriched(make_chunk(chunk_id="a-old"), summary="a-old"),
                    vec,
                )
            ],
        )
        store.upsert(
            RepoCommitScope("repo-a", "keepsha"),
            [
                make_record(
                    make_enriched(make_chunk(chunk_id="a-keep"), summary="a-keep"),
                    vec,
                )
            ],
        )
        store.upsert(
            RepoCommitScope("repo-b", "other"),
            [
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="b-1", path="src/b.py"), summary="b"
                    ),
                    vec,
                )
            ],
        )
        store.purge_other_commits(RepoCommitScope("repo-a", "keepsha"))
        hits_a = store.search(vec, limit=20, repo_ids=["repo-a"])
        hits_b = store.search(vec, limit=20, repo_ids=["repo-b"])
        self.assertTrue(all(h.commit_sha == "keepsha" for h in hits_a))
        self.assertFalse(any(h.commit_sha == "oldsha" for h in hits_a))
        self.assertEqual(len(hits_b), 1)

    def test_ut_q08_empty_replace_clears_repo(self) -> None:
        store = make_store()
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            RepoCommitScope("repo-a", "old"),
            [make_record(make_enriched(make_chunk(chunk_id="x"), summary="x"), vec)],
        )
        store.replace_repo_commit(RepoCommitScope("repo-a", "tip"), ())
        self.assertEqual(len(store.search(vec, limit=10, repo_ids=["repo-a"])), 0)

    def test_ut_q09_delete_paths(self) -> None:
        store = make_store()
        scope_a = RepoCommitScope("repo-a", "c1")
        scope_b = RepoCommitScope("repo-b", "c1")
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            scope_a,
            [
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="pa", path="src/a.py"), summary="a"
                    ),
                    vec,
                ),
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="pb", path="src/b.py"), summary="b"
                    ),
                    vec,
                ),
            ],
        )
        store.upsert(
            scope_b,
            [
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="pc", path="src/c.py"), summary="c"
                    ),
                    vec,
                )
            ],
        )
        store.delete_paths(scope_a, ["src/a.py"])
        paths_a = {h.chunk.path for h in store.search(vec, limit=20, repo_ids=["repo-a"])}
        self.assertNotIn("src/a.py", paths_a)
        self.assertIn("src/b.py", paths_a)
        self.assertEqual(len(store.search(vec, limit=5, repo_ids=["repo-b"])), 1)

    def test_ut_q21_delete_paths_scoped_to_commit(self) -> None:
        """delete_paths só remove path no scope.commit_sha (interfaces §3.9)."""
        store = make_store()
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        path = "src/a.py"
        store.upsert(
            RepoCommitScope("repo-a", "oldsha"),
            [
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="old-a", path=path), summary="old"
                    ),
                    vec,
                )
            ],
        )
        store.upsert(
            RepoCommitScope("repo-a", "newsha"),
            [
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="new-a", path=path), summary="new"
                    ),
                    vec,
                )
            ],
        )
        store.delete_paths(RepoCommitScope("repo-a", "newsha"), [path])
        hits = store.search(vec, limit=20, repo_ids=["repo-a"])
        by_sha = {h.commit_sha: h for h in hits}
        self.assertIn("oldsha", by_sha)
        self.assertEqual(by_sha["oldsha"].chunk.path, path)
        self.assertNotIn("newsha", by_sha)

    def test_ut_q10_delete_repo(self) -> None:
        store = make_store()
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            RepoCommitScope("repo-a", "c1"),
            [make_record(make_enriched(make_chunk(chunk_id="a"), summary="a"), vec)],
        )
        store.upsert(
            RepoCommitScope("repo-b", "c1"),
            [
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="b", path="src/b.py"), summary="b"
                    ),
                    vec,
                )
            ],
        )
        store.delete_repo("repo-a")
        self.assertEqual(len(store.search(vec, limit=10, repo_ids=["repo-a"])), 0)
        self.assertEqual(len(store.search(vec, limit=5, repo_ids=["repo-b"])), 1)

    def test_ut_q13_upsert_does_not_purge_other_commits(self) -> None:
        store = make_store()
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            RepoCommitScope("repo-a", "oldsha"),
            [
                make_record(
                    make_enriched(make_chunk(chunk_id="old"), summary="old"), vec
                )
            ],
        )
        store.upsert(
            RepoCommitScope("repo-a", "newsha"),
            [
                make_record(
                    make_enriched(make_chunk(chunk_id="new"), summary="new"), vec
                )
            ],
        )
        hits = store.search(vec, limit=20, repo_ids=["repo-a"])
        shas = {h.commit_sha for h in hits}
        self.assertEqual(shas, {"oldsha", "newsha"})


class TestValidationAndDimensions(unittest.TestCase):
    """UT-Q04, UT-Q05, UT-Q06, UT-Q16, UT-Q17."""

    def test_ut_q04_empty_or_whitespace_summary(self) -> None:
        store = make_store()
        scope = RepoCommitScope("repo-a", "c1")
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        for summary in ("", "   "):
            with self.subTest(summary=repr(summary)):
                with self.assertRaises(VectorValidationError) as ctx:
                    store.upsert(
                        scope,
                        [
                            make_record(
                                make_enriched(
                                    make_chunk(chunk_id=f"s-{summary!r}"),
                                    summary=summary,
                                ),
                                vec,
                            )
                        ],
                    )
                self.assertIsInstance(ctx.exception, VectorStoreError)
        self.assertEqual(len(store.search(vec, limit=5, repo_ids=["repo-a"])), 0)

    def test_ut_q05_empty_text_and_chunk_id(self) -> None:
        store = make_store()
        scope = RepoCommitScope("repo-a", "c1")
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        empty_text = SemanticChunk(
            chunk_id="x",
            path="src/app.py",
            language=SourceLanguage.PYTHON,
            kind="function",
            text="",
            start_byte=0,
            end_byte=0,
            start_point=(0, 0),
            end_point=(0, 0),
        )
        with self.assertRaises(VectorValidationError):
            store.upsert(
                scope,
                [make_record(make_enriched(empty_text, summary="ok"), vec)],
            )
        with self.assertRaises(VectorValidationError):
            store.upsert(
                scope,
                [
                    make_record(
                        make_enriched(make_chunk(chunk_id=""), summary="ok"),
                        vec,
                    )
                ],
            )

    def test_ut_q06_wrong_dimension(self) -> None:
        store = make_store(vector_size=4)
        with self.assertRaises(VectorDimensionError) as ctx:
            store.upsert(
                RepoCommitScope("repo-a", "c1"),
                [
                    make_record(
                        make_enriched(make_chunk(chunk_id="d"), summary="ok"),
                        (1.0, 0.0),
                    )
                ],
            )
        self.assertIsInstance(ctx.exception, VectorStoreError)

    def test_ut_q16_empty_upsert_ok(self) -> None:
        store = make_store()
        store.upsert(RepoCommitScope("repo-a", "c1"), ())

    def test_ut_q17_invalid_scope(self) -> None:
        store = make_store()
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        record = make_record(
            make_enriched(make_chunk(chunk_id="x"), summary="ok"), vec
        )
        for scope in (
            RepoCommitScope("", "c1"),
            RepoCommitScope("   ", "c1"),
            RepoCommitScope("repo-a", ""),
            RepoCommitScope("repo-a", "  "),
        ):
            with self.subTest(scope=scope, method="upsert"):
                with self.assertRaises(VectorValidationError):
                    store.upsert(scope, [record])
            with self.subTest(scope=scope, method="purge"):
                with self.assertRaises(VectorValidationError):
                    store.purge_other_commits(scope)
            with self.subTest(scope=scope, method="replace"):
                with self.assertRaises(VectorValidationError):
                    store.replace_repo_commit(scope, ())
            with self.subTest(scope=scope, method="delete_paths"):
                with self.assertRaises(VectorValidationError):
                    store.delete_paths(scope, ["src/a.py"])

    def test_ut_q20_sdk_failure_maps_to_vector_store_error(self) -> None:
        """Falha do client Qdrant → VectorStoreError (interfaces §3.10)."""
        client = MagicMock()
        client.get_collection.side_effect = RuntimeError("qdrant down")
        client.get_collections.side_effect = RuntimeError("qdrant down")
        client.create_collection.side_effect = RuntimeError("qdrant down")
        client.upsert.side_effect = RuntimeError("qdrant down")
        store = QdrantVectorStore(
            client=client,
            collection_name="github_rag_chunks_unit",
            vector_size=VECTOR_SIZE,
        )
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        with self.assertRaises(VectorStoreError) as ctx:
            store.upsert(
                RepoCommitScope("repo-a", "c1"),
                [
                    make_record(
                        make_enriched(make_chunk(chunk_id="x"), summary="ok"),
                        vec,
                    )
                ],
            )
        self.assertNotIsInstance(ctx.exception, VectorValidationError)
        self.assertNotIsInstance(ctx.exception, VectorDimensionError)


class TestSearchFilterIdempotencySdk(unittest.TestCase):
    """UT-Q11, UT-Q12, UT-Q18, no-chunking."""

    def test_ut_q11_filter_and_limit(self) -> None:
        store = make_store()
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            RepoCommitScope("repo-a", "c1"),
            [make_record(make_enriched(make_chunk(chunk_id="a1"), summary="a"), vec)],
        )
        store.upsert(
            RepoCommitScope("repo-b", "c1"),
            [
                make_record(
                    make_enriched(
                        make_chunk(chunk_id="b1", path="src/b.py"), summary="b"
                    ),
                    vec,
                )
            ],
        )
        hits = store.search(vec, limit=1, repo_ids=["repo-a"])
        self.assertLessEqual(len(hits), 1)
        self.assertTrue(all(h.repo_id == "repo-a" for h in hits))

    def test_ut_q12_upsert_idempotent_point_id(self) -> None:
        store = make_store()
        scope = RepoCommitScope("repo-a", "c1")
        vec1 = normalize((1.0, 0.0, 0.0, 0.0))
        vec2 = normalize((0.0, 1.0, 0.0, 0.0))
        chunk = make_chunk(chunk_id="same-id")
        store.upsert(scope, [make_record(make_enriched(chunk, summary="v1"), vec1)])
        store.upsert(scope, [make_record(make_enriched(chunk, summary="v2"), vec2)])
        hits = store.search(vec2, limit=10, repo_ids=["repo-a"])
        same = [h for h in hits if h.chunk.chunk_id == "same-id"]
        self.assertEqual(len(same), 1)
        self.assertEqual(same[0].metadata.summary, "v2")

    def test_ut_q18_uses_official_qdrant_sdk(self) -> None:
        import qdrant_client  # noqa: F401

        source = inspect.getsource(QdrantVectorStore)
        self.assertIn("qdrant", source.lower())
        self.assertNotIn("requests.", source)
        self.assertNotIn("httpx.", source)
        self.assertNotIn("urllib.request", source)
        store = make_store()
        self.assertIsInstance(store, QdrantVectorStore)

    def test_no_chunking_params_on_store(self) -> None:
        assert_no_chunking_params(QdrantVectorStore)
        self.assertIn("records", inspect.signature(QdrantVectorStore.upsert).parameters)


class TestCoverageBranches(unittest.TestCase):
    """Cobertura de ramos tipados (delete vazio, ensure_collection, _invoke)."""

    def test_delete_repo_rejects_blank_repo_id(self) -> None:
        store = make_store()
        for repo_id in ("", "   "):
            with self.subTest(repo_id=repo_id):
                with self.assertRaises(VectorValidationError):
                    store.delete_repo(repo_id)

    def test_delete_paths_empty_is_noop(self) -> None:
        store = make_store()
        scope = RepoCommitScope("repo-a", "c1")
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            scope,
            [make_record(make_enriched(make_chunk(chunk_id="keep"), summary="ok"), vec)],
        )
        store.delete_paths(scope, ())
        hits = store.search(vec, limit=5, repo_ids=["repo-a"])
        self.assertEqual(len(hits), 1)

    def test_ensure_collection_reuses_existing(self) -> None:
        client = MagicMock()
        client.get_collection.return_value = MagicMock()
        store = QdrantVectorStore(
            client=client,
            collection_name="existing",
            vector_size=VECTOR_SIZE,
        )
        store._ensure_collection()
        client.get_collection.assert_called_once_with("existing")
        client.create_collection.assert_not_called()
        store._ensure_collection()
        self.assertEqual(client.get_collection.call_count, 1)

    def test_ensure_collection_create_race_recovers(self) -> None:
        client = MagicMock()
        client.get_collection.side_effect = [
            RuntimeError("missing"),
            MagicMock(),
        ]
        client.create_collection.side_effect = RuntimeError("already exists")
        store = QdrantVectorStore(
            client=client,
            collection_name="race",
            vector_size=VECTOR_SIZE,
        )
        store._ensure_collection()
        self.assertTrue(store._collection_ready)

    def test_ensure_collection_propagates_vector_store_error_on_get(self) -> None:
        client = MagicMock()
        client.get_collection.side_effect = VectorStoreError("auth failed")
        store = QdrantVectorStore(
            client=client,
            collection_name="denied",
            vector_size=VECTOR_SIZE,
        )
        with self.assertRaises(VectorStoreError) as ctx:
            store._ensure_collection()
        self.assertEqual(str(ctx.exception), "auth failed")
        client.create_collection.assert_not_called()

    def test_ensure_collection_propagates_vector_store_error_on_create(self) -> None:
        client = MagicMock()
        client.get_collection.side_effect = RuntimeError("missing")
        client.create_collection.side_effect = VectorStoreError("quota")
        store = QdrantVectorStore(
            client=client,
            collection_name="quota",
            vector_size=VECTOR_SIZE,
        )
        with self.assertRaises(VectorStoreError) as ctx:
            store._ensure_collection()
        self.assertEqual(str(ctx.exception), "quota")

    def test_invoke_reraises_vector_store_error(self) -> None:
        store = make_store()

        def boom() -> None:
            raise VectorStoreError("already typed")

        with self.assertRaises(VectorStoreError) as ctx:
            store._invoke("noop", boom)
        self.assertEqual(str(ctx.exception), "already typed")

    def test_invoke_wraps_generic_exception(self) -> None:
        store = make_store()

        def boom() -> None:
            raise RuntimeError("network")

        with self.assertRaises(VectorStoreError) as ctx:
            store._invoke("upsert", boom)
        self.assertIn("qdrant upsert failed", str(ctx.exception))
        self.assertIn("network", str(ctx.exception))


class TestPayloadIndexes(unittest.TestCase):
    """UT-Q22, UT-Q23, UT-Q24, UT-Q25 — create_payload_index no setup."""

    def test_ut_q22_indexes_requested_on_new_collection(self) -> None:
        client = MagicMock()
        client.get_collection.side_effect = RuntimeError("missing")
        client.create_collection.return_value = MagicMock()
        store = QdrantVectorStore(
            client=client,
            collection_name="new-coll",
            vector_size=VECTOR_SIZE,
        )
        store._ensure_collection()
        client.create_collection.assert_called_once()
        self.assertEqual(_index_field_names(client), _PAYLOAD_INDEX_FIELDS)
        self.assertEqual(len(client.create_payload_index.call_args_list), 3)
        for schema in _index_schemas(client):
            self.assertEqual(schema, PayloadSchemaType.KEYWORD)
        for c in client.create_payload_index.call_args_list:
            self.assertEqual(c.kwargs.get("collection_name"), "new-coll")
        self.assertTrue(store._collection_ready)

    def test_ut_q23_indexes_requested_when_collection_exists(self) -> None:
        client = MagicMock()
        client.get_collection.return_value = MagicMock()
        store = QdrantVectorStore(
            client=client,
            collection_name="existing",
            vector_size=VECTOR_SIZE,
        )
        store._ensure_collection()
        client.create_collection.assert_not_called()
        self.assertEqual(_index_field_names(client), _PAYLOAD_INDEX_FIELDS)
        self.assertEqual(len(client.create_payload_index.call_args_list), 3)
        for schema in _index_schemas(client):
            self.assertEqual(schema, PayloadSchemaType.KEYWORD)
        self.assertTrue(store._collection_ready)

    def test_ut_q24_index_failure_does_not_abort_setup(self) -> None:
        client = MagicMock()
        client.get_collection.return_value = MagicMock()
        client.create_payload_index.side_effect = RuntimeError("already exists")
        store = QdrantVectorStore(
            client=client,
            collection_name="idx-fail",
            vector_size=VECTOR_SIZE,
        )
        store._ensure_collection()
        self.assertTrue(store._collection_ready)
        self.assertEqual(client.create_payload_index.call_count, 3)

    def test_ut_q25_ready_skips_reindex_calls(self) -> None:
        client = MagicMock()
        client.get_collection.return_value = MagicMock()
        store = QdrantVectorStore(
            client=client,
            collection_name="cached",
            vector_size=VECTOR_SIZE,
        )
        store._ensure_collection()
        first_count = client.create_payload_index.call_count
        self.assertEqual(first_count, 3)
        store._ensure_collection()
        self.assertEqual(client.create_payload_index.call_count, first_count)
        self.assertEqual(client.get_collection.call_count, 1)

    def test_ut_q22_memory_client_setup_ok_with_warning(self) -> None:
        """`:memory:` emite UserWarning; setup e filtros seguem ok."""
        import warnings

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            store = make_store()
            store._ensure_collection()
        self.assertTrue(store._collection_ready)
        # Warning may or may not surface depending on SDK; filters must work.
        vec = normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            RepoCommitScope("repo-a", "c1"),
            [make_record(make_enriched(make_chunk(chunk_id="ix"), summary="ok"), vec)],
        )
        hits = store.search(vec, limit=5, repo_ids=["repo-a"])
        self.assertEqual(len(hits), 1)
        del caught  # recorded for debug; not asserted as SDK-dependent


if __name__ == "__main__":
    unittest.main()
