"""Unit — DefaultRobotMvpSuite orquestração (T21 / UT-S*)."""

from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from unittest import mock

from tests.unit.e2e.helpers import (
    GREEN_PATH_SUITE_MARKERS,
    REPO_ROOT,
    SECRET_TOKEN,
    RecordingLauncher,
    RecordingRobotRunner,
    hitl_env_with_token,
    import_e2e,
    robot_call_blob,
    suite_run,
)


class TestDefaultRobotMvpSuiteOrchestration(unittest.TestCase):
    """UT-S01..S15."""

    def test_ut_s01_green_path_order_and_exit_zero(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=0)
        code = suite_run(
            environ=hitl_env_with_token(),
            launcher=launcher,
            robot_runner=robot,
            e2e_pkg=e2e,
        )
        self.assertEqual(code, 0)
        self.assertEqual(launcher.order, ["up", "wait_healthy", "robot", "down"])

    def test_ut_s02_missing_credential_no_up(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        code = suite_run(
            environ={"GITHUB_ACTIONS": "false"},
            launcher=launcher,
            e2e_pkg=e2e,
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(launcher.up_calls, [])

    def test_ut_s03_ci_actions_token_only_no_up(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        code = suite_run(
            environ={
                "GITHUB_ACTIONS": "true",
                "GITHUB_TOKEN": SECRET_TOKEN,
            },
            launcher=launcher,
            e2e_pkg=e2e,
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(launcher.up_calls, [])

    def test_ut_s04_up_failure_skips_robot_and_calls_down(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher(up_error=e2e.E2eStackError("compose failed"))
        robot = RecordingRobotRunner(exit_code=0)
        code = suite_run(
            environ=hitl_env_with_token(),
            launcher=launcher,
            robot_runner=robot,
            e2e_pkg=e2e,
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(robot.calls, [])
        self.assertEqual(launcher.down_calls, 1)

    def test_ut_s05_health_failure_skips_robot_and_calls_down(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher(
            healthy_error=e2e.E2eStackError("healthz timeout"),
        )
        robot = RecordingRobotRunner(exit_code=0)
        code = suite_run(
            environ=hitl_env_with_token(),
            launcher=launcher,
            robot_runner=robot,
            e2e_pkg=e2e,
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(robot.calls, [])
        self.assertEqual(launcher.down_calls, 1)
        self.assertIn("up", launcher.order)
        self.assertIn("wait_healthy", launcher.order)

    def test_ut_s06_robot_nonzero_blocks_mvp_but_downs(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=1)
        code = suite_run(
            environ=hitl_env_with_token(),
            launcher=launcher,
            robot_runner=robot,
            e2e_pkg=e2e,
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(len(robot.calls), 1)
        self.assertEqual(launcher.down_calls, 1)

    def test_ut_s07_robot_excludes_bdd015_explicitly(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=0)
        code = suite_run(
            environ=hitl_env_with_token(),
            launcher=launcher,
            robot_runner=robot,
            e2e_pkg=e2e,
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(robot.calls), 1)
        blob = robot_call_blob(robot.calls[0]).lower()
        self.assertRegex(
            blob,
            r"(--exclude(\s+|=)bdd015|exclude[=:].*bdd015|\bexcludes?\b.*\bbdd015\b)",
            msg=f"exclude bdd015 não explícito: {robot.calls[0]!r}",
        )

    def test_ut_s08_green_path_suite_markers_present(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=0)
        suite_run(
            environ=hitl_env_with_token(),
            launcher=launcher,
            robot_runner=robot,
            e2e_pkg=e2e,
        )
        blob = robot_call_blob(robot.calls[0]).lower()
        for marker in GREEN_PATH_SUITE_MARKERS:
            self.assertIn(marker, blob, msg=marker)

    def test_ut_s09_token_never_in_robot_argv_kwargs(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=0)
        suite_run(
            environ=hitl_env_with_token(),
            launcher=launcher,
            robot_runner=robot,
            e2e_pkg=e2e,
        )
        for call in robot.calls:
            self.assertNotIn(SECRET_TOKEN, repr(call))
            for arg in call["args"]:
                self.assertNotIn(SECRET_TOKEN, str(arg))
            for val in call["kwargs"].values():
                self.assertNotIn(SECRET_TOKEN, str(val))

    def test_ut_s10_up_receives_host_config_and_repos(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher(inject_host_env=False)
        robot = RecordingRobotRunner(exit_code=0)
        # Suite deve passar HOST_* ao launcher.up
        code = suite_run(
            environ=hitl_env_with_token(),
            launcher=launcher,
            robot_runner=robot,
            e2e_pkg=e2e,
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(launcher.up_calls), 1)
        up_env = launcher.up_calls[0]
        host_config = up_env.get("HOST_CONFIG", "")
        host_repos = up_env.get("HOST_REPOS", "")
        self.assertTrue(
            host_config.endswith("e2e/fixtures/config.e2e.json")
            or Path(host_config) == REPO_ROOT / "e2e" / "fixtures" / "config.e2e.json",
            host_config,
        )
        self.assertTrue(
            host_repos.endswith("e2e/fixtures/repos")
            or Path(host_repos) == REPO_ROOT / "e2e" / "fixtures" / "repos",
            host_repos,
        )

    def test_ut_s11_protocol_isinstance(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        suite = e2e.DefaultRobotMvpSuite(
            launcher=launcher,
            robot_runner=RecordingRobotRunner(),
            environ=hitl_env_with_token(),
        )
        self.assertIsInstance(suite, e2e.RobotMvpSuite)

    def test_ut_s12_keyword_only_and_run_mvp_e2e(self) -> None:
        e2e = import_e2e()
        sig = inspect.signature(e2e.DefaultRobotMvpSuite.__init__)
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            self.assertNotEqual(
                param.kind,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                msg=f"{name} deve ser keyword-only",
            )
        launcher = RecordingLauncher()
        with self.assertRaises(TypeError):
            e2e.DefaultRobotMvpSuite(launcher)  # type: ignore[misc]
        # run_mvp_e2e não aceita robot_runner — mock no módulo suite (sem Robot real)
        self.assertTrue(callable(e2e.run_mvp_e2e))
        import github_rag.e2e.suite as suite_mod  # noqa: PLC0415

        with mock.patch.object(suite_mod, "DefaultRobotMvpSuite") as suite_cls:
            suite_cls.return_value.run.return_value = 0
            code = suite_mod.run_mvp_e2e(
                launcher=launcher,
                environ=hitl_env_with_token(),
            )
        self.assertEqual(code, 0)
        suite_cls.assert_called_once()
        kwargs = suite_cls.call_args.kwargs
        self.assertIs(kwargs.get("launcher"), launcher)

    def test_ut_s13_credential_error_mapped_to_nonzero_exit(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        # Não deve propagar E2eCredentialError ao caller estável
        try:
            code = suite_run(
                environ={"GITHUB_ACTIONS": "false"},
                launcher=launcher,
                e2e_pkg=e2e,
            )
        except e2e.E2eCredentialError:
            self.fail("suite.run deve capturar E2eCredentialError e retornar ≠0")
        self.assertNotEqual(code, 0)

    def test_ut_s14_down_after_robot_unexpected_exception(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(
            raise_on_call=RuntimeError("robot crashed"),
        )
        try:
            code = suite_run(
                environ=hitl_env_with_token(),
                launcher=launcher,
                robot_runner=robot,
                e2e_pkg=e2e,
            )
        except RuntimeError:
            code = 1
        self.assertNotEqual(code, 0)
        self.assertEqual(launcher.down_calls, 1)

    def test_ut_s15_two_green_runs_each_call_down(self) -> None:
        e2e = import_e2e()
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=0)
        for _ in range(2):
            code = suite_run(
                environ=hitl_env_with_token(),
                launcher=launcher,
                robot_runner=robot,
                e2e_pkg=e2e,
            )
            self.assertEqual(code, 0)
        self.assertEqual(launcher.down_calls, 2)


if __name__ == "__main__":
    unittest.main()
