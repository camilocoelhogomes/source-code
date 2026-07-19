"""Unit — paths canônicos e timeouts (T21 / UT-P*)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.unit.e2e.helpers import REPO_ROOT, import_e2e


class TestE2ePaths(unittest.TestCase):
    """UT-P01..P04 / UT-P06."""

    def test_ut_p01_compose_e2e_name(self) -> None:
        e2e = import_e2e()
        from github_rag.e2e import paths as e2e_paths  # noqa: PLC0415

        self.assertEqual(e2e_paths.COMPOSE_E2E_NAME, "docker-compose.e2e.yml")
        self.assertTrue(str(e2e.COMPOSE_E2E).endswith("docker-compose.e2e.yml"))

    def test_ut_p02_canonical_fixture_and_robot_paths(self) -> None:
        e2e = import_e2e()
        self.assertIn("e2e/robot", str(e2e.ROBOT_ROOT).replace("\\", "/"))
        self.assertTrue(
            str(e2e.E2E_CONFIG_FIXTURE).endswith("e2e/fixtures/config.e2e.json")
            or Path(e2e.E2E_CONFIG_FIXTURE).name == "config.e2e.json"
        )
        self.assertTrue(
            str(e2e.E2E_REPOS_FIXTURE).endswith("e2e/fixtures/repos")
            or Path(e2e.E2E_REPOS_FIXTURE).name == "repos"
        )

    def test_ut_p03_resolve_repo_root_finds_real_repo(self) -> None:
        from github_rag.e2e.paths import resolve_repo_root  # noqa: PLC0415

        root = resolve_repo_root(start=REPO_ROOT / "tests" / "unit" / "e2e")
        self.assertTrue((root / "docker-compose.e2e.yml").is_file())
        self.assertTrue((root / "pyproject.toml").is_file())

    def test_ut_p04_resolve_repo_root_without_anchor_fails(self) -> None:
        from github_rag.e2e.paths import resolve_repo_root  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            orphan = Path(tmp) / "orphan"
            orphan.mkdir()
            with self.assertRaises((OSError, ValueError, FileNotFoundError, RuntimeError)):
                resolve_repo_root(start=orphan)

    def test_ut_p06_results_dirname(self) -> None:
        from github_rag.e2e import paths as e2e_paths  # noqa: PLC0415

        self.assertEqual(e2e_paths.E2E_RESULTS_DIRNAME, "e2e/results")


class TestE2eTimeouts(unittest.TestCase):
    """UT-P05 — defaults design §3.7."""

    def test_ut_p05_timeout_defaults(self) -> None:
        e2e = import_e2e()
        t = e2e.timeouts
        self.assertEqual(t.COMPOSE_UP_HEALTHY_TIMEOUT_SECONDS, 600.0)
        self.assertEqual(t.INDEXING_TIMEOUT_SECONDS, 900.0)
        self.assertEqual(t.INDEXING_POLL_INTERVAL_SECONDS, 5.0)
        self.assertEqual(t.SEARCH_TIMEOUT_SECONDS, 60.0)
        self.assertEqual(t.SEARCH_HTTP_429_MAX_RETRIES, 3)
        self.assertEqual(t.GITHUB_RATE_LIMIT_MAX_RETRIES, 3)
        self.assertEqual(t.GITHUB_RATE_LIMIT_WAIT_MIN_SECONDS, 30.0)
        self.assertEqual(t.GITHUB_RATE_LIMIT_WAIT_MAX_SECONDS, 60.0)


if __name__ == "__main__":
    unittest.main()
