"""
BDD executável — T02-hitl-env-prep (artefato HitlEnvPrep / checklist HITL).

Valida existência/conteúdo de
    spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md
conforme design §3.3 e BDD-002. Não roda Robot/e2e.
Não lê nem asserta o valor do token em `.env` real.

Cenários: HITL-01..HITL-10 — ver
    spec/features/mvp-e2e-audit-hardening/tasks/T02-hitl-env-prep/bdd.md

Execução:
    python -m pytest tests/bdd/test_mvp_e2e_audit_hitl_env_prep.py -q

TDD: checklist ausente → falha esperada até a implementação documental.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_PATH = (
    REPO_ROOT
    / "spec"
    / "features"
    / "mvp-e2e-audit-hardening"
    / "audit"
    / "hitl-env-checklist.md"
)
GITIGNORE = REPO_ROOT / ".gitignore"
ENV_EXAMPLE = REPO_ROOT / ".env.example"

TOKEN_PREFIX_RE = re.compile(r"\b(ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{8,}")
TOKEN_ASSIGN_RE = re.compile(
    r"(?m)^(?:export\s+)?(?:GITHUB_TOKEN|E2E_GITHUB_TOKEN)\s*=\s*"
    r"['\"]?[A-Za-z0-9_\-]{20,}"
)

GATE_CHECKS = (
    (".env", "exist"),
    ("ignor",),  # ignorado / check-ignore
    ("track",),  # não trackeado / ls-files
    ("token", "present"),
    ("podman",),
)


def _read_checklist() -> str:
    if not CHECKLIST_PATH.is_file():
        raise AssertionError(f"artefato ausente: {CHECKLIST_PATH}")
    return CHECKLIST_PATH.read_text(encoding="utf-8")


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"arquivo ausente: {path}")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# HITL-01 — artefato canônico
# ---------------------------------------------------------------------------


class TestHITL01ArtifactExists(unittest.TestCase):
    """HITL-01 — hitl-env-checklist.md no path canônico."""

    def test_checklist_file_exists(self) -> None:
        self.assertTrue(
            CHECKLIST_PATH.is_file(),
            f"artefato ausente: {CHECKLIST_PATH}",
        )


# ---------------------------------------------------------------------------
# HITL-02 — pré-requisitos
# ---------------------------------------------------------------------------


class TestHITL02Prerequisites(unittest.TestCase):
    """HITL-02 — Podman, repo de referência, .env.example, e2e/README.md."""

    def test_prerequisites_documented(self) -> None:
        text = _read_checklist()
        lower = text.lower()
        self.assertIn("podman", lower)
        self.assertIn("camilocoelhogomes/source-code", lower)
        self.assertIn(".env.example", lower)
        self.assertTrue(
            "e2e/readme.md" in lower or "e2e/README.md" in text,
            "checklist deve referenciar e2e/README.md",
        )


# ---------------------------------------------------------------------------
# HITL-03 — passo PAT
# ---------------------------------------------------------------------------


class TestHITL03PatStep(unittest.TestCase):
    """HITL-03 — operador gera PAT; sem valor secreto documentado."""

    def test_pat_operator_step_present(self) -> None:
        text = _read_checklist()
        lower = text.lower()
        self.assertTrue(
            "pat" in lower or "personal access token" in lower,
            "checklist deve instruir geração de PAT pelo operador",
        )
        self.assertTrue(
            "operador" in lower or "humano" in lower or "human" in lower,
            "checklist deve indicar que o operador humano gera o PAT",
        )
        self.assertIn("camilocoelhogomes/source-code", lower)
        self.assertIsNone(
            TOKEN_PREFIX_RE.search(text),
            "passo PAT não deve embutir valor de token",
        )


# ---------------------------------------------------------------------------
# HITL-04 — passo .env
# ---------------------------------------------------------------------------


class TestHITL04EnvStep(unittest.TestCase):
    """HITL-04 — cp .env.example .env; GITHUB_TOKEN e/ou E2E_GITHUB_TOKEN."""

    def test_env_copy_and_token_vars_documented(self) -> None:
        text = _read_checklist()
        lower = text.lower()
        self.assertTrue(
            "cp .env.example .env" in lower
            or "cp .env.example .env" in text,
            "checklist deve incluir cp .env.example .env",
        )
        self.assertIn("GITHUB_TOKEN", text)
        self.assertIn("E2E_GITHUB_TOKEN", text)
        self.assertIn("camilocoelhogomes/source-code", lower)


# ---------------------------------------------------------------------------
# HITL-05 — proibições
# ---------------------------------------------------------------------------


class TestHITL05Prohibitions(unittest.TestCase):
    """HITL-05 — nunca git add .env; nunca colar token em artefatos."""

    def test_secret_and_commit_prohibitions(self) -> None:
        text = _read_checklist()
        lower = text.lower()
        self.assertTrue(
            "git add .env" in lower
            or ("commit" in lower and ".env" in lower),
            "checklist deve proibir git add/commit de .env",
        )
        self.assertTrue(
            "nunca" in lower or "proib" in lower or "não" in lower or "nao" in lower,
            "checklist deve declarar proibições explícitas",
        )
        self.assertTrue(
            "token" in lower and ("spec/" in lower or "commit" in lower),
            "checklist deve proibir colar/versionar token em spec/commits",
        )


# ---------------------------------------------------------------------------
# HITL-06 — comandos de verificação
# ---------------------------------------------------------------------------


class TestHITL06VerificationCommands(unittest.TestCase):
    """HITL-06 — test -f, check-ignore, ls-files, presença bool, podman."""

    def test_operator_verification_commands_present(self) -> None:
        text = _read_checklist()
        lower = text.lower()
        self.assertTrue(
            "test -f .env" in lower or "test -f .env" in text,
            "checklist deve incluir test -f .env",
        )
        self.assertIn("git check-ignore", lower)
        self.assertIn("git ls-files", lower)
        self.assertTrue(
            "github_token" in lower and "e2e_github_token" in lower,
            "verificação de presença deve citar ambas as vars de token",
        )
        self.assertTrue(
            "present" in lower or "não vazio" in lower or "nao vazio" in lower,
            "verificação de token deve ser booleana (presente/não vazio)",
        )
        self.assertNotIn("cat .env", lower)
        self.assertNotIn("echo $github_token", lower)
        self.assertNotIn("echo $e2e_github_token", lower)
        self.assertTrue(
            "podman info" in lower or "command -v podman" in lower,
            "checklist deve verificar Podman (command -v / podman info)",
        )


# ---------------------------------------------------------------------------
# HITL-07 — gate T04
# ---------------------------------------------------------------------------


class TestHITL07GateT04Table(unittest.TestCase):
    """HITL-07 — tabela READY/BLOCKED com checks booleanos."""

    def test_gate_table_has_required_checks_and_statuses(self) -> None:
        text = _read_checklist()
        lower = text.lower()
        self.assertTrue(
            "ready" in lower and "blocked" in lower,
            "gate T04 deve admitir READY e BLOCKED",
        )
        self.assertTrue(
            "t04" in lower or "gate" in lower,
            "checklist deve declarar gate T04",
        )
        for tokens in GATE_CHECKS:
            self.assertTrue(
                any(t in lower for t in tokens),
                f"tabela de gate deve cobrir check relacionado a {tokens!r}",
            )
        self.assertTrue(
            "pass" in lower and "fail" in lower,
            "checks do gate devem usar PASS/FAIL (ou equivalente)",
        )
        self.assertTrue(
            "present=true" in lower
            or "present=false" in lower
            or ("present" in lower and ("true" in lower or "false" in lower))
            or ("token presente" in lower),
            "evidência de token deve ser booleana, nunca o valor",
        )


# ---------------------------------------------------------------------------
# HITL-08 — sem padrões de token no checklist
# ---------------------------------------------------------------------------


class TestHITL08NoSecretsInChecklist(unittest.TestCase):
    """HITL-08 — checklist sem ghp_/gho_/… nem assigns longos."""

    def test_checklist_has_no_token_patterns(self) -> None:
        text = _read_checklist()
        self.assertIsNone(
            TOKEN_PREFIX_RE.search(text),
            "checklist não deve conter padrões de token GitHub (ghp_/gho_/…)",
        )
        self.assertIsNone(
            TOKEN_ASSIGN_RE.search(text),
            "checklist não deve atribuir valor longo a GITHUB_TOKEN/E2E_GITHUB_TOKEN",
        )


# ---------------------------------------------------------------------------
# HITL-09 — .gitignore
# ---------------------------------------------------------------------------


class TestHITL09GitignoreCoversEnv(unittest.TestCase):
    """HITL-09 — .gitignore contém .env (BR-004)."""

    def test_gitignore_contains_env(self) -> None:
        text = _read(GITIGNORE)
        self.assertIn(".env", text)


# ---------------------------------------------------------------------------
# HITL-10 — .env.example
# ---------------------------------------------------------------------------


class TestHITL10EnvExampleTokenPlaceholder(unittest.TestCase):
    """HITL-10 — .env.example tem E2E_GITHUB_TOKEN= sem secret."""

    def test_env_example_has_empty_e2e_github_token(self) -> None:
        text = _read(ENV_EXAMPLE)
        self.assertRegex(
            text,
            r"(?m)^E2E_GITHUB_TOKEN=\s*$",
            ".env.example deve declarar E2E_GITHUB_TOKEN= (vazio)",
        )
        self.assertIsNone(
            TOKEN_PREFIX_RE.search(text),
            ".env.example não deve embutir token real",
        )


if __name__ == "__main__":
    unittest.main()
