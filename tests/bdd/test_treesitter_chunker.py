"""
BDD executável — T11-treesitter-chunker.

Valida TS-01..TS-15 (BDD-007, BDD-024, DEC-003, corners tipados) conforme bdd.md 0.1.1.

Execução:
    python -m pytest tests/bdd/test_treesitter_chunker.py -q
"""

from __future__ import annotations

import hashlib
import inspect
import unittest
from typing import Any

from github_rag.index.chunk.errors import (
    BinarySourceError,
    ChunkingError,
    EmptySourceError,
    GrammarUnavailableError,
    ParseFailureError,
)
from github_rag.index.chunk.grammar_registry import OfficialGrammarRegistry
from github_rag.index.chunk.node_selectors import select_semantic_nodes
from github_rag.index.chunk.ports import ContextualChunker
from github_rag.index.chunk.treesitter import TreeSitterContextualChunker
from github_rag.index.chunk.types import (
    ChunkSourceFile,
    SourceLanguage,
    compute_chunk_id,
)

_CANONICAL_CHUNK_ID = (
    "3bde810075b3f01ce7c66f67d9a2fbc8bb76ff43f11c74b27b1a4e5ddd1904f2"
)

_PY_CLASS_METHOD = b'''\
class Greeter:
    def hello(self):
        return "hi"
'''

_MD_TWO_SECTIONS = b"""\
# A

paragrafo a

# B

paragrafo b
"""

_JAVA_CLASS_METHOD = b"""\
public class Greeter {
    public String hello() {
        return "hi";
    }
}
"""

_TS_FN = b"export function greet(name: string): string { return name; }\n"
_TSX_FN = b"export function Greeter(): JSX.Element { return <div/>; }\n"


class FakeNode:
    def __init__(
        self,
        type: str,
        start_byte: int,
        end_byte: int,
        *,
        children: list[FakeNode] | None = None,
    ) -> None:
        self.type = type
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.start_point = (0, 0)
        self.end_point = (0, 0)
        self.children = children or []


class FakeUnavailableRegistry:
    def resolve(self, language: SourceLanguage, *, path_extension: str) -> Any:
        raise GrammarUnavailableError("ausente", language=language)


class FakeExplodingRegistry:
    def resolve(self, language: SourceLanguage, *, path_extension: str) -> Any:
        return object()


class TestTS01PythonChunks(unittest.TestCase):
    """TS-01 / BDD-007 — Python gera chunks Tree-sitter não vazios."""

    def test_python_class_and_def(self) -> None:
        chunker = TreeSitterContextualChunker()
        source = ChunkSourceFile(path="src/app.py", content=_PY_CLASS_METHOD)
        chunks = chunker.chunk(source)

        self.assertIsInstance(chunks, tuple)
        self.assertGreaterEqual(len(chunks), 1)
        for ch in chunks:
            self.assertTrue(ch.text)
            self.assertEqual(ch.path, "src/app.py")
            self.assertEqual(ch.language, SourceLanguage.PYTHON)
            self.assertLessEqual(0, ch.start_byte)
            self.assertLess(ch.start_byte, ch.end_byte)
            slice_text = source.content[ch.start_byte : ch.end_byte].decode("utf-8")
            self.assertEqual(slice_text, ch.text)
            self.assertIsInstance(ch.start_point, tuple)
            self.assertIsInstance(ch.end_point, tuple)
            self.assertEqual(len(ch.start_point), 2)
            self.assertEqual(len(ch.end_point), 2)
        kinds = {c.kind for c in chunks}
        self.assertTrue(
            kinds
            & {
                "class",
                "function",
                "method",
                "class_definition",
                "function_definition",
            }
        )


