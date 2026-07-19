"""Unit — PodmanE2eStackLauncher (T21 / UT-L*)."""

from __future__ import annotations

import unittest
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from unittest import mock

from tests.unit.e2e.helpers import REPO_ROOT, SECRET_TOKEN, import_e2e


class RecordingCommand:
    """Double de subprocess Podman compose."""

    def __init__(
        self,
        *,
        exit_code: int = 0,
        stderr: str = "",
        stdout: str = "",
    ) -> None:
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        self.calls: list[tuple[Sequence[str], Mapping[str, str]]] = []

    def __call__(
        self,
        cmd: Sequence[str],
        env: Mapping[str, str],
    ) -> tuple[int, str, str]:
        self.calls.append((list(cmd), dict(env)))
        return self.exit_code, self.stdout, self.stderr


class TestPodmanE2eStackLauncher(unittest.TestCase):
    """UT-L01..L10."""

    def _make_launcher(
        self,
        *,
        run_command: RecordingCommand | None = None,
        **kwargs: Any,
    ) -> Any:
        e2e = import_e2e()
        runner = run_command or RecordingCommand()
        return e2e.PodmanE2eStackLauncher(
            repo_root=REPO_ROOT,
            run_command=runner,
            host_app=False,
            **kwargs,
        ), runner, e2e

    def test_ut_l01_up_invokes_podman_compose_without_build(self) -> None:
        launcher, runner, _e2e = self._make_launcher()
        launcher.up(env={"E2E_GITHUB_TOKEN": SECRET_TOKEN})
        self.assertEqual(len(runner.calls), 1)
        cmd = [str(x) for x in runner.calls[0][0]]
        blob = " ".join(cmd).lower()
        self.assertIn("podman", blob)
        self.assertIn("compose", blob)
        self.assertTrue(
            any(str(c).endswith("docker-compose.dev.yml") for c in cmd)
            or "docker-compose.dev.yml" in blob,
            cmd,
        )
        self.assertIn("up", cmd)
        self.assertIn("-d", cmd)
        self.assertNotIn("--build", cmd)

    def test_ut_l02_up_injects_host_config_and_repos(self) -> None:
        launcher, runner, _e2e = self._make_launcher()
        launcher.up(env={})
        env = runner.calls[0][1]
        host_config = env.get("HOST_CONFIG", "")
        host_repos = env.get("HOST_REPOS", "")
        self.assertTrue(
            host_config.endswith("e2e/fixtures/config.e2e.json")
            or Path(host_config).name == "config.e2e.json",
            host_config,
        )
        self.assertTrue(Path(host_config).is_absolute(), host_config)
        self.assertTrue(
            host_repos.endswith("e2e/fixtures/repos")
            or Path(host_repos).name == "repos",
            host_repos,
        )
        self.assertTrue(Path(host_repos).is_absolute(), host_repos)

    def test_ut_l03_up_preserves_caller_host_env(self) -> None:
        launcher, runner, _e2e = self._make_launcher()
        custom_cfg = "/tmp/custom-config.e2e.json"
        custom_repos = "/tmp/custom-repos"
        launcher.up(
            env={
                "HOST_CONFIG": custom_cfg,
                "HOST_REPOS": custom_repos,
            }
        )
        env = runner.calls[0][1]
        self.assertEqual(env["HOST_CONFIG"], custom_cfg)
        self.assertEqual(env["HOST_REPOS"], custom_repos)

    def test_ut_l04_up_nonzero_raises_stack_error_redacted(self) -> None:
        runner = RecordingCommand(
            exit_code=1,
            stderr=f"podman boom token={SECRET_TOKEN}",
        )
        launcher, _r, e2e = self._make_launcher(run_command=runner)
        with self.assertRaises(e2e.E2eStackError) as ctx:
            launcher.up(env={})
        self.assertNotIn(SECRET_TOKEN, str(ctx.exception))

    def test_ut_l05_wait_healthy_timeout_raises(self) -> None:
        """Timeout health → E2eStackError; sem Podman/compose real (HTTP mock)."""
        launcher_fast, _r2, e2e2 = self._make_launcher(
            healthy_timeout_seconds=0.05,
        )
        failing = mock.Mock(side_effect=OSError("health endpoint down"))
        with mock.patch("urllib.request.urlopen", failing):
            with mock.patch("httpx.get", failing):
                with self.assertRaises(e2e2.E2eStackError):
                    launcher_fast.wait_healthy(timeout_seconds=0.05)

    def test_ut_l06_wait_healthy_success(self) -> None:
        launcher, _runner, _e2e = self._make_launcher()
        ok_body = b'{"status":"ok","ui":"ready","mcp":"ready"}'

        class _Resp:
            status = 200

            def read(self) -> bytes:
                return ok_body

            def __enter__(self) -> _Resp:
                return self

            def __exit__(self, *_a: object) -> None:
                return None

        httpx_resp = mock.Mock()
        httpx_resp.status_code = 200
        httpx_resp.content = ok_body
        httpx_resp.json.return_value = {
            "status": "ok",
            "ui": "ready",
            "mcp": "ready",
        }
        # Cobrir urllib e httpx: implementação usa um dos dois (stdlib preferido).
        with mock.patch("urllib.request.urlopen", return_value=_Resp()):
            with mock.patch("httpx.get", return_value=httpx_resp):
                launcher.wait_healthy(timeout_seconds=1.0)

    def test_ut_l07_down_is_idempotent(self) -> None:
        launcher, runner, _e2e = self._make_launcher()
        launcher.down()
        launcher.down()  # 2ª chamada não deve crashar
        self.assertGreaterEqual(len(runner.calls), 1)

    def test_ut_l08_down_command_failure_is_best_effort(self) -> None:
        runner = RecordingCommand(
            exit_code=1,
            stderr=f"down failed {SECRET_TOKEN}",
        )
        launcher, _r, e2e = self._make_launcher(run_command=runner)
        try:
            launcher.down()
        except e2e.E2eStackError as exc:
            self.assertNotIn(SECRET_TOKEN, str(exc))
        # best-effort: engolir falha (sem raise) também é válido

    def test_ut_l09_protocol_isinstance(self) -> None:
        launcher, _runner, e2e = self._make_launcher()
        self.assertIsInstance(launcher, e2e.E2eStackLauncher)

    def test_ut_l10_default_compose_file(self) -> None:
        launcher, _runner, e2e = self._make_launcher()
        compose = getattr(launcher, "compose_file", None) or e2e.COMPOSE_DEV
        self.assertTrue(str(compose).endswith("docker-compose.dev.yml"))


if __name__ == "__main__":
    unittest.main()
