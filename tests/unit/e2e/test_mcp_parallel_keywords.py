"""Unit — McpKeywords paralelo / SLO (T26 / UT-K*)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
KEYWORDS_PATH = ROOT / "e2e" / "robot" / "libraries" / "McpKeywords.py"
ROBOT_PATH = ROOT / "e2e" / "robot" / "mcp.robot"


def _load_keywords():
    spec = importlib.util.spec_from_file_location("mcp_keywords_t26", KEYWORDS_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestMcpParallelKeywords(unittest.TestCase):
    def test_ut_k01_parallel_call_shape(self) -> None:
        mod = _load_keywords()
        with patch.object(mod, "mcp_call_tool", return_value='{"hits":[]}'):
            out = mod.mcp_parallel_call_tools(
                "search_code",
                '{"pattern":"def","max_matches":3}',
                4,
                "http://127.0.0.1:8001",
            )
        self.assertEqual(out["n_calls"], 4)
        self.assertEqual(len(out["results"]), 4)
        self.assertIsInstance(out["wall_seconds"], float)
        self.assertGreaterEqual(out["wall_seconds"], 0.0)

    def test_ut_k02_assert_parallel_slo_raises_on_serial(self) -> None:
        mod = _load_keywords()
        with self.assertRaises(AssertionError):
            mod.mcp_assert_parallel_slo(
                capacity=4,
                n_calls=8,
                wall_seconds=8.0,
                single_seconds=1.0,
            )

    def test_ut_k03_measure_single_median(self) -> None:
        mod = _load_keywords()
        times = iter([0.10, 0.30, 0.20])

        def fake_call(*_a, **_k):
            # consume scheduled durations via sleep patch below
            return '{"hits":[]}'

        with patch.object(mod, "mcp_call_tool", side_effect=fake_call):
            with patch.object(mod.time, "perf_counter", side_effect=[
                0.0, 0.10,  # sample1
                1.0, 1.30,  # sample2
                2.0, 2.20,  # sample3
            ]):
                median = mod.mcp_measure_single_call_seconds(
                    "search_code",
                    "{}",
                    samples=3,
                )
        self.assertAlmostEqual(median, 0.20, places=5)

    def test_ut_k04_robot_bdd013_not_sequential_smoke(self) -> None:
        text = ROBOT_PATH.read_text(encoding="utf-8")
        self.assertIn("BDD-013", text)
        self.assertIn("Mcp Parallel Call Tools", text)
        self.assertIn("Mcp Assert Parallel Slo", text)
        # Anti falso-verde: o caso bdd013 não pode ser só duas calls sequenciais
        # sem as keywords paralelas (já assertadas acima).
        idx = text.index("BDD-013 Parallel")
        block = text[idx : idx + 800]
        self.assertIn("Mcp Parallel Call Tools", block)
        self.assertNotIn(
            "Duas calls sequenciais",
            block,
        )


if __name__ == "__main__":
    unittest.main()