class TestTS02Markdown(unittest.TestCase):
    """TS-02 / BDD-007 — Markdown estrutural."""

    def test_markdown_sections(self) -> None:
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(
            ChunkSourceFile(path="docs/guide.md", content=_MD_TWO_SECTIONS)
        )
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(c.language == SourceLanguage.MARKDOWN for c in chunks))
        self.assertTrue(all(c.text for c in chunks))
        params = set(inspect.signature(TreeSitterContextualChunker.chunk).parameters)
        self.assertNotIn("max_lines", params)
        self.assertNotIn("chunk_size", params)


class TestTS03Java(unittest.TestCase):
    """TS-03 / BDD-007 — Java estrutural."""

    def test_java_class_and_method(self) -> None:
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(
            ChunkSourceFile(path="Greeter.java", content=_JAVA_CLASS_METHOD)
        )
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(c.language == SourceLanguage.JAVA for c in chunks))
        kinds = {c.kind for c in chunks}
        self.assertTrue(
            kinds & {"class", "method", "class_declaration", "method_declaration"}
        )


class TestTS04NoSizeChunkingApi(unittest.TestCase):
    """TS-04 / DEC-003 — sem API de tamanho/overlap/linhas."""

    def test_public_surface_has_no_size_params(self) -> None:
        init_params = set(inspect.signature(TreeSitterContextualChunker.__init__).parameters)
        chunk_params = set(inspect.signature(TreeSitterContextualChunker.chunk).parameters)
        forbidden = {"max_chars", "chunk_size", "overlap", "max_lines"}
        self.assertTrue(forbidden.isdisjoint(init_params | chunk_params))
        self.assertIsInstance(TreeSitterContextualChunker(), ContextualChunker)


class TestTS05EmptySource(unittest.TestCase):
    """TS-05 — arquivo vazio → EmptySourceError."""

    def test_empty_raises(self) -> None:
        chunker = TreeSitterContextualChunker()
        with self.assertRaises(EmptySourceError) as ctx:
            chunker.chunk(ChunkSourceFile(path="empty.py", content=b""))
        self.assertIsInstance(ctx.exception, ChunkingError)


class TestTS06BinarySource(unittest.TestCase):
    """TS-06 — NUL / UTF-8 inválido → BinarySourceError."""

    def test_nul(self) -> None:
        chunker = TreeSitterContextualChunker()
        with self.assertRaises(BinarySourceError):
            chunker.chunk(ChunkSourceFile(path="a.py", content=b"a\x00b"))

    def test_invalid_utf8(self) -> None:
        chunker = TreeSitterContextualChunker()
        with self.assertRaises(BinarySourceError):
            chunker.chunk(ChunkSourceFile(path="a.py", content=b"\xff\xfe"))


class TestTS07GrammarUnavailable(unittest.TestCase):
    """TS-07 — extensão sem grammar MVP → GrammarUnavailableError."""

    def test_rust_extension(self) -> None:
        chunker = TreeSitterContextualChunker()
        with self.assertRaises(GrammarUnavailableError):
            chunker.chunk(ChunkSourceFile(path="main.rs", content=b"fn main() {}"))

    def test_injected_registry(self) -> None:
        chunker = TreeSitterContextualChunker(
            grammar_registry=FakeUnavailableRegistry()
        )
        with self.assertRaises(GrammarUnavailableError):
            chunker.chunk(ChunkSourceFile(path="a.py", content=b"x = 1\n"))


class TestTS08RootFallback(unittest.TestCase):
    """TS-08 — sem nós-alvo → um chunk root."""

    def test_import_only_python(self) -> None:
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(
            ChunkSourceFile(path="only_import.py", content=b"import os\n")
        )
        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0].text)
        self.assertIn(chunks[0].kind, {"module", "program", "document"})


