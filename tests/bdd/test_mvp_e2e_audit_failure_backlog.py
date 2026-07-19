"""
BDD executável — T05-open-failure-tasks-parent (ParentFailureBacklog).

Valida:
  - spec/features/mvp-e2e-audit-hardening/audit/failure-backlog-index.md
  - spec/features/github-etl-mcp-rag/tasks/T22-fix-tooling-e2e-compose-zoekt.md

conforme design §3 e BDD FAIL-01..FAIL-10.
Não implementa fixes de produto; não altera compose/robot/src.

Execução:
    python -m pytest tests/bdd/test_mvp_e2e_audit_failure_backlog.py -q --no-cov

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
    / "failure-backlog-index.md"
)
T22_PATH = (
    REPO_ROOT
    / "spec"
    / "features"
    / "github-etl-mcp-rag"
    / "tasks"
    / "T22-fix-tooling-e2e-compose-zoekt.md"
)
PARENT_TASKS_DIR = (
    REPO_ROOT / "spec" / "features" / "github-etl-mcp-rag" / "tasks"
)

TOKEN_PREFIX_RE = re.compile(r"\b(ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{8,}")
TOKEN_ASSIGN_RE = re.compile(
    r"(?m)^(?:export\s+)?(?:GITHUB_TOKEN|E2E_GITHUB_TOKEN)\s*=\s*"
    r"['\"]?[A-Za-z0-9_\-]{20,}"
)

SURFACES_NO_FAILURE = (
    "health",
    "catalog_indexing",
    "ui",
    "mcp",
    "negative",
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"artefato ausente: {path}")
    return path.read_text(encoding="utf-8")


def _read_index() -> str:
    return _read(INDEX_PATH)


def _read_t22() -> str:
    return _read(T22_PATH)


# ---------------------------------------------------------------------------
# FAIL-01 — índice canônico
# ---------------------------------------------------------------------------


class TestFAIL01IndexExists(unittest.TestCase):
    """FAIL-01 — failure-backlog-index.md existe."""

    def test_index_exists(self) -> None:
        self.assertTrue(
            INDEX_PATH.is_file(),
            f"artefato ausente: {INDEX_PATH}",
        )


# ---------------------------------------------------------------------------
# FAIL-02 — T22 no pai
# ---------------------------------------------------------------------------


class TestFAIL02T22Exists(unittest.TestCase):
    """FAIL-02 — T22-fix-tooling-e2e-compose-zoekt.md existe."""

    def test_t22_exists(self) -> None:
        self.assertTrue(
            T22_PATH.is_file(),
            f"artefato ausente: {T22_PATH}",
        )


# ---------------------------------------------------------------------------
# FAIL-03 — superfície tooling-e2e
# ---------------------------------------------------------------------------


class TestFAIL03ToolingSurface(unittest.TestCase):
    """FAIL-03 — índice e T22 declaram tooling-e2e."""

    def test_surface_declared(self) -> None:
        index = _read_index().lower()
        t22 = _read_t22().lower()
        self.assertIn("tooling-e2e", index)
        self.assertIn("tooling-e2e", t22)


# ---------------------------------------------------------------------------
# FAIL-04 — classificação combinada
# ---------------------------------------------------------------------------


class TestFAIL04Classification(unittest.TestCase):
    """FAIL-04 — F-T04-001→flakiness; F-T04-002→produto; F-T04-003→consequência."""

    def test_combined_classification(self) -> None:
        t22 = _read_t22().lower()
        # combinação / REQ-017 deve ser explícita
        self.assertTrue(
            "classifica" in t22 or "req-017" in t22 or "combina" in t22,
            "T22 deve declarar classificação REQ-017 (combinação)",
        )
        # vínculo ID → classificação (design 0.1.1 / D-T05-003)
        self.assertRegex(
            t22,
            r"f-t04-001.{0,160}flakiness|flakiness.{0,160}f-t04-001",
            "T22 deve vincular F-T04-001 → flakiness",
        )
        self.assertRegex(
            t22,
            r"f-t04-002.{0,160}produto|produto.{0,160}f-t04-002",
            "T22 deve vincular F-T04-002 → produto",
        )
        self.assertRegex(
            t22,
            r"f-t04-003.{0,160}consequ|consequ.{0,160}f-t04-003",
            "T22 deve vincular F-T04-003 → consequência (de F-T04-002)",
        )


# ---------------------------------------------------------------------------
# FAIL-05 — evidências F-T04-*
# ---------------------------------------------------------------------------


class TestFAIL05EvidenceIds(unittest.TestCase):
    """FAIL-05 — F-T04-001..003 referenciados."""

    def test_failure_ids_present(self) -> None:
        blob = (_read_index() + "\n" + _read_t22()).upper()
        for fid in ("F-T04-001", "F-T04-002", "F-T04-003"):
            self.assertIn(
                fid,
                blob,
                f"backlog deve referenciar {fid}",
            )


# ---------------------------------------------------------------------------
# FAIL-06 — zero falhas pytest
# ---------------------------------------------------------------------------


class TestFAIL06ZeroPytestFailures(unittest.TestCase):
    """FAIL-06 — índice declara zero falhas pytest."""

    def test_zero_pytest_failures(self) -> None:
        index = _read_index().lower()
        self.assertTrue(
            ("pytest" in index)
            and (
                "zero" in index
                or "0 falha" in index
                or "nenhuma falha" in index
                or "failed=`0`" in index
                or "failed=0" in index
                or "failed | `0`" in index
                or "| `0`" in index
            ),
            "índice deve declarar zero falhas runtime pytest",
        )
        # não deve haver task pytest inventada no pai
        inventadas = list(PARENT_TASKS_DIR.glob("T2*-fix-pytest*"))
        self.assertEqual(
            inventadas,
            [],
            f"não inventar tasks pytest: {inventadas}",
        )


# ---------------------------------------------------------------------------
# FAIL-07 — sem T23 health fantasma
# ---------------------------------------------------------------------------


class TestFAIL07NoPhantomHealthTask(unittest.TestCase):
    """FAIL-07 — sem T23-fix-health*; health sem falha observável."""

    def test_no_t23_health_fix_task(self) -> None:
        phantoms = list(PARENT_TASKS_DIR.glob("T23-fix-health*"))
        phantoms += list(PARENT_TASKS_DIR.glob("T2*-fix-health*"))
        self.assertEqual(
            phantoms,
            [],
            f"não abrir task health fantasma: {phantoms}",
        )
        index = _read_index().lower()
        self.assertIn("health", index)
        self.assertTrue(
            "sem falha" in index
            or "não afetad" in index
            or "nao afetad" in index
            or "sem falha observ" in index
            or "nenhuma falha" in index,
            "índice deve declarar health sem falha observável independente",
        )


# ---------------------------------------------------------------------------
# FAIL-08 — sem falhas inventadas nas demais superfícies
# ---------------------------------------------------------------------------


class TestFAIL08NoInventedSuiteFailures(unittest.TestCase):
    """FAIL-08 — catalog/ui/mcp/negative sem falha runtime observável."""

    def test_surfaces_without_runtime_failure(self) -> None:
        index = _read_index().lower()
        for surface in SURFACES_NO_FAILURE:
            if surface == "health":
                continue  # coberto em FAIL-07
            self.assertIn(
                surface,
                index,
                f"índice deve mencionar superfície {surface}",
            )
        self.assertTrue(
            "t06" in index or "lacuna" in index or "gap" in index,
            "índice deve apontar lacunas para T06 (não inventar falha)",
        )


# ---------------------------------------------------------------------------
# FAIL-09 — sanitização
# ---------------------------------------------------------------------------


class TestFAIL09NoSecrets(unittest.TestCase):
    """FAIL-09 — sem tokens nos artefatos."""

    def test_no_token_leak(self) -> None:
        blob = _read_index() + "\n" + _read_t22()
        self.assertIsNone(
            TOKEN_PREFIX_RE.search(blob),
            "artefatos não devem conter prefixos de token GitHub",
        )
        self.assertIsNone(
            TOKEN_ASSIGN_RE.search(blob),
            "artefatos não devem conter assignment de token com valor",
        )


# ---------------------------------------------------------------------------
# FAIL-10 — ENG-010 sem fix nesta feature
# ---------------------------------------------------------------------------


class TestFAIL10NoFixInThisFeature(unittest.TestCase):
    """FAIL-10 — correção só no pipeline do pai; sem patch nesta feature."""

    def test_no_fix_claim_in_child_feature(self) -> None:
        text = _read_index() + "\n" + _read_t22()
        blob = text.lower()
        self.assertTrue(
            "não implement" in blob
            or "nao implement" in blob
            or "sem implementação" in blob
            or "sem implementacao" in blob
            or "pipeline do pai" in blob
            or "eng-010" in blob,
            "deve declarar que esta feature não implementa o fix",
        )
        # D-T05-005 / ENG-010 — escopo sem alteração de produto (paridade T03/T04)
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
