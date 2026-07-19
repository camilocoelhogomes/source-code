"""Unit — E2eCredentialResolver HITL/CI (T21 / UT-C*)."""

from __future__ import annotations

import unittest

from tests.unit.e2e.helpers import SECRET_TOKEN, import_e2e


class TestCredentialResolverHitl(unittest.TestCase):
    """UT-C01..C05 / UT-C09 / UT-C10 — política HITL."""

    def test_ut_c01_hitl_missing_token_raises(self) -> None:
        e2e = import_e2e()
        env = {"GITHUB_ACTIONS": "false"}
        with self.assertRaises(e2e.E2eCredentialError):
            e2e.E2eCredentialResolver().resolve(environ=env)

    def test_ut_c02_hitl_github_token_only(self) -> None:
        e2e = import_e2e()
        env = {"GITHUB_ACTIONS": "false", "GITHUB_TOKEN": SECRET_TOKEN}
        resolved = e2e.E2eCredentialResolver().resolve(environ=env)
        self.assertEqual(resolved.token, SECRET_TOKEN)
        self.assertEqual(resolved.source, "GITHUB_TOKEN")

    def test_ut_c03_hitl_e2e_token_only(self) -> None:
        e2e = import_e2e()
        env = {"GITHUB_ACTIONS": "false", "E2E_GITHUB_TOKEN": SECRET_TOKEN}
        resolved = e2e.E2eCredentialResolver().resolve(environ=env)
        self.assertEqual(resolved.token, SECRET_TOKEN)
        self.assertEqual(resolved.source, "E2E_GITHUB_TOKEN")

    def test_ut_c04_hitl_prefers_e2e_when_both(self) -> None:
        e2e = import_e2e()
        preferred = "ghp_preferred_e2e_token_aaaaaaaa"
        env = {
            "GITHUB_ACTIONS": "false",
            "E2E_GITHUB_TOKEN": preferred,
            "GITHUB_TOKEN": SECRET_TOKEN,
        }
        resolved = e2e.E2eCredentialResolver().resolve(environ=env)
        self.assertEqual(resolved.token, preferred)
        self.assertEqual(resolved.source, "E2E_GITHUB_TOKEN")

    def test_ut_c05_hitl_blank_token_rejected(self) -> None:
        e2e = import_e2e()
        for blank in ("", "   ", "\t"):
            with self.subTest(blank=repr(blank)):
                env = {"GITHUB_ACTIONS": "false", "GITHUB_TOKEN": blank}
                with self.assertRaises(e2e.E2eCredentialError):
                    e2e.E2eCredentialResolver().resolve(environ=env)

    def test_ut_c05b_hitl_blank_e2e_falls_back_to_github_token(self) -> None:
        """E2E_GITHUB_TOKEN blank não conta como presente — usa GITHUB_TOKEN."""
        e2e = import_e2e()
        env = {
            "GITHUB_ACTIONS": "false",
            "E2E_GITHUB_TOKEN": "   ",
            "GITHUB_TOKEN": SECRET_TOKEN,
        }
        resolved = e2e.E2eCredentialResolver().resolve(environ=env)
        self.assertEqual(resolved.token, SECRET_TOKEN)
        self.assertEqual(resolved.source, "GITHUB_TOKEN")

    def test_ut_c09_github_actions_false_is_hitl(self) -> None:
        e2e = import_e2e()
        env = {"GITHUB_ACTIONS": "false", "GITHUB_TOKEN": SECRET_TOKEN}
        resolved = e2e.E2eCredentialResolver().resolve(environ=env)
        self.assertEqual(resolved.token, SECRET_TOKEN)

    def test_ut_c10_error_message_never_contains_token(self) -> None:
        e2e = import_e2e()
        env = {"GITHUB_ACTIONS": "true", "GITHUB_TOKEN": SECRET_TOKEN}
        with self.assertRaises(e2e.E2eCredentialError) as ctx:
            e2e.E2eCredentialResolver().resolve(environ=env)
        self.assertNotIn(SECRET_TOKEN, str(ctx.exception))
        self.assertNotIn("ghp_", str(ctx.exception))


class TestCredentialResolverCi(unittest.TestCase):
    """UT-C06..C08 — política CI / E2E_REQUIRE_E2E_TOKEN."""

    def test_ut_c06_ci_actions_token_only_fails(self) -> None:
        e2e = import_e2e()
        env = {"GITHUB_ACTIONS": "true", "GITHUB_TOKEN": SECRET_TOKEN}
        with self.assertRaises(e2e.E2eCredentialError):
            e2e.E2eCredentialResolver().resolve(environ=env)

    def test_ut_c07_ci_with_e2e_token_succeeds(self) -> None:
        e2e = import_e2e()
        env = {
            "GITHUB_ACTIONS": "true",
            "E2E_GITHUB_TOKEN": SECRET_TOKEN,
            "GITHUB_TOKEN": "actions_default_should_not_win",
        }
        resolved = e2e.E2eCredentialResolver().resolve(environ=env)
        self.assertEqual(resolved.token, SECRET_TOKEN)
        self.assertEqual(resolved.source, "E2E_GITHUB_TOKEN")

    def test_ut_c08_require_flag_forces_ci_policy(self) -> None:
        e2e = import_e2e()
        env = {
            "E2E_REQUIRE_E2E_TOKEN": "1",
            "GITHUB_TOKEN": SECRET_TOKEN,
        }
        with self.assertRaises(e2e.E2eCredentialError):
            e2e.E2eCredentialResolver().resolve(environ=env)

    def test_ut_c08b_ci_blank_e2e_token_fails(self) -> None:
        """CI com E2E_GITHUB_TOKEN vazio/whitespace + GITHUB_TOKEN → falha."""
        e2e = import_e2e()
        for blank in ("", "   ", "\t"):
            with self.subTest(blank=repr(blank)):
                env = {
                    "GITHUB_ACTIONS": "true",
                    "E2E_GITHUB_TOKEN": blank,
                    "GITHUB_TOKEN": SECRET_TOKEN,
                }
                with self.assertRaises(e2e.E2eCredentialError) as ctx:
                    e2e.E2eCredentialResolver().resolve(environ=env)
                self.assertNotIn(SECRET_TOKEN, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
