"""Unit tests — DefaultFileRagPipeline."""

from __future__ import annotations

import unittest

from github_rag.index.metadata.fakes import FakeMetadataGenerator
from github_rag.indexing.errors import IndexingPipelineError
from github_rag.indexing.pipeline import DefaultFileRagPipeline
from tests.unit.indexing.helpers import FakeChunker, FakeEmbedder


class TestFileRagPipeline(unittest.TestCase):
    def test_empty_chunks(self) -> None:
        pipe = DefaultFileRagPipeline(
            chunker=FakeChunker(),
            metadata_generator=FakeMetadataGenerator(),
            embedder=FakeEmbedder(),
        )
        # whitespace-only still produces chunk from FakeChunker if non-empty after strip
        self.assertEqual(
            pipe.process_file(path="x.py", content=b"   \n"),
            (),
        )

    def test_success_records(self) -> None:
        pipe = DefaultFileRagPipeline(
            chunker=FakeChunker(),
            metadata_generator=FakeMetadataGenerator(),
            embedder=FakeEmbedder(),
        )
        records = pipe.process_file(path="a.py", content=b"def a():\n  return 1\n")
        self.assertEqual(len(records), 1)
        self.assertEqual(len(records[0].vector), 3)

    def test_embedder_count_mismatch(self) -> None:
        class BadEmbedder:
            dimensions = 2

            def embed(self, texts):  # noqa: ANN001
                return ()

        pipe = DefaultFileRagPipeline(
            chunker=FakeChunker(),
            metadata_generator=FakeMetadataGenerator(),
            embedder=BadEmbedder(),  # type: ignore[arg-type]
        )
        with self.assertRaises(IndexingPipelineError):
            pipe.process_file(path="a.py", content=b"def a():\n  pass\n")

    def test_metadata_failure_wrapped(self) -> None:
        from github_rag.index.chunk.types import (
            SemanticChunk,
            SourceLanguage,
            compute_chunk_id,
        )

        class OneChunk:
            def chunk(self, source):  # noqa: ANN001
                cid = compute_chunk_id(
                    path=source.path,
                    start_byte=0,
                    end_byte=1,
                    language=SourceLanguage.PYTHON,
                    kind="module",
                )
                return (
                    SemanticChunk(
                        chunk_id="fail",
                        path=source.path,
                        language=SourceLanguage.PYTHON,
                        kind="module",
                        text="x",
                        start_byte=0,
                        end_byte=1,
                        start_point=(0, 0),
                        end_point=(0, 1),
                    ),
                )

        pipe = DefaultFileRagPipeline(
            chunker=OneChunk(),  # type: ignore[arg-type]
            metadata_generator=FakeMetadataGenerator(fail_chunk_ids={"fail"}),
            embedder=FakeEmbedder(),
        )
        with self.assertRaises(IndexingPipelineError):
            pipe.process_file(path="a.py", content=b"x")


if __name__ == "__main__":
    unittest.main()
