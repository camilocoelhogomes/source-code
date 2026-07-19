"""Unit — manifesto Dockerfile/compose/pyproject (T19 / UT-M*)."""

from __future__ import annotations

import re
import tomllib
import unittest

from tests.unit.delivery.helpers import (
    COMPOSE,
    COMPOSE_DEV,
    COMPOSE_E2E,
    COMPOSE_FILES,
    DEC015_RUNTIME_PACKAGES,
    DEC015_TREE_SITTER_GRAMMARS,
    DOCKERFILE,
    ENV_EXAMPLE,
    PYPROJECT,
    read_text,
)

_VENV_MOUNT_RE = re.compile(
    r"(COPY|ADD)\s+[^\n]*\.venv"
    r"|-\s*\./\.venv"
    r"|/\.venv:"
    r"|:\s*\.venv\b",
    re.I,
)


def _dep_name(spec: str) -> str:
    return re.split(r"[<>=!~;\[]", spec, maxsplit=1)[0].strip()


class TestDockerfileManifest(unittest.TestCase):
    """UT-M01 / UT-M02."""

    def test_ut_m01_pip_install_no_dev_no_venv(self) -> None:
        text = read_text(DOCKERFILE)
        self.assertRegex(
            text,
            re.compile(r"pip\s+install\b.{0,80}\.", re.I | re.S),
        )
        self.assertNotRegex(
            text,
            re.compile(r"pip\s+install\b.{0,40}\[dev\]", re.I),
        )
        self.assertNotRegex(
            text,
            re.compile(
                r"(COPY|ADD)\s+[^\n]*\.venv"
                r"|-\s*\./\.venv"
                r"|/\.venv:"
                r"|:\s*\.venv\b",
                re.I,
            ),
        )

    def test_ut_m02_git_and_delivery_cmd(self) -> None:
        text = read_text(DOCKERFILE)
        self.assertRegex(text, re.compile(r"\bgit\b", re.I))
        self.assertRegex(
            text,
            re.compile(r"python\s+-m\s+github_rag\.delivery", re.I),
        )


class TestComposeManifest(unittest.TestCase):
    """UT-M03 / UT-M04 — contratos compose."""

    _INFRA = ("postgres", "qdrant", "zoekt", "slm")

    def test_ut_m03_infra_services_all_composes(self) -> None:
        for path in COMPOSE_FILES:
            text = read_text(path)
            for svc in self._INFRA:
                self.assertRegex(
                    text,
                    re.compile(rf"^\s*{svc}\s*:", re.M),
                    f"{path.name}: serviço ausente: {svc}",
                )

    def test_ut_m03_user_compose_app_and_surface_ports(self) -> None:
        text = read_text(COMPOSE)
        self.assertRegex(text, re.compile(r"^\s*app\s*:", re.M))
        self.assertRegex(text, re.compile(r"8080", re.I))
        self.assertRegex(text, re.compile(r"8001|MCP_PORT", re.I))

    def test_ut_m04_user_compose_volumes_and_healthz(self) -> None:
        text = read_text(COMPOSE)
        self.assertRegex(text, re.compile(r"CONFIG_PATH", re.I))
        self.assertRegex(text, re.compile(r"/repos"))
        self.assertRegex(text, re.compile(r"healthcheck\s*:", re.I))
        self.assertRegex(text, re.compile(r"/healthz", re.I))
        self.assertNotRegex(text, _VENV_MOUNT_RE)


class TestThreeComposeRoles(unittest.TestCase):
    """UT-M07 / UT-M08 / UT-M09 — papéis D-T19-020 (BDD-025)."""

    def test_ut_m07_e2e_isolation_infra_only(self) -> None:
        text = read_text(COMPOSE_E2E)
        self.assertRegex(
            text,
            re.compile(r"^\s*name\s*:\s*github-rag-e2e\s*$", re.M),
        )
        self.assertRegex(text, re.compile(r"e2e_", re.I))
        self.assertNotRegex(text, re.compile(r"^\s*app\s*:", re.M))
        self.assertNotRegex(text, re.compile(r"-\s*\./src\b|:\s*\./src\b"))

    def test_ut_m08_dev_infra_only_exposes_postgres(self) -> None:
        text = read_text(COMPOSE_DEV)
        self.assertRegex(
            text,
            re.compile(r"^\s*name\s*:\s*github-rag-dev\s*$", re.M),
        )
        self.assertNotRegex(text, re.compile(r"^\s*app\s*:", re.M))
        self.assertRegex(text, re.compile(r"5432:5432"))
        self.assertNotRegex(text, _VENV_MOUNT_RE)

    def test_ut_m09_user_compose_no_src_mount(self) -> None:
        text = read_text(COMPOSE)
        self.assertNotRegex(text, re.compile(r"-\s*\./src\b|:\s*\./src\b"))


class TestPyprojectAndEnvExample(unittest.TestCase):
    """UT-M05 / UT-M06."""

    def test_ut_m05_pyproject_dec015_uvicorn_grammars(self) -> None:
        data = tomllib.loads(read_text(PYPROJECT))
        deps = data.get("project", {}).get("dependencies", [])
        self.assertIsInstance(deps, list)
        names = {_dep_name(str(d)) for d in deps}
        missing = [p for p in DEC015_RUNTIME_PACKAGES if p not in names]
        self.assertEqual(missing, [], f"deps ausentes: {missing}")
        missing_g = [g for g in DEC015_TREE_SITTER_GRAMMARS if g not in names]
        self.assertEqual(missing_g, [], f"grammars ausentes: {missing_g}")

    def test_ut_m06_env_example_canonical_names_no_secrets(self) -> None:
        text = read_text(ENV_EXAMPLE)
        for name in (
            "CONFIG_PATH",
            "GITHUB_TOKEN",
            "E2E_GITHUB_TOKEN",
            "INDEX_WORKERS",
            "QUERY_WORKERS",
            "INDEX_CRON",
            "DATABASE_URL",
            "ZOEKT_URL",
            "QDRANT_URL",
            "OPENAI_BASE_URL",
            "UI_PORT",
            "MCP_PORT",
            "MCP_TRANSPORT",
        ):
            self.assertIn(name, text, msg=name)
        self.assertNotIn("ghp_", text)
        self.assertNotRegex(
            text,
            re.compile(r"GITHUB_TOKEN\s*=\s*\S{8,}"),
        )


if __name__ == "__main__":
    unittest.main()
