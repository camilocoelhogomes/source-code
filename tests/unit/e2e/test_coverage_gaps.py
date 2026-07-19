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
        self.assertTrue(str(launcher.compose_file).endswith("docker-compose.e2e.yml"))


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
                exclude="bdd015",
                suites=["health"],
                outputdir=str(REPO_ROOT / "e2e" / "results"),
            )
        self.assertEqual(code, 0)
        cmd = run.call_args.args[0]
        self.assertIn("robot", cmd)
        self.assertIn("--exclude", cmd)
        self.assertIn("bdd015", cmd)

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
