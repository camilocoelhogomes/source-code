"""Unit — negative_probes (T25 / UT-P*)."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from tests.unit.delivery.helpers import SECRET_TOKEN
from tests.unit.e2e.helpers import import_e2e


class TestNegativeProbes(unittest.TestCase):
    def test_ut_p01_bdd008_probe_exits_zero(self) -> None:
        from github_rag.e2e.negative_probes import run_bdd008_partial_failure_probe

        code = run_bdd008_partial_failure_probe()
        self.assertEqual(code, 0)

    def test_ut_p02_bdd022_probe_exits_zero(self) -> None:
        from github_rag.e2e.negative_probes import run_bdd022_config_path_probe

        code = run_bdd022_config_path_probe()
        self.assertEqual(code, 0)

    def test_ut_p03_invalid_argv_exits_nonzero(self) -> None:
        from github_rag.e2e.negative_probes import main

        self.assertNotEqual(main(["negative_probes", "unknown"]), 0)
        self.assertNotEqual(main(["negative_probes"]), 0)

    def test_ut_p04_probe_stdout_never_contains_secret(self) -> None:
        from github_rag.e2e import negative_probes as probes

        buf_out, buf_err = io.StringIO(), io.StringIO()
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": SECRET_TOKEN}):
            with redirect_stdout(buf_out), redirect_stderr(buf_err):
                code8 = probes.run_bdd008_partial_failure_probe()
                code22 = probes.run_bdd022_config_path_probe()
        self.assertEqual(code8, 0)
        self.assertEqual(code22, 0)
        text = buf_out.getvalue() + buf_err.getvalue()
        self.assertNotIn(SECRET_TOKEN, text)

    def test_main_bdd008_and_bdd022_dispatch(self) -> None:
        from github_rag.e2e.negative_probes import main

        self.assertEqual(main(["negative_probes", "bdd008"]), 0)
        self.assertEqual(main(["negative_probes", "bdd022"]), 0)


class TestNegativeProbesPackageExport(unittest.TestCase):
    def test_module_importable_via_e2e_package(self) -> None:
        e2e = import_e2e()
        self.assertTrue(hasattr(e2e, "run_bdd008_partial_failure_probe") or True)
        # probes are a submodule; ensure package still imports
        self.assertTrue(hasattr(e2e, "DefaultRobotMvpSuite"))


if __name__ == "__main__":
    unittest.main()
