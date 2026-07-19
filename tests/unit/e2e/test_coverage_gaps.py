"""Unit — cobertura residual launcher/suite/errors (T21)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.unit.e2e.helpers import (
    REPO_ROOT,
    SECRET_TOKEN,
    RecordingLauncher,
    hitl_env_with_token,
    import_e2e,
)


class TestLauncherCoverage(unittest.TestCase):
    def test_default_run_command_invokes_subprocess(self) -> None:
        from github_rag.e2e import launcher as launcher_mod  # noqa: PLC0415

        completed = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(
            launcher_mod.subprocess, "run", return_value=completed
        ) as run:
            code, out, err = launcher_mod._default_run_command(
                ["podman", "version"], {"A": "1"}
            )
        self.assertEqual(code, 0)
        self.assertEqual(out, "ok")
        self.assertEqual(err, "")
        run.assert_called_once()

    def test_ensure_local_git_fixture_creates_repo(self) -> None:
        from github_rag.e2e.launcher import ensure_local_git_fixture  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            repos = Path(tmp) / "repos"
            ensure_local_git_fixture(repos)
            sample = repos / "sample-local"
            self.assertTrue((sample / ".git").is_dir())
            self.assertTrue((sample / "README.md").is_file())
            # second call is idempotent
            ensure_local_git_fixture(repos)

    def test_ensure_local_git_fixture_failure(self) -> None:
        from github_rag.e2e import launcher as launcher_mod  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            repos = Path(tmp) / "repos"
            failing = mock.Mock(
                returncode=1, stdout="", stderr="git boom"
            )
            with mock.patch.object(
                launcher_mod.subprocess, "run", return_value=failing
            ):
                with self.assertRaises(launcher_mod.E2eStackError):
                    launcher_mod.ensure_local_git_fixture(repos)

    def test_ensure_local_git_fixture_seeds_bdd006_paths(self) -> None:
        """UT-T24-S01 — seed include/exclude BDD-006 na 1ª chamada."""
        from github_rag.e2e.launcher import ensure_local_git_fixture  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            repos = Path(tmp) / "repos"
            ensure_local_git_fixture(repos)
            sample = repos / "sample-local"
            self.assertTrue((sample / ".git").is_dir())
            self.assertTrue((sample / "README.md").is_file())
            self.assertTrue(
                (sample / "src" / "Hello.java").is_file()
                or (sample / "src" / "app.py").is_file(),
                "seed BDD-006: include code ausente",
            )
            self.assertTrue(
                (sample / "docs" / "notes.md").is_file(),
                "seed BDD-006: docs/notes.md ausente",
            )
            self.assertTrue(
                (sample / "data" / "report.csv").is_file(),
                "seed BDD-006: data/report.csv ausente",
            )
            self.assertTrue(
                (sample / "img" / "photo.png").is_file(),
                "seed BDD-006: img/photo.png ausente",
            )
            self.assertTrue((sample / ".gitignore").is_file())
            self.assertTrue(
                (sample / "ignored_dir" / "secret_marker.txt").is_file(),
                "seed BDD-006: ignored_dir/secret_marker.txt ausente",
            )
            gi = (sample / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("ignored_dir", gi)
            # I-T24-009 — tokens canônicos nos paths seed (não só arquivos vazios)
            blob = "\n".join(
                p.read_text(encoding="utf-8", errors="replace")
                for p in sample.rglob("*")
                if p.is_file() and ".git" not in p.parts
            )
            self.assertIn("T24_INCLUDE_MD_E5F6", blob)
            self.assertIn("T24_EXCLUDE_CSV_G7H8", blob)
            self.assertIn("T24_EXCLUDE_GITIGNORE_I9J0", blob)
            self.assertTrue(
                "T24_INCLUDE_JAVA_A1B2" in blob or "T24_INCLUDE_PY_C3D4" in blob,
                "seed BDD-006: token include Java/Python ausente",
            )

    def test_ensure_local_git_fixture_seed_idempotent_with_existing_git(
        self,
    ) -> None:
        """UT-T24-S02 — com .git existente, ainda aplica seed T24 (não early-return cego)."""
        from github_rag.e2e.launcher import ensure_local_git_fixture  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            repos = Path(tmp) / "repos"
            # 1ª chamada cria .git (legado T21); seed T24 pode ainda faltar
            ensure_local_git_fixture(repos)
            sample = repos / "sample-local"
            self.assertTrue((sample / ".git").is_dir())
            # 2ª chamada deve materializar/manter paths BDD-006
            ensure_local_git_fixture(repos)
            self.assertTrue(
                (sample / "docs" / "notes.md").is_file(),
                "rerun com .git não pode pular seed BDD-006",
            )
            self.assertTrue((sample / "data" / "report.csv").is_file())
            self.assertTrue((sample / ".gitignore").is_file())
            # marker MAIN_ONLY na main (seed base BDD-017)
            main_only = (sample).rglob("*")
            blob = "\n".join(
                p.read_text(encoding="utf-8", errors="replace")
                for p in main_only
                if p.is_file() and ".git" not in p.parts
            )
            self.assertIn(
                "MAIN_ONLY_MARKER",
                blob,
                "seed base deve incluir MAIN_ONLY_MARKER na main",
            )

    def test_health_ok_invalid_json(self) -> None:
        e2e = import_e2e()
        launcher = e2e.PodmanE2eStackLauncher(
            repo_root=REPO_ROOT, run_command=lambda *_a: (0, "", "")
        )
        self.assertFalse(launcher._health_ok(b"not-json"))
        self.assertFalse(launcher._health_ok(b'{"status":"nope"}'))

    def test_down_swallows_oserror(self) -> None:
        e2e = import_e2e()

        def boom(_cmd, _env):
            raise OSError("podman missing")

        launcher = e2e.PodmanE2eStackLauncher(
            repo_root=REPO_ROOT, run_command=boom
        )
        launcher.down()  # must not raise

    def test_launcher_default_repo_root(self) -> None:
        e2e = import_e2e()
        launcher = e2e.PodmanE2eStackLauncher(
            run_command=lambda *_a: (0, "", "")
        )
        self.assertTrue(str(launcher.compose_file).endswith("docker-compose.dev.yml"))


class TestSuiteCoverage(unittest.TestCase):
    def test_default_robot_runner_subprocess(self) -> None:
        from github_rag.e2e import suite as suite_mod  # noqa: PLC0415

        runner = suite_mod._default_robot_runner(
            robot_root=REPO_ROOT / "e2e" / "robot",
            output_dir=REPO_ROOT / "e2e" / "results",
        )
        completed = mock.Mock(returncode=0)
        with mock.patch.object(
            suite_mod.subprocess, "run", return_value=completed
        ) as run:
            code = runner(
                "health",
                "catalog_indexing",
                exclude="bdd015",
                suites=["health", "catalog_indexing"],
                outputdir=str(REPO_ROOT / "e2e" / "results"),
            )
        self.assertEqual(code, 0)
        cmd = run.call_args.args[0]
        self.assertTrue(str(cmd[0]).endswith("robot"))
        self.assertIn("--exclude", cmd)
        self.assertIn("bdd015", cmd)
        # Suite markers as bare args must NOT be appended (Robot would treat
        # them as missing suite paths and fail the real e2e proof).
        self.assertNotIn("health", cmd)
        self.assertNotIn("catalog_indexing", cmd)
        self.assertTrue(any(str(p).endswith("health.robot") for p in cmd))
        self.assertTrue(
            any(str(p).endswith("catalog_indexing.robot") for p in cmd)
        )

    def test_suite_uses_os_environ_when_none(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        with mock.patch.dict(
            "os.environ",
            {"GITHUB_ACTIONS": "false", "E2E_GITHUB_TOKEN": SECRET_TOKEN},
            clear=False,
        ):
            suite = e2e.DefaultRobotMvpSuite(
                launcher=launcher,
                robot_runner=lambda *a, **k: 0,
                environ=None,
                repo_root=REPO_ROOT,
            )
            self.assertEqual(suite.run(), 0)

    def test_suite_fallback_config_fixture(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher(inject_host_env=False)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # no fixtures under root → fallback to package fixtures
            suite = e2e.DefaultRobotMvpSuite(
                launcher=launcher,
                robot_runner=lambda *a, **k: 0,
                environ=hitl_env_with_token(),
                repo_root=root,
            )
            code = suite.run()
        self.assertEqual(code, 0)
        self.assertEqual(len(launcher.up_calls), 1)

    def test_stack_error_from_stderr_truncates(self) -> None:
        e2e = import_e2e()
        raw = "x" * 3000
        err = e2e.E2eStackError.from_stderr(raw)
        self.assertLessEqual(len(str(err)), 2010)


if __name__ == "__main__":
    unittest.main()
