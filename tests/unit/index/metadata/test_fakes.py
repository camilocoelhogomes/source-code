"""Testes unitários — FakeMetadataGenerator (T12)."""

from __future__ import annotations

import unittest

from github_rag.index.metadata.errors import MetadataGenerationError, MetadataModelError
from github_rag.index.metadata.fakes import FakeMetadataGenerator
from github_rag.index.metadata.types import ChunkMetadata
from tests.unit.index.metadata.helpers import make_chunk, make_chunks


class TestFakeMetadataGenerator(unittest.TestCase):
    """UT-F01..UT-F05, UT-X01, UT-X06."""

    def test_ut_f01_per_chunk(self) -> None:
        chunks = make_chunks(2)
        gen = FakeMetadataGenerator()
        results = [gen.generate(c) for c in chunks]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].chunk_id, chunks[0].chunk_id)
        self.assertEqual(results[1].chunk_id, chunks[1].chunk_id)
        self.assertNotEqual(results[0].summary, results[1].summary)
        self.assertTrue(results[0].summary.strip())
        self.assertTrue(results[1].summary.strip())

    def test_ut_f02_fail_mid_list(self) -> None:
        chunks = make_chunks(3)
        fail_id = chunks[1].chunk_id
        gen = FakeMetadataGenerator(fail_chunk_ids={fail_id})
        first = gen.generate(chunks[0])
        self.assertEqual(first.chunk_id, chunks[0].chunk_id)
        with self.assertRaises(MetadataGenerationError) as ctx:
            gen.generate(chunks[1])
        self.assertIsInstance(ctx.exception, MetadataModelError)
        self.assertEqual(ctx.exception.chunk_id, fail_id)

    def test_ut_f03_by_chunk_id_map(self) -> None:
        chunk = make_chunk(chunk_id="mapped")
        expected = ChunkMetadata(
            chunk_id="mapped",
            summary="custom",
            symbols=("S",),
            keywords=("k",),
            intent="i",
            extra=(),
        )
        gen = FakeMetadataGenerator(by_chunk_id={"mapped": expected})
        self.assertEqual(gen.generate(chunk), expected)

    def test_ut_f04_does_not_invent_chunk_id(self) -> None:
        chunk = make_chunk(chunk_id="stable-id")
        meta = FakeMetadataGenerator().generate(chunk)
        self.assertEqual(meta.chunk_id, "stable-id")

    def test_ut_f05_idempotent_for_same_chunk(self) -> None:
        chunk = make_chunk(chunk_id="idem")
        gen = FakeMetadataGenerator()
        a = gen.generate(chunk)
        b = gen.generate(chunk)
        self.assertEqual(a.chunk_id, b.chunk_id)
        self.assertEqual(a.summary, b.summary)
        self.assertEqual(a.symbols, b.symbols)
        self.assertEqual(a.keywords, b.keywords)
        self.assertEqual(a.intent, b.intent)
        self.assertEqual(a.extra, b.extra)

    def test_ut_x01_empty_caller_loop(self) -> None:
        gen = FakeMetadataGenerator()
        results = [gen.generate(c) for c in ()]
        self.assertEqual(results, [])

    def test_ut_x06_independent_sequential_calls(self) -> None:
        a, b = make_chunks(2)
        gen = FakeMetadataGenerator()
        ra = gen.generate(a)
        rb = gen.generate(b)
        self.assertEqual(ra.chunk_id, a.chunk_id)
        self.assertEqual(rb.chunk_id, b.chunk_id)


if __name__ == "__main__":
    unittest.main()
