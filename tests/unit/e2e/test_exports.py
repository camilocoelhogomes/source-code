"""Unit — superfície pública / entry (T21 / UT-X*)."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path
from unittest import mock

from tests.unit.e2e.helpers import REPO_ROOT, import_e2e

E2E_PKG = REPO_ROOT / "src" / "github_rag" / "e2e"
FORBIDDEN_DOMAIN_IMPORTS = frozenset(
    {
        "github_rag.catalog",
        "github_rag.indexing",
        "github_rag.index",
        "github_rag.query",
    }
)


def _module_import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class TestE2ePublicExports(unittest.TestCase):
    """UT-X01..X04."""

    def test_ut_x01_handoff_exports(self) -> None:
        e2e = import_e2e()
        for name in (
            "E2eStackLauncher",
            "RobotMvpSuite",
            "PodmanE2eStackLauncher",
            "DefaultRobotMvpSuite",
        ):
            self.assertTrue(hasattr(e2e, name), name)

    def test_ut_x02_package_test_surface_exports(self) -> None:
        e2e = import_e2e()
        for name in (
            "E2eCredentialResolver",
            "ResolvedE2eCredential",
            "E2eCredentialError",
            "E2eStackError",
            "run_mvp_e2e",
            "COMPOSE_E2E",
            "ROBOT_ROOT",
            "E2E_CONFIG_FIXTURE",
            "E2E_REPOS_FIXTURE",
            "timeouts",
        ):
            self.assertTrue(hasattr(e2e, name), name)

    def test_ut_x03_main_exits_with_run_mvp_e2e(self) -> None:
        e2e = import_e2e()
        main_path = E2E_PKG / "__main__.py"
        self.assertTrue(main_path.is_file(), "__main__.py deve existir")
        source = main_path.read_text(encoding="utf-8")
        self.assertIn("run_mvp_e2e", source)
        from github_rag.e2e import __main__ as e2e_main  # noqa: PLC0415

        self.assertTrue(callable(getattr(e2e_main, "main", None)))
        self.assertTrue(callable(e2e.run_mvp_e2e))
        # SystemExit com código de run_mvp_e2e — sem Robot/compose real
        with mock.patch.object(e2e_main, "run_mvp_e2e", return_value=7):
            with self.assertRaises(SystemExit) as ctx:
                e2e_main.main()
        self.assertEqual(ctx.exception.code, 7)

    def test_ut_x04_e2e_package_avoids_domain_adapters(self) -> None:
        import_e2e()
        self.assertTrue(E2E_PKG.is_dir(), "pacote e2e ausente")
        for py in E2E_PKG.rglob("*.py"):
            imports = _module_import_roots(py)
            for forbidden in FORBIDDEN_DOMAIN_IMPORTS:
                self.assertNotIn(
                    forbidden,
                    imports,
                    msg=f"{py.name} importou {forbidden}",
                )
            for imp in imports:
                for forbidden in FORBIDDEN_DOMAIN_IMPORTS:
                    self.assertFalse(
                        imp.startswith(forbidden + "."),
                        msg=f"{py.name} importou {imp}",
                    )


if __name__ == "__main__":
    unittest.main()
