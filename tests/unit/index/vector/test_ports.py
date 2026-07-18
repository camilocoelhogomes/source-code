"""Testes unitários — Protocols Embedder / VectorStore (T13)."""

from __future__ import annotations

import unittest
from typing import Sequence

from github_rag.index.vector.embedder import OpenAICompatibleEmbedder
from github_rag.index.vector.ports import Embedder, VectorStore
from github_rag.index.vector.qdrant_store import QdrantVectorStore
from github_rag.index.vector.types import (
    RepoCommitScope,
    SemanticHit,
    VectorRecord,
)
from tests.unit.index.vector.fixtures import (
    assert_no_chunking_params,
    make_embedder,
    make_store,
)


class _FakeEmbedder:
    @property
    def dimensions(self) -> int:
        return 4

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        return tuple((0.0,) * 4 for _ in texts)


class _FakeVectorStore:
    def upsert(
        self, scope: RepoCommitScope, records: Sequence[VectorRecord]
    ) -> None:
        return None

    def purge_other_commits(self, scope: RepoCommitScope) -> None:
        return None

    def replace_repo_commit(
        self, scope: RepoCommitScope, records: Sequence[VectorRecord]
    ) -> None:
        return None

    def delete_repo(self, repo_id: str) -> None:
        return None

    def delete_paths(
        self, scope: RepoCommitScope, paths: Sequence[str]
    ) -> None:
        return None

    def search(
        self,
        query_vector: Sequence[float],
        *,
        limit: int,
        repo_ids: Sequence[str] | None = None,
    ) -> tuple[SemanticHit, ...]:
        return ()


class TestPortsRuntimeCheckable(unittest.TestCase):
    """UT-P01, UT-P02, UT-P03."""

    def test_ut_p01_embedder_protocol(self) -> None:
        self.assertTrue(isinstance(_FakeEmbedder(), Embedder))

    def test_ut_p02_vector_store_protocol(self) -> None:
        self.assertTrue(isinstance(_FakeVectorStore(), VectorStore))

    def test_ut_p03_adapters_satisfy_ports(self) -> None:
        store = make_store()
        embedder = make_embedder()
        self.assertIsInstance(store, QdrantVectorStore)
        self.assertIsInstance(embedder, OpenAICompatibleEmbedder)
        self.assertTrue(isinstance(store, VectorStore))
        self.assertTrue(isinstance(embedder, Embedder))


class TestPortsNoChunkingParams(unittest.TestCase):
    """UT-P04 / VS-14."""

    def test_ut_p04_no_chunking_params_on_surfaces(self) -> None:
        assert_no_chunking_params(QdrantVectorStore)
        assert_no_chunking_params(OpenAICompatibleEmbedder)
        assert_no_chunking_params(_FakeEmbedder)
        assert_no_chunking_params(_FakeVectorStore)


if __name__ == "__main__":
    unittest.main()
