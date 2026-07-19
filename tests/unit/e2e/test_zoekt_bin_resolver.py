"""Unit — zoekt_index_bin resolver (T33 / UT-P08)."""

from __future__ import annotations

import os
import stat
import tempfile
import unittest
from collections.abc import Mapping, Sequence
from pathlib import Path
from unittest import mock

from tests.unit.e2e.helpers import REPO_ROOT


class RecordingPodmanCommand:
    """Double de podman compose/ps/cp/exec."""

    def __init__(
        self,
        *,
        container_id: str = "abc123zoekt",
        cp_code: int = 0,
        exec_code: int = 0,
        ps_code: int = 0,
        ps_stdout: str | None = None,
    ) -> None:
        self.container_id = container_id
        self.cp_code = cp_code
        self.exec_code = exec_code
        self.ps_code = ps_code
        self.ps_stdout = ps_stdout if ps_stdout is not None else f"{container_id}\n"
        self.calls: list[tuple[Sequence[str], Mapping[str, str]]] = []

    def __call__(
        self,
        cmd: Sequence[str],
        env: Mapping[str, str],
    ) -> tuple[int, str, str]:
        self.calls.append((list(cmd), dict(env)))
        blob = " ".join(str(c) for c in cmd)
        if " ps " in blob or blob.endswith(" ps") or " ps -q" in blob:
            return self.ps_code, self.ps_stdout, ""
        if cmd[:2] == ["podman", "cp"]:
            return self.cp_code, "", "" if self.cp_code == 0 else "cp failed"
        if cmd[:2] == ["podman", "exec"] and "rm" not in cmd:
            return self.exec_code, "", "" if self.exec_code == 0 else "index failed"
        if cmd[:2] == ["podman", "exec"] and "rm" in cmd:
            return 0, "", ""
        return 0, "", ""


