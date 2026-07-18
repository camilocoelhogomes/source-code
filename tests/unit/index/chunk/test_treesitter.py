"""Testes unitários — TreeSitterContextualChunker (T11)."""

from __future__ import annotations

import inspect
import unittest

from github_rag.index.chunk.errors import (
    BinarySourceError,
    EmptySourceError,
    GrammarUnavailableError,
    ParseFailureError,
)
from github_rag.index.chunk.ports import ContextualChunker
from github_rag.index.chunk.treesitter import TreeSitterContextualChunker
from github_rag.index.chunk.types import ChunkSourceFile, SourceLanguage


class FakeUnavailableRegistry:
    def resolve(self, language: SourceLanguage, *, path_extension: str):
        raise GrammarUnavailableError(
            "grammar ausente (fake)",
            path=None,
            language=language,
        )


class FakeExplodingLanguage:
    """Language fake cujo parse levanta — fronteira ParseFailureError."""

    def __init__(self) -> None:
        pass


class FakeExplodingRegistry:
    def resolve(self, language: SourceLanguage, *, path_extension: str):
        # Objeto sem API de parse utilizável; chunker deve mapear para ParseFailureError.
        return FakeExplodingLanguage()


_PY_CLASS_DEF = b'''\
class Greeter:
    def hello(self):
        return "hi"
'''

_MD_SECTIONS = b"""\
# A

paragrafo a

# B

paragrafo b
"""

_JAVA_CLASS = b"""\
public class Greeter {
    public String hello() {
        return "hi";
    }
}
"""