class TestTS09ChunkIdContract(unittest.TestCase):
    """TS-09 — chunk_id estável + fórmula canônica §4.3.1."""

    def test_idempotent_sequence_and_canonical_formula(self) -> None:
        chunker = TreeSitterContextualChunker()
        source = ChunkSourceFile(path="src/app.py", content=_PY_CLASS_METHOD)
        first = chunker.chunk(source)
        second = chunker.chunk(source)
        key = lambda c: (c.chunk_id, c.path, c.start_byte, c.end_byte, c.kind, c.language)
        self.assertEqual([key(c) for c in first], [key(c) for c in second])

        for ch in first:
            expected = hashlib.sha256(
                f"{ch.path}\0{ch.start_byte}\0{ch.end_byte}\0{ch.language.value}\0{ch.kind}".encode(
                    "utf-8"
                )
            ).hexdigest()
            self.assertEqual(ch.chunk_id, expected)
            self.assertEqual(len(ch.chunk_id), 64)
            self.assertEqual(ch.chunk_id, ch.chunk_id.lower())

        fixture_id = compute_chunk_id(
            path="src/app.py",
            start_byte=0,
            end_byte=10,
            language=SourceLanguage.PYTHON,
            kind="function",
        )
        self.assertEqual(fixture_id, _CANONICAL_CHUNK_ID)


class TestTS10OfficialSdk(unittest.TestCase):
    """TS-10 / BDD-024 — SDK oficial tree-sitter + grammar."""

    def test_uses_official_registry_and_tree_sitter(self) -> None:
        import tree_sitter  # noqa: F401 — presença do SDK oficial

        registry = OfficialGrammarRegistry()
        lang = registry.resolve(SourceLanguage.PYTHON, path_extension=".py")
        self.assertIsNotNone(lang)
        chunks = TreeSitterContextualChunker(grammar_registry=registry).chunk(
            ChunkSourceFile(path="a.py", content=b"def f():\n    pass\n")
        )
        self.assertGreaterEqual(len(chunks), 1)


class TestTS11TypescriptVsTsx(unittest.TestCase):
    """TS-11 — variantes language_typescript vs language_tsx."""

    def test_both_extensions(self) -> None:
        registry = OfficialGrammarRegistry()
        ts_lang = registry.resolve(SourceLanguage.TYPESCRIPT, path_extension=".ts")
        tsx_lang = registry.resolve(SourceLanguage.TYPESCRIPT, path_extension=".tsx")
        self.assertIsNot(ts_lang, tsx_lang)

        chunker = TreeSitterContextualChunker(grammar_registry=registry)
        ts_chunks = chunker.chunk(ChunkSourceFile(path="a.ts", content=_TS_FN))
        tsx_chunks = chunker.chunk(ChunkSourceFile(path="a.tsx", content=_TSX_FN))
        self.assertGreaterEqual(len(ts_chunks), 1)
        self.assertGreaterEqual(len(tsx_chunks), 1)
        self.assertTrue(all(c.language == SourceLanguage.TYPESCRIPT for c in ts_chunks))
        self.assertTrue(all(c.language == SourceLanguage.TYPESCRIPT for c in tsx_chunks))


class TestTS12NestedClassMethod(unittest.TestCase):
    """TS-12 — class e method ambos emitidos."""

    def test_nested_ranges(self) -> None:
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(
            ChunkSourceFile(path="nested.py", content=_PY_CLASS_METHOD)
        )
        ranges = {(c.start_byte, c.end_byte) for c in chunks}
        self.assertGreaterEqual(len(ranges), 2)
        keys = [(c.start_byte, c.end_byte, c.kind) for c in chunks]
        self.assertEqual(keys, sorted(keys))


class TestTS13DedupeIdenticalRange(unittest.TestCase):
    """TS-13 — mesmo (start_byte, end_byte) → um chunk com kind prioritário."""

    def test_export_wrapper_dedupe_via_selector(self) -> None:
        inner = FakeNode("function_declaration", 0, 30)
        wrapper = FakeNode("export_statement", 0, 30, children=[inner])
        root = FakeNode("program", 0, 30, children=[wrapper])
        selected = list(select_semantic_nodes(SourceLanguage.JAVASCRIPT, root))
        same = [n for n in selected if (n.start_byte, n.end_byte) == (0, 30) and n.kind != "program"]
        self.assertEqual(len(same), 1)
        self.assertEqual(same[0].kind, "function_declaration")