class TestZoektBinResolver(unittest.TestCase):
    """UT-P08-01..08."""

    def setUp(self) -> None:
        from github_rag.e2e.zoekt_bin import default_wrapper_dir

        self._default_wrapper_dir = default_wrapper_dir

    def test_ut_p08_01_default_wrapper_dir_e2e_vs_dev(self) -> None:
        e2e = self._default_wrapper_dir(REPO_ROOT, e2e=True)
        dev = self._default_wrapper_dir(REPO_ROOT, e2e=False)
        self.assertIn("e2e-zoekt-index-bin", str(e2e))
        self.assertIn("dev-zoekt-index-bin", str(dev))

    def test_ut_p08_02_find_zoekt_container_id(self) -> None:
        from github_rag.e2e.zoekt_bin import find_zoekt_container_id

        runner = RecordingPodmanCommand(container_id="cid999")
        compose = REPO_ROOT / "docker-compose.e2e.yml"
        cid = find_zoekt_container_id(compose, runner)
        self.assertEqual(cid, "cid999")
        ps_calls = [c for c, _ in runner.calls if "ps" in c]
        self.assertTrue(ps_calls)
        self.assertIn("zoekt", ps_calls[0])

    def test_ut_p08_03_container_absent_raises(self) -> None:
        from github_rag.e2e.errors import E2eStackError
        from github_rag.e2e.zoekt_bin import find_zoekt_container_id

        runner = RecordingPodmanCommand(ps_stdout="")
        compose = REPO_ROOT / "docker-compose.dev.yml"
        with self.assertRaises(E2eStackError) as ctx:
            find_zoekt_container_id(compose, runner)
        self.assertIn("not running", str(ctx.exception).lower())

    def test_ut_p08_04_exec_translates_index_path(self) -> None:
        from github_rag.e2e.zoekt_bin import exec_zoekt_index_cli

        runner = RecordingPodmanCommand()
        compose = REPO_ROOT / "docker-compose.e2e.yml"
        with tempfile.TemporaryDirectory() as tmp:
            code = exec_zoekt_index_cli(
                [
                    "-index",
                    str(REPO_ROOT / ".data/e2e-zoekt-index"),
                    "-name",
                    "org/repo",
                    tmp,
                ],
                compose_file=compose,
                run_command=runner,
            )
        self.assertEqual(code, 0)
        exec_calls = [
            c for c, _ in runner.calls if c[:2] == ["podman", "exec"] and "rm" not in c
        ]
        self.assertEqual(len(exec_calls), 1)
        self.assertIn("/data/index", exec_calls[0])
        self.assertNotIn(str(REPO_ROOT), exec_calls[0])

    def test_ut_p08_05_exec_podman_cp_and_cleanup(self) -> None:
        from github_rag.e2e.zoekt_bin import exec_zoekt_index_cli

        runner = RecordingPodmanCommand()
        compose = REPO_ROOT / "docker-compose.dev.yml"
        with tempfile.TemporaryDirectory() as tmp:
            exec_zoekt_index_cli(
                ["-index", "/host/index", "-name", "r", tmp],
                compose_file=compose,
                run_command=runner,
            )
        cp_calls = [c for c, _ in runner.calls if c[:2] == ["podman", "cp"]]
        rm_calls = [
            c for c, _ in runner.calls if c[:2] == ["podman", "exec"] and "rm" in c
        ]
        self.assertEqual(len(cp_calls), 1)
        self.assertEqual(len(rm_calls), 1)

    def test_ut_p08_06_materialize_wrapper_executable(self) -> None:
        from github_rag.e2e.zoekt_bin import materialize_zoekt_index_wrapper

        with tempfile.TemporaryDirectory() as tmp:
            wrapper_dir = Path(tmp)
            path = materialize_zoekt_index_wrapper(
                REPO_ROOT / "docker-compose.e2e.yml",
                wrapper_dir,
            )
            self.assertTrue(path.is_file())
            mode = path.stat().st_mode
            self.assertTrue(mode & stat.S_IXUSR)
            content = path.read_text(encoding="utf-8")
            self.assertIn("exec_zoekt_index_cli", content)

    def test_ut_p08_07_resolve_explicit_override(self) -> None:
        from github_rag.e2e.zoekt_bin import resolve_zoekt_index_bin

        runner = RecordingPodmanCommand()
        custom = "/opt/zoekt/zoekt-index"
        resolved = resolve_zoekt_index_bin(
            REPO_ROOT,
            REPO_ROOT / "docker-compose.e2e.yml",
            run_command=runner,
            env={"ZOEKT_INDEX_BIN": custom},
        )
        self.assertEqual(str(resolved), str(Path(custom).resolve()))
        ps_calls = [c for c, _ in runner.calls if "ps" in c]
        self.assertEqual(ps_calls, [])

    def test_ut_p08_08_resolve_materializes_when_default(self) -> None:
        from github_rag.e2e.zoekt_bin import resolve_zoekt_index_bin

        runner = RecordingPodmanCommand()
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / ".data" / "e2e-zoekt-index-bin"
            clean = {
                k: v for k, v in os.environ.items() if k != "ZOEKT_INDEX_BIN"
            }
            with mock.patch.dict(os.environ, clean, clear=True):
                with mock.patch(
                    "github_rag.e2e.zoekt_bin.default_wrapper_dir",
                    return_value=data_dir,
                ):
                    resolved = resolve_zoekt_index_bin(
                        REPO_ROOT,
                        REPO_ROOT / "docker-compose.e2e.yml",
                        run_command=runner,
                        env={},
                    )
            self.assertTrue(resolved.is_file())
            self.assertEqual(resolved.name, "zoekt-index")

    def test_ut_p08_11_ps_failure_raises(self) -> None:
        from github_rag.e2e.errors import E2eStackError
        from github_rag.e2e.zoekt_bin import find_zoekt_container_id

        runner = RecordingPodmanCommand(ps_code=1)
        with self.assertRaises(E2eStackError):
            find_zoekt_container_id(REPO_ROOT / "docker-compose.e2e.yml", runner)

    def test_ut_p08_12_invalid_argv_raises(self) -> None:
        from github_rag.e2e.errors import E2eStackError
        from github_rag.e2e.zoekt_bin import exec_zoekt_index_cli

        runner = RecordingPodmanCommand()
        with self.assertRaises(E2eStackError):
            exec_zoekt_index_cli(
                ["-index", "/x"],
                compose_file=REPO_ROOT / "docker-compose.e2e.yml",
                run_command=runner,
            )

    def test_ut_p08_13_cp_failure_raises(self) -> None:
        from github_rag.e2e.errors import E2eStackError
        from github_rag.e2e.zoekt_bin import exec_zoekt_index_cli

        runner = RecordingPodmanCommand(cp_code=1)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(E2eStackError):
                exec_zoekt_index_cli(
                    ["-index", "/x", "-name", "r", tmp],
                    compose_file=REPO_ROOT / "docker-compose.e2e.yml",
                    run_command=runner,
                )

    def test_ut_p08_14_exec_nonzero_exit_code(self) -> None:
        from github_rag.e2e.zoekt_bin import exec_zoekt_index_cli

        runner = RecordingPodmanCommand(exec_code=2)
        with tempfile.TemporaryDirectory() as tmp:
            code = exec_zoekt_index_cli(
                ["-index", "/x", "-name", "r", tmp],
                compose_file=REPO_ROOT / "docker-compose.e2e.yml",
                run_command=runner,
                env={"EXTRA": "1"},
            )
        self.assertEqual(code, 2)

    def test_ut_p08_15_resolve_none_env_uses_os_environ_override(self) -> None:
        from github_rag.e2e.zoekt_bin import resolve_zoekt_index_bin

        runner = RecordingPodmanCommand()
        custom = "/opt/custom-zoekt-index"
        with mock.patch.dict(os.environ, {"ZOEKT_INDEX_BIN": custom}, clear=False):
            resolved = resolve_zoekt_index_bin(
                REPO_ROOT,
                REPO_ROOT / "docker-compose.dev.yml",
                run_command=runner,
                env=None,
            )
        self.assertEqual(str(resolved), str(Path(custom).resolve()))

    def test_ut_p08_16_default_run_command_delegates_subprocess(self) -> None:
        from github_rag.e2e.zoekt_bin import _default_run_command

        completed = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch("subprocess.run", return_value=completed) as run:
            code, out, err = _default_run_command(["echo", "x"], {"PATH": "/usr/bin"})
        self.assertEqual((code, out, err), (0, "ok", ""))
        run.assert_called_once()

    def test_ut_p08_17_explicit_index_bin_none(self) -> None:
        from github_rag.e2e.zoekt_bin import _explicit_index_bin

        self.assertIsNone(_explicit_index_bin(None))
        self.assertIsNone(_explicit_index_bin({"ZOEKT_INDEX_BIN": "zoekt-index"}))


