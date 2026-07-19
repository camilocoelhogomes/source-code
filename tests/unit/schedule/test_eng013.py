"""UT-S15/S16/S17 — ENG-013 / BDD-024 / BR-017."""

from __future__ import annotations

import ast
import inspect
import unittest
from pathlib import Path

SCHEDULE_SRC = (
    Path(__file__).resolve().parents[3] / "src" / "github_rag" / "schedule"
)

FORBIDDEN_IN_DOMAIN = {"apscheduler", "sqlalchemy"}
ADAPTER_OK = {
    "cron_expr.py": {"apscheduler"},
    "scheduler.py": {"apscheduler"},
    "postgres.py": {"sqlalchemy"},
}


def _top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


class TestEng013Confinement(unittest.TestCase):
    def test_ports_errors_memory_have_no_sdk(self) -> None:
        for name in ("ports.py", "errors.py", "memory.py"):
            path = SCHEDULE_SRC / name
            self.assertTrue(path.is_file(), f"missing {name}")
            imports = _top_level_imports(path)
            for forbidden in FORBIDDEN_IN_DOMAIN:
                self.assertNotIn(
                    forbidden,
                    imports,
                    f"{name} must not import {forbidden}",
                )

    def test_adapters_use_expected_sdk(self) -> None:
        for name, allowed in ADAPTER_OK.items():
            path = SCHEDULE_SRC / name
            self.assertTrue(path.is_file(), f"missing {name}")
            source = path.read_text(encoding="utf-8")
            for sdk in allowed:
                self.assertIn(sdk, source, f"{name} should reference {sdk}")


class TestNoConnectionCrud(unittest.TestCase):
    def test_public_surface_has_no_connection_crud(self) -> None:
        import github_rag.schedule as schedule_pkg

        names = set(dir(schedule_pkg))
        banned = {
            "create_connection",
            "update_connection",
            "delete_connection",
            "upsert_connection",
            "ConfigLoader",
            "connections",
        }
        self.assertFalse(names & banned)


class TestUsesApscheduler(unittest.TestCase):
    def test_scheduler_module_imports_apscheduler(self) -> None:
        import github_rag.schedule.scheduler as mod

        source = inspect.getsource(mod)
        self.assertIn("apscheduler", source.lower())


if __name__ == "__main__":
    unittest.main()