class TestTreeSitterContextualChunker(unittest.TestCase):
    """UT-C01..UT-C13, UT-X01..UT-X04."""

    def test_ut_c01_python_happy_path(self) -> None:
        chunker = TreeSitterContextualChunker()
        source = ChunkSourceFile(path="src/app.py", content=_PY_CLASS_DEF)
        chunks = chunker.chunk(source)
        self.assertIsInstance(chunks, tuple)
        self.assertGreaterEqual(len(chunks), 1)
        for ch in chunks:
            self.assertTrue(ch.text)
            self.assertEqual(ch.path, "src/app.py")
            self.assertEqual(ch.language, SourceLanguage.PYTHON)

    def test_ut_c02_empty_raises(self) -> None:
        chunker = TreeSitterContextualChunker()
        with self.assertRaises(EmptySourceError):
            chunker.chunk(ChunkSourceFile(path="empty.py", content=b""))

    def test_ut_c03_nul_raises_binary(self) -> None:
        chunker = TreeSitterContextualChunker()
        with self.assertRaises(BinarySourceError):
            chunker.chunk(ChunkSourceFile(path="a.py", content=b"a\x00b"))

    def test_ut_c04_invalid_utf8_raises_binary(self) -> None:
        chunker = TreeSitterContextualChunker()
        with self.assertRaises(BinarySourceError):
            chunker.chunk(ChunkSourceFile(path="a.py", content=b"\xff\xfe"))

    def test_ut_c05_unknown_extension_raises_grammar_unavailable(self) -> None:
        chunker = TreeSitterContextualChunker()
        with self.assertRaises(GrammarUnavailableError):
            chunker.chunk(ChunkSourceFile(path="main.rs", content=b"fn main() {}"))

    def test_ut_c06_injected_registry_propagates(self) -> None:
        chunker = TreeSitterContextualChunker(grammar_registry=FakeUnavailableRegistry())
        with self.assertRaises(GrammarUnavailableError):
            chunker.chunk(ChunkSourceFile(path="a.py", content=b"x = 1\n"))

    def test_ut_c07_parse_failure(self) -> None:
        chunker = TreeSitterContextualChunker(grammar_registry=FakeExplodingRegistry())
        with self.assertRaises(ParseFailureError):
            chunker.chunk(ChunkSourceFile(path="a.py", content=b"x = 1\n"))

    def test_ut_c08_partial_syntax_error_still_succeeds(self) -> None:
        chunker = TreeSitterContextualChunker()
        # Sintaxe parcial: class ok + corpo quebrado — ERROR nodes não falham sozinhos.
        content = b"class A:\n    def broken(\n"
        chunks = chunker.chunk(ChunkSourceFile(path="broken.py", content=content))
        self.assertGreaterEqual(len(chunks), 1)

    def test_ut_c09_no_size_api_on_public_surface(self) -> None:
        init_params = set(inspect.signature(TreeSitterContextualChunker.__init__).parameters)
        chunk_params = set(inspect.signature(TreeSitterContextualChunker.chunk).parameters)
        forbidden = {"max_chars", "chunk_size", "overlap", "max_lines"}
        self.assertTrue(forbidden.isdisjoint(init_params))
        self.assertTrue(forbidden.isdisjoint(chunk_params))

    def test_ut_c10_markdown(self) -> None:
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(ChunkSourceFile(path="docs/a.md", content=_MD_SECTIONS))
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(c.language == SourceLanguage.MARKDOWN for c in chunks))

    def test_ut_c11_java(self) -> None:
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(ChunkSourceFile(path="Main.java", content=_JAVA_CLASS))
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(c.language == SourceLanguage.JAVA for c in chunks))
        kinds = {c.kind for c in chunks}
        self.assertTrue(kinds & {"class", "method", "class_declaration", "method_declaration"})

    def test_ut_c12_idempotent(self) -> None:
        chunker = TreeSitterContextualChunker()
        source = ChunkSourceFile(path="src/app.py", content=_PY_CLASS_DEF)
        a = chunker.chunk(source)
        b = chunker.chunk(source)
        self.assertEqual(
            [(c.chunk_id, c.path, c.start_byte, c.end_byte, c.kind, c.language) for c in a],
            [(c.chunk_id, c.path, c.start_byte, c.end_byte, c.kind, c.language) for c in b],
        )

    def test_ut_c13_runtime_protocol(self) -> None:
        chunker = TreeSitterContextualChunker()
        self.assertIsInstance(chunker, ContextualChunker)

    def test_ut_x01_empty_path_grammar_unavailable(self) -> None:
        chunker = TreeSitterContextualChunker()
        with self.assertRaises(GrammarUnavailableError):
            chunker.chunk(ChunkSourceFile(path="", content=b"x = 1\n"))

    def test_ut_c14_language_override_ignores_unknown_extension(self) -> None:
        # Contrato ChunkSourceFile.language: override explícito ignora extensão.
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(
            ChunkSourceFile(
                path="main.rs",
                content=b"def f():\n    pass\n",
                language=SourceLanguage.PYTHON,
            )
        )
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(c.language == SourceLanguage.PYTHON for c in chunks))

    def test_ut_c15_binary_precedes_unknown_extension(self) -> None:
        # Ordem design §3/§6: binário antes de grammar (NUL + .rs → Binary).
        chunker = TreeSitterContextualChunker()
        with self.assertRaises(BinarySourceError):
            chunker.chunk(ChunkSourceFile(path="main.rs", content=b"a\x00b"))

    def test_ut_x02_whitespace_only_succeeds(self) -> None:
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(ChunkSourceFile(path="ws.py", content=b"   \n\t\n"))
        self.assertGreaterEqual(len(chunks), 1)

    def test_ut_x03_large_synthetic_python(self) -> None:
        body = b"def f0():\n    return 0\n" + b"x = 1\n" * 3000
        self.assertGreater(len(body), 50_000)
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(ChunkSourceFile(path="big.py", content=body))
        self.assertGreaterEqual(len(chunks), 1)

    def test_ut_x04_no_cross_call_state(self) -> None:
        chunker = TreeSitterContextualChunker()
        a = chunker.chunk(ChunkSourceFile(path="a.py", content=b"def a():\n    pass\n"))
        b = chunker.chunk(ChunkSourceFile(path="b.py", content=b"def b():\n    pass\n"))
        self.assertTrue(all(c.path == "a.py" for c in a))
        self.assertTrue(all(c.path == "b.py" for c in b))


if __name__ == "__main__":
    unittest.main()
