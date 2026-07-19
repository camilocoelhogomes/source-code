"""Unit — conformidade ENG-013 / exports (T19 / UT-X*)."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from tests.unit.delivery.helpers import DELIVERY_PKG, FORBIDDEN_IN_PORTS


def _module_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def _package_source_files() -> list[Path]:
    if not DELIVERY_PKG.is_dir():
        raise AssertionError(f"pacote delivery ausente: {DELIVERY_PKG}")
    return sorted(p for p in DELIVERY_PKG.rglob("*.py") if p.is_file())


class TestDeliveryImportsAndExports(unittest.TestCase):
    """UT-X01..X04."""

    def test_ut_x01_ports_has_no_forbidden_sdks(self) -> None:
        ports = DELIVERY_PKG / "ports.py"
        self.assertTrue(ports.is_file(), "ports.py deve existir (I-T19-002)")
        imports = _module_imports(ports)
        for forbidden in FORBIDDEN_IN_PORTS:
            self.assertNotIn(forbidden, imports, msg=forbidden)

    def test_ut_x02_public_exports(self) -> None:
        from github_rag.delivery import (
            ContainerRuntime,
            DefaultContainerRuntime,
            run_container_boot,
        )

        self.assertTrue(callable(DefaultContainerRuntime))
        self.assertTrue(callable(run_container_boot))
        self.assertIsNotNone(ContainerRuntime)

    def test_ut_x03_runtime_does_not_reparse_json(self) -> None:
        runtime = DELIVERY_PKG / "runtime.py"
        self.assertTrue(runtime.is_file(), "runtime.py deve existir")
        source = runtime.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(runtime))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "json"
                    and node.func.attr in {"loads", "load"}
                ):
                    self.fail(
                        "runtime.py não deve fazer json.loads/load "
                        "(ConfigLoader T02 é o parser)"
                    )

    def test_ut_x04_main_calls_run_container_boot(self) -> None:
        main_path = DELIVERY_PKG / "__main__.py"
        self.assertTrue(main_path.is_file(), "__main__.py deve existir")
        source = main_path.read_text(encoding="utf-8")
        self.assertIn("run_container_boot", source)
        tree = ast.parse(source, filename=str(main_path))
        called = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "run_container_boot":
                    called = True
                if isinstance(func, ast.Attribute) and func.attr == "run_container_boot":
                    called = True
        self.assertTrue(called, "__main__ deve invocar run_container_boot()")

    def test_ut_x05_mcp_stdio_entry_exists(self) -> None:
        """I-T19-010/015 — entry alternativo stdio sem bind UI."""
        stdio_path = DELIVERY_PKG / "mcp_stdio.py"
        self.assertTrue(stdio_path.is_file(), "mcp_stdio.py deve existir")
        source = stdio_path.read_text(encoding="utf-8")
        self.assertIn("def main", source)
        self.assertRegex(source, r"stdio", "entry deve referenciar transport stdio")
        # Não deve ser o path que sobe UI HTTP
        self.assertNotIn("default_bind_ui", source)
        self.assertNotIn("uvicorn", source.lower())


if __name__ == "__main__":
    unittest.main()
