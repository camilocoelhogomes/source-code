"""Testes unitários — types / chunk_id / language_from_path (T11)."""

from __future__ import annotations

import dataclasses
import hashlib
import unittest

from github_rag.index.chunk.types import (
    ChunkSourceFile,
    SemanticChunk,
    SourceLanguage,
    compute_chunk_id,
    language_from_path,
)

# Fixture canônica design §4.3.1 / unit-test-plan.
_CANONICAL_CHUNK_ID = (
    "3bde810075b3f01ce7c66f67d9a2fbc8bb76ff43f11c74b27b1a4e5ddd1904f2"
)


class TestComputeChunkId(unittest.TestCase):
    """UT-T01..UT-T03."""

    def test_ut_t01_canonical_sha256_hex(self) -> None:
        expected_payload = b"src/app.py\x000\x0010\x00python\x00function"
        self.assertEqual(
            hashlib.sha256(expected_payload).hexdigest(),
            _CANONICAL_CHUNK_ID,
        )
        chunk_id = compute_chunk_id(
            path="src/app.py",
            start_byte=0,
            end_byte=10,
            language=SourceLanguage.PYTHON,
            kind="function",
        )
        self.assertEqual(chunk_id, _CANONICAL_CHUNK_ID)
        self.assertEqual(len(chunk_id), 64)
        self.assertEqual(chunk_id, chunk_id.lower())

    def test_ut_t02_stable_across_calls(self) -> None:
        kwargs = dict(
            path="pkg/mod.py",
            start_byte=4,
            end_byte=40,
            language=SourceLanguage.PYTHON,
            kind="class",
        )
        self.assertEqual(compute_chunk_id(**kwargs), compute_chunk_id(**kwargs))

    def test_ut_t03_sensitive_to_start_byte(self) -> None:
        base = dict(
            path="pkg/mod.py",
            end_byte=40,
            language=SourceLanguage.PYTHON,
            kind="class",
        )
        a = compute_chunk_id(start_byte=0, **base)
        b = compute_chunk_id(start_byte=1, **base)
        self.assertNotEqual(a, b)


class TestLanguageFromPath(unittest.TestCase):
    """UT-T04, UT-T05, UT-X01 (parte pura)."""

    def test_ut_t04_mvp_extensions(self) -> None:
        cases = {
            "src/app.py": SourceLanguage.PYTHON,
            "types.pyi": SourceLanguage.PYTHON,
            "Main.java": SourceLanguage.JAVA,
            "docs/readme.md": SourceLanguage.MARKDOWN,
            "notes.markdown": SourceLanguage.MARKDOWN,
            "ui/app.js": SourceLanguage.JAVASCRIPT,
            "lib/mod.mjs": SourceLanguage.JAVASCRIPT,
            "lib/mod.cjs": SourceLanguage.JAVASCRIPT,
            "ui/comp.ts": SourceLanguage.TYPESCRIPT,
            "ui/Comp.tsx": SourceLanguage.TYPESCRIPT,
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(language_from_path(path), expected)

    def test_ut_t05_unknown_extension_returns_none(self) -> None:
        self.assertIsNone(language_from_path("main.rs"))
        self.assertIsNone(language_from_path("Makefile"))
        self.assertIsNone(language_from_path("noext"))

    def test_ut_x01_empty_path_returns_none(self) -> None:
        self.assertIsNone(language_from_path(""))


class TestFrozenDataclasses(unittest.TestCase):
    """UT-T06."""

    def test_chunk_source_file_frozen(self) -> None:
        source = ChunkSourceFile(path="a.py", content=b"x")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            source.path = "b.py"  # type: ignore[misc]

    def test_semantic_chunk_frozen(self) -> None:
        chunk = SemanticChunk(
            chunk_id=_CANONICAL_CHUNK_ID,
            path="src/app.py",
            language=SourceLanguage.PYTHON,
            kind="function",
            text="def f():",
            start_byte=0,
            end_byte=10,
            start_point=(0, 0),
            end_point=(0, 8),
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            chunk.kind = "class"  # type: ignore[misc]

    def test_source_language_closed_values(self) -> None:
        self.assertEqual(
            {m.value for m in SourceLanguage},
            {"python", "java", "javascript", "typescript", "markdown"},
        )


if __name__ == "__main__":
    unittest.main()
