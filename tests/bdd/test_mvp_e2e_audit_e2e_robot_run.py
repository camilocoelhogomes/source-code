"""
BDD executável — T04-run-e2e-robot (artefato RobotGreenPathRun).

Valida existência/conteúdo de
    spec/features/mvp-e2e-audit-hardening/runs/e2e-robot-green-path.md
conforme design §3.3 e BDD-003. Não reexecuta Podman/Robot.
Não corrige falhas de produto nem altera src/e2e.

Cenários: E2E-01..E2E-10 — ver
    spec/features/mvp-e2e-audit-hardening/tasks/T04-run-e2e-robot/bdd.md

Execução:
    python -m pytest tests/bdd/test_mvp_e2e_audit_e2e_robot_run.py -q --no-cov

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
    / "e2e-robot-green-path.md"
)

CANONICAL_COMMAND = "python -m github_rag.e2e"

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

GREEN_PATH_SUITES = (
    "health",
    "catalog_indexing",
    "ui",
    "mcp",
    "negative",
)

PHASE_MARKERS = (
    "credential",
    "compose",
    "healthy",
    "robot",
    "down",
)


def _read_artifact() -> str:
    if not ARTIFACT_PATH.is_file():
        raise AssertionError(f"artefato ausente: {ARTIFACT_PATH}")
    return ARTIFACT_PATH.read_text(encoding="utf-8")


def _failure_list_section(text: str) -> str:
    lower = text.lower()
    markers = (
        "## lista de falhas",
        "## falhas",
        "### lista de falhas",
        "falhas acionáveis",
        "falhas para t05",
        "handoff t05",
    )
    start = -1
    for marker in markers:
        idx = lower.find(marker)
        if idx != -1 and (start == -1 or idx < start):
            start = idx
    if start == -1:
        return text
    rest = text[start:]
    next_sec = re.search(r"\n##\s+", rest[1:])
    if next_sec:
        return rest[: next_sec.start() + 1]
    return rest


# ---------------------------------------------------------------------------
# E2E-01 — artefato canônico
# ---------------------------------------------------------------------------


class TestE2E01ArtifactExists(unittest.TestCase):
    """E2E-01 — e2e-robot-green-path.md no path canônico."""

    def test_artifact_file_exists(self) -> None:
        self.assertTrue(
            ARTIFACT_PATH.is_file(),
            f"artefato ausente: {ARTIFACT_PATH}",
        )


# ---------------------------------------------------------------------------
# E2E-02 — metadados e comando
# ---------------------------------------------------------------------------


class TestE2E02Metadata(unittest.TestCase):
    """E2E-02 — ISO, branch/commit, comando canônico, python, OS, Podman."""

    def test_run_metadata_present(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertIsNotNone(
            ISO_DATETIME_RE.search(text),
            "artefato deve registrar data/hora ISO",
        )
        self.assertIn("branch", lower, "artefato deve registrar branch")
        self.assertIsNotNone(
            COMMIT_SHA_RE.search(text),
            "artefato deve registrar commit SHA",
        )
        self.assertIn(
            CANONICAL_COMMAND,
            text,
            f"artefato deve documentar o comando canônico: {CANONICAL_COMMAND}",
        )
        self.assertIn("python", lower, "artefato deve registrar versão Python")
        self.assertTrue(
            "os" in lower
            or "darwin" in lower
            or "linux" in lower
            or "windows" in lower
            or "plataforma" in lower,
            "artefato deve registrar OS resumido",
        )
        self.assertIn("podman", lower, "artefato deve registrar Podman")


# ---------------------------------------------------------------------------
# E2E-03 — pré-condições T02 / HITL
# ---------------------------------------------------------------------------


class TestE2E03Preconditions(unittest.TestCase):
    """E2E-03 — gate T02, token bool, Podman, repo ref."""

    def test_hitl_preconditions(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertTrue(
            "ready" in lower or "gate t02" in lower or "t02" in lower,
            "artefato deve registrar gate T02 / READY",
        )
        self.assertRegex(
            lower,
            r"present\s*=\s*(true|false)",
            "artefato deve registrar token present=true/false",
        )
        self.assertIn("podman", lower)
        self.assertIn("camilocoelhogomes/source-code", text)


# ---------------------------------------------------------------------------
# E2E-04 — resultado agregado
# ---------------------------------------------------------------------------


class TestE2E04AggregatedResult(unittest.TestCase):
    """E2E-04 — exit code; ≠0 válido como evidência."""

    def test_exit_code_present(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertTrue(
            "exit" in lower
            and ("code" in lower or "código" in lower or "codigo" in lower),
            "artefato deve registrar exit code",
        )
        self.assertIsNotNone(
            re.search(r"exit\s*code\s*[|:]\s*`?\d+`?", lower)
            or re.search(r"\|\s*exit code\s*\|\s*`?\d+`?", lower),
            "artefato deve conter valor numérico de exit code",
        )
        self.assertTrue(
            "evidência" in lower
            or "evidencia" in lower
            or "válid" in lower
            or "valid" in lower
            or "≠ 0" in text
            or "!= 0" in text
            or "exit ≠ 0" in lower
            or "falha" in lower,
            "artefato deve reconhecer exit ≠ 0 como evidência válida "
            "ou registrar falhas/sucesso observável",
        )


# ---------------------------------------------------------------------------
# E2E-05 — fases
# ---------------------------------------------------------------------------


class TestE2E05Phases(unittest.TestCase):
    """E2E-05 — credential / compose / healthy / robot / down."""

    def test_phases_documented(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        for marker in PHASE_MARKERS:
            self.assertIn(
                marker,
                lower,
                f"artefato deve documentar fase contendo '{marker}'",
            )
        self.assertTrue(
            "ok" in lower or "fail" in lower or "skip" in lower or "pass" in lower,
            "fases devem ter status observável",
        )


# ---------------------------------------------------------------------------
# E2E-06 — suítes green path
# ---------------------------------------------------------------------------


class TestE2E06GreenPathSuites(unittest.TestCase):
    """E2E-06 — cinco suítes T21 + exclude bdd015 + resultado."""

    def test_suites_and_exclude(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        for suite in GREEN_PATH_SUITES:
            self.assertIn(
                suite,
                lower,
                f"artefato deve mencionar suíte '{suite}'",
            )
        self.assertTrue(
            "bdd015" in lower or "exclude bdd015" in lower,
            "artefato deve registrar exclusão bdd015",
        )
        self.assertTrue(
            "pass" in lower or "fail" in lower or "unknown" in lower,
            "artefato deve registrar resultado por suíte (pass/fail/unknown)",
        )


# ---------------------------------------------------------------------------
# E2E-07 — falhas para T05
# ---------------------------------------------------------------------------


class TestE2E07FailuresForT05(unittest.TestCase):
    """E2E-07 — falhas com superfície; lista vazia ok."""

    def test_failure_list_contract(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertTrue(
            "falha" in lower or "failure" in lower or "t05" in lower,
            "artefato deve ter seção/lista de falhas (pode ser vazia)",
        )
        self.assertTrue(
            any(s in lower for s in SURFACES)
            or "superfície" in lower
            or "superficie" in lower,
            "artefato deve documentar superfícies candidatas ENG-006",
        )
        section = _failure_list_section(text)
        section_lower = section.lower()
        empty_ok = (
            "lista vazia" in section_lower
            or "nenhuma" in section_lower
            or "sem falha" in section_lower
            or "no failure" in section_lower
            or "0 falha" in section_lower
        )
        has_entries = bool(
            re.search(
                r"\|\s*`?(health|catalog_indexing|ui|mcp|negative|tooling-e2e)",
                section_lower,
            )
            or re.search(r"(cenário|scenario|suite|fase)\s*[|:]", section_lower)
        )
        if has_entries and not empty_ok:
            self.assertTrue(
                any(s in section_lower for s in SURFACES),
                "entradas devem mapear superfície candidata",
            )
            self.assertTrue(
                "motivo" in section_lower
                or "mensagem" in section_lower
                or "message" in section_lower
                or "tipo" in section_lower
                or "fail" in section_lower,
                "entradas devem incluir motivo/tipo sanitizado",
            )


# ---------------------------------------------------------------------------
# E2E-08 — soft-dep T03
# ---------------------------------------------------------------------------


class TestE2E08SoftDepT03(unittest.TestCase):
    """E2E-08 — nota T03 + evidência independente."""

    def test_soft_dep_t03_independent(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertTrue(
            "t03" in lower,
            "artefato deve declarar estado da soft-dep T03",
        )
        self.assertTrue(
            "independente" in lower
            or "independent" in lower
            or "não rebase" in lower
            or "nao rebase" in lower
            or "sem rebase" in lower,
            "artefato deve declarar evidência T04 independente de T03",
        )


# ---------------------------------------------------------------------------
# E2E-09 — sem secrets
# ---------------------------------------------------------------------------


class TestE2E09NoSecrets(unittest.TestCase):
    """E2E-09 — sem prefixos PAT / assigns longos."""

    def test_no_token_patterns(self) -> None:
        text = _read_artifact()
        self.assertIsNone(
            TOKEN_PREFIX_RE.search(text),
            "artefato não deve conter prefixos de token GitHub",
        )
        self.assertIsNone(
            TOKEN_ASSIGN_RE.search(text),
            "artefato não deve conter atribuição longa de GITHUB_TOKEN/"
            "E2E_GITHUB_TOKEN",
        )


# ---------------------------------------------------------------------------
# E2E-10 — sem expansão / sem produto
# ---------------------------------------------------------------------------


class TestE2E10Scope(unittest.TestCase):
    """E2E-10 — declara sem expansão Robot e sem mudança src/robot."""

    def test_no_product_or_robot_expansion(self) -> None:
        text = _read_artifact()
        lower = text.lower()
        self.assertTrue(
            "não" in lower
            or "nao" in lower
            or "sem expansão" in lower
            or "sem expansao" in lower
            or "no expansion" in lower
            or "proibido" in lower
            or "fora de escopo" in lower,
            "artefato deve declarar ausência de expansão Robot/browser",
        )
        self.assertTrue(
            "src/github_rag" in lower or "src/github_rag/**" in text,
            "artefato deve mencionar src/github_rag/** sem alteração",
        )
        self.assertTrue(
            "e2e/robot" in lower,
            "artefato deve mencionar e2e/robot/** sem alteração",
        )


if __name__ == "__main__":
    unittest.main()
