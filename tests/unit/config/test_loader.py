"""
Testes unitários — ConfigLoader / ConfigLoadError (T02).

Cobre path None, arquivo vazio, JSON parcial, type desconhecido, orgs/repos,
token literal, env blank, file:// relativo/Windows, sem parcial, idempotência
e não-vazamento de segredo.

Pré-implementação: load permanece stub (...); casos comportamentais em red.

Execução:
    PYTHONPATH=src python3 -m pytest tests/unit/config/test_loader.py -q
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from github_rag.config import (
    AppConfig,
    ConfigLoadError,
    ConfigLoader,
    GitConnection,
    GitHubConnection,
)
from github_rag.config.secrets import SecretResolutionError

from .helpers import (
    SECRET_TOKEN_VALUE,
    TOKEN_ENV_NAME,
    git_connection,
    github_connection,
    load_with_environ,
    write_config,
    write_raw,
)


def _assert_app_config(result: object) -> Any:
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


def _assert_raises_load_error(call: Any) -> ConfigLoadError:
    try:
        result = call()
    except ConfigLoadError as exc:
        return exc
    if result is None or result is ...:
        raise AssertionError(
            "load retornou None/Ellipsis em vez de ConfigLoadError — "
            "stub sem implementação (red esperado)"
        )
    raise AssertionError(
        f"esperado ConfigLoadError, obteve retorno {type(result)!r}: {result!r}"
    )


class TestConfigLoadErrorContract(unittest.TestCase):
    """UT-M08 parcial — erro tipado."""

    def test_config_load_error_is_exception(self) -> None:
        self.assertTrue(issubclass(ConfigLoadError, Exception))
        err = ConfigLoadError("path missing")
        self.assertIsInstance(err, Exception)


class TestLoaderPathAndIo(unittest.TestCase):
    """UT-L01..L04, UT-L35 — path e I/O."""

    def test_ut_l01_path_none_raises(self) -> None:
        exc = _assert_raises_load_error(
            lambda: load_with_environ(None, environ={})
        )
        self.assertIsInstance(exc, ConfigLoadError)
        message = str(exc).lower()
        self.assertTrue(
            "path" in message or "config_path" in message or "ausente" in message
            or "missing" in message or "none" in message,
            msg=f"mensagem deveria indicar path ausente: {exc!s}",
        )

    def test_ut_l02_missing_file_raises(self) -> None:
        missing = Path(tempfile.gettempdir()) / "github-rag-no-such-config.json"
        if missing.exists():
            missing.unlink()
        exc = _assert_raises_load_error(
            lambda: load_with_environ(missing, environ={})
        )
        self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l03_empty_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_raw("", Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(path, environ={})
            )
        self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l04_malformed_json_raises_without_full_dump(self) -> None:
        poison = (
            "not-json-{{{UNIQUE_FULL_FILE_DUMP_MARKER_MUST_NOT_APPEAR_WHOLE"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = write_raw(poison, Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(path, environ={})
            )
        self.assertIsInstance(exc, ConfigLoadError)
        # CFG-07 / design §6: sem dump integral do arquivo na mensagem.
        self.assertNotIn(poison, str(exc))
        self.assertNotIn(poison, repr(exc))
        self.assertNotIn(SECRET_TOKEN_VALUE, str(exc))

    def test_ut_l35_unreadable_file_raises(self) -> None:
        if os.name == "nt":
            self.skipTest("chmod semântica POSIX; Windows fora deste extremo")
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config({"connections": {}}, Path(tmp))
            os.chmod(path, 0o000)
            try:
                exc = _assert_raises_load_error(
                    lambda: load_with_environ(path, environ={})
                )
                self.assertIsInstance(exc, ConfigLoadError)
            finally:
                os.chmod(path, 0o644)


class TestLoaderSchemaBasics(unittest.TestCase):
    """UT-L05..L09, UT-L27..L30 — schema raiz e extras."""

    def test_ut_l05_missing_connections_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config({"other": {}}, Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(path, environ={})
            )
        self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l06_connections_wrong_type(self) -> None:
        for bad in ([], "x", None, 1):
            with self.subTest(bad=bad):
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config({"connections": bad}, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(path, environ={})
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l07_empty_connections_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config({"connections": {}}, Path(tmp))
            result = _assert_app_config(load_with_environ(path, environ={}))
        self.assertEqual(dict(result.connections), {})

    def test_ut_l08_valid_github_and_git(self) -> None:
        payload = {
            "connections": {
                "github-microservices": github_connection(),
                "local-microservices": git_connection(),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            result = _assert_app_config(
                load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            )
        self.assertEqual(
            set(result.connections.keys()),
            {"github-microservices", "local-microservices"},
        )
        self.assertIsInstance(
            result.connections["github-microservices"], GitHubConnection
        )
        self.assertIsInstance(
            result.connections["local-microservices"], GitConnection
        )

    def test_ut_l09_unknown_type(self) -> None:
        for bad_type in ("gitlab", "bitbucket", "", "GITHUB"):
            with self.subTest(bad_type=bad_type):
                payload = {
                    "connections": {
                        "x": {
                            "type": bad_type,
                            "url": "file:///repos",
                            "revisions": {"branches": ["main"]},
                        }
                    }
                }
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(path, environ={})
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l09b_missing_type(self) -> None:
        payload = {
            "connections": {
                "x": {
                    "orgs": ["o"],
                    "repos": [],
                    "token": {"env": TOKEN_ENV_NAME},
                    "revisions": {"branches": ["main"]},
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            )
        self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l27_blank_connection_name(self) -> None:
        for name in ("", " ", "\t"):
            with self.subTest(name=repr(name)):
                payload = {"connections": {name: git_connection()}}
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(path, environ={})
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l28_partial_github_missing_required_fields(self) -> None:
        cases = [
            {"type": "github", "repos": [], "token": {"env": TOKEN_ENV_NAME},
             "revisions": {"branches": ["main"]}},  # sem orgs
            {"type": "github", "orgs": ["o"], "token": {"env": TOKEN_ENV_NAME},
             "revisions": {"branches": ["main"]}},  # sem repos
            {"type": "github", "orgs": ["o"], "repos": [],
             "token": {"env": TOKEN_ENV_NAME}},  # sem revisions
            {"type": "git", "revisions": {"branches": ["main"]}},  # sem url
        ]
        for partial in cases:
            with self.subTest(partial=partial):
                payload = {"connections": {"c": partial}}
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(
                            path,
                            environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE},
                        )
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l29_top_level_extra_keys_ignored(self) -> None:
        payload = {
            "$schema": "https://example.com/schema.json",
            "version": 1,
            "connections": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            result = _assert_app_config(load_with_environ(path, environ={}))
        self.assertEqual(dict(result.connections), {})

    def test_ut_l30_unknown_connection_fields_ignored(self) -> None:
        payload = {
            "connections": {
                "gh": github_connection(extra={"ignoredField": 123}),
                "local": git_connection(extra={"alsoIgnored": True}),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            result = _assert_app_config(
                load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            )
        self.assertIn("gh", result.connections)
        self.assertIn("local", result.connections)


class TestLoaderGithubFields(unittest.TestCase):
    """UT-L10..L19 — orgs, repos, token, env."""

    def test_ut_l10_empty_orgs_rejected(self) -> None:
        payload = {
            "connections": {"gh": github_connection(orgs=[])}
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            )
        self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l11_blank_org_item_rejected(self) -> None:
        for item in ("", " ", "\t"):
            with self.subTest(item=repr(item)):
                payload = {
                    "connections": {"gh": github_connection(orgs=[item])}
                }
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(
                            path,
                            environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE},
                        )
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l12_empty_repos_allowed(self) -> None:
        payload = {
            "connections": {"gh": github_connection(repos=[])}
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            result = _assert_app_config(
                load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            )
        self.assertEqual(list(result.connections["gh"].repos), [])

    def test_ut_l13_blank_repo_item_rejected(self) -> None:
        payload = {
            "connections": {"gh": github_connection(repos=[""])}
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            )
        self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l14_repos_wildcards_preserved(self) -> None:
        wildcards = ["my-org/microservice-*", "my-org/*-api", "*"]
        payload = {
            "connections": {"gh": github_connection(repos=wildcards)}
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            result = _assert_app_config(
                load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            )
        self.assertEqual(list(result.connections["gh"].repos), wildcards)

    def test_ut_l15_literal_token_rejected(self) -> None:
        payload = {
            "connections": {
                "gh": github_connection(token="ghp_literal_token_value")
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(path, environ={})
            )
        self.assertIsInstance(exc, ConfigLoadError)
        self.assertNotIn("ghp_literal_token_value", str(exc))

    def test_ut_l16_blank_token_env_name_rejected(self) -> None:
        for blank in ("", " ", "\t"):
            with self.subTest(blank=repr(blank)):
                payload = {
                    "connections": {
                        "gh": github_connection(token={"env": blank})
                    }
                }
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(
                            path,
                            environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE},
                        )
                    )
                self.assertIsInstance(exc, ConfigLoadError)
                self.assertNotIn(SECRET_TOKEN_VALUE, str(exc))

    def test_ut_l17_invalid_token_shapes(self) -> None:
        for token in (None, [], {}, {"ENV": TOKEN_ENV_NAME}, {"env": 1}):
            with self.subTest(token=token):
                payload = {
                    "connections": {"gh": github_connection(token=token)}
                }
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(
                            path,
                            environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE},
                        )
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l18_missing_token_env(self) -> None:
        payload = {"connections": {"gh": github_connection()}}
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(path, environ={})
            )
        self.assertIsInstance(exc, ConfigLoadError)
        self.assertIn(TOKEN_ENV_NAME, str(exc))
        self.assertNotIn(SECRET_TOKEN_VALUE, str(exc))

    def test_ut_l19_blank_token_env_value(self) -> None:
        for blank in ("", " ", "\t", "\n"):
            with self.subTest(blank=repr(blank)):
                payload = {"connections": {"gh": github_connection()}}
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(
                            path, environ={TOKEN_ENV_NAME: blank}
                        )
                    )
                self.assertIsInstance(exc, ConfigLoadError)
                self.assertIn(TOKEN_ENV_NAME, str(exc))


class TestLoaderRevisionsAndUrls(unittest.TestCase):
    """UT-L20..L25 — branches e file://."""

    def test_ut_l20_branches_without_main(self) -> None:
        payload = {
            "connections": {
                "gh": github_connection(branches=["develop"]),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            )
        self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l21_empty_branches(self) -> None:
        payload = {
            "connections": {"local": git_connection(branches=[])}
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(path, environ={})
            )
        self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l21b_blank_branch_items_rejected(self) -> None:
        for branches in ([""], [" "], ["\t"], ["main", ""], ["main", " "]):
            with self.subTest(branches=branches):
                payload = {
                    "connections": {
                        "gh": github_connection(branches=branches),
                    }
                }
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(
                            path,
                            environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE},
                        )
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l22_relative_file_urls_rejected(self) -> None:
        for url in ("file://repos", "file://./repos", "file://repos/*"):
            with self.subTest(url=url):
                payload = {
                    "connections": {"local": git_connection(url=url)}
                }
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(path, environ={})
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l22b_empty_or_case_invalid_file_url_rejected(self) -> None:
        # design §4.4: path vazio; prefixo file:// case-sensitive.
        for url in ("file://", "FILE:///repos/*", "File:///repos/*"):
            with self.subTest(url=url):
                payload = {
                    "connections": {"local": git_connection(url=url)}
                }
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(path, environ={})
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l23_non_file_scheme_rejected(self) -> None:
        for url in (
            "https://example.com/repo.git",
            "http://example.com/repo.git",
            "git@github.com:org/repo.git",
            "/absolute/path",
            "",
        ):
            with self.subTest(url=url):
                payload = {
                    "connections": {"local": git_connection(url=url)}
                }
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(path, environ={})
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l24_posix_absolute_file_url(self) -> None:
        payload = {
            "connections": {
                "posix": git_connection(url="file:///repos/*"),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            result = _assert_app_config(load_with_environ(path, environ={}))
        conn = result.connections["posix"]
        self.assertIsInstance(conn, GitConnection)
        self.assertEqual(conn.url, "file:///repos/*")

    def test_ut_l25_windows_absolute_file_url(self) -> None:
        payload = {
            "connections": {
                "windows": git_connection(url="file:///C:/repos/*"),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            result = _assert_app_config(load_with_environ(path, environ={}))
        conn = result.connections["windows"]
        self.assertIsInstance(conn, GitConnection)
        self.assertEqual(conn.url, "file:///C:/repos/*")


class TestLoaderPartialAndInjection(unittest.TestCase):
    """UT-L26, UT-L31..L34 — BR-021, injeção, fronteira T01, idempotência."""

    def test_ut_l26_no_partial_config_on_one_invalid(self) -> None:
        payload = {
            "connections": {
                "good": github_connection(),
                "bad": {
                    "type": "unknown",
                    "revisions": {"branches": ["main"]},
                },
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            try:
                result = load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            except ConfigLoadError as exc:
                self.assertIsInstance(exc, ConfigLoadError)
                # Mesmo se a conexão válida já tiver sido resolvida na
                # validação, a mensagem não pode vazar o token (CFG-13).
                self.assertNotIn(SECRET_TOKEN_VALUE, str(exc))
                self.assertNotIn(SECRET_TOKEN_VALUE, repr(exc))
                return
            if result is None or result is ...:
                raise AssertionError(
                    "load retornou None/Ellipsis em vez de ConfigLoadError — red"
                )
            raise AssertionError(
                "não deve retornar AppConfig (parcial ou completo) com conexão inválida"
            )

    def test_ut_l28b_wrong_types_for_list_fields(self) -> None:
        cases = [
            github_connection(orgs="not-a-list"),  # type: ignore[arg-type]
            github_connection(repos="not-a-list"),  # type: ignore[arg-type]
            github_connection(branches="main"),  # type: ignore[arg-type]
            {
                "type": "github",
                "orgs": None,
                "repos": [],
                "token": {"env": TOKEN_ENV_NAME},
                "revisions": {"branches": ["main"]},
            },
            {
                "type": "git",
                "url": "file:///repos",
                "revisions": None,
            },
            {
                "type": "git",
                "url": "file:///repos",
                "revisions": {"branches": None},
            },
        ]
        for partial in cases:
            with self.subTest(partial=partial):
                payload = {"connections": {"c": partial}}
                with tempfile.TemporaryDirectory() as tmp:
                    path = write_config(payload, Path(tmp))
                    exc = _assert_raises_load_error(
                        lambda: load_with_environ(
                            path,
                            environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE},
                        )
                    )
                self.assertIsInstance(exc, ConfigLoadError)

    def test_ut_l31_injected_secret_resolver(self) -> None:
        class FakeResolver:
            def resolve(self, env_name: str) -> str:
                if env_name != TOKEN_ENV_NAME:
                    raise SecretResolutionError(f"{env_name}: missing")
                return SECRET_TOKEN_VALUE

        payload = {"connections": {"gh": github_connection()}}
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            loader = ConfigLoader(secret_resolver=FakeResolver())
            # Sem GITHUB_TOKEN no processo — deve usar injeção.
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop(TOKEN_ENV_NAME, None)
                result = _assert_app_config(loader.load(path))
        self.assertIn("gh", result.connections)

    def test_ut_l32_does_not_reread_config_path_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good = write_config({"connections": {}}, Path(tmp))
            other = write_raw(
                '{"connections": {"trap": {"type": "gitlab"}}}',
                Path(tmp),
                name="other.json",
            )
            with mock.patch.dict(
                os.environ, {"CONFIG_PATH": str(other)}, clear=False
            ):
                result = _assert_app_config(
                    ConfigLoader().load(good)
                )
        self.assertEqual(dict(result.connections), {})

    def test_ut_l33_secret_resolution_error_translated(self) -> None:
        class FailingResolver:
            def resolve(self, env_name: str) -> str:
                raise SecretResolutionError(f"{env_name}: missing")

        payload = {"connections": {"gh": github_connection()}}
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            loader = ConfigLoader(secret_resolver=FailingResolver())
            try:
                result = loader.load(path)
            except ConfigLoadError as exc:
                self.assertNotIsInstance(exc, SecretResolutionError)
                self.assertIn(TOKEN_ENV_NAME, str(exc))
                self.assertNotIn(SECRET_TOKEN_VALUE, str(exc))
                return
            except SecretResolutionError:
                raise AssertionError(
                    "SecretResolutionError deve ser traduzido para ConfigLoadError"
                ) from None
            if result is None or result is ...:
                raise AssertionError(
                    "load retornou None/Ellipsis — stub; red esperado"
                )
            raise AssertionError(
                f"esperado ConfigLoadError, obteve {type(result)!r}"
            )

    def test_ut_l34_load_idempotent(self) -> None:
        payload = {
            "connections": {
                "gh": github_connection(repos=[]),
                "local": git_connection(url="file:///repos"),
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            raw_before = path.read_text(encoding="utf-8")
            env = {TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
            first = _assert_app_config(load_with_environ(path, environ=env))
            second = _assert_app_config(load_with_environ(path, environ=env))
            raw_after = path.read_text(encoding="utf-8")
        self.assertEqual(raw_before, raw_after)
        self.assertEqual(set(first.connections.keys()), set(second.connections.keys()))
        self.assertEqual(
            list(first.connections["gh"].repos),
            list(second.connections["gh"].repos),
        )


class TestLoaderSecretNotInErrors(unittest.TestCase):
    """UT-M06 / CFG-13 — valor ausente em mensagens de erro do loader."""

    def test_secret_not_in_config_load_error_on_schema_failure(self) -> None:
        payload = {
            "connections": {
                "bad": {
                    "type": "unknown",
                    "token": {"env": TOKEN_ENV_NAME},
                    "orgs": ["o"],
                    "repos": [],
                    "revisions": {"branches": ["main"]},
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(payload, Path(tmp))
            exc = _assert_raises_load_error(
                lambda: load_with_environ(
                    path, environ={TOKEN_ENV_NAME: SECRET_TOKEN_VALUE}
                )
            )
        self.assertNotIn(SECRET_TOKEN_VALUE, str(exc))
        self.assertNotIn(SECRET_TOKEN_VALUE, repr(exc))
