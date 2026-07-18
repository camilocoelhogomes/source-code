"""
BDD executável — T13-qdrant-vector-store.

Valida VS-01..VS-14 (BDD-010, BDD-024, DEC-003, reindex, invariantes, corners)
conforme bdd.md 0.1.1 / design 0.1.0.

Estratégia (design §11): QdrantClient(":memory:") + stub openai para Embedder.

Execução:
    python -m pytest tests/bdd/test_qdrant_vector_store.py -q
"""

from __future__ import annotations

import inspect
import math
import unittest
from typing import Any
from unittest.mock import MagicMock

# Imports do contrato T13 primeiro — RED esperado enquanto a API não existir.
from github_rag.index.vector.types import (
    ChunkMetadata,
    EnrichedChunk,
    RepoCommitScope,
    SemanticHit,
    VectorRecord,
)
from github_rag.index.vector.errors import (
    EmbeddingError,
    EmbeddingValidationError,
    VectorDimensionError,
    VectorStoreError,
    VectorValidationError,
)
from github_rag.index.vector.qdrant_store import QdrantVectorStore
from github_rag.index.vector.embedder import OpenAICompatibleEmbedder
from github_rag.index.chunk.types import SemanticChunk, SourceLanguage

_VECTOR_SIZE = 4
_CHUNKING_PARAM_NAMES = frozenset(
    {"max_chars", "chunk_size", "overlap", "max_lines", "window_size"}
)


def _normalize(v: tuple[float, ...]) -> tuple[float, ...]:
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return tuple(x / norm for x in v)


def _chunk(
    *,
    chunk_id: str,
    path: str = "src/app.py",
    text: str = "def hello():\n    return 1\n",
    kind: str = "function",
    start_byte: int | None = None,
    end_byte: int | None = None,
    start_point: tuple[int, int] = (0, 0),
    end_point: tuple[int, int] = (1, 0),
) -> SemanticChunk:
    encoded = text.encode("utf-8")
    sb = 0 if start_byte is None else start_byte
    eb = len(encoded) if end_byte is None else end_byte
    return SemanticChunk(
        chunk_id=chunk_id,
        path=path,
        language=SourceLanguage.PYTHON,
        kind=kind,
        text=text,
        start_byte=sb,
        end_byte=eb,
        start_point=start_point,
        end_point=end_point,
    )


def _enriched(
    chunk: SemanticChunk,
    *,
    summary: str = "função hello",
    keywords: tuple[str, ...] = ("hello",),
    symbols: tuple[str, ...] = ("hello",),
) -> EnrichedChunk:
    return EnrichedChunk(
        chunk=chunk,
        metadata=ChunkMetadata(summary=summary, keywords=keywords, symbols=symbols),
    )


def _record(
    enriched: EnrichedChunk,
    vector: tuple[float, ...],
) -> VectorRecord:
    return VectorRecord(enriched=enriched, vector=vector)


def _make_store(vector_size: int = _VECTOR_SIZE) -> QdrantVectorStore:
    from qdrant_client import QdrantClient

    client = QdrantClient(":memory:")
    return QdrantVectorStore(
        client=client,
        collection_name="github_rag_chunks_bdd",
        vector_size=vector_size,
    )


def _make_embedder(*, client: Any | None = None) -> OpenAICompatibleEmbedder:
    stub = client if client is not None else MagicMock()
    return OpenAICompatibleEmbedder(
        client=stub,
        model="test-embedding",
        dimensions=_VECTOR_SIZE,
    )


def _public_callables(cls: type) -> list[Any]:
    items: list[Any] = [cls.__init__]
    for name, member in inspect.getmembers(cls):
        if name.startswith("_"):
            continue
        if inspect.isfunction(member) or inspect.ismethod(member):
            items.append(member)
    return items


def _assert_no_chunking_params(cls: type) -> None:
    for fn in _public_callables(cls):
        try:
            params = inspect.signature(fn).parameters
        except (TypeError, ValueError):
            continue
        overlap = _CHUNKING_PARAM_NAMES.intersection(params)
        assert not overlap, f"{cls.__name__}.{fn.__name__} expõe {overlap}"


