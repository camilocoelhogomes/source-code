"""Unit tests — compute_progress_percent."""

from __future__ import annotations

import unittest

from github_rag.indexing.progress import compute_progress_percent


class TestComputeProgressPercent(unittest.TestCase):
    def test_zero_total(self) -> None:
        self.assertEqual(
            compute_progress_percent(files_processed=0, files_total=0), 0
        )

    def test_negative_total(self) -> None:
        self.assertEqual(
            compute_progress_percent(files_processed=1, files_total=-1), 0
        )

    def test_mid(self) -> None:
        self.assertEqual(
            compute_progress_percent(files_processed=1, files_total=4), 25
        )

    def test_clamp_100(self) -> None:
        self.assertEqual(
            compute_progress_percent(files_processed=5, files_total=4), 100
        )

    def test_empty_processed(self) -> None:
        self.assertEqual(
            compute_progress_percent(files_processed=0, files_total=3), 0
        )


if __name__ == "__main__":
    unittest.main()
