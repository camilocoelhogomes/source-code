"""
BDD executável — T23-gap-ui-browser (Camada A / manifesto).

Valida UB-01..UB-09 e UB-18 (texto) sem Playwright / rfbrowser / browser real.

Cenários: ver
    spec/features/github-etl-mcp-rag/tasks/T23-gap-ui-browser/bdd.md

Execução:
    python -m pytest tests/bdd/test_ui_browser_gap.py -q --no-cov
"""

from __future__ import annotations

import json
import re
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
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
CANONICAL_SELECTORS = (
    "#repos-table",
    "#btn-index",
    "#btn-refresh",
    "#exact-pattern",
    "#semantic-query",
    "#search-results",
    "#repo-detail",
)
LEGACY_E2E_DEPS = (
    "robotframework",
    "robotframework-requests",
    "httpx",
)
_PAT_REAL = re.compile(r"ghp_[A-Za-z0-9_]{20,}")
_TOKEN_ASSIGN = re.compile(
    r"(GITHUB_TOKEN|E2E_GITHUB_TOKEN)\s*=\s*"
    r"(?!ghp_\.\.\.)(?!\.\.\.)(?!\$\{)(?!\S*:-)\S{8,}",
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"artefato ausente: {path}")
    return path.read_text(encoding="utf-8")


def _e2e_optional_deps() -> list[str]:
    data = tomllib.loads(_read(PYPROJECT))
    opts = data.get("project", {}).get("optional-dependencies", {})
    e2e = opts.get("e2e")
    if not isinstance(e2e, list) or not e2e:
        raise AssertionError("pyproject.toml sem [project.optional-dependencies].e2e")
    return [str(x) for x in e2e]


def _dep_names(entries: list[str]) -> set[str]:
    names: set[str] = set()
    for entry in entries:
        name = re.split(r"[><=!;\[ ]", entry.strip(), maxsplit=1)[0].strip().lower()
        if name:
            names.add(name)
    return names


def _assert_browser_dep(entries: list[str] | str, *, label: str) -> None:
    blob = "\n".join(entries) if isinstance(entries, list) else entries
    if not re.search(r"robotframework-browser", blob, re.I):
        raise AssertionError(
            f"{label}: deve declarar robotframework-browser (D-T23-001 / UB-01)"
        )
    if not re.search(
        r"robotframework-browser\s*>=\s*18|robotframework-browser==1[8-9]",
        blob,
        re.I,
    ):
        # Aceita pin >=18 ou ==18.x / ==19.x; exige menção de versão mínima
        if not re.search(r"robotframework-browser\s*[><=!]+\s*\d+", blob, re.I):
            raise AssertionError(
                f"{label}: robotframework-browser deve ter versão "
                f"(mínimo >=18 ou pin compatível)"
            )
        # pin numérico presente — exige major >= 18 se parseável
        m = re.search(
            r"robotframework-browser\s*[><=!]+\s*(\d+)",
            blob,
            re.I,
        )
        if m and int(m.group(1)) < 18:
            raise AssertionError(
                f"{label}: robotframework-browser major deve ser >=18 "
                f"(got {m.group(1)})"
            )


def _extract_tuple_literal(source: str, name: str) -> tuple[str, ...]:
    # Aceita `NAME = (` e `NAME: tuple[...] = (`.
    pattern = re.compile(
        rf"{re.escape(name)}\s*(?::[^=]+)?=\s*\((.*?)\)",
        re.S,
    )
    match = pattern.search(source)
    if match is None:
        raise AssertionError(f"{name} não encontrado como tupla literal")
    items = re.findall(r'"([^"]+)"|\'([^\']+)\'', match.group(1))
    return tuple(a or b for a, b in items)


def _assert_no_embedded_secrets(text: str, *, label: str) -> None:
    if _PAT_REAL.search(text):
        raise AssertionError(f"{label}: não deve embutir PAT real (ghp_…)")
    if _TOKEN_ASSIGN.search(text):
        raise AssertionError(f"{label}: não deve embutir valor de token")


def _github_inclusion_patterns(config: dict) -> list[str]:
    connections = config.get("connections") or {}
    patterns: list[str] = []
    for conn in connections.values():
        if not isinstance(conn, dict):
            continue
        if conn.get("type") != "github":
            continue
        repos = conn.get("repos") or []
        if isinstance(repos, list):
            patterns.extend(str(r) for r in repos)
    return patterns


def _pattern_has_wildcard(pattern: str) -> bool:
    return any(ch in pattern for ch in "*?[")


def _reference_matches_inclusion(patterns: list[str]) -> bool:
    import fnmatch

    return any(fnmatch.fnmatch(REFERENCE_REPO, p) for p in patterns)


