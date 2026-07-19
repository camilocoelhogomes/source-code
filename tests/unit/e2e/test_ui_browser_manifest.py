"""Unit — manifesto UI browser (T23 / UT-UB*).

Extremos/corners dos contratos M-T23-* / I-T23-* sem Playwright.
Não altera produção; TDD red até Developer materializar artefatos.
"""

from __future__ import annotations

import json
import re
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT = REPO_ROOT / "pyproject.toml"
REQUIREMENTS_E2E = REPO_ROOT / "requirements-e2e.txt"
SUITE_PY = REPO_ROOT / "src" / "github_rag" / "e2e" / "suite.py"
HELPERS_PY = REPO_ROOT / "tests" / "unit" / "e2e" / "helpers.py"
UI_BROWSER_ROBOT = REPO_ROOT / "e2e" / "robot" / "ui_browser.robot"
BROWSER_RESOURCE = REPO_ROOT / "e2e" / "robot" / "resources" / "browser.resource"
UI_ROBOT = REPO_ROOT / "e2e" / "robot" / "ui.robot"
CATALOG_ROBOT = REPO_ROOT / "e2e" / "robot" / "catalog_indexing.robot"
E2E_README = REPO_ROOT / "e2e" / "README.md"
CONFIG_E2E = REPO_ROOT / "e2e" / "fixtures" / "config.e2e.json"

REFERENCE_REPO = "camilocoelhogomes/source-code"
REQUIRED_BDD_TAGS = (
    "bdd001",
    "bdd002",
    "bdd007",
    "bdd009",
    "bdd010",
    "bdd016",
    "bdd019",
    "bdd023",
)
CANONICAL_GREEN_PATH = (
    "health",
    "catalog_indexing",
    "ui",
    "ui_browser",
    "mcp",
    "negative",
)
_PAT_REAL = re.compile(r"ghp_[A-Za-z0-9_]{20,}")


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"artefato ausente: {path}")
    return path.read_text(encoding="utf-8")


def _extract_tuple_literal(source: str, name: str) -> tuple[str, ...]:
    # Aceita `NAME = (` e `NAME: tuple[...] = (`.
    match = re.search(
        rf"{re.escape(name)}\s*(?::[^=]+)?=\s*\((.*?)\)",
        source,
        re.S,
    )
    if match is None:
        raise AssertionError(f"{name} não encontrado")
    items = re.findall(r'"([^"]+)"|\'([^\']+)\'', match.group(1))
    return tuple(a or b for a, b in items)


def assert_ui_browser_after_ui(suites: tuple[str, ...]) -> None:
    """Contrato de ordem I-T23-006 — usado em reais e sintéticos."""
    if "ui" not in suites:
        raise AssertionError("green path sem suite ui (regressão T21)")
    if "ui_browser" not in suites:
        raise AssertionError("green path sem ui_browser (UB-02 / UB-08)")
    if suites.index("ui_browser") != suites.index("ui") + 1:
        raise AssertionError(
            f"ui_browser deve vir imediatamente após ui; got {suites!r}"
        )
    for required in ("health", "catalog_indexing", "ui", "mcp", "negative"):
        if required not in suites:
            raise AssertionError(f"suite T21 ausente: {required}")


def assert_inclusion_wildcard_covers_reference(patterns: list[str]) -> None:
    import fnmatch

    if not patterns:
        raise AssertionError("lista de inclusão vazia")
    if not any(any(ch in p for ch in "*?[") for p in patterns):
        raise AssertionError(
            f"inclusão sem wildcard: {patterns!r} (D-T23-005)"
        )
    if not any(fnmatch.fnmatch(REFERENCE_REPO, p) for p in patterns):
        raise AssertionError(
            f"{REFERENCE_REPO} não casa padrões {patterns!r}"
        )


def assert_readme_rfbrowser_bootstrap(text: str) -> None:
    if not text.strip():
        raise AssertionError("README vazio")
    if not re.search(r"rfbrowser\s+init", text, re.I):
        raise AssertionError("README sem rfbrowser init")
    if not re.search(r"ui_browser\.robot", text, re.I):
        raise AssertionError("README sem ui_browser.robot")
    if not re.search(r"headless", text, re.I):
        raise AssertionError("README sem nota headless")


