"""Unit — host delivery env (dev/e2e app no host)."""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.unit.e2e.helpers import REPO_ROOT


class TestHostDeliveryEnv(unittest.TestCase):
    def test_build_host_delivery_env_uses_localhost(self) -> None:
        from github_rag.e2e.host_env import build_host_delivery_env

        cfg = REPO_ROOT / "e2e/fixtures/config.e2e.json"
        repos = REPO_ROOT / "e2e/fixtures/repos"
        zoekt = REPO_ROOT / ".data/test-zoekt-index"
        env = build_host_delivery_env(
            repo_root=REPO_ROOT,
            config_path=cfg,
            repos_dir=repos,
            zoekt_index_dir=zoekt,
        )
        self.assertEqual(env["CONFIG_PATH"], str(cfg.resolve()))
        self.assertIn("127.0.0.1:5432", env["DATABASE_URL"])
        self.assertEqual(env["ZOEKT_URL"], "http://127.0.0.1:6070")
        self.assertEqual(env["QDRANT_URL"], "http://127.0.0.1:6333")
        self.assertTrue(zoekt.is_dir())


if __name__ == "__main__":
    unittest.main()