class TestUB01BrowserDep(unittest.TestCase):
    """UB-01 — robotframework-browser no optional e2e + requirements-e2e."""

    def test_pyproject_declares_robotframework_browser(self) -> None:
        deps = _e2e_optional_deps()
        _assert_browser_dep(deps, label="pyproject.toml [e2e]")
        names = _dep_names(deps)
        for legacy in LEGACY_E2E_DEPS:
            self.assertIn(legacy, names, msg=f"deps e2e deve manter {legacy}")

    def test_requirements_e2e_mirrors_browser_dep(self) -> None:
        text = _read(REQUIREMENTS_E2E)
        _assert_browser_dep(text, label="requirements-e2e.txt")
        for legacy in LEGACY_E2E_DEPS:
            self.assertRegex(
                text,
                re.compile(rf"^{re.escape(legacy)}\b", re.M | re.I),
                msg=f"requirements-e2e.txt deve manter {legacy}",
            )


class TestUB02GreenPathSuites(unittest.TestCase):
    """UB-02 — GREEN_PATH_SUITES / markers incluem ui_browser após ui."""

    def test_green_path_suites_include_ui_browser_after_ui(self) -> None:
        suites = _extract_tuple_literal(_read(SUITE_PY), "GREEN_PATH_SUITES")
        self.assertIn("ui_browser", suites, msg="UB-02 / M-T23-013")
        self.assertIn("ui", suites)
        self.assertEqual(
            suites.index("ui_browser"),
            suites.index("ui") + 1,
            msg="ui_browser deve vir imediatamente após ui (I-T23-006)",
        )
        for required in (
            "health",
            "catalog_indexing",
            "ui",
            "mcp",
            "negative",
        ):
            self.assertIn(required, suites)

    def test_helpers_markers_mirror_ui_browser(self) -> None:
        markers = _extract_tuple_literal(
            _read(HELPERS_PY), "GREEN_PATH_SUITE_MARKERS"
        )
        self.assertIn("ui_browser", markers, msg="I-T23-007 / UB-02")
        self.assertEqual(
            markers.index("ui_browser"),
            markers.index("ui") + 1,
            msg="markers: ui_browser após ui",
        )


class TestUB03RobotArtifacts(unittest.TestCase):
    """UB-03 — browser.resource + ui_browser.robot com Library Browser."""

    def test_browser_resource_exists_with_canonical_keywords(self) -> None:
        text = _read(BROWSER_RESOURCE)
        for kw in (
            "Open Ui Browser",
            "Close Ui Browser",
            "Wait Repos Table Loaded",
        ):
            self.assertIn(kw, text, msg=f"keyword ausente: {kw}")

    def test_ui_browser_robot_exists_with_browser_library(self) -> None:
        text = _read(UI_BROWSER_ROBOT)
        self.assertRegex(
            text,
            re.compile(r"Library\s+Browser\b", re.I),
            msg="ui_browser.robot deve declarar Library Browser",
        )
        self.assertRegex(
            text,
            re.compile(r"Resource\s+.*browser\.resource", re.I),
            msg="ui_browser.robot deve Resource browser.resource",
        )


class TestUB04Tags(unittest.TestCase):
    """UB-04 — Force Tags ui/browser/mvp + tags bdd00x do inventário."""

    def test_force_tags_and_bdd_inventory_tags(self) -> None:
        text = _read(UI_BROWSER_ROBOT)
        force = re.search(r"Force Tags\s+(.+)", text, re.I)
        self.assertIsNotNone(force, msg="Force Tags ausente")
        force_blob = force.group(1).lower()  # type: ignore[union-attr]
        for tag in ("ui", "browser", "mvp"):
            self.assertIn(tag, force_blob.split(), msg=f"Force Tags falta {tag}")
        lowered = text.lower()
        for tag in REQUIRED_BDD_TAGS:
            self.assertIn(tag, lowered, msg=f"tag inventário ausente: {tag}")


class TestUB05Readme(unittest.TestCase):
    """UB-05 — README documenta rfbrowser init + suite ui_browser."""

    def test_readme_documents_rfbrowser_init_and_suite(self) -> None:
        text = _read(E2E_README)
        self.assertRegex(
            text,
            re.compile(r"rfbrowser\s+init", re.I),
            msg="e2e/README.md deve documentar rfbrowser init (D-T23-013)",
        )
        self.assertRegex(
            text,
            re.compile(r"ui_browser\.robot", re.I),
            msg="e2e/README.md deve listar ui_browser.robot",
        )
        self.assertRegex(
            text,
            re.compile(r"pip\s+install.*\[e2e\]|requirements-e2e", re.I),
            msg="README deve citar instalação deps e2e",
        )
        self.assertRegex(
            text,
            re.compile(r"headless", re.I),
            msg="README deve notar headless default",
        )
        _assert_no_embedded_secrets(text, label="e2e/README.md")


