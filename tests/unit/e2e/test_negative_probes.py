"""Unit — e2e/probes/negative_probes (T25 / UT-P*)."""

from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from tests.unit.delivery.helpers import SECRET_TOKEN
from tests.unit.e2e.helpers import REPO_ROOT, import_e2e

_PROBE_PATH = REPO_ROOT / "e2e" / "probes" / "negative_probes.py"


def _load_probes():
    spec = importlib.util.spec_from_file_location(
        "e2e_negative_probes", _PROBE_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["e2e_negative_probes"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestNegativeProbes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.probes = _load_probes()

    def test_ut_p01_bdd008_probe_exits_zero(self) -> None:
        self.assertEqual(self.probes.run_bdd008_partial_failure_probe(), 0)

    def test_ut_p02_bdd022_probe_exits_zero(self) -> None:
        self.assertEqual(self.probes.run_bdd022_config_path_probe(), 0)

    def test_ut_p03_invalid_argv_exits_nonzero(self) -> None:
        self.assertNotEqual(self.probes.main(["negative_probes", "unknown"]), 0)
        self.assertNotEqual(self.probes.main(["negative_probes"]), 0)

    def test_ut_p04_probe_stdout_never_contains_secret(self) -> None:
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": SECRET_TOKEN}):
            with redirect_stdout(buf_out), redirect_stderr(buf_err):
                code8 = self.probes.run_bdd008_partial_failure_probe()
                code22 = self.probes.run_bdd022_config_path_probe()
        self.assertEqual(code8, 0)
        self.assertEqual(code22, 0)
        text = buf_out.getvalue() + buf_err.getvalue()
        self.assertNotIn(SECRET_TOKEN, text)

    def test_main_bdd008_and_bdd022_dispatch(self) -> None:
        self.assertEqual(self.probes.main(["negative_probes", "bdd008"]), 0)
        self.assertEqual(self.probes.main(["negative_probes", "bdd022"]), 0)


class TestNegativeProbesLocation(unittest.TestCase):
    def test_probe_lives_outside_github_rag_e2e_package(self) -> None:
        self.assertTrue(_PROBE_PATH.is_file())
        e2e_pkg = REPO_ROOT / "src" / "github_rag" / "e2e"
        self.assertFalse((e2e_pkg / "negative_probes.py").exists())
        import_e2e()
        self.assertTrue(hasattr(import_e2e(), "DefaultRobotMvpSuite"))


if __name__ == "__main__":
    unittest.main()
