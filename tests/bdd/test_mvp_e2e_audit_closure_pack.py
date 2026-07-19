"""
BDD executável — T07-consolidate-evidence-close (AuditClosurePack).

Valida:
  - spec/features/mvp-e2e-audit-hardening/audit/closure-pack.md

conforme design §3 e BDD CLOSE-01..CLOSE-12.
Não implementa fixes; não declara MVP entregue; não altera compose/robot/src.

Execução:
    python -m pytest tests/bdd/test_mvp_e2e_audit_closure_pack.py -q --no-cov

TDD: artefato ausente → falha esperada até a implementação documental.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURE_DIR = REPO_ROOT / "spec" / "features" / "mvp-e2e-audit-hardening"
PACK_PATH = FEATURE_DIR / "audit" / "closure-pack.md"
PARENT_TASKS_DIR = REPO_ROOT / "spec" / "features" / "github-etl-mcp-rag" / "tasks"

PARENT_TASK_SLUGS = {
    "T22": "T22-fix-tooling-e2e-compose-zoekt.md",
    "T23": "T23-gap-ui-browser.md",
    "T24": "T24-gap-catalog-indexing-integral.md",
    "T25": "T25-gap-negative-integral.md",
    "T26": "T26-gap-mcp-parallel-slo.md",
    "T27": "T27-gap-sdk-dec015-conformity.md",
}

TOKEN_PREFIX_RE = re.compile(r"\b(ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{8,}")
TOKEN_ASSIGN_RE = re.compile(
    r"(?m)^(?:export\s+)?(?:GITHUB_TOKEN|E2E_GITHUB_TOKEN)\s*=\s*"
    r"['\"]?[A-Za-z0-9_\-]{20,}"
)

MVP_DELIVERED_POSITIVE_RE = re.compile(
    r"(?i)\b(mvp\s+(de\s+produto\s+)?(est[aá]\s+)?entregue"
    r"|mvp\s+delivered"
    r"|declarar?\s+mvp\s+entregue)\b"
)


def _read_pack() -> str:
    if not PACK_PATH.is_file():
        raise AssertionError(f"artefato ausente: {PACK_PATH}")
    return PACK_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# CLOSE-01 — pacote canônico
# ---------------------------------------------------------------------------


class TestCLOSE01PackExists(unittest.TestCase):
    """CLOSE-01 — closure-pack.md existe."""

    def test_pack_exists(self) -> None:
        self.assertTrue(PACK_PATH.is_file(), f"artefato ausente: {PACK_PATH}")


# ---------------------------------------------------------------------------
# CLOSE-02 — inventário T01
# ---------------------------------------------------------------------------


class TestCLOSE02Inventory(unittest.TestCase):
    """CLOSE-02 — referencia coverage-inventory / T01."""

    def test_inventory_referenced(self) -> None:
        text = _read_pack().lower()
        self.assertTrue(
            "coverage-inventory" in text or "inventário" in text or "inventario" in text,
            "pacote deve referenciar inventário T01",
        )
        self.assertTrue(
            "t01" in text,
            "pacote deve mencionar T01",
        )


# ---------------------------------------------------------------------------
# CLOSE-03 — HITL T02
# ---------------------------------------------------------------------------


class TestCLOSE03Hitl(unittest.TestCase):
    """CLOSE-03 — referencia hitl-env-checklist / T02."""

    def test_hitl_referenced(self) -> None:
        text = _read_pack().lower()
        self.assertTrue(
            "hitl-env-checklist" in text or "hitl" in text,
            "pacote deve referenciar checklist HITL T02",
        )
        self.assertIn("t02", text)


# ---------------------------------------------------------------------------
# CLOSE-04 — pytest T03
# ---------------------------------------------------------------------------


class TestCLOSE04PytestRun(unittest.TestCase):
    """CLOSE-04 — referencia pytest-all-tasks / T03."""

    def test_pytest_run_referenced(self) -> None:
        text = _read_pack().lower()
        self.assertTrue(
            "pytest-all-tasks" in text
            or "parentpytestrun" in text
            or ("pytest" in text and "t03" in text),
            "pacote deve referenciar run pytest T03",
        )
        self.assertIn("t03", text)


# ---------------------------------------------------------------------------
# CLOSE-05 — e2e T04
# ---------------------------------------------------------------------------


class TestCLOSE05E2eRun(unittest.TestCase):
    """CLOSE-05 — referencia e2e-robot-green-path / T04."""

    def test_e2e_run_referenced(self) -> None:
        text = _read_pack().lower()
        self.assertTrue(
            "e2e-robot-green-path" in text
            or "robotgreenpathrun" in text
            or ("e2e" in text and "t04" in text),
            "pacote deve referenciar run e2e T04",
        )
        self.assertIn("t04", text)


# ---------------------------------------------------------------------------
# CLOSE-06 — falhas T05 / T22
# ---------------------------------------------------------------------------


class TestCLOSE06FailureBacklog(unittest.TestCase):
    """CLOSE-06 — failure-backlog + T22."""

    def test_failure_and_t22(self) -> None:
        text = _read_pack()
        lower = text.lower()
        self.assertTrue(
            "failure-backlog-index" in lower or "t05" in lower,
            "pacote deve referenciar índice de falhas T05",
        )
        self.assertIn("t22", lower)
        self.assertTrue(
            "fix-tooling" in lower or "t22-fix-tooling-e2e-compose-zoekt" in lower,
            "pacote deve listar slug/task T22 fix-tooling",
        )
        self.assertTrue(
            (PARENT_TASKS_DIR / PARENT_TASK_SLUGS["T22"]).is_file(),
            "task pai T22 deve existir (pré-condição base T06)",
        )


# ---------------------------------------------------------------------------
# CLOSE-07 — gap-fill T06 / T23–T27
# ---------------------------------------------------------------------------


class TestCLOSE07GapFillBacklog(unittest.TestCase):
    """CLOSE-07 — gap-fill-backlog + T23–T27."""

    def test_gap_fill_and_t23_t27(self) -> None:
        text = _read_pack()
        lower = text.lower()
        self.assertTrue(
            "gap-fill-backlog-index" in lower or "t06" in lower,
            "pacote deve referenciar índice gap-fill T06",
        )
        for task_id, slug in PARENT_TASK_SLUGS.items():
            if task_id == "T22":
                continue
            self.assertIn(
                task_id.lower(),
                lower,
                f"pacote deve listar {task_id}",
            )
            # slug fragment (gap-*)
            fragment = slug.replace(".md", "").lower()
            self.assertTrue(
                fragment in lower or fragment.split("-", 1)[-1][:8] in lower,
                f"pacote deve referenciar slug {slug}",
            )
            self.assertTrue(
                (PARENT_TASKS_DIR / slug).is_file(),
                f"task pai {slug} deve existir",
            )


# ---------------------------------------------------------------------------
# CLOSE-08 — ordem run-first → falha → gap-fill
# ---------------------------------------------------------------------------


class TestCLOSE08Order(unittest.TestCase):
    """CLOSE-08 — ordem run-first → falhas → lacunas."""

    def test_order_demonstrated(self) -> None:
        text = _read_pack().lower()
        self.assertTrue(
            "run-first" in text
            or "run first" in text
            or "bdd-007" in text
            or "br-007" in text
            or "ordem" in text,
            "pacote deve declarar ordem run-first → gap-fill",
        )
        # falhas antes de lacunas (posições relativas de menções)
        pos_t22 = text.find("t22")
        pos_t23 = text.find("t23")
        self.assertNotEqual(pos_t22, -1, "T22 deve aparecer")
        self.assertNotEqual(pos_t23, -1, "T23 deve aparecer")
        # seção de ordem ou menção explícita falhas antes lacunas
        self.assertTrue(
            "antes" in text
            or "após" in text
            or "apos" in text
            or "depois" in text
            or "→" in text
            or "->" in text
            or "falha" in text
            and "lacuna" in text,
            "pacote deve demonstrar falhas antes de lacunas / gap-fill",
        )


# ---------------------------------------------------------------------------
# CLOSE-09 — métricas + BR-005
# ---------------------------------------------------------------------------


class TestCLOSE09SuccessMetrics(unittest.TestCase):
    """CLOSE-09 — métricas de sucesso e IDs T22–T27."""

    def test_metrics_and_parent_ids(self) -> None:
        text = _read_pack().lower()
        self.assertTrue(
            "métrica" in text or "metrica" in text or "sucesso" in text,
            "pacote deve verificar métricas de sucesso",
        )
        self.assertTrue(
            "invent" in text,
            "métrica inventário",
        )
        self.assertTrue(
            "pytest" in text,
            "métrica pytest",
        )
        self.assertTrue(
            "e2e" in text or "robot" in text,
            "métrica e2e/robot",
        )
        self.assertTrue(
            "br-005" in text or "toda falha" in text or "toda lacuna" in text,
            "pacote deve refletir BR-005",
        )
        for tid in ("t22", "t23", "t24", "t25", "t26", "t27"):
            self.assertIn(tid, text, f"backlog aberto deve incluir {tid}")


# ---------------------------------------------------------------------------
# CLOSE-10 — encerrável; anti-MVP entregue
# ---------------------------------------------------------------------------


class TestCLOSE10ClosureStatus(unittest.TestCase):
    """CLOSE-10 — CLOSURE_READY / encerrável; MVP não entregue."""

    def test_closure_ready_not_mvp_delivered(self) -> None:
        text = _read_pack()
        lower = text.lower()
        self.assertTrue(
            "closure_ready" in lower
            or "encerrável" in lower
            or "encerravel" in lower
            or "aguardando merge" in lower,
            "pacote deve declarar feature encerrável / CLOSURE_READY / aguardando merge",
        )
        self.assertTrue(
            ("mvp" in lower)
            and (
                "não" in lower
                or "nao" in lower
                or "não entregue" in lower
                or "nao entregue" in lower
                or "não está entregue" in lower
                or "nao esta entregue" in lower
            ),
            "pacote deve declarar explicitamente que MVP não está entregue",
        )
        # rejeitar conclusão positiva de MVP entregue (exceto negação na mesma frase)
        for match in MVP_DELIVERED_POSITIVE_RE.finditer(text):
            window = text[max(0, match.start() - 40) : match.end() + 10].lower()
            self.assertTrue(
                "não" in window
                or "nao" in window
                or "sem " in window
                or "proíbe" in window
                or "proibe" in window,
                f"não declarar MVP entregue positivamente: {match.group(0)!r}",
            )


# ---------------------------------------------------------------------------
# CLOSE-11 — sanitização
# ---------------------------------------------------------------------------


class TestCLOSE11NoSecrets(unittest.TestCase):
    """CLOSE-11 — sem tokens no pacote."""

    def test_no_token_leak(self) -> None:
        blob = _read_pack()
        self.assertIsNone(
            TOKEN_PREFIX_RE.search(blob),
            "pacote não deve conter prefixos de token GitHub",
        )
        self.assertIsNone(
            TOKEN_ASSIGN_RE.search(blob),
            "pacote não deve conter assignment de token com valor",
        )


# ---------------------------------------------------------------------------
# CLOSE-12 — ENG-010
# ---------------------------------------------------------------------------


class TestCLOSE12Eng010(unittest.TestCase):
    """CLOSE-12 — sem fix nesta feature; pipeline do pai."""

    def test_eng010_no_product_fix(self) -> None:
        text = _read_pack()
        blob = text.lower()
        self.assertTrue(
            "eng-010" in blob
            or "não implement" in blob
            or "nao implement" in blob
            or "pipeline do pai" in blob,
            "deve declarar que correções ficam no pipeline do pai",
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
            "deve afirmar escopo sem alteração em composes",
        )


if __name__ == "__main__":
    unittest.main()
