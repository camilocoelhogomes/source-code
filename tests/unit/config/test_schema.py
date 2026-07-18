"""
Testes unitários — schema tipado / redaction (T02).

Valida Protocols runtime_checkable e invariantes de AppConfig/conexões/
ResolvedSecret após carga ok (red enquanto load for stub).

Execução:
    PYTHONPATH=src python3 -m pytest tests/unit/config/test_schema.py -q
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Protocol

from github_rag.config import (
    AppConfig,
    ConfigLoadError,
    ConfigLoader,
    EnvSecretRef,
    EnvironSecretResolver,
    GitConnection,
    GitHubConnection,
    ResolvedSecret,
    Revisions,
    SecretResolutionError,
    SecretResolver,
)
from github_rag.config import schema as schema_mod

from .helpers import (
    SECRET_TOKEN_VALUE,
    TOKEN_ENV_NAME,
    git_connection,
    github_connection,
    load_with_environ,
    write_config,
)


def _assert_app_config(result: object) -> AppConfig:
    if result is None or result is ...:
        raise AssertionError(
            "load retornou None/Ellipsis — stub sem implementação "
            "(esperado red até Developer implementar o corpo)"
        )
    if not isinstance(result, AppConfig):
        raise AssertionError(
            f"retorno {type(result)!r} não satisfaz AppConfig Protocol"
        )
    return result


class TestSchemaProtocolsSurface(unittest.TestCase):
    """UT-M01, UT-M08 — superfície de contrato."""

    def test_ut_m01_protocols_are_runtime_checkable(self) -> None:
        for proto in (
            AppConfig,
            GitHubConnection,
            GitConnection,
            EnvSecretRef,
            ResolvedSecret,
            Revisions,
            SecretResolver,
        ):
            with self.subTest(proto=proto.__name__):
                self.assertTrue(issubclass(proto, Protocol))
                # @runtime_checkable permite isinstance sem TypeError
                self.assertFalse(isinstance(object(), proto))

    def test_ut_m08_public_reexports(self) -> None:
        self.assertTrue(issubclass(ConfigLoadError, Exception))
        self.assertTrue(issubclass(SecretResolutionError, Exception))
        self.assertIs(ConfigLoader, ConfigLoader)
        self.assertIs(EnvironSecretResolver, EnvironSecretResolver)
        # Símbolos do schema exportados pelo pacote
        self.assertIs(schema_mod.AppConfig, AppConfig)
        self.assertIs(schema_mod.GitHubConnection, GitHubConnection)
        self.assertIs(schema_mod.GitConnection, GitConnection)


class TestSchemaPostLoadInvariants(unittest.TestCase):
    """UT-M02..M07 — invariantes após carga bem-sucedida."""

    def _load_valid(self) -> AppConfig:
        payload = {
            "connections": {
                "gh": github_connection(
                    orgs=["acme"],
                    repos=["acme/*"],
                    branches=["main", "develop"],
                ),
                "local": git_connection(
                    url="file:///C:/repos/my-org/*",
                    branches=["main"],
                ),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            return _assert_app_config(
                load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            )

    def test_ut_m02_instances_satisfy_protocols(self) -> None:
        result = self._load_valid()
        self.assertIsInstance(result, AppConfig)
        gh = result.connections["gh"]
        local = result.connections["local"]
        self.assertIsInstance(gh, GitHubConnection)
        self.assertIsInstance(local, GitConnection)
        self.assertEqual(gh.type, "github")
        self.assertEqual(local.type, "git")
        self.assertEqual(list(gh.orgs), ["acme"])
        self.assertEqual(list(gh.repos), ["acme/*"])
        self.assertIn("main", list(gh.revisions.branches))
        self.assertEqual(local.url, "file:///C:/repos/my-org/*")

    def test_ut_m03_resolved_secret_get_value(self) -> None:
        result = self._load_valid()
        gh = result.connections["gh"]
        assert isinstance(gh, GitHubConnection)
        secret = gh.secret
        self.assertIsInstance(secret, ResolvedSecret)
        value = secret.get_value()
        self.assertEqual(value, SECRET_TOKEN_VALUE)
        self.assertTrue(value.strip())

    def test_ut_m04_resolved_secret_redacted_str_repr(self) -> None:
        result = self._load_valid()
        gh = result.connections["gh"]
        assert isinstance(gh, GitHubConnection)
        secret = gh.secret
        self.assertNotIn(SECRET_TOKEN_VALUE, str(secret))
        self.assertNotIn(SECRET_TOKEN_VALUE, repr(secret))

    def test_ut_m05_appconfig_and_connection_redacted(self) -> None:
        result = self._load_valid()
        gh = result.connections["gh"]
        for target in (result, gh, result.connections):
            self.assertNotIn(SECRET_TOKEN_VALUE, str(target))
            self.assertNotIn(SECRET_TOKEN_VALUE, repr(target))

    def test_ut_m07_token_remains_env_secret_ref(self) -> None:
        result = self._load_valid()
        gh = result.connections["gh"]
        assert isinstance(gh, GitHubConnection)
        self.assertIsInstance(gh.token, EnvSecretRef)
        self.assertEqual(gh.token.env, TOKEN_ENV_NAME)
        self.assertNotIn(SECRET_TOKEN_VALUE, str(gh.token))
        self.assertNotIn(SECRET_TOKEN_VALUE, repr(gh.token))


class TestEmptyConnectionsSchema(unittest.TestCase):
    """connections {} → AppConfig com Mapping vazio tipado."""

    def test_empty_connections_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config({"connections": {}}, Path(tmp))
            result = _assert_app_config(load_with_environ(path, environ={}))
        self.assertIsInstance(result, AppConfig)
        self.assertEqual(len(result.connections), 0)
        self.assertEqual(dict(result.connections), {})
