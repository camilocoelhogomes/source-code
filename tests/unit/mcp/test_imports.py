"""Unit — import ban + SDK mcp (T17 / UT-X* / UT-F01)."""

from __future__ import annotations

import ast
import tomllib
import unittest
from pathlib import Path

from .helpers import FORBIDDEN_IMPORTS, MCP_PKG, collect_imports

_SLM_BANNED_NAMES = frozenset({"MetadataGenerator", "QueryReformulator"})


def _imported_names(package_dir: Path) -> set[str]:
    """Nomes importados (AST) — ignora menções em docstrings/comentários."""
    names: set[str] = set()
    for path in package_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
                    if alias.asname:
                        names.add(alias.asname)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names.add(node.module.split(".")[0])
                for alias in node.names:
                    names.add(alias.name)
                    if alias.asname:
                        names.add(alias.asname)
    return names


class TestImportBanAndSdk(unittest.TestCase):
    """UT-X01..X03 / UT-F01."""

    def test_ut_x01_forbidden_imports_absent(self) -> None:
        imports = collect_imports(MCP_PKG)
        for forbidden in FORBIDDEN_IMPORTS:
            self.assertNotIn(forbidden, imports, msg=forbidden)

    def test_ut_x02_official_mcp_sdk_present_and_pinned(self) -> None:
        import mcp
        from mcp.server.fastmcp import FastMCP

        self.assertIsNotNone(mcp)
        self.assertTrue(callable(FastMCP))
        imports = collect_imports(MCP_PKG)
        self.assertIn("mcp", imports)
        self.assertNotIn("fastmcp", imports)

        root = Path(__file__).resolve().parents[3]
        data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        deps = data["project"]["dependencies"]
        mcp_pins = [d for d in deps if d.startswith("mcp")]
        self.assertEqual(len(mcp_pins), 1)
        pin = mcp_pins[0]
        self.assertIn(">=1.27", pin)
        self.assertIn("<2", pin)

    def test_ut_x03_no_slm_imports_in_mcp_package(self) -> None:
        imported = _imported_names(MCP_PKG)
        for banned in _SLM_BANNED_NAMES:
            self.assertNotIn(banned, imported, msg=banned)
        self.assertNotIn("openai", imported)

    def test_ut_f01_fake_server_symbol_importable(self) -> None:
        from github_rag.mcp.fake import FakeMcpEvidenceServer

        fake = FakeMcpEvidenceServer()
        self.assertTrue(hasattr(fake, "build"))
        self.assertTrue(hasattr(fake, "run"))
        with self.assertRaises(NotImplementedError):
            fake.build()
        with self.assertRaises(NotImplementedError):
            fake.run()


if __name__ == "__main__":
    unittest.main()
