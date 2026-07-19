"""
BDD executável — T06-open-gap-fill-tasks-parent (ParentGapFillBacklog).

Valida:
  - spec/features/mvp-e2e-audit-hardening/audit/gap-fill-backlog-index.md
  - spec/features/github-etl-mcp-rag/tasks/T23-gap-ui-browser.md
  - ... T24..T27 gap-*.md

conforme design §3 e BDD GAP-01..GAP-12.
Não implementa keywords/browser; não altera compose/robot/src.

Execução:
    python -m pytest tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py -q --no-cov

TDD: artefatos ausentes → falha esperada até a implementação documental.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = (
    REPO_ROOT
    / "spec"
    / "features"
    / "mvp-e2e-audit-hardening"
    / "audit"
    / "gap-fill-backlog-index.md"
)
INVENTORY_PATH = (
    REPO_ROOT
    / "spec"
    / "features"
    / "mvp-e2e-audit-hardening"
    / "audit"
    / "coverage-inventory.md"
)
PARENT_TASKS_DIR = (
    REPO_ROOT / "spec" / "features" / "github-etl-mcp-rag" / "tasks"
)

TASK_PATHS = {
    "T23": PARENT_TASKS_DIR / "T23-gap-ui-browser.md",
    "T24": PARENT_TASKS_DIR / "T24-gap-catalog-indexing-integral.md",
    "T25": PARENT_TASKS_DIR / "T25-gap-negative-integral.md",
    "T26": PARENT_TASKS_DIR / "T26-gap-mcp-parallel-slo.md",
    "T27": PARENT_TASKS_DIR / "T27-gap-sdk-dec015-conformity.md",
}

SURFACE_BY_TASK = {
    "T23": "ui",
    "T24": "catalog_indexing",
    "T25": "negative",
    "T26": "mcp",
    "T27": "sdk",
}

TOKEN_PREFIX_RE = re.compile(r"\b(ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{8,}")
TOKEN_ASSIGN_RE = re.compile(
    r"(?m)^(?:export\s+)?(?:GITHUB_TOKEN|E2E_GITHUB_TOKEN)\s*=\s*"
    r"['\"]?[A-Za-z0-9_\-]{20,}"
)

# Lacunas esperadas do inventário (BDD-015 excluído)
EXPECTED_LACUNA_BDDS = {
    "BDD-001",
    "BDD-002",
    "BDD-003",
    "BDD-005",
    "BDD-006",
    "BDD-007",
    "BDD-008",
    "BDD-009",
    "BDD-010",
    "BDD-013",
    "BDD-016",
    "BDD-017",
    "BDD-018",
    "BDD-019",
    "BDD-022",
    "BDD-023",
}

DENYLIST_PARTIAL = ("BDD-003", "BDD-006", "BDD-013", "BDD-024")


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"artefato ausente: {path}")
    return path.read_text(encoding="utf-8")


def _read_index() -> str:
    return _read(INDEX_PATH)


def _all_backlog_text() -> str:
    parts = [_read_index()]
    for path in TASK_PATHS.values():
        parts.append(_read(path))
    return "\n".join(parts)


def _lacunas_from_inventory() -> set[str]:
    text = _read(INVENTORY_PATH)
    found: set[str] = set()
    for line in text.splitlines():
        if "| lacuna |" not in line and "|lacuna|" not in line.replace(" ", ""):
            # aceitar "| lacuna |" padrão da matriz
            if "lacuna" not in line.lower():
                continue
        m = re.search(r"\|\s*(BDD-\d{3})\s*\|", line)
        if m and "lacuna" in line.lower():
            found.add(m.group(1))
    return found


# ---------------------------------------------------------------------------
# GAP-01 — índice canônico
# ---------------------------------------------------------------------------


class TestGAP01IndexExists(unittest.TestCase):
    """GAP-01 — gap-fill-backlog-index.md existe."""

    def test_index_exists(self) -> None:
        self.assertTrue(
            INDEX_PATH.is_file(),
            f"artefato ausente: {INDEX_PATH}",
        )


# ---------------------------------------------------------------------------
# GAP-02 — T23–T27 no pai
# ---------------------------------------------------------------------------


class TestGAP02TasksExist(unittest.TestCase):
    """GAP-02 — tasks T23–T27 gap-* existem no pai."""

    def test_all_gap_tasks_exist(self) -> None:
        missing = [p.name for p in TASK_PATHS.values() if not p.is_file()]
        self.assertEqual(
            missing,
            [],
            f"tasks gap ausentes no pai: {missing}",
        )


# ---------------------------------------------------------------------------
# GAP-03 — superfícies
# ---------------------------------------------------------------------------


class TestGAP03Surfaces(unittest.TestCase):
    """GAP-03 — superfícies ui/catalog_indexing/negative/mcp/sdk."""

    def test_surfaces_declared(self) -> None:
        index = _read_index().lower()
        for task_id, surface in SURFACE_BY_TASK.items():
            self.assertIn(
                surface,
                index,
                f"índice deve mencionar superfície {surface}",
            )
            task_text = _read(TASK_PATHS[task_id]).lower()
            self.assertIn(
                surface,
                task_text,
                f"{task_id} deve declarar superfície {surface}",
            )


# ---------------------------------------------------------------------------
# GAP-04 — classificação
# ---------------------------------------------------------------------------


class TestGAP04Classification(unittest.TestCase):
    """GAP-04 — gap-teste e/ou assert-fraco em cada task."""

    def test_classification_on_each_task(self) -> None:
        for task_id, path in TASK_PATHS.items():
            text = _read(path).lower()
            self.assertTrue(
                "gap-teste" in text or "assert-fraco" in text,
                f"{task_id} deve declarar gap-teste e/ou assert-fraco",
            )


# ---------------------------------------------------------------------------
# GAP-05 — UI browser
# ---------------------------------------------------------------------------


class TestGAP05UiBrowser(unittest.TestCase):
    """GAP-05 — T23 exige browser; API sozinha insuficiente."""

    def test_t23_requires_browser(self) -> None:
        t23 = _read(TASK_PATHS["T23"]).lower()
        self.assertTrue(
            "browser" in t23
            and (
                "playwright" in t23
                or "browser library" in t23
                or "browserlibrary" in t23
                or "automação browser" in t23
                or "automacao browser" in t23
            ),
            "T23 deve exigir automação browser (Browser Library / Playwright / equiv.)",
        )
        self.assertTrue(
            ("api" in t23)
            and (
                "não encerra" in t23
                or "nao encerra" in t23
                or "insuficiente" in t23
                or "sozinha" in t23
                or "não fecha" in t23
                or "nao fecha" in t23
            ),
            "T23 deve declarar que API HTTP sozinha não encerra lacuna UI",
        )


# ---------------------------------------------------------------------------
# GAP-06 — todas as lacunas
# ---------------------------------------------------------------------------


class TestGAP06AllLacunasCovered(unittest.TestCase):
    """GAP-06 — cada lacuna do inventário (exc. 015) no backlog."""

    def test_all_inventory_lacunas_covered(self) -> None:
        from_inv = _lacunas_from_inventory()
        # inventário SoT deve conter o conjunto esperado (regressão T01)
        self.assertTrue(
            EXPECTED_LACUNA_BDDS.issubset(from_inv) or from_inv == EXPECTED_LACUNA_BDDS,
            f"inventário lacunas inesperado: {sorted(from_inv)}",
        )
        lacunas = from_inv or EXPECTED_LACUNA_BDDS
        lacunas.discard("BDD-015")
        blob = _all_backlog_text().upper()
        missing = [b for b in sorted(lacunas) if b not in blob]
        self.assertEqual(
            missing,
            [],
            f"lacunas sem task/índice: {missing}",
        )


# ---------------------------------------------------------------------------
# GAP-07 — denylist parcial
# ---------------------------------------------------------------------------


class TestGAP07DenylistPartial(unittest.TestCase):
    """GAP-07 — BDD-003/006/013/024 cobertos."""

    def test_denylist_covered(self) -> None:
        blob = _all_backlog_text().upper()
        for bdd in DENYLIST_PARTIAL:
            self.assertIn(bdd, blob, f"denylist parcial deve cobrir {bdd}")


# ---------------------------------------------------------------------------
# GAP-08 — sem BDD-015
# ---------------------------------------------------------------------------


class TestGAP08NoBdd015(unittest.TestCase):
    """GAP-08 — BDD-015 não gera task de gap."""

    def test_no_bdd015_task(self) -> None:
        # arquivos de task não devem ser dedicados a BDD-015
        # (não usar glob *015* — colide com nomes legítimos como dec015)
        phantoms = list(PARENT_TASKS_DIR.glob("*bdd-015*"))
        phantoms += list(PARENT_TASKS_DIR.glob("*BDD-015*"))
        phantoms += list(PARENT_TASKS_DIR.glob("*gap*bdd-015*"))
        phantoms += [
            p
            for p in PARENT_TASKS_DIR.glob("T*-gap-*.md")
            if re.search(r"bdd[-_]?015", p.name, re.I)
        ]
        self.assertEqual(phantoms, [], f"não abrir task BDD-015: {phantoms}")
        # índice pode mencionar exclusão, mas não aceite de implementação 015
        index = _read_index()
        # se mencionar BDD-015, deve ser exclusão
        if "BDD-015" in index or "bdd-015" in index.lower():
            self.assertTrue(
                "exclu" in index.lower()
                or "fora" in index.lower()
                or "não gera" in index.lower()
                or "nao gera" in index.lower(),
                "menção a BDD-015 no índice deve ser exclusão",
            )
        # nenhuma task pai deve listar BDD-015 como lacuna a implementar
        for path in TASK_PATHS.values():
            text = _read(path)
            lower = text.lower()
            if "bdd-015" not in lower:
                continue
            self.assertTrue(
                "fora de escopo" in lower
                or "exclu" in lower
                or "não gera" in lower
                or "nao gera" in lower,
                f"{path.name} só pode mencionar BDD-015 como exclusão",
            )


# ---------------------------------------------------------------------------
# GAP-09 — não duplica T22
# ---------------------------------------------------------------------------


class TestGAP09NoDuplicateT22(unittest.TestCase):
    """GAP-09 — sem gap-tooling; índice referencia não-duplicar T22."""

    def test_no_gap_tooling_and_crossref_t22(self) -> None:
        gap_tooling = list(PARENT_TASKS_DIR.glob("T2*-gap-tooling*"))
        self.assertEqual(
            gap_tooling,
            [],
            f"não duplicar T22 como gap-tooling: {gap_tooling}",
        )
        index = _read_index().lower()
        self.assertTrue(
            "t22" in index
            and (
                "não duplic" in index
                or "nao duplic" in index
                or "não mistur" in index
                or "nao mistur" in index
                or "sem duplic" in index
            ),
            "índice deve referenciar T22 e declarar não duplicar",
        )


# ---------------------------------------------------------------------------
# GAP-10 — ordem após falhas
# ---------------------------------------------------------------------------


class TestGAP10AfterFailures(unittest.TestCase):
    """GAP-10 — índice referencia T05 / falhas antes de lacunas."""

    def test_order_after_failures(self) -> None:
        index = _read_index().lower()
        self.assertTrue(
            "t05" in index
            or "failure" in index
            or "falha" in index
            or "parentfailurebacklog" in index
            or "t22" in index,
            "índice deve referenciar fase de falhas (T05/T22)",
        )
        self.assertTrue(
            "antes" in index
            or "após" in index
            or "apos" in index
            or "depois" in index
            or "req-019" in index
            or "br-007" in index
            or "bdd-007" in index,
            "índice deve declarar ordem falhas → lacunas",
        )


# ---------------------------------------------------------------------------
# GAP-11 — sanitização
# ---------------------------------------------------------------------------


class TestGAP11NoSecrets(unittest.TestCase):
    """GAP-11 — sem tokens nos artefatos."""

    def test_no_token_leak(self) -> None:
        blob = _all_backlog_text()
        self.assertIsNone(
            TOKEN_PREFIX_RE.search(blob),
            "artefatos não devem conter prefixos de token GitHub",
        )
        self.assertIsNone(
            TOKEN_ASSIGN_RE.search(blob),
            "artefatos não devem conter assignment de token com valor",
        )


# ---------------------------------------------------------------------------
# GAP-12 — ENG-010 sem keywords nesta feature
# ---------------------------------------------------------------------------


class TestGAP12NoKeywordsInThisFeature(unittest.TestCase):
    """GAP-12 — keywords/browser só no pipeline do pai; sem patch produto."""

    def test_no_keyword_impl_in_child_feature(self) -> None:
        text = _all_backlog_text()
        blob = text.lower()
        self.assertTrue(
            "não implement" in blob
            or "nao implement" in blob
            or "pipeline do pai" in blob
            or "eng-010" in blob
            or "sem keyword" in blob,
            "deve declarar que esta feature não implementa keywords/browser",
        )
        self.assertTrue(
            "src/github_rag" in blob or "src/github_rag/**" in text,
            "deve afirmar escopo sem alteração em src/github_rag/**",
        )
        self.assertTrue(
            "e2e/robot" in blob,
            "deve afirmar escopo sem alteração em e2e/robot/**",
        )
        self.assertTrue(
            "compose" in blob,
            "deve afirmar escopo sem alteração em composes nesta feature",
        )


if __name__ == "__main__":
    unittest.main()
