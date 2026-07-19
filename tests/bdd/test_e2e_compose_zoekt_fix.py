"""
BDD executável — T22-fix-tooling-e2e-compose-zoekt.

Valida F-T04-001/002/003 via manifesto compose + docs (padrão T19).
Sem compose up real e sem expandir suíte Robot.

Cenários: EZ-01..EZ-05 — ver
    spec/features/github-etl-mcp-rag/tasks/T22-fix-tooling-e2e-compose-zoekt/bdd.md

Execução:
    python -m pytest tests/bdd/test_e2e_compose_zoekt_fix.py -q
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE = REPO_ROOT / "docker-compose.yml"
COMPOSE_E2E = REPO_ROOT / "docker-compose.e2e.yml"
COMPOSE_DEV = REPO_ROOT / "docker-compose.dev.yml"
COMPOSE_FILES = (COMPOSE, COMPOSE_E2E, COMPOSE_DEV)
E2E_README = REPO_ROOT / "e2e" / "README.md"
RUNBOOK = REPO_ROOT / "docs" / "runbook-local.md"

# Argv mínimo do filho do tini (D-T22-001 / design §3.1).
ZOEKT_COMMAND_TOKENS = (
    "zoekt-webserver",
    "-index",
    "/data/index",
    "-rpc",
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"artefato ausente: {path}")
    return path.read_text(encoding="utf-8")


def _service_block(compose_text: str, service: str) -> str:
    """Extrai o bloco YAML do serviço (indentação de 2 espaços sob `services:`)."""
    pattern = re.compile(
        rf"^  {re.escape(service)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:|\Z)",
        re.M | re.S,
    )
    match = pattern.search(compose_text)
    if match is None:
        raise AssertionError(f"serviço compose ausente: {service}")
    return match.group(0)


def _zoekt_command_blob(compose_text: str) -> str:
    """Retorna o texto do `command` do serviço zoekt (scalar ou lista)."""
    block = _service_block(compose_text, "zoekt")
    # Forma lista JSON-like: command: ["zoekt-webserver", ...]
    list_match = re.search(
        r"^\s*command\s*:\s*\[(.*?)\]\s*$",
        block,
        re.M | re.S,
    )
    if list_match is not None:
        return list_match.group(0)
    # Forma bloco YAML ou scalar
    scalar_match = re.search(
        r"^\s*command\s*:\s*(.+)$",
        block,
        re.M,
    )
    if scalar_match is not None:
        return scalar_match.group(0)
    raise AssertionError(
        "serviço zoekt sem `command` — ENTRYPOINT tini sem filho "
        "(F-T04-002: tini help → exit 1)"
    )


def _assert_zoekt_webserver_command(compose_text: str, *, compose_name: str) -> str:
    command_blob = _zoekt_command_blob(compose_text)
    for token in ZOEKT_COMMAND_TOKENS:
        if token not in command_blob:
            raise AssertionError(
                f"{compose_name}: command zoekt deve conter {token!r} "
                f"(got: {command_blob!r})"
            )
    block = _service_block(compose_text, "zoekt")
    if "/data/index" not in block:
        raise AssertionError(
            f"{compose_name}: serviço zoekt deve montar/usar /data/index"
        )
    return command_blob


def _assert_compose_provider_prereq_docs(text: str, *, doc_name: str) -> None:
    """Pré-req F-T04-001: binário provider + verificação PATH + instalação.

    Não aceita menção a arquivo `docker-compose*.yml` como substituto do
    binário `podman-compose` / provider no PATH.
    """
    if not re.search(r"\bpodman-compose\b", text, re.I):
        raise AssertionError(
            f"{doc_name}: deve citar o binário `podman-compose` como pré-req "
            "(não apenas `podman compose` / nome de arquivo compose)"
        )
    if not re.search(
        r"command\s+-v\s+podman-compose"
        r"|podman\s+compose\s+version"
        r"|provider.*\bPATH\b|\bPATH\b.*(?:compose|provider)",
        text,
        re.I,
    ):
        raise AssertionError(
            f"{doc_name}: deve documentar verificação do provider no PATH"
        )
    if not re.search(
        r"brew\s+install\s+podman-compose"
        r"|install(?:ar)?\s+podman-compose",
        text,
        re.I,
    ):
        raise AssertionError(
            f"{doc_name}: deve orientar instalação tipica do provider "
            "(ex.: brew install podman-compose)"
        )


class TestEZ01ComposeProviderDocs(unittest.TestCase):
    """EZ-01 / F-T04-001 — pré-req provider Compose documentado."""

    def test_e2e_readme_documents_compose_provider_prereq(self) -> None:
        _assert_compose_provider_prereq_docs(
            _read(E2E_README), doc_name="e2e/README.md"
        )

    def test_runbook_documents_compose_provider_prereq(self) -> None:
        _assert_compose_provider_prereq_docs(
            _read(RUNBOOK), doc_name="docs/runbook-local.md"
        )


class TestEZ02ZoektCommandManifest(unittest.TestCase):
    """EZ-02 / F-T04-002 — command zoekt-webserver nos três composes."""

    def test_zoekt_command_present_in_all_composes(self) -> None:
        for path in COMPOSE_FILES:
            with self.subTest(compose=path.name):
                text = _read(path)
                _assert_zoekt_webserver_command(text, compose_name=path.name)


class TestEZ03ZoektCommandParity(unittest.TestCase):
    """EZ-03 / D-T22-002 — paridade do argv zoekt entre os três composes."""

    def test_zoekt_command_tokens_aligned_across_composes(self) -> None:
        blobs: dict[str, str] = {}
        for path in COMPOSE_FILES:
            blobs[path.name] = _assert_zoekt_webserver_command(
                _read(path), compose_name=path.name
            )
        # Todos devem conter o mesmo conjunto de tokens canônicos.
        for name, blob in blobs.items():
            for token in ZOEKT_COMMAND_TOKENS:
                self.assertIn(
                    token,
                    blob,
                    msg=f"{name}: token canônico ausente no command zoekt",
                )


class TestEZ04RuntimeAcceptanceDocumented(unittest.TestCase):
    """EZ-04 / F-T04-003 — aceite runtime rastreável; gate = pré-condições manifesto/docs.

    Runtime real (`python -m github_rag.e2e`) é prova operacional pós-fix,
    não executada nesta camada (D-T22-006).
    """

    def test_preconditions_for_runtime_acceptance(self) -> None:
        # Pré-condições de tooling que desbloqueiam compose → healthy → robot.
        for path in COMPOSE_FILES:
            _assert_zoekt_webserver_command(_read(path), compose_name=path.name)
        for doc in (E2E_README, RUNBOOK):
            _assert_compose_provider_prereq_docs(
                _read(doc), doc_name=str(doc.relative_to(REPO_ROOT))
            )
        # Aceite runtime documentado na superfície e2e (prova canônica T21).
        e2e_readme = _read(E2E_README)
        self.assertRegex(
            e2e_readme,
            re.compile(r"python\s+-m\s+github_rag\.e2e", re.I),
            "e2e/README.md deve apontar a prova canônica T21",
        )


class TestEZ05NoSecretsInToolingArtifacts(unittest.TestCase):
    """EZ-05 — sem secrets versionados nos artefatos desta task."""

    def test_composes_and_docs_have_no_embedded_pat(self) -> None:
        paths = (*COMPOSE_FILES, E2E_README, RUNBOOK)
        for path in paths:
            with self.subTest(path=path.name):
                text = _read(path)
                # Placeholder documental `ghp_...` é ok; PAT real não.
                self.assertNotRegex(
                    text,
                    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
                    f"{path.name}: não deve embutir PAT real",
                )
                self.assertNotRegex(
                    text,
                    re.compile(
                        r"(GITHUB_TOKEN|E2E_GITHUB_TOKEN)\s*=\s*"
                        r"(?!ghp_\.\.\.)(?!\.\.\.)(?!\$\{)(?!\S*:-)\S{8,}",
                    ),
                    f"{path.name}: não deve embutir valor de token",
                )


if __name__ == "__main__":
    unittest.main()