class TestVS01UpsertPersistsChunkAndMetadata(unittest.TestCase):
    """VS-01 / BDD-010 — upsert persiste chunk Tree-sitter + metadados SLM."""

    def test_upsert_then_search_rehydrates_payload(self) -> None:
        store = _make_store()
        scope = RepoCommitScope(repo_id="repo-a", commit_sha="aaa111")
        chunk = _chunk(
            chunk_id="chunk-1",
            start_byte=10,
            end_byte=42,
            start_point=(2, 0),
            end_point=(5, 4),
        )
        enriched = _enriched(chunk, summary="saudação hello", keywords=("greet",))
        vector = _normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(scope, [_record(enriched, vector)])

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


class TestVS02SemanticSearchRanking(unittest.TestCase):
    """VS-02 / BDD-010 — search retorna hits semanticamente relacionados."""

    def test_closer_vector_ranks_first(self) -> None:
        store = _make_store()
        scope = RepoCommitScope(repo_id="repo-a", commit_sha="c1")
        vec_a = _normalize((1.0, 0.0, 0.0, 0.0))
        vec_b = _normalize((0.0, 1.0, 0.0, 0.0))
        query = _normalize((0.95, 0.05, 0.0, 0.0))

        rec_a = _record(
            _enriched(_chunk(chunk_id="a", text="def auth():\n    pass\n"), summary="auth"),
            vec_a,
        )
        rec_b = _record(
            _enriched(
                _chunk(chunk_id="b", path="src/other.py", text="def paint():\n    pass\n"),
                summary="paint",
            ),
            vec_b,
        )
        store.upsert(scope, [rec_a, rec_b])

        hits = store.search(query, limit=2)
        self.assertGreaterEqual(len(hits), 1)
        self.assertEqual(hits[0].chunk.chunk_id, "a")
        self.assertEqual(hits[0].metadata.summary, "auth")
        self.assertEqual(hits[0].chunk.path, "src/app.py")
        if len(hits) >= 2:
            self.assertGreater(hits[0].score, hits[1].score)
            self.assertEqual(hits[1].chunk.chunk_id, "b")


class TestVS03ReplaceRepoCommit(unittest.TestCase):
    """VS-03 — replace_repo_commit substitui vetores do commit anterior."""

    def test_old_commit_purged_after_replace(self) -> None:
        store = _make_store()
        old = RepoCommitScope(repo_id="repo-a", commit_sha="oldsha")
        new = RepoCommitScope(repo_id="repo-a", commit_sha="newsha")
        vec = _normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            old,
            [
                _record(
                    _enriched(_chunk(chunk_id="old-1"), summary="old summary"),
                    vec,
                )
            ],
        )
        store.replace_repo_commit(
            new,
            [
                _record(
                    _enriched(_chunk(chunk_id="new-1"), summary="new summary"),
                    vec,
                )
            ],
        )

        hits = store.search(vec, limit=10, repo_ids=["repo-a"])
        self.assertTrue(hits)
        self.assertTrue(all(h.commit_sha == "newsha" for h in hits))
        self.assertFalse(any(h.commit_sha == "oldsha" for h in hits))
        self.assertEqual(hits[0].metadata.summary, "new summary")
        self.assertEqual(hits[0].chunk.chunk_id, "new-1")


