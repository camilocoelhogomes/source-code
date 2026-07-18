"""
Testes unitários — EnvironSecretResolver / SecretResolutionError (T02).

Pré-implementação: resolve permanece stub (...); casos comportamentais
devem falhar (red) pela ausência de implementação.

Execução:
    PYTHONPATH=src python3 -m pytest tests/unit/config/test_secrets.py -q
"""

from __future__ import annotations

import os
import unittest
from unittest import mock

from github_rag.config.secrets import (
    EnvironSecretResolver,
    SecretResolutionError,
    SecretResolver,
)

from .helpers import SECRET_TOKEN_VALUE, TOKEN_ENV_NAME


def _assert_resolved(value: object) -> str:
    if value is None or value is ...:
        raise AssertionError(
            "resolve retornou None/Ellipsis — stub sem implementação "
            "(esperado red até Developer implementar o corpo)"
        )
    if not isinstance(value, str):
        raise AssertionError(f"resolve retornou {type(value)!r}, esperado str")
    return value


def _assert_raises_secret_error(call: object) -> SecretResolutionError:
    try:
        result = call()  # type: ignore[operator]
    except SecretResolutionError as exc:
        return exc
    if result is None or result is ...:
        raise AssertionError(
            "resolve retornou None/Ellipsis em vez de SecretResolutionError — "
            "stub sem implementação (red esperado)"
        )
    raise AssertionError(
        f"esperado SecretResolutionError, obteve retorno {type(result)!r}: {result!r}"
    )


class TestSecretResolutionErrorContract(unittest.TestCase):
    """UT-S08 — superfície estática."""

    def test_ut_s08_is_exception(self) -> None:
        self.assertTrue(issubclass(SecretResolutionError, Exception))
        err = SecretResolutionError(f"{TOKEN_ENV_NAME}: missing")
        self.assertIsInstance(err, Exception)
        self.assertIn(TOKEN_ENV_NAME, str(err))


class TestEnvironSecretResolverResolve(unittest.TestCase):
    """UT-S01..S07, UT-S09 — comportamento de resolução."""

    def test_ut_s01_resolve_ok_via_mapping(self) -> None:
        resolver = EnvironSecretResolver(
            environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
        )
        value = _assert_resolved(resolver.resolve(TOKEN_ENV_NAME))
        self.assertEqual(value, SECRET_TOKEN_VALUE)

    def test_ut_s02_resolve_ok_via_os_environ(self) -> None:
        resolver = EnvironSecretResolver(environ=None)
        with mock.patch.dict(
            os.environ, {TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}, clear=False
        ):
            value = _assert_resolved(resolver.resolve(TOKEN_ENV_NAME))
        self.assertEqual(value, SECRET_TOKEN_VALUE)

    def test_ut_s03_missing_env_raises(self) -> None:
        resolver = EnvironSecretResolver(environ={"OTHER": "x"})
        exc = _assert_raises_secret_error(
            lambda: resolver.resolve(TOKEN_ENV_NAME)
        )
        self.assertIn(TOKEN_ENV_NAME, str(exc))
        self.assertNotIn(SECRET_TOKEN_VALUE, str(exc))

    def test_ut_s04_blank_env_value_raises(self) -> None:
        for blank in ("", " ", "  ", "\t", "\n", " \t\n "):
            with self.subTest(blank=repr(blank)):
                resolver = EnvironSecretResolver(
                    environ={TOKEN_ENV_NAME: blank}
                )
                exc = _assert_raises_secret_error(
                    lambda r=resolver: r.resolve(TOKEN_ENV_NAME)
                )
                self.assertIn(TOKEN_ENV_NAME, str(exc))

    def test_ut_s05_blank_env_name_raises(self) -> None:
        resolver = EnvironSecretResolver(
            environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
        )
        for blank in ("", " ", "\t", "\n"):
            with self.subTest(blank=repr(blank)):
                exc = _assert_raises_secret_error(
                    lambda b=blank: resolver.resolve(b)
                )
                self.assertNotIn(SECRET_TOKEN_VALUE, str(exc))

    def test_ut_s06_secret_value_not_in_error_str_repr(self) -> None:
        resolver = EnvironSecretResolver(
            environ={
                TOKEN_ENV_NAME: SECRET_TOKEN_VALUE,
                "OTHER_TOKEN": "another-secret-value-xyz",
            }
        )
        exc = _assert_raises_secret_error(
            lambda: resolver.resolve("MISSING_ENV")
        )
        self.assertNotIn(SECRET_TOKEN_VALUE, str(exc))
        self.assertNotIn(SECRET_TOKEN_VALUE, repr(exc))
        self.assertNotIn("another-secret-value-xyz", str(exc))
        self.assertNotIn("another-secret-value-xyz", repr(exc))
        self.assertIn("MISSING_ENV", str(exc))

    def test_ut_s07_does_not_mutate_mapping(self) -> None:
        environ = {TOKEN_ENV_NAME: SECRET_TOKEN_VALUE, "KEEP": "1"}
        snapshot = dict(environ)
        resolver = EnvironSecretResolver(environ=environ)
        _assert_resolved(resolver.resolve(TOKEN_ENV_NAME))
        self.assertEqual(environ, snapshot)

    def test_ut_s09_resolve_idempotent(self) -> None:
        resolver = EnvironSecretResolver(
            environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
        )
        first = _assert_resolved(resolver.resolve(TOKEN_ENV_NAME))
        second = _assert_resolved(resolver.resolve(TOKEN_ENV_NAME))
        self.assertEqual(first, second)
        self.assertEqual(first, SECRET_TOKEN_VALUE)


class TestSecretResolverProtocol(unittest.TestCase):
    """Contrato Protocol."""

    def test_environ_resolver_satisfies_protocol_when_implemented(self) -> None:
        resolver = EnvironSecretResolver(
            environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
        )
        value = resolver.resolve(TOKEN_ENV_NAME)
        if value is None or value is ...:
            raise AssertionError(
                "EnvironSecretResolver.resolve é stub (None/Ellipsis) — red esperado"
            )
        self.assertIsInstance(resolver, SecretResolver)
        self.assertIsInstance(value, str)