def assert_robot_browser_surface(text: str) -> None:
    if not re.search(r"Library\s+Browser\b", text, re.I):
        raise AssertionError("suite sem Library Browser")
    if re.search(r"Library\s+RequestsLibrary\b", text, re.I) and not re.search(
        r"Library\s+Browser\b", text, re.I
    ):
        raise AssertionError("RequestsLibrary sozinha não basta")
    if not re.search(r"Force Tags\s+.*\bbrowser\b", text, re.I):
        raise AssertionError("Force Tags sem browser")
    lowered = text.lower()
    missing = [t for t in REQUIRED_BDD_TAGS if t not in lowered]
    if missing:
        raise AssertionError(f"tags bdd ausentes: {missing}")


def assert_no_real_pat(text: str) -> None:
    if _PAT_REAL.search(text):
        raise AssertionError("PAT real embutido")


class TestUTUBRepoContracts(unittest.TestCase):
    """UT-UB-01..43 — contratos nos artefatos reais (RED até Developer)."""

    def test_ut_ub_01_02_browser_dep_in_pyproject_and_requirements(self) -> None:
        data = tomllib.loads(_read(PYPROJECT))
        e2e = data["project"]["optional-dependencies"]["e2e"]
        blob_py = "\n".join(str(x) for x in e2e)
        self.assertRegex(
            blob_py,
            re.compile(r"robotframework-browser", re.I),
            msg="UT-UB-01: pyproject [e2e] sem robotframework-browser",
        )
        req = _read(REQUIREMENTS_E2E)
        self.assertRegex(
            req,
            re.compile(r"robotframework-browser", re.I),
            msg="UT-UB-02: requirements-e2e.txt sem robotframework-browser",
        )

    def test_ut_ub_03_legacy_e2e_deps_remain(self) -> None:
        data = tomllib.loads(_read(PYPROJECT))
        names = {
            re.split(r"[><=!;\[ ]", str(x), maxsplit=1)[0].lower()
            for x in data["project"]["optional-dependencies"]["e2e"]
        }
        for dep in ("robotframework", "robotframework-requests", "httpx"):
            self.assertIn(dep, names)
        req = _read(REQUIREMENTS_E2E).lower()
        for dep in ("robotframework", "robotframework-requests", "httpx"):
            self.assertIn(dep, req)

    def test_ut_ub_10_14_green_path_order(self) -> None:
        suites = _extract_tuple_literal(_read(SUITE_PY), "GREEN_PATH_SUITES")
        markers = _extract_tuple_literal(
            _read(HELPERS_PY), "GREEN_PATH_SUITE_MARKERS"
        )
        assert_ui_browser_after_ui(suites)
        assert_ui_browser_after_ui(markers)

    def test_ut_ub_20_27_robot_artifacts(self) -> None:
        resource = _read(BROWSER_RESOURCE)
        for kw in (
            "Open Ui Browser",
            "Close Ui Browser",
            "Wait Repos Table Loaded",
        ):
            self.assertIn(kw, resource)
        robot = _read(UI_BROWSER_ROBOT)
        assert_robot_browser_surface(robot)
        self.assertRegex(robot, re.compile(r"Suite Setup\s+Open Ui Browser", re.I))
        self.assertRegex(
            robot, re.compile(r"Suite Teardown\s+Close Ui Browser", re.I)
        )
        for sel in ("#repos-table", "#btn-index", "#search-results"):
            self.assertIn(sel, robot)

    def test_ut_ub_30_31_api_suites_preserved(self) -> None:
        self.assertTrue(UI_ROBOT.is_file())
        self.assertTrue(CATALOG_ROBOT.is_file())
        ui = _read(UI_ROBOT).lower()
        cat = _read(CATALOG_ROBOT).lower()
        for tag in ("bdd009", "bdd010", "bdd023"):
            self.assertIn(tag, ui)
        for tag in ("bdd001", "bdd002", "bdd007", "bdd016"):
            self.assertIn(tag, cat)

    def test_ut_ub_40_42_fixture_and_readme(self) -> None:
        config = json.loads(_read(CONFIG_E2E))
        patterns: list[str] = []
        for conn in (config.get("connections") or {}).values():
            if isinstance(conn, dict) and conn.get("type") == "github":
                patterns.extend(str(r) for r in (conn.get("repos") or []))
        assert_inclusion_wildcard_covers_reference(patterns)
        assert_readme_rfbrowser_bootstrap(_read(E2E_README))

    def test_ut_ub_43_no_secrets_in_manifest_artifacts(self) -> None:
        for path in (
            PYPROJECT,
            REQUIREMENTS_E2E,
            E2E_README,
            CONFIG_E2E,
            UI_ROBOT,
            CATALOG_ROBOT,
        ):
            assert_no_real_pat(_read(path))