class TestVS04UpsertInvariants(unittest.TestCase):
    """VS-04 — upsert exige chunk Tree-sitter + metadata SLM válidos."""

    def test_empty_summary_raises(self) -> None:
        store = _make_store()
        scope = RepoCommitScope(repo_id="repo-a", commit_sha="c1")
        vec = _normalize((1.0, 0.0, 0.0, 0.0))
        bad = _record(
            _enriched(_chunk(chunk_id="x"), summary="   "),
            vec,
        )
        with self.assertRaises(VectorValidationError) as ctx:
            store.upsert(scope, [bad])
        self.assertIsInstance(ctx.exception, VectorStoreError)

        hits = store.search(vec, limit=5, repo_ids=["repo-a"])
        self.assertEqual(len(hits), 0)

    def test_empty_chunk_text_raises(self) -> None:
        store = _make_store()
        scope = RepoCommitScope(repo_id="repo-a", commit_sha="c1")
        vec = _normalize((1.0, 0.0, 0.0, 0.0))
        chunk = SemanticChunk(
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
            store.upsert(scope, [_record(_enriched(chunk, summary="ok"), vec)])

    def test_empty_chunk_id_raises(self) -> None:
        store = _make_store()
        scope = RepoCommitScope(repo_id="repo-a", commit_sha="c1")
        vec = _normalize((1.0, 0.0, 0.0, 0.0))
        with self.assertRaises(VectorValidationError):
            store.upsert(
                scope,
                [_record(_enriched(_chunk(chunk_id=""), summary="ok"), vec)],
            )


class TestVS05QdrantOfficialSdk(unittest.TestCase):
    """VS-05 / BDD-024 — Qdrant via qdrant-client."""

    def test_adapter_uses_qdrant_client(self) -> None:
        import qdrant_client  # noqa: F401 — presença do SDK oficial

        source = inspect.getsource(QdrantVectorStore)
        self.assertIn("qdrant", source.lower())
        self.assertNotIn("requests.", source)
        self.assertNotIn("httpx.", source)
        self.assertNotIn("urllib.request", source)

        store = _make_store()
        self.assertIsInstance(store, QdrantVectorStore)


class TestVS06OpenAIEmbedderSdk(unittest.TestCase):
    """VS-06 / BDD-024 — embeddings via openai; sem chat/completions."""

    def test_adapter_uses_openai_embeddings_only(self) -> None:
        import openai  # noqa: F401 — presença do SDK oficial

        source = inspect.getsource(OpenAICompatibleEmbedder)
        self.assertIn("openai", source.lower())
        self.assertIn("embeddings", source.lower())
        self.assertNotIn("chat.completions", source)
        self.assertNotIn("requests.", source)
        self.assertNotIn("httpx.", source)


class TestVS07PurgeOtherCommits(unittest.TestCase):
    """VS-07 — purge_other_commits remove só outros commits do mesmo repo."""

    def test_purge_scoped_to_repo(self) -> None:
        store = _make_store()
        vec = _normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            RepoCommitScope("repo-a", "oldsha"),
            [_record(_enriched(_chunk(chunk_id="a-old"), summary="a-old"), vec)],
        )
        store.upsert(
            RepoCommitScope("repo-a", "keepsha"),
            [_record(_enriched(_chunk(chunk_id="a-keep"), summary="a-keep"), vec)],
        )
        store.upsert(
            RepoCommitScope("repo-b", "other"),
            [
                _record(
                    _enriched(
                        _chunk(chunk_id="b-1", path="src/b.py"),
                        summary="b",
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
        self.assertEqual(hits_b[0].repo_id, "repo-b")


class TestVS08EmptyReplaceClearsRepo(unittest.TestCase):
    """VS-08 — replace_repo_commit com records vazios limpa o repo."""

    def test_empty_replace(self) -> None:
        store = _make_store()
        scope_old = RepoCommitScope("repo-a", "old")
        vec = _normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            scope_old,
            [_record(_enriched(_chunk(chunk_id="x"), summary="x"), vec)],
        )
        store.replace_repo_commit(RepoCommitScope("repo-a", "tip"), ())
        hits = store.search(vec, limit=10, repo_ids=["repo-a"])
        self.assertEqual(len(hits), 0)


class TestVS09VectorDimensionError(unittest.TestCase):
    """VS-09 — dimensão incompatível → VectorDimensionError."""

    def test_wrong_dimension(self) -> None:
        store = _make_store(vector_size=4)
        scope = RepoCommitScope("repo-a", "c1")
        bad_vec = (1.0, 0.0)  # len 2 != 4
        with self.assertRaises(VectorDimensionError) as ctx:
            store.upsert(
                scope,
                [_record(_enriched(_chunk(chunk_id="d"), summary="ok"), bad_vec)],
            )
        self.assertIsInstance(ctx.exception, VectorStoreError)


class TestVS10DeleteRepoAndPaths(unittest.TestCase):
    """VS-10 — delete_paths e delete_repo."""

    def test_delete_paths_then_delete_repo(self) -> None:
        store = _make_store()
        scope_a = RepoCommitScope("repo-a", "c1")
        scope_b = RepoCommitScope("repo-b", "c1")
        vec = _normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            scope_a,
            [
                _record(
                    _enriched(_chunk(chunk_id="pa", path="src/a.py"), summary="a"),
                    vec,
                ),
                _record(
                    _enriched(_chunk(chunk_id="pb", path="src/b.py"), summary="b"),
                    vec,
                ),
            ],
        )
        store.upsert(
            scope_b,
            [
                _record(
                    _enriched(_chunk(chunk_id="pc", path="src/c.py"), summary="c"),
                    vec,
                )
            ],
        )

        store.delete_paths(scope_a, ["src/a.py"])
        hits_a = store.search(vec, limit=20, repo_ids=["repo-a"])
        paths_a = {h.chunk.path for h in hits_a}
        self.assertNotIn("src/a.py", paths_a)
        self.assertIn("src/b.py", paths_a)
        self.assertEqual(len(store.search(vec, limit=5, repo_ids=["repo-b"])), 1)

        store.delete_repo("repo-a")
        self.assertEqual(len(store.search(vec, limit=10, repo_ids=["repo-a"])), 0)
        self.assertEqual(len(store.search(vec, limit=5, repo_ids=["repo-b"])), 1)


class TestVS11SearchFilterAndLimit(unittest.TestCase):
    """VS-11 — filtro repo_ids e limit."""

    def test_filter_and_limit(self) -> None:
        store = _make_store()
        vec = _normalize((1.0, 0.0, 0.0, 0.0))
        store.upsert(
            RepoCommitScope("repo-a", "c1"),
            [_record(_enriched(_chunk(chunk_id="a1"), summary="a"), vec)],
        )
        store.upsert(
            RepoCommitScope("repo-b", "c1"),
            [
                _record(
                    _enriched(_chunk(chunk_id="b1", path="src/b.py"), summary="b"),
                    vec,
                )
            ],
        )
        hits = store.search(vec, limit=1, repo_ids=["repo-a"])
        self.assertLessEqual(len(hits), 1)
        self.assertTrue(all(h.repo_id == "repo-a" for h in hits))


class TestVS12EmbedderPortCorners(unittest.TestCase):
    """VS-12 — OpenAICompatibleEmbedder: batch vazio e texto inválido."""

    def test_empty_batch_and_blank_text(self) -> None:
        stub = MagicMock()
        embedder = _make_embedder(client=stub)
        self.assertEqual(embedder.embed(()), ())
        stub.embeddings.create.assert_not_called()

        with self.assertRaises(EmbeddingValidationError) as ctx:
            embedder.embed(("   ",))
        self.assertIsInstance(ctx.exception, EmbeddingError)
        stub.embeddings.create.assert_not_called()


class TestVS13UpsertIdempotentPointId(unittest.TestCase):
    """VS-13 — upsert idempotente por point id (repo/commit/chunk_id)."""

    def test_second_upsert_overwrites(self) -> None:
        store = _make_store()
        scope = RepoCommitScope("repo-a", "c1")
        vec1 = _normalize((1.0, 0.0, 0.0, 0.0))
        vec2 = _normalize((0.0, 1.0, 0.0, 0.0))
        chunk = _chunk(chunk_id="same-id")
        store.upsert(scope, [_record(_enriched(chunk, summary="v1"), vec1)])
        store.upsert(scope, [_record(_enriched(chunk, summary="v2"), vec2)])

        hits = store.search(vec2, limit=10, repo_ids=["repo-a"])
        same = [h for h in hits if h.chunk.chunk_id == "same-id"]
        self.assertEqual(len(same), 1)
        self.assertEqual(same[0].metadata.summary, "v2")


class TestVS14NoChunkRedefinition(unittest.TestCase):
    """VS-14 — DEC-003 / ENG-008: T13 não redefine unidade de chunk."""

    def test_no_chunking_params_on_production_surfaces(self) -> None:
        _assert_no_chunking_params(QdrantVectorStore)
        _assert_no_chunking_params(OpenAICompatibleEmbedder)

        upsert_sig = inspect.signature(QdrantVectorStore.upsert)
        self.assertIn("records", upsert_sig.parameters)
        replace_sig = inspect.signature(QdrantVectorStore.replace_repo_commit)
        self.assertIn("records", replace_sig.parameters)


if __name__ == "__main__":
    unittest.main()
