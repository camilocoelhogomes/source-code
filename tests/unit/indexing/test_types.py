"""Unit tests — to_vector_metadata."""

from __future__ import annotations

import unittest

from github_rag.index.metadata.types import ChunkMetadata as SlmMeta
from github_rag.indexing.types import to_vector_metadata


class TestToVectorMetadata(unittest.TestCase):
    def test_maps_fields(self) -> None:
        slm = SlmMeta(
            chunk_id="c1",
            summary="sum",
            symbols=("S",),
            keywords=("k",),
            intent="intent",
            extra=(("x", 1),),
        )
        vec = to_vector_metadata(slm)
        self.assertEqual(vec.summary, "sum")
        self.assertEqual(vec.keywords, ("k",))
        self.assertEqual(vec.symbols, ("S",))
        self.assertFalse(hasattr(vec, "intent"))


if __name__ == "__main__":
    unittest.main()
