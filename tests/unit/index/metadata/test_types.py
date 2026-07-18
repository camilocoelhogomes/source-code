"""Testes unitários — ChunkMetadata / to_payload (T12)."""

from __future__ import annotations

import dataclasses
import json
import unittest

from github_rag.index.metadata.types import ChunkMetadata


class TestChunkMetadataFrozen(unittest.TestCase):
    """UT-T01, UT-T05."""

    def _sample(self) -> ChunkMetadata:
        return ChunkMetadata(
            chunk_id="c-1",
            summary="resumo",
            symbols=("Foo",),
            keywords=("bar",),
            intent="role",
            extra=(("k", 1),),
        )

    def test_ut_t01_frozen(self) -> None:
        meta = self._sample()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            meta.summary = "outro"  # type: ignore[misc]

    def test_ut_t05_extra_is_tuple_of_pairs(self) -> None:
        meta = self._sample()
        self.assertIsInstance(meta.extra, tuple)
        self.assertEqual(meta.extra[0], ("k", 1))


class TestToPayload(unittest.TestCase):
    """UT-T02..UT-T04."""

    def test_ut_t02_json_safe_payload(self) -> None:
        meta = ChunkMetadata(
            chunk_id="c-1",
            summary="resumo contextual",
            symbols=("ClassA", "method_b"),
            keywords=("auth", "token"),
            intent="valida credenciais",
            extra=(("confidence", 0.9), ("flag", True), ("note", None)),
        )
        payload = meta.to_payload()
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["chunk_id"], "c-1")
        self.assertEqual(payload["summary"], "resumo contextual")
        self.assertEqual(payload["intent"], "valida credenciais")
        self.assertEqual(payload["symbols"], ["ClassA", "method_b"])
        self.assertEqual(payload["keywords"], ["auth", "token"])
        self.assertIsInstance(payload["symbols"], list)
        self.assertIsInstance(payload["keywords"], list)
        self.assertEqual(
            payload["extra"],
            {"confidence": 0.9, "flag": True, "note": None},
        )
        self.assertIsInstance(payload["extra"], dict)
        json.dumps(payload)  # não levanta

    def test_ut_t03_empty_symbols_keywords(self) -> None:
        meta = ChunkMetadata(
            chunk_id="c-2",
            summary="ok",
            symbols=(),
            keywords=(),
            intent="",
            extra=(),
        )
        payload = meta.to_payload()
        self.assertEqual(payload["symbols"], [])
        self.assertEqual(payload["keywords"], [])
        self.assertEqual(payload["extra"], {})
        json.dumps(payload)

    def test_ut_t04_extra_scalar_types(self) -> None:
        meta = ChunkMetadata(
            chunk_id="c-3",
            summary="ok",
            symbols=(),
            keywords=(),
            intent="",
            extra=(
                ("s", "x"),
                ("i", 2),
                ("f", 1.5),
                ("b", False),
                ("n", None),
            ),
        )
        extra = meta.to_payload()["extra"]
        assert isinstance(extra, dict)
        self.assertEqual(extra["s"], "x")
        self.assertEqual(extra["i"], 2)
        self.assertEqual(extra["f"], 1.5)
        self.assertIs(extra["b"], False)
        self.assertIsNone(extra["n"])


if __name__ == "__main__":
    unittest.main()
