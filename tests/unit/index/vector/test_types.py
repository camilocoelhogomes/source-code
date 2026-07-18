"""Testes unitários — types frozen / composição (T13)."""

from __future__ import annotations

import dataclasses
import unittest

from github_rag.index.chunk.types import SemanticChunk, SourceLanguage
from github_rag.index.vector.types import (
    ChunkMetadata,
    EnrichedChunk,
    RepoCommitScope,
    SemanticHit,
    VectorRecord,
)


def _sample_chunk() -> SemanticChunk:
    return SemanticChunk(
        chunk_id="cid-1",
        path="src/app.py",
        language=SourceLanguage.PYTHON,
        kind="function",
        text="def f():\n    pass\n",
        start_byte=0,
        end_byte=16,
        start_point=(0, 0),
        end_point=(1, 0),
    )


class TestChunkMetadata(unittest.TestCase):
    """UT-T01, UT-T02."""

    def test_ut_t01_frozen(self) -> None:
        meta = ChunkMetadata(summary="s", keywords=("k",), symbols=("sym",))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            meta.summary = "x"  # type: ignore[misc]

    def test_ut_t02_symbols_default_empty(self) -> None:
        meta = ChunkMetadata(summary="s", keywords=("k",))
        self.assertEqual(meta.symbols, ())


class TestEnrichedAndScope(unittest.TestCase):
    """UT-T03, UT-T04, UT-T07."""

    def test_ut_t03_enriched_frozen(self) -> None:
        enriched = EnrichedChunk(
            chunk=_sample_chunk(),
            metadata=ChunkMetadata(summary="s", keywords=()),
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            enriched.metadata = ChunkMetadata(summary="other", keywords=())  # type: ignore[misc]

    def test_ut_t04_scope_frozen(self) -> None:
        scope = RepoCommitScope(repo_id="repo-a", commit_sha="abc")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            scope.repo_id = "other"  # type: ignore[misc]

    def test_ut_t07_composition_preserves_fields(self) -> None:
        chunk = _sample_chunk()
        meta = ChunkMetadata(
            summary="resumo",
            keywords=("a", "b"),
            symbols=("f",),
        )
        enriched = EnrichedChunk(chunk=chunk, metadata=meta)
        self.assertIs(enriched.chunk, chunk)
        self.assertEqual(enriched.metadata.summary, "resumo")
        self.assertEqual(enriched.metadata.keywords, ("a", "b"))
        self.assertEqual(enriched.metadata.symbols, ("f",))
        self.assertEqual(enriched.chunk.language, SourceLanguage.PYTHON)


class TestVectorRecordAndHit(unittest.TestCase):
    """UT-T05, UT-T06."""

    def test_ut_t05_vector_record_frozen(self) -> None:
        record = VectorRecord(
            enriched=EnrichedChunk(
                chunk=_sample_chunk(),
                metadata=ChunkMetadata(summary="s", keywords=()),
            ),
            vector=(1.0, 0.0, 0.0, 0.0),
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            record.vector = (0.0, 1.0, 0.0, 0.0)  # type: ignore[misc]

    def test_ut_t06_semantic_hit_frozen(self) -> None:
        hit = SemanticHit(
            score=0.9,
            repo_id="repo-a",
            commit_sha="c1",
            chunk=_sample_chunk(),
            metadata=ChunkMetadata(summary="s", keywords=()),
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            hit.score = 0.1  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