class TestHostEnvZoektBin(unittest.TestCase):
    def test_ut_p08_09_build_host_delivery_env_includes_zoekt_index_bin(self) -> None:
        from github_rag.e2e.host_env import build_host_delivery_env

        cfg = REPO_ROOT / "e2e/fixtures/config.e2e.json"
        repos = REPO_ROOT / "e2e/fixtures/repos"
        zoekt = REPO_ROOT / ".data/test-zoekt-index-bin-env"
        custom_bin = "/tmp/wrapper-zoekt-index"
        env = build_host_delivery_env(
            repo_root=REPO_ROOT,
            config_path=cfg,
            repos_dir=repos,
            zoekt_index_dir=zoekt,
            zoekt_index_bin=custom_bin,
        )
        self.assertEqual(env["ZOEKT_INDEX_BIN"], custom_bin)


class TestLauncherZoektBinPropagation(unittest.TestCase):
    def test_ut_p08_10_start_host_app_propagates_resolved_bin(self) -> None:
        from github_rag.e2e.launcher import PodmanE2eStackLauncher

        wrapper_path = REPO_ROOT / ".data/test-launcher-zoekt-bin/zoekt-index"
        launcher = PodmanE2eStackLauncher(
            repo_root=REPO_ROOT,
            host_app=True,
            run_command=RecordingPodmanCommand(),
        )
        effective = {
            "HOST_CONFIG": str(REPO_ROOT / "e2e/fixtures/config.e2e.json"),
            "HOST_REPOS": str(REPO_ROOT / "e2e/fixtures/repos"),
            "ZOEKT_INDEX_HOST": str(REPO_ROOT / ".data/e2e-zoekt-index"),
        }
        with mock.patch(
            "github_rag.e2e.launcher.resolve_zoekt_index_bin",
            return_value=wrapper_path,
        ):
            with mock.patch("github_rag.e2e.launcher.subprocess.Popen") as popen:
                launcher._start_host_app(effective)
        popen.assert_called_once()
        host_env = popen.call_args.kwargs["env"]
        self.assertEqual(host_env["ZOEKT_INDEX_BIN"], str(wrapper_path))


if __name__ == "__main__":
    unittest.main()
