"""Unit — PodmanE2eStackLauncher (T21 / UT-L*)."""

from __future__ import annotations

import io
import os
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
        host_app: bool = False,
        **kwargs: Any,
    ) -> Any:
        e2e = import_e2e()
        runner = run_command or RecordingCommand()
        return e2e.PodmanE2eStackLauncher(
            repo_root=REPO_ROOT,
            run_command=runner,
            host_app=host_app,
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
        clean = {k: v for k, v in os.environ.items() if k not in ("HOST_CONFIG", "HOST_REPOS")}
        with mock.patch.dict(os.environ, clean, clear=True):
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

    def test_t29_host_exit_before_poll(self) -> None:
        launcher, _r, e2e = self._make_launcher(host_app=True)
        proc = mock.Mock(poll=mock.Mock(return_value=1), stderr=io.StringIO(f"x {SECRET_TOKEN}"))
        launcher._app_process = proc
        with self.assertRaises(e2e.E2eStackError) as ctx:
            launcher.wait_healthy(timeout_seconds=0.05)
        self.assertIn("code=1", str(ctx.exception))
        self.assertNotIn(SECRET_TOKEN, str(ctx.exception))

    def test_t33_up_with_host_app_resolves_zoekt_bin(self) -> None:
        launcher, runner, _e2e = self._make_launcher(host_app=True)
        wrapper = REPO_ROOT / ".data/test-up-zoekt-bin/zoekt-index"
        proc = mock.Mock(poll=mock.Mock(return_value=None))
        with mock.patch("github_rag.e2e.launcher.ensure_local_git_fixture"):
            with mock.patch(
                "github_rag.e2e.launcher.resolve_zoekt_index_bin",
                return_value=wrapper,
            ):
                with mock.patch(
                    "github_rag.e2e.launcher.subprocess.Popen",
                    return_value=proc,
                ) as popen:
                    launcher.up(env={})
        self.assertEqual(len(runner.calls), 1)
        popen.assert_called_once()
        host_env = popen.call_args.kwargs["env"]
        self.assertEqual(host_env["ZOEKT_INDEX_BIN"], str(wrapper))

    def test_t35_e2e_compose_sets_defer_startup_index(self) -> None:
        e2e = import_e2e()
        launcher, runner, _e2e = self._make_launcher(
            host_app=True,
            compose_file=e2e.COMPOSE_E2E,
        )
        wrapper = REPO_ROOT / ".data/test-up-zoekt-bin/zoekt-index"
        proc = mock.Mock(poll=mock.Mock(return_value=None))
        with mock.patch("github_rag.e2e.launcher.ensure_local_git_fixture"):
            with mock.patch(
                "github_rag.e2e.launcher.resolve_zoekt_index_bin",
                return_value=wrapper,
            ):
                with mock.patch(
                    "github_rag.e2e.launcher.subprocess.Popen",
                    return_value=proc,
                ) as popen:
                    launcher.up(env={})
        host_env = popen.call_args.kwargs["env"]
        self.assertEqual(host_env.get("E2E_DEFER_STARTUP_INDEX"), "1")

    def test_t35_dev_compose_sets_defer_startup_index(self) -> None:
        e2e = import_e2e()
        launcher, _runner, _e2e = self._make_launcher(host_app=True)
        wrapper = REPO_ROOT / ".data/test-up-zoekt-bin/zoekt-index"
        proc = mock.Mock(poll=mock.Mock(return_value=None))
        with mock.patch("github_rag.e2e.launcher.ensure_local_git_fixture"):
            with mock.patch(
                "github_rag.e2e.launcher.resolve_zoekt_index_bin",
                return_value=wrapper,
            ):
                with mock.patch(
                    "github_rag.e2e.launcher.subprocess.Popen",
                    return_value=proc,
                ) as popen:
                    launcher.up(env={})
        host_env = popen.call_args.kwargs["env"]
        self.assertEqual(host_env.get("E2E_DEFER_STARTUP_INDEX"), "1")

    def test_t33_resolve_failure_surfaces_stack_error(self) -> None:
        from github_rag.e2e.errors import E2eStackError

        launcher, _runner, e2e = self._make_launcher(host_app=True)
        with mock.patch("github_rag.e2e.launcher.ensure_local_git_fixture"):
            with mock.patch(
                "github_rag.e2e.launcher.resolve_zoekt_index_bin",
                side_effect=E2eStackError.from_stderr("zoekt container not running"),
            ):
                with self.assertRaises(e2e.E2eStackError):
                    launcher.up(env={})

    def test_t29_host_exit_during_poll(self) -> None:
        launcher, _r, e2e = self._make_launcher(host_app=True, healthy_timeout_seconds=5.0)
        proc = mock.Mock(poll=mock.Mock(side_effect=[None, None, 1]), stderr=io.StringIO("fail"))
        launcher._app_process = proc
        with mock.patch("urllib.request.urlopen", mock.Mock(side_effect=OSError("down"))):
            with self.assertRaises(e2e.E2eStackError) as ctx:
                launcher.wait_healthy(timeout_seconds=5.0)
        self.assertIn("code=1", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
