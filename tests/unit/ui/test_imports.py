"""Unit — conformidade imports UI / FastAPI (T18 / BDD-024)."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

UI_PKG = Path(__file__).resolve().parents[3] / "src" / "github_rag" / "ui"

DOMAIN_MODULES = ("ports.py", "labels.py", "serialize.py", "errors.py")
FASTAPI_MODULES = ("app.py", "api.py")
FORBIDDEN_IN_DOMAIN = frozenset({"fastapi", "starlette", "uvicorn", "httpx"})
FORBIDDEN_HOMEMADE = frozenset({"urllib", "urllib3", "aiohttp", "requests"})


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


class TestUiImports(unittest.TestCase):
    def test_domain_modules_without_fastapi(self) -> None:
        for name in DOMAIN_MODULES:
            path = UI_PKG / name
            self.assertTrue(path.is_file(), msg=name)
            found = _imports(path) & FORBIDDEN_IN_DOMAIN
            self.assertFalse(found, msg=f"{name}: {found}")

    def test_app_api_use_fastapi(self) -> None:
        for name in FASTAPI_MODULES:
            path = UI_PKG / name
            self.assertTrue(path.is_file(), msg=name)
            self.assertIn("fastapi", _imports(path), msg=name)

    def test_no_homemade_http_clients_in_ui_pkg(self) -> None:
        for path in UI_PKG.glob("*.py"):
            found = _imports(path) & FORBIDDEN_HOMEMADE
            self.assertFalse(found, msg=f"{path.name}: {found}")


if __name__ == "__main__":
    unittest.main()
