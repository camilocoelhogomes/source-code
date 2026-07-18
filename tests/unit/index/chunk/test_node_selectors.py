"""Testes unitários — select_semantic_nodes / SelectedNode (T11)."""

from __future__ import annotations

import dataclasses
import unittest
from typing import Any

from github_rag.index.chunk.node_selectors import SelectedNode, select_semantic_nodes
from github_rag.index.chunk.types import SourceLanguage


class FakeNode:
    """Nó mínimo com superfície tree_sitter.Node usada pelos seletores."""

    def __init__(
        self,
        type: str,
        start_byte: int,
        end_byte: int,
        *,
        start_point: tuple[int, int] = (0, 0),
        end_point: tuple[int, int] = (0, 0),
        children: list[FakeNode] | None = None,
    ) -> None:
        self.type = type
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.start_point = start_point
        self.end_point = end_point
        self.children = children or []

    def walk(self) -> Any:
        return _FakeWalk(self)


class _FakeWalk:
    def __init__(self, root: FakeNode) -> None:
        self._root = root
        self.node = root
        self._stack: list[tuple[FakeNode, int]] = [(root, -1)]

    def goto_first_child(self) -> bool:
        node, _ = self._stack[-1]
        if not node.children:
            return False
        child = node.children[0]
        self._stack.append((child, 0))
        self.node = child
        return True

    def goto_next_sibling(self) -> bool:
        if len(self._stack) < 2:
            return False
        parent, idx = self._stack[-2]
        next_idx = idx + 1
        if next_idx >= len(parent.children):
            return False
        sibling = parent.children[next_idx]
        self._stack[-1] = (sibling, next_idx)
        self.node = sibling
        return True

    def goto_parent(self) -> bool:
        if len(self._stack) <= 1:
            return False
        self._stack.pop()
        self.node = self._stack[-1][0]
        return True


class TestSelectSemanticNodes(unittest.TestCase):
    """UT-N01..UT-N04."""

    def test_ut_n01_python_class_and_method_both_emitted(self) -> None:
        method = FakeNode(
            "function_definition",
            20,
            40,
            start_point=(1, 4),
            end_point=(2, 0),
        )
        klass = FakeNode(
            "class_definition",
            0,
            50,
            start_point=(0, 0),
            end_point=(3, 0),
            children=[method],
        )
        root = FakeNode("module", 0, 50, children=[klass])

        selected = list(select_semantic_nodes(SourceLanguage.PYTHON, root))
        ranges = {(n.start_byte, n.end_byte) for n in selected}
        self.assertIn((0, 50), ranges)
        self.assertIn((20, 40), ranges)
        self.assertGreaterEqual(len(selected), 2)

    def test_ut_n02_identical_range_dedupes_with_priority_kind(self) -> None:
        # Mesmo range: wrapper export_statement + declaração interna.
        inner = FakeNode(
            "function_declaration",
            0,
            30,
            start_point=(0, 0),
            end_point=(2, 1),
        )
        wrapper = FakeNode(
            "export_statement",
            0,
            30,
            start_point=(0, 0),
            end_point=(2, 1),
            children=[inner],
        )
        root = FakeNode("program", 0, 30, children=[wrapper])

        selected = list(select_semantic_nodes(SourceLanguage.JAVASCRIPT, root))
        same_range = [n for n in selected if (n.start_byte, n.end_byte) == (0, 30)]
        # Zero-alvo root não conta como dedupe deste range se já houver alvo.
        targetish = [n for n in same_range if n.kind != "program"]
        self.assertEqual(len(targetish), 1)
        self.assertEqual(targetish[0].kind, "function_declaration")

    def test_ut_n03_zero_targets_emits_root(self) -> None:
        imp = FakeNode("import_statement", 0, 18)
        root = FakeNode("module", 0, 18, children=[imp])

        selected = list(select_semantic_nodes(SourceLanguage.PYTHON, root))
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].kind, "module")
        self.assertEqual((selected[0].start_byte, selected[0].end_byte), (0, 18))

    def test_ut_n04_sorted_by_start_end_kind(self) -> None:
        # Filhos fora de ordem; saída deve ordenar (start, end, kind).
        b = FakeNode("function_definition", 30, 50)
        a = FakeNode("function_definition", 0, 20)
        c1 = FakeNode("class_definition", 60, 80)
        root = FakeNode("module", 0, 80, children=[b, a, c1])

        selected = list(select_semantic_nodes(SourceLanguage.PYTHON, root))
        keys = [(n.start_byte, n.end_byte, n.kind) for n in selected]
        self.assertEqual(keys, sorted(keys))

    def test_selected_node_is_frozen(self) -> None:
        node = SelectedNode(
            kind="function",
            start_byte=0,
            end_byte=1,
            start_point=(0, 0),
            end_point=(0, 1),
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            node.kind = "class"  # type: ignore[misc]

    def test_ut_n05_config_language_targets(self) -> None:
        """UT-N05 — alvos estruturais yaml/json/xml/toml (design §4.4)."""
        yaml_pair = FakeNode("block_mapping_pair", 0, 10)
        yaml_doc = FakeNode("document", 0, 20, children=[yaml_pair])
        yaml_root = FakeNode("stream", 0, 20, children=[yaml_doc])
        yaml_sel = list(select_semantic_nodes(SourceLanguage.YAML, yaml_root))
        self.assertTrue({n.kind for n in yaml_sel} & {"document", "block_mapping_pair"})

        json_pair = FakeNode("pair", 1, 7)
        json_obj = FakeNode("object", 0, 10, children=[json_pair])
        json_root = FakeNode("document", 0, 10, children=[json_obj])
        json_sel = list(select_semantic_nodes(SourceLanguage.JSON, json_root))
        self.assertTrue({n.kind for n in json_sel} & {"object", "pair", "array"})

        child = FakeNode("element", 6, 20)
        parent = FakeNode("element", 0, 30, children=[child])
        xml_root = FakeNode("document", 0, 30, children=[parent])
        xml_sel = list(select_semantic_nodes(SourceLanguage.XML, xml_root))
        self.assertGreaterEqual(len([n for n in xml_sel if n.kind == "element"]), 2)

        toml_pair = FakeNode("pair", 10, 20)
        toml_table = FakeNode("table", 0, 25, children=[toml_pair])
        toml_root = FakeNode("document", 0, 25, children=[toml_table])
        toml_sel = list(select_semantic_nodes(SourceLanguage.TOML, toml_root))
        self.assertTrue({n.kind for n in toml_sel} & {"table", "pair"})


if __name__ == "__main__":
    unittest.main()
