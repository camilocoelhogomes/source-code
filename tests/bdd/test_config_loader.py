"""
BDD executável — T02-config-loader.

Valida BDD-021 (parcial), BDD-022 e BDD-014 (parcial) conforme design 0.2.0.
Os cenários devem falhar enquanto github_rag.config não exportar o loader.

Superfície esperada (refinada no gate interfaces):
    from github_rag.config import (
        AppConfig, ConfigLoadError, ConfigLoader, GitConnection, GitHubConnection,
    )
    ConfigLoader().load(path: Path | None) -> AppConfig

Segredos: SecretResolver default lê o ambiente do processo; estes BDD usam
patch.dict(os.environ) sem prescrever assinatura de injeção no ConfigLoader.

Execução:
    python -m pytest tests/bdd/test_config_loader.py -q
    PYTHONPATH=src python3 -m unittest discover -s tests/bdd -p "test_config_loader.py" -v
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from unittest import mock

SECRET_TOKEN_VALUE = "super-secret-token-value-do-not-leak"
TOKEN_ENV_NAME = "GITHUB_TOKEN"


def _import_config_surface() -> tuple[Any, Any, Any, Any, Any]:
    """Importa símbolos esperados de github_rag.config (red até implementação)."""
    from github_rag.config import (  # noqa: PLC0415 — import tardio para mensagem clara
        AppConfig,
        ConfigLoadError,
        ConfigLoader,
        GitConnection,
        GitHubConnection,
    )

    return AppConfig, ConfigLoadError, ConfigLoader, GitConnection, GitHubConnection


def _write_config(payload: dict[str, Any], directory: Path) -> Path:
    path = directory / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _github_connection(
    *,
    orgs: list[str] | None = None,
    repos: list[str] | None = None,
    branches: list[str] | None = None,
    token_env: str = TOKEN_ENV_NAME,
) -> dict[str, Any]:
    return {
        "type": "github",
        "token": {"env": token_env},
        "orgs": orgs if orgs is not None else ["my-org"],
        "repos": (
            repos
            if repos is not None
            else ["my-org/microservice-*", "my-org/*-api"]
        ),
        "revisions": {"branches": branches if branches is not None else ["main"]},
    }


def _git_connection(
    *,
    url: str = "file:///repos/*",
    branches: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "git",
        "url": url,
        "revisions": {"branches": branches if branches is not None else ["main"]},
    }


def _load(
    path: Path | None,
    *,
    environ: Mapping[str, str] | None = None,
) -> Any:
    """Carrega via ConfigLoader().load(path); controla env via patch.dict."""
    _, _, ConfigLoader, _, _ = _import_config_surface()
    loader = ConfigLoader()
    env_map = dict(environ) if environ is not None else {}
    with mock.patch.dict(os.environ, env_map, clear=False):
        if TOKEN_ENV_NAME not in env_map:
            os.environ.pop(TOKEN_ENV_NAME, None)
        return loader.load(path)


class TestCFG01ValidGithubAndGitConnections(unittest.TestCase):
    """CFG-01 — BDD-021 parcial: JSON válido → AppConfig tipado completo."""

    def test_loads_named_github_and_git_connections(self) -> None:
        AppConfig, _, _, GitConnection, GitHubConnection = _import_config_surface()
        payload = {
            "connections": {
                "github-microservices": _github_connection(),
                "local-microservices": _git_connection(),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            result = _load(path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE})

        self.assertIsInstance(result, AppConfig)
        self.assertEqual(
            set(result.connections.keys()),
            {"github-microservices", "local-microservices"},
        )
        github = result.connections["github-microservices"]
        local = result.connections["local-microservices"]
        self.assertIsInstance(github, GitHubConnection)
        self.assertIsInstance(local, GitConnection)
        self.assertEqual(github.type, "github")
        self.assertEqual(list(github.orgs), ["my-org"])
        self.assertEqual(
            list(github.repos),
            ["my-org/microservice-*", "my-org/*-api"],
        )
        self.assertIn("main", list(github.revisions.branches))
        self.assertEqual(local.type, "git")
        self.assertEqual(local.url, "file:///repos/*")
        self.assertIn("main", list(local.revisions.branches))


class TestCFG02EmptyConnections(unittest.TestCase):
    """CFG-02 — connections {} é válido."""

    def test_empty_connections_object_is_valid(self) -> None:
        AppConfig, _, _, _, _ = _import_config_surface()
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config({"connections": {}}, Path(tmp))
            result = _load(path, environ={})

        self.assertIsInstance(result, AppConfig)
        self.assertEqual(dict(result.connections), {})


class TestCFG03ReposWildcardsFormOnly(unittest.TestCase):
    """CFG-03 — wildcards de inclusão preservados (sem expansão)."""

    def test_inclusion_wildcards_preserved_without_expansion(self) -> None:
        _, _, _, _, GitHubConnection = _import_config_surface()
        wildcards = ["my-org/microservice-*", "my-org/*-api"]
        payload = {
            "connections": {
                "gh": _github_connection(repos=wildcards),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            result = _load(path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE})

        github = result.connections["gh"]
        self.assertIsInstance(github, GitHubConnection)
        self.assertEqual(list(github.repos), wildcards)


class TestCFG04FileUrlAbsolutePosixAndWindows(unittest.TestCase):
    """CFG-04 — file:// absoluto POSIX e Windows (forma apenas)."""

    def test_absolute_file_urls_posix_and_windows_accepted(self) -> None:
        _, _, _, GitConnection, _ = _import_config_surface()
        payload = {
            "connections": {
                "posix": _git_connection(url="file:///repos/*"),
                "windows": _git_connection(url="file:///C:/repos/*"),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            result = _load(path, environ={})

        self.assertIsInstance(result.connections["posix"], GitConnection)
        self.assertIsInstance(result.connections["windows"], GitConnection)
        self.assertEqual(result.connections["posix"].url, "file:///repos/*")
        self.assertEqual(result.connections["windows"].url, "file:///C:/repos/*")


class TestCFG05PathNone(unittest.TestCase):
    """CFG-05 — path None → ConfigLoadError (BDD-022)."""

    def test_none_path_raises_config_load_error(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        with self.assertRaises(ConfigLoadError) as ctx:
            _load(None, environ={})
        self.assertIsInstance(ctx.exception, ConfigLoadError)


class TestCFG06PathMissing(unittest.TestCase):
    """CFG-06 — path inexistente → ConfigLoadError (BDD-022)."""

    def test_missing_file_raises_config_load_error(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        missing = Path(tempfile.gettempdir()) / "github-rag-missing-config-xyz.json"
        if missing.exists():
            missing.unlink()
        with self.assertRaises(ConfigLoadError):
            _load(missing, environ={})


class TestCFG07InvalidJson(unittest.TestCase):
    """CFG-07 — JSON malformado → ConfigLoadError (BDD-022)."""

    def test_malformed_json_raises_config_load_error(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(ConfigLoadError):
                _load(path, environ={})


class TestCFG08InvalidSchemaAndType(unittest.TestCase):
    """CFG-08 — schema/type inválidos → ConfigLoadError (BDD-022)."""

    def test_missing_connections_key_raises(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config({"other": {}}, Path(tmp))
            with self.assertRaises(ConfigLoadError):
                _load(path, environ={})

    def test_unknown_connection_type_raises(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        payload = {
            "connections": {
                "weird": {
                    "type": "bitbucket",
                    "revisions": {"branches": ["main"]},
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            with self.assertRaises(ConfigLoadError):
                _load(path, environ={})


class TestCFG09MissingTokenEnv(unittest.TestCase):
    """CFG-09 — env do token ausente/blank → ConfigLoadError (BDD-022)."""

    def test_missing_token_env_raises_citing_env_name(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        payload = {"connections": {"gh": _github_connection()}}
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            with self.assertRaises(ConfigLoadError) as ctx:
                _load(path, environ={})
        message = str(ctx.exception)
        self.assertIn(TOKEN_ENV_NAME, message)

    def test_blank_token_env_raises_citing_env_name(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        payload = {"connections": {"gh": _github_connection()}}
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            with self.assertRaises(ConfigLoadError) as ctx:
                _load(path, environ={TOKEN_ENV_NAME: "   "})
        message = str(ctx.exception)
        self.assertIn(TOKEN_ENV_NAME, message)
        self.assertNotIn(SECRET_TOKEN_VALUE, message)


class TestCFG10NoPartialConfig(unittest.TestCase):
    """CFG-10 — falha em uma conexão → zero AppConfig (BR-021 / BDD-022)."""

    def test_one_invalid_connection_rejects_entire_config(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        payload = {
            "connections": {
                "good": _github_connection(),
                "bad": {
                    "type": "svn",
                    "revisions": {"branches": ["main"]},
                },
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            with self.assertRaises(ConfigLoadError):
                _load(path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE})


class TestCFG11RejectRelativeOrNonFileUrl(unittest.TestCase):
    """CFG-11 — file:// relativo / não-file rejeitados (BDD-022 / §4.4)."""

    def test_relative_file_url_rejected(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        payload = {
            "connections": {"local": _git_connection(url="file://repos")}
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            with self.assertRaises(ConfigLoadError):
                _load(path, environ={})

    def test_non_file_scheme_rejected(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        payload = {
            "connections": {
                "remote": _git_connection(url="https://example.com/repo.git")
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            with self.assertRaises(ConfigLoadError):
                _load(path, environ={})


class TestCFG12BranchesRequireMain(unittest.TestCase):
    """CFG-12 — branches sem main → ConfigLoadError (ENG-T02-001)."""

    def test_branches_without_main_rejected(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        payload = {
            "connections": {
                "gh": _github_connection(branches=["develop"]),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            with self.assertRaises(ConfigLoadError):
                _load(path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE})


class TestCFG13SecretNotInErrorMessage(unittest.TestCase):
    """CFG-13 — BDD-014 parcial: token ausente de str(exc)."""

    def test_secret_value_absent_from_config_load_error(self) -> None:
        _, ConfigLoadError, _, _, _ = _import_config_surface()
        payload = {
            "connections": {
                "gh": _github_connection(),
                "bad": {"type": "unknown", "revisions": {"branches": ["main"]}},
            }
        }
        environ = {TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            with self.assertRaises(ConfigLoadError) as ctx:
                _load(path, environ=environ)
        message = str(ctx.exception)
        self.assertNotIn(SECRET_TOKEN_VALUE, message)


class TestCFG14SecretNotInModelString(unittest.TestCase):
    """CFG-14 — BDD-014 parcial: token ausente de str/repr do modelo."""

    def test_secret_value_absent_from_appconfig_str_and_repr(self) -> None:
        AppConfig, _, _, _, GitHubConnection = _import_config_surface()
        payload = {
            "connections": {
                "github-microservices": _github_connection(),
                "local-microservices": _git_connection(),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(payload, Path(tmp))
            result = _load(path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE})

        self.assertIsInstance(result, AppConfig)
        self.assertNotIn(SECRET_TOKEN_VALUE, str(result))
        self.assertNotIn(SECRET_TOKEN_VALUE, repr(result))
        github = result.connections["github-microservices"]
        self.assertIsInstance(github, GitHubConnection)
        self.assertNotIn(SECRET_TOKEN_VALUE, str(github))
        self.assertNotIn(SECRET_TOKEN_VALUE, repr(github))


if __name__ == "__main__":
    unittest.main()