class TestUB06FixtureWildcard(unittest.TestCase):
    """UB-06 — config.e2e.json inclusão com wildcard cobrindo REFERENCE_REPO."""

    def test_github_inclusion_uses_wildcard_covering_reference(self) -> None:
        config = json.loads(_read(CONFIG_E2E))
        patterns = _github_inclusion_patterns(config)
        self.assertTrue(patterns, msg="fixture sem padrões de inclusão github")
        self.assertTrue(
            any(_pattern_has_wildcard(p) for p in patterns),
            msg=(
                "inclusão GitHub deve usar wildcard "
                f"(ex. source-*); got {patterns!r}"
            ),
        )
        self.assertTrue(
            _reference_matches_inclusion(patterns),
            msg=f"{REFERENCE_REPO} deve casar inclusão {patterns!r}",
        )
        # token env-only + conexão local
        blob = json.dumps(config)
        self.assertRegex(blob, r'"env"\s*:\s*"GITHUB_TOKEN"')
        self.assertIn("file://", blob)


class TestUB07NoSecrets(unittest.TestCase):
    """UB-07 — artefatos T23 sem secrets versionados."""

    def test_touched_artifacts_have_no_embedded_pat(self) -> None:
        paths = [
            PYPROJECT,
            REQUIREMENTS_E2E,
            E2E_README,
            CONFIG_E2E,
            UI_ROBOT,
            CATALOG_ROBOT,
        ]
        # Artefatos novos podem ainda não existir no RED — só checa se existirem.
        for optional in (UI_BROWSER_ROBOT, BROWSER_RESOURCE):
            if optional.is_file():
                paths.append(optional)
        for path in paths:
            with self.subTest(path=path.name):
                _assert_no_embedded_secrets(
                    _read(path), label=str(path.relative_to(REPO_ROOT))
                )


class TestUB08RequestsAloneNotEnough(unittest.TestCase):
    """UB-08 — API RequestsLibrary sozinha NÃO fecha a lacuna browser."""

    def test_green_path_and_browser_artifacts_required(self) -> None:
        suites = _extract_tuple_literal(_read(SUITE_PY), "GREEN_PATH_SUITES")
        self.assertIn(
            "ui_browser",
            suites,
            msg=(
                "UB-08: presença só de ui.robot/catalog_indexing (HTTP) "
                "não basta — GREEN_PATH_SUITES deve incluir ui_browser"
            ),
        )
        self.assertTrue(
            UI_BROWSER_ROBOT.is_file(),
            msg="UB-08: ui_browser.robot obrigatório no green path",
        )
        self.assertTrue(
            BROWSER_RESOURCE.is_file(),
            msg="UB-08: browser.resource obrigatório",
        )


class TestUB09ApiSuitesPreserved(unittest.TestCase):
    """UB-09 — ui.robot / catalog_indexing.robot permanecem (API)."""

    def test_requests_library_suites_still_present(self) -> None:
        self.assertTrue(UI_ROBOT.is_file(), msg="ui.robot removido")
        self.assertTrue(
            CATALOG_ROBOT.is_file(), msg="catalog_indexing.robot removido"
        )
        ui = _read(UI_ROBOT).lower()
        catalog = _read(CATALOG_ROBOT).lower()
        for tag in ("bdd009", "bdd010", "bdd023"):
            self.assertIn(tag, ui, msg=f"ui.robot perdeu {tag}")
        for tag in ("bdd001", "bdd002", "bdd007", "bdd016"):
            self.assertIn(tag, catalog, msg=f"catalog_indexing.robot perdeu {tag}")
        self.assertIn("requestslibrary", ui)
        self.assertIn("requestslibrary", catalog)


class TestUB18LifecycleSelectors(unittest.TestCase):
    """UB-18 — Setup/Teardown Open/Close + seletores estáveis no texto Robot."""

    def test_suite_setup_teardown_and_stable_selectors(self) -> None:
        text = _read(UI_BROWSER_ROBOT)
        self.assertRegex(
            text,
            re.compile(r"Suite Setup\s+Open Ui Browser", re.I),
        )
        self.assertRegex(
            text,
            re.compile(r"Suite Teardown\s+Close Ui Browser", re.I),
        )
        for selector in CANONICAL_SELECTORS:
            self.assertIn(
                selector,
                text,
                msg=f"seletor canônico ausente na suite: {selector}",
            )


if __name__ == "__main__":
    unittest.main()