class TestUTUBCornersSynthetic(unittest.TestCase):
    """UT-UB-50..63 — extremos com entradas sintéticas."""

    def test_ut_ub_50_exact_match_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_inclusion_wildcard_covers_reference(
                ["camilocoelhogomes/source-code"]
            )

    def test_ut_ub_51_wildcard_not_covering_reference_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_inclusion_wildcard_covers_reference(
                ["camilocoelhogomes/other-*"]
            )

    def test_ut_ub_52_empty_inclusion_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_inclusion_wildcard_covers_reference([])

    def test_ut_ub_53_ui_browser_before_ui_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_ui_browser_after_ui(
                (
                    "health",
                    "catalog_indexing",
                    "ui_browser",
                    "ui",
                    "mcp",
                    "negative",
                )
            )

    def test_ut_ub_54_missing_ui_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_ui_browser_after_ui(
                ("health", "catalog_indexing", "ui_browser", "mcp", "negative")
            )

    def test_ut_ub_55_requests_only_suite_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_robot_browser_surface(
                "*** Settings ***\nLibrary    RequestsLibrary\n"
                "Force Tags    ui    mvp\n"
            )

    def test_ut_ub_56_force_tags_without_browser_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_robot_browser_surface(
                "*** Settings ***\nLibrary    Browser\n"
                "Force Tags    ui    mvp\n"
                "[Tags]    bdd001 bdd002 bdd007 bdd009 bdd010 "
                "bdd016 bdd019 bdd023\n"
            )

    def test_ut_ub_57_missing_bdd_tag_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_robot_browser_surface(
                "*** Settings ***\nLibrary    Browser\n"
                "Force Tags    ui    browser    mvp\n"
                "[Tags]    bdd001 bdd002 bdd007 bdd009 bdd010 bdd016 bdd023\n"
            )

    def test_ut_ub_58_readme_without_rfbrowser_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_readme_rfbrowser_bootstrap(
                "Install .[e2e]\nRun ui_browser.robot\nheadless default\n"
            )

    def test_ut_ub_59_empty_readme_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_readme_rfbrowser_bootstrap("   \n")

    def test_ut_ub_60_resource_missing_close_keyword(self) -> None:
        text = (
            "*** Keywords ***\nOpen Ui Browser\n    No Operation\n"
            "Wait Repos Table Loaded\n    No Operation\n"
        )
        self.assertNotIn("Close Ui Browser", text)

    def test_ut_ub_61_real_pat_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            assert_no_real_pat("token=ghp_" + ("a" * 22))

    def test_ut_ub_62_placeholder_pat_accepted(self) -> None:
        assert_no_real_pat("Exemplo: GITHUB_TOKEN=ghp_...\n")

    def test_ut_ub_63_canonical_green_path_accepted(self) -> None:
        assert_ui_browser_after_ui(CANONICAL_GREEN_PATH)

    def test_ut_ub_happy_wildcard_source_star(self) -> None:
        assert_inclusion_wildcard_covers_reference(
            ["camilocoelhogomes/source-*"]
        )


if __name__ == "__main__":
    unittest.main()