class TestTS14ParseFailure(unittest.TestCase):
    """TS-14 — falha de parse / impossível materializar → ParseFailureError."""

    def test_exploding_registry_language(self) -> None:
        chunker = TreeSitterContextualChunker(grammar_registry=FakeExplodingRegistry())
        with self.assertRaises(ParseFailureError) as ctx:
            chunker.chunk(ChunkSourceFile(path="a.py", content=b"x = 1\n"))
        self.assertIsInstance(ctx.exception, ChunkingError)


class TestTS15ErrorNodesDoNotFailAlone(unittest.TestCase):
    """TS-15 — nós ERROR não invalidam sozinhos."""

    def test_partial_invalid_python(self) -> None:
        chunker = TreeSitterContextualChunker()
        content = b"class A:\n    def broken(\n"
        chunks = chunker.chunk(ChunkSourceFile(path="broken.py", content=content))
        self.assertGreaterEqual(len(chunks), 1)


_YAML_CFG = b"name: app\nnested:\n  enabled: true\n"
_JSON_CFG = b'{"a": 1, "b": {"c": 2}}\n'
_XML_CFG = b"<root><child attr=\"x\">text</child></root>\n"
_TOML_CFG = b'[section]\nkey = "value"\n\n[other]\nx = 1\n'


class TestTS16YamlStructural(unittest.TestCase):
    """TS-16 — YAML chunking estrutural (não por tamanho/linhas)."""

    def test_yaml_and_yml(self) -> None:
        chunker = TreeSitterContextualChunker()
        for path in ("config/app.yaml", "config/app.yml"):
            with self.subTest(path=path):
                chunks = chunker.chunk(ChunkSourceFile(path=path, content=_YAML_CFG))
                self.assertGreaterEqual(len(chunks), 1)
                self.assertTrue(all(c.language == SourceLanguage.YAML for c in chunks))
                self.assertTrue(all(c.text for c in chunks))
                self.assertTrue(
                    {c.kind for c in chunks} & {"document", "block_mapping_pair", "stream"}
                )


class TestTS17JsonStructural(unittest.TestCase):
    """TS-17 — JSON chunking estrutural."""

    def test_json_object_pairs(self) -> None:
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(ChunkSourceFile(path="package.json", content=_JSON_CFG))
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(c.language == SourceLanguage.JSON for c in chunks))
        self.assertTrue({c.kind for c in chunks} & {"object", "pair", "array", "document"})


class TestTS18XmlStructural(unittest.TestCase):
    """TS-18 — XML chunking estrutural via language_xml."""

    def test_xml_nested_elements(self) -> None:
        registry = OfficialGrammarRegistry()
        lang = registry.resolve(SourceLanguage.XML, path_extension=".xml")
        self.assertIsNotNone(lang)
        chunker = TreeSitterContextualChunker(grammar_registry=registry)
        chunks = chunker.chunk(ChunkSourceFile(path="pom.xml", content=_XML_CFG))
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(c.language == SourceLanguage.XML for c in chunks))
        self.assertTrue(any(c.kind == "element" for c in chunks))
        element_ranges = {
            (c.start_byte, c.end_byte) for c in chunks if c.kind == "element"
        }
        self.assertGreaterEqual(len(element_ranges), 1)


class TestTS19TomlStructural(unittest.TestCase):
    """TS-19 — TOML chunking estrutural."""

    def test_toml_tables(self) -> None:
        chunker = TreeSitterContextualChunker()
        chunks = chunker.chunk(ChunkSourceFile(path="pyproject.toml", content=_TOML_CFG))
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(c.language == SourceLanguage.TOML for c in chunks))
        self.assertTrue({c.kind for c in chunks} & {"table", "pair", "document"})


if __name__ == "__main__":
    unittest.main()
