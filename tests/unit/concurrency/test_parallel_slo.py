"""Unit — parallel_slo (T26 / UT-S*)."""

from __future__ import annotations

import unittest

from github_rag.concurrency.parallel_slo import (
    evaluate_parallel_slo,
    min_waves,
)


class TestMinWaves(unittest.TestCase):
    def test_ut_s01_basic(self) -> None:
        self.assertEqual(min_waves(8, 4), 2)

    def test_ut_s02_remainder(self) -> None:
        self.assertEqual(min_waves(5, 2), 3)

    def test_ut_s03_invalid(self) -> None:
        with self.assertRaises(ValueError):
            min_waves(0, 1)
        with self.assertRaises(ValueError):
            min_waves(1, 0)


class TestEvaluateParallelSlo(unittest.TestCase):
    def test_ut_s04_accepts_two_waves(self) -> None:
        result = evaluate_parallel_slo(
            capacity=4,
            n_calls=8,
            wall_seconds=2.0,
            single_seconds=1.0,
        )
        self.assertTrue(result.ok, msg=result.reason)
        self.assertEqual(result.min_waves, 2)

    def test_ut_s05_rejects_serial(self) -> None:
        result = evaluate_parallel_slo(
            capacity=4,
            n_calls=8,
            wall_seconds=8.0,
            single_seconds=1.0,
        )
        self.assertFalse(result.ok)
        self.assertTrue(result.reason)

    def test_ut_s06_rejects_unlimited(self) -> None:
        result = evaluate_parallel_slo(
            capacity=4,
            n_calls=8,
            wall_seconds=1.0,
            single_seconds=1.0,
        )
        self.assertFalse(result.ok)

    def test_ut_s07_single_non_positive(self) -> None:
        result = evaluate_parallel_slo(
            capacity=2,
            n_calls=2,
            wall_seconds=1.0,
            single_seconds=0.0,
        )
        self.assertFalse(result.ok)

    def test_ut_s08_invalid_capacity(self) -> None:
        result = evaluate_parallel_slo(
            capacity=0,
            n_calls=2,
            wall_seconds=1.0,
            single_seconds=1.0,
        )
        self.assertFalse(result.ok)

    def test_ut_s09_parallel_when_n_equals_capacity(self) -> None:
        result = evaluate_parallel_slo(
            capacity=2,
            n_calls=2,
            wall_seconds=1.05,
            single_seconds=1.0,
        )
        self.assertTrue(result.ok, msg=result.reason)


if __name__ == "__main__":
    unittest.main()
