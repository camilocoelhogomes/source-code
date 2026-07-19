"""Unit — E2eStackError / E2eCredentialError redaction (T21 / UT-E*)."""

from __future__ import annotations

import unittest

from tests.unit.e2e.helpers import SECRET_TOKEN, import_e2e


class TestE2eStackErrorRedaction(unittest.TestCase):
    """UT-E01..E05."""

    def test_ut_e01_from_stderr_redacts_known_secrets(self) -> None:
        e2e = import_e2e()
        raw = f"podman failed env_token={SECRET_TOKEN} exit=1"
        err = e2e.E2eStackError.from_stderr(raw, secrets=[SECRET_TOKEN])
        self.assertNotIn(SECRET_TOKEN, str(err))

    def test_ut_e02_from_stderr_redacts_ghp_pattern(self) -> None:
        e2e = import_e2e()
        raw = f"compose stderr leaked {SECRET_TOKEN} in log"
        err = e2e.E2eStackError.from_stderr(raw)
        self.assertNotIn(SECRET_TOKEN, str(err))
        self.assertNotRegex(str(err), r"ghp_[A-Za-z0-9_]{10,}")

    def test_ut_e03_from_stderr_empty_raw(self) -> None:
        e2e = import_e2e()
        for raw in ("", "   ", "\n"):
            with self.subTest(raw=repr(raw)):
                err = e2e.E2eStackError.from_stderr(raw)
                self.assertIsInstance(err, e2e.E2eStackError)
                self.assertNotIn(SECRET_TOKEN, str(err))

    def test_ut_e04_from_stderr_without_secrets_preserves_safe_gist(self) -> None:
        e2e = import_e2e()
        raw = "Error: image pull failed for ghcr.io/example/app:latest"
        err = e2e.E2eStackError.from_stderr(raw)
        self.assertIn("image pull failed", str(err))
        self.assertNotIn(SECRET_TOKEN, str(err))

    def test_ut_e05_error_types_are_distinct(self) -> None:
        e2e = import_e2e()
        self.assertFalse(
            issubclass(e2e.E2eStackError, e2e.E2eCredentialError),
        )
        self.assertFalse(
            issubclass(e2e.E2eCredentialError, e2e.E2eStackError),
        )
        self.assertTrue(issubclass(e2e.E2eStackError, Exception))
        self.assertTrue(issubclass(e2e.E2eCredentialError, Exception))


if __name__ == "__main__":
    unittest.main()
