"""Testes unitários — SubprocessZoektIndexRunner (T10) com mock subprocess."""

from __future__ import annotations

import dataclasses
import subprocess
import unittest
from unittest import mock

from github_rag.index.zoekt.runner import (
    SubprocessZoektIndexRunner,
    ZoektIndexRunResult,
)


class TestZoektIndexRunResult(unittest.TestCase):
    def test_is_frozen(self) -> None:
        result = ZoektIndexRunResult(returncode=0, stdout="ok", stderr="")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.returncode = 1  # type: ignore[misc]


class TestSubprocessZoektIndexRunner(unittest.TestCase):
    def test_run_invokes_subprocess_with_argv_list_no_shell(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["zoekt-index", "-index", "/data/index", "/tmp/tree"],
            returncode=0,
            stdout="indexed",
            stderr="",
        )
        with mock.patch("subprocess.run", return_value=completed) as run:
            runner = SubprocessZoektIndexRunner(timeout_seconds=60.0)
            result = runner.run(
                ["zoekt-index", "-index", "/data/index", "/tmp/tree"]
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "indexed")
        run.assert_called_once()
        call_args = run.call_args
        argv = call_args.args[0]
        self.assertEqual(
            list(argv),
            ["zoekt-index", "-index", "/data/index", "/tmp/tree"],
        )
        self.assertFalse(call_args.kwargs.get("shell", False))
        self.assertEqual(call_args.kwargs.get("timeout"), 60.0)

    def test_exit_zero_returns_result(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["zoekt-index"],
            returncode=0,
            stdout="out",
            stderr="err",
        )
        with mock.patch("subprocess.run", return_value=completed):
            result = SubprocessZoektIndexRunner().run(["zoekt-index", "x"])
        self.assertIsInstance(result, ZoektIndexRunResult)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "out")
        self.assertEqual(result.stderr, "err")

    def test_nonzero_exit_still_returns_result(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["zoekt-index"],
            returncode=2,
            stdout="",
            stderr="fatal: bad tree",
        )
        with mock.patch("subprocess.run", return_value=completed):
            result = SubprocessZoektIndexRunner().run(["zoekt-index", "x"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("fatal", result.stderr)

    def test_missing_binary_raises_envelopable(self) -> None:
        with mock.patch(
            "subprocess.run",
            side_effect=FileNotFoundError("zoekt-index"),
        ):
            with self.assertRaises((FileNotFoundError, OSError)):
                SubprocessZoektIndexRunner().run(["zoekt-index", "-index", "/x", "/y"])


if __name__ == "__main__":
    unittest.main()
