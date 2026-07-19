"""
BDD executável — T03-run-pytest-all-tasks (artefato ParentPytestRun).

Valida existência/conteúdo de
    spec/features/mvp-e2e-audit-hardening/runs/pytest-all-tasks.md
conforme design §3.3 e BDD-004. Não roda Robot/e2e.
Não corrige falhas de produto nem altera src/e2e.

Cenários: PYTEST-01..PYTEST-09 — ver
    spec/features/mvp-e2e-audit-hardening/tasks/T03-run-pytest-all-tasks/bdd.md

Execução:
    python -m pytest tests/bdd/test_mvp_e2e_audit_pytest_run.py -q --no-cov

TDD: artefato ausente → falha esperada até a implementação documental.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = (
    REPO_ROOT
    / "spec"
    / "features"
    / "mvp-e2e-audit-hardening"
    / "runs"
    / "pytest-all-tasks.md"
)

CANONICAL_COMMAND = "python -m pytest tests/ -q --tb=line"

TOKEN_PREFIX_RE = re.compile(r"\b(ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{8,}")
TOKEN_ASSIGN_RE = re.compile(
    r"(?m)^(?:export\s+)?(?:GITHUB_TOKEN|E2E_GITHUB_TOKEN)\s*=\s*"
    r"['\"]?[A-Za-z0-9_\-]{20,}"
)

ISO_DATETIME_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
)
COMMIT_SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE)

SURFACES = (
    "health",
    "catalog_indexing",
    "ui",
    "mcp",
    "negative",
    "tooling-e2e",
)

CHILD_NODEID_RE = re.compile(r"mvp_e2e_audit_", re.IGNORECASE)


def _read_artifact() -> str:
    if not ARTIFACT_PATH.is_file():
        raise AssertionError(f"artefato ausente: {ARTIFACT_PATH}")
    return ARTIFACT_PATH.read_text(encoding="utf-8")


def _failure_list_section(text: str) -> str:
    """Extrai bloco da lista de falhas do pai (até próxima seção ## ou fim)."""
    lower = text.lower()
    markers = (
        "## lista de falhas",
        "## falhas do pai",
        "## falhas (pai)",
        "### lista de falhas",
        "lista de falhas (pai)",
        "lista de falhas do pai",
    )
    start = -1
    for marker in markers:
        idx = lower.find(marker)
        if idx != -1 and (start == -1 or idx < start):
            start = idx
    if start == -1:
        return text
    rest = text[start:]
    # próxima seção de nível ## após o início
    next_sec = re.search(r"\n##\s+", rest[1:])
    if next_sec:
        return rest[: next_sec.start() + 1]
    return rest


# ---------------------------------------------------------------------------
# PYTEST-01 — artefato canônico
# ---------------------------------------------------------------------------


class TestPYTEST01ArtifactExists(unittest.TestCase):
    """PYTEST-01 — pytest-all-tasks.md no path canônico."""

    def test_artifact_file_exists(self) -> None:
        self.assertTrue(
            ARTIFACT_PATH.is_file(),
            f"artefato ausente: {ARTIFACT_PATH}",
        )


# ---------------------------------------------------------------------------
# PYTEST-02 — metadados
# ---------------------------------------------------------------------------


class TestPYTEST02Metadata(unittest.TestCase):
    """PYTEST-02 — ISO, branch/commit, comando canônico, python, OS."""

    def test_run_metadata_present(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertIsNotNone(
            ISO_DATETIME_RE.search(text),
            "artefato deve registrar data/hora ISO",
        )
        self.assertTrue(
            "branch" in lower,
            "artefato deve registrar branch",
        )
        self.assertIsNotNone(
            COMMIT_SHA_RE.search(text),
            "artefato deve registrar commit SHA",
        )
        self.assertIn(
            CANONICAL_COMMAND,
            text,
            f"artefato deve documentar o comando canônico: {CANONICAL_COMMAND}",
        )
        self.assertTrue(
            "python" in lower,
            "artefato deve registrar versão Python",
        )
        self.assertTrue(
            "os" in lower
            or "darwin" in lower
            or "linux" in lower
            or "windows" in lower
            or "plataforma" in lower,
            "artefato deve registrar OS resumido",
        )


# ---------------------------------------------------------------------------
# PYTEST-03 — resultado agregado
# ---------------------------------------------------------------------------


class TestPYTEST03AggregatedResult(unittest.TestCase):
    """PYTEST-03 — exit code; passed/failed/skipped/errors/total."""

    def test_aggregated_counts_present(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertTrue(
            "exit" in lower and ("code" in lower or "código" in lower or "codigo" in lower),
            "artefato deve registrar exit code",
        )
        for key in ("passed", "failed", "skipped", "errors", "total"):
            self.assertIn(
                key,
                lower,
                f"artefato deve registrar contagem '{key}'",
            )


# ---------------------------------------------------------------------------
# PYTEST-04 — cobertura / coverage_gate
# ---------------------------------------------------------------------------


class TestPYTEST04Coverage(unittest.TestCase):
    """PYTEST-04 — cobertura % ou N/A; coverage_gate quando aplicável."""

    def test_coverage_or_na_and_gate_field(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        has_pct = bool(re.search(r"\b\d{1,3}(?:\.\d+)?\s*%", text))
        has_na = "n/a" in lower or "na" in lower.split() or "não disponível" in lower or "nao disponivel" in lower
        self.assertTrue(
            has_pct or "n/a" in lower or "cobertura" in lower,
            "artefato deve registrar cobertura % ou N/A (com motivo)",
        )
        if not has_pct:
            self.assertTrue(
                "n/a" in lower or "motivo" in lower or "indispon" in lower,
                "quando sem %, deve declarar N/A com motivo",
            )
        # Campo coverage_gate deve existir no contrato (valor true/false/N/A)
        self.assertTrue(
            "coverage_gate" in lower or "coverage gate" in lower,
            "artefato deve documentar campo coverage_gate (D-T03 / design §3.3)",
        )
        # evita unused em linters locais
        _ = has_na


# ---------------------------------------------------------------------------
# PYTEST-05 — lista de falhas do pai
# ---------------------------------------------------------------------------


class TestPYTEST05ParentFailures(unittest.TestCase):
    """PYTEST-05 — nodeid, tipo, mensagem sanitizada, superfície candidata."""

    def test_failure_list_contract(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertTrue(
            "falha" in lower or "failure" in lower or "nodeid" in lower,
            "artefato deve ter seção/lista de falhas do pai (pode ser vazia)",
        )
        self.assertTrue(
            "superfície" in lower
            or "superficie" in lower
            or "surface" in lower
            or any(s in lower for s in SURFACES),
            "artefato deve documentar superfícies candidatas para T05",
        )
        section = _failure_list_section(text)
        section_lower = section.lower()
        # Se há entradas tipadas, validar campos; lista vazia ok
        has_entries = bool(
            re.search(r"nodeid|tests/[^\s]+\.py", section, re.IGNORECASE)
        )
        if has_entries:
            self.assertTrue(
                "nodeid" in section_lower or "tests/" in section_lower,
                "entradas devem incluir nodeid",
            )
            self.assertTrue(
                "failed" in section_lower or "error" in section_lower,
                "entradas devem declarar tipo failed/error",
            )
            self.assertTrue(
                any(s in section_lower for s in SURFACES)
                or "superfície" in section_lower
                or "superficie" in section_lower,
                "entradas devem mapear superfície candidata",
            )
        for surface in SURFACES:
            self.assertTrue(
                surface in lower or surface.replace("_", "-") in lower
                or "superfície" in lower
                or "superficie" in lower,
                f"mapa/lista deve admitir superfície {surface}",
            )


# ---------------------------------------------------------------------------
# PYTEST-06 — soft-dep T01
# ---------------------------------------------------------------------------


class TestPYTEST06SoftDepT01(unittest.TestCase):
    """PYTEST-06 — nota soft-dep T01; run não depende do inventário."""

    def test_t01_soft_dep_note(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertTrue(
            "t01" in lower,
            "artefato deve mencionar T01 (soft-dep)",
        )
        self.assertTrue(
            "soft" in lower
            or "não depend" in lower
            or "nao depend" in lower
            or "opcional" in lower
            or "não bloque" in lower
            or "nao bloque" in lower,
            "artefato deve declarar que o run não depende do inventário T01",
        )


# ---------------------------------------------------------------------------
# PYTEST-07 — sem secrets
# ---------------------------------------------------------------------------


class TestPYTEST07NoSecrets(unittest.TestCase):
    """PYTEST-07 — sem ghp_/gho_/… nem assigns longos."""

    def test_artifact_has_no_token_patterns(self) -> None:
        text = _read_artifact()
        self.assertIsNone(
            TOKEN_PREFIX_RE.search(text),
            "artefato não deve conter padrões de token GitHub (ghp_/gho_/…)",
        )
        self.assertIsNone(
            TOKEN_ASSIGN_RE.search(text),
            "artefato não deve atribuir valor longo a GITHUB_TOKEN/E2E_GITHUB_TOKEN",
        )


# ---------------------------------------------------------------------------
# PYTEST-08 — D-T03-002 exclui mvp_e2e_audit_*
# ---------------------------------------------------------------------------


class TestPYTEST08ExcludesChildNodeids(unittest.TestCase):
    """PYTEST-08 — lista de falhas do pai sem nodeids mvp_e2e_audit_*."""

    def test_parent_failure_list_excludes_child_contract_nodeids(self) -> None:
        text = _read_artifact()
        section = _failure_list_section(text)
        # Declaração explícita D-T03-002 OU ausência de nodeids filhos na lista
        lower = text.lower()
        self.assertTrue(
            "d-t03-002" in lower
            or "mvp_e2e_audit_" in lower
            or "feature filha" in lower
            or "contrato da filha" in lower
            or "excluir" in lower
            or "exclu" in lower,
            "artefato deve declarar exclusão de nodeids da feature filha (D-T03-002)",
        )
        # Na seção de falhas do pai, linhas de nodeid não devem ser mvp_e2e_audit_*
        for line in section.splitlines():
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
            if "mvp_e2e_audit_" in line_stripped and (
                "tests/" in line_stripped or "nodeid" in line_stripped.lower()
            ):
                # permitir menção na regra de exclusão, não como item de falha
                if any(
                    k in line_stripped.lower()
                    for k in ("exclu", "não inclu", "nao inclu", "d-t03-002", "filha")
                ):
                    continue
                self.fail(
                    f"lista de falhas do pai não deve incluir nodeid filho: {line_stripped}"
                )
        self.assertIsNone(
            CHILD_NODEID_RE.search(
                "\n".join(
                    ln
                    for ln in section.splitlines()
                    if "tests/" in ln and "exclu" not in ln.lower()
                )
            )
            if any("tests/" in ln for ln in section.splitlines())
            else None,
        )


# ---------------------------------------------------------------------------
# PYTEST-09 — sem mudança de produto
# ---------------------------------------------------------------------------


class TestPYTEST09NoProductChange(unittest.TestCase):
    """PYTEST-09 — declaração explícita: sem mudança de produto / src / e2e/robot."""

    def test_no_product_change_declared(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertTrue(
            ("não" in lower or "nao" in lower)
            and (
                "mudança de produto" in lower
                or "mudanca de produto" in lower
                or "alteração de produto" in lower
                or "alteracao de produto" in lower
                or "sem mudança" in lower
                or "sem mudanca" in lower
                or "não altera" in lower
                or "nao altera" in lower
            ),
            "artefato deve declarar que não há mudança de produto exigida",
        )
        self.assertTrue(
            "src/github_rag" in lower or "src/**" in lower or "src/github_rag/**" in text,
            "artefato deve afirmar escopo sem alteração em src/github_rag/**",
        )
        self.assertTrue(
            "e2e/robot" in lower,
            "artefato deve afirmar escopo sem alteração em e2e/robot/**",
        )


if __name__ == "__main__":
    unittest.main()
