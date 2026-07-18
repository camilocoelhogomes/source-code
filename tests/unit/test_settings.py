"""
Testes unitários — contratos T01 settings (AppSettings / load_settings).

Cobre defaults, blank, conversões, erros, paths nativos (Windows/POSIX),
environ injetado vs os.environ, e ausência de domínio.

Pré-implementação: load_settings permanece stub (...); casos de carga tipada
devem falhar (red) pela ausência de implementação.

Execução (stdlib, src layout):
    PYTHONPATH=src python3 -m unittest discover -s tests/unit -p "test_*.py" -v
"""

from __future__ import annotations

import ast
import os
import re
import unittest
from pathlib import Path
from unittest import mock

from github_rag.settings import (
    DEFAULT_INDEX_WORKERS,
    DEFAULT_QUERY_WORKERS,
    ENV_CONFIG_PATH,
    ENV_INDEX_WORKERS,
    ENV_QUERY_WORKERS,
    AppSettings,
    SettingsBootstrapError,
    load_settings,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_SOURCE = REPO_ROOT / "src" / "github_rag" / "settings.py"

SHELL_JARGON = (
    "Activate.ps1",
    "activate.bat",
    "bin/activate",
    "Scripts\\",
    "Scripts/",
    "PowerShell",
    "powershell",
    " cmd",
    "bash",
    "source ",
)

DOMAIN_FORBIDDEN = (
    re.compile(r"json\.loads", re.I),
    re.compile(r"sourcebot", re.I),
    re.compile(r"psycopg|sqlalchemy|asyncpg|create_engine", re.I),
    re.compile(r"SecretResolver|GITHUB_TOKEN|resolve_secret", re.I),
)


def _assert_app_settings(result: object) -> AppSettings:
    """Garante snapshot tipado compatível com AppSettings."""
    if result is None:
        raise AssertionError(
            "load_settings retornou None — stub sem implementação "
            "(esperado red até Developer implementar o corpo)"
        )
    if not isinstance(result, AppSettings):
        raise AssertionError(
            f"retorno {type(result)!r} não satisfaz AppSettings Protocol"
        )
    return result


class TestContractConstants(unittest.TestCase):
    """UT-01, UT-02, UT-21 — superfície estática do contrato."""

    def test_ut01_env_name_constants(self) -> None:
        self.assertEqual(ENV_INDEX_WORKERS, "INDEX_WORKERS")
        self.assertEqual(ENV_QUERY_WORKERS, "QUERY_WORKERS")
        self.assertEqual(ENV_CONFIG_PATH, "CONFIG_PATH")

    def test_ut02_default_literals(self) -> None:
        self.assertEqual(DEFAULT_INDEX_WORKERS, 2)
        self.assertEqual(DEFAULT_QUERY_WORKERS, 4)
        self.assertIsInstance(DEFAULT_INDEX_WORKERS, int)
        self.assertIsInstance(DEFAULT_QUERY_WORKERS, int)

    def test_ut21_settings_bootstrap_error_is_exception(self) -> None:
        self.assertTrue(issubclass(SettingsBootstrapError, Exception))
        err = SettingsBootstrapError("INDEX_WORKERS: invalid literal")
        self.assertIsInstance(err, Exception)
        self.assertIn("INDEX_WORKERS", str(err))


class TestLoadSettingsDefaults(unittest.TestCase):
    """UT-03..UT-06 — defaults e blank."""

    def test_ut03_empty_mapping_uses_defaults(self) -> None:
        result = _assert_app_settings(load_settings({}))
        self.assertEqual(result.index_workers, 2)
        self.assertEqual(result.query_workers, 4)
        self.assertIsNone(result.config_path)

    def test_ut04_missing_keys_use_defaults(self) -> None:
        result = _assert_app_settings(
            load_settings({"OTHER": "1", "UNRELATED": "x"})
        )
        self.assertEqual(result.index_workers, DEFAULT_INDEX_WORKERS)
        self.assertEqual(result.query_workers, DEFAULT_QUERY_WORKERS)
        self.assertIsNone(result.config_path)

    def test_ut05_whitespace_only_workers_use_defaults(self) -> None:
        for blank in ("", " ", "  ", "\t", "\n", " \t\n "):
            with self.subTest(blank=repr(blank)):
                result = _assert_app_settings(
                    load_settings(
                        {
                            ENV_INDEX_WORKERS: blank,
                            ENV_QUERY_WORKERS: blank,
                        }
                    )
                )
                self.assertEqual(result.index_workers, 2)
                self.assertEqual(result.query_workers, 4)

    def test_ut06_whitespace_only_config_path_is_none(self) -> None:
        for blank in ("", " ", "\t", "\n", "  \t  "):
            with self.subTest(blank=repr(blank)):
                result = _assert_app_settings(
                    load_settings({ENV_CONFIG_PATH: blank})
                )
                self.assertIsNone(result.config_path)


class TestLoadSettingsValidInts(unittest.TestCase):
    """UT-07, UT-08 — conversão int válida."""

    def test_ut07_valid_integer_strings(self) -> None:
        result = _assert_app_settings(
            load_settings(
                {
                    ENV_INDEX_WORKERS: "8",
                    ENV_QUERY_WORKERS: "16",
                }
            )
        )
        self.assertEqual(result.index_workers, 8)
        self.assertEqual(result.query_workers, 16)
        self.assertIsInstance(result.index_workers, int)
        self.assertIsInstance(result.query_workers, int)

    def test_ut08_valid_ints_with_surrounding_whitespace(self) -> None:
        result = _assert_app_settings(
            load_settings(
                {
                    ENV_INDEX_WORKERS: " 3 ",
                    ENV_QUERY_WORKERS: "\t12\n",
                }
            )
        )
        self.assertEqual(result.index_workers, 3)
        self.assertEqual(result.query_workers, 12)

    def test_ut07_zero_and_negative_accepted_without_minmax(self) -> None:
        """T01 não aplica min/max (I-T01-008) — conversão int pura."""
        result = _assert_app_settings(
            load_settings(
                {
                    ENV_INDEX_WORKERS: "0",
                    ENV_QUERY_WORKERS: "-1",
                }
            )
        )
        self.assertEqual(result.index_workers, 0)
        self.assertEqual(result.query_workers, -1)


class TestLoadSettingsInvalidInts(unittest.TestCase):
    """UT-09..UT-11 — SettingsBootstrapError sem fallback."""

    def test_ut09_invalid_index_workers_raises(self) -> None:
        for bad in ("abc", "2.5", "1e2", "two", "8x"):
            with self.subTest(bad=bad):
                with self.assertRaises(SettingsBootstrapError) as ctx:
                    load_settings({ENV_INDEX_WORKERS: bad})
                message = str(ctx.exception)
                self.assertIn(ENV_INDEX_WORKERS, message)
                # Sem fallback silencioso: não devolver defaults
                self.assertNotIsInstance(ctx.exception, type(None))

    def test_ut09_invalid_index_does_not_return_default_snapshot(self) -> None:
        try:
            outcome = load_settings({ENV_INDEX_WORKERS: "not-an-int"})
        except SettingsBootstrapError:
            return
        self.fail(
            f"esperado SettingsBootstrapError; obtido {outcome!r} "
            "(fallback silencioso ou stub incompleto)"
        )

    def test_ut10_invalid_query_workers_raises(self) -> None:
        for bad in ("xyz", "4.0", "NaN"):
            with self.subTest(bad=bad):
                with self.assertRaises(SettingsBootstrapError) as ctx:
                    load_settings({ENV_QUERY_WORKERS: bad})
                self.assertIn(ENV_QUERY_WORKERS, str(ctx.exception))

    def test_ut11_error_message_has_no_shell_jargon(self) -> None:
        with self.assertRaises(SettingsBootstrapError) as ctx:
            load_settings({ENV_INDEX_WORKERS: "bad"})
        message = str(ctx.exception)
        for jargon in SHELL_JARGON:
            with self.subTest(jargon=jargon):
                self.assertNotIn(jargon, message)


class TestLoadSettingsConfigPath(unittest.TestCase):
    """UT-12..UT-14 — CONFIG_PATH via pathlib (Windows + POSIX)."""

    def test_ut12_posix_path_string(self) -> None:
        raw = "/etc/app/config.json"
        result = _assert_app_settings(load_settings({ENV_CONFIG_PATH: raw}))
        self.assertIsInstance(result.config_path, Path)
        self.assertEqual(result.config_path, Path(raw))

    def test_ut13_windows_drive_path_string(self) -> None:
        raw = r"C:\Users\dev\config.json"
        result = _assert_app_settings(load_settings({ENV_CONFIG_PATH: raw}))
        self.assertIsInstance(result.config_path, Path)
        self.assertEqual(result.config_path, Path(raw))

    def test_ut14_windows_unc_path_string(self) -> None:
        raw = r"\\server\share\config.json"
        result = _assert_app_settings(load_settings({ENV_CONFIG_PATH: raw}))
        self.assertIsInstance(result.config_path, Path)
        self.assertEqual(result.config_path, Path(raw))

    def test_config_path_does_not_require_file_to_exist(self) -> None:
        raw = "/nonexistent/path/that/should/not/be/opened.json"
        result = _assert_app_settings(load_settings({ENV_CONFIG_PATH: raw}))
        self.assertEqual(result.config_path, Path(raw))
        self.assertFalse(Path(raw).exists())


class TestLoadSettingsEnvironInjection(unittest.TestCase):
    """UT-15..UT-17 — environ injetado vs os.environ; imutabilidade."""

    def test_ut15_injected_environ_ignores_os_environ(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                ENV_INDEX_WORKERS: "99",
                ENV_QUERY_WORKERS: "88",
                ENV_CONFIG_PATH: "/from/os/environ.json",
            },
            clear=False,
        ):
            result = _assert_app_settings(
                load_settings(
                    {
                        ENV_INDEX_WORKERS: "5",
                        ENV_QUERY_WORKERS: "7",
                    }
                )
            )
            self.assertEqual(result.index_workers, 5)
            self.assertEqual(result.query_workers, 7)
            self.assertIsNone(result.config_path)

    def test_ut16_none_uses_process_environ(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ[ENV_INDEX_WORKERS] = "11"
            os.environ[ENV_QUERY_WORKERS] = "13"
            os.environ[ENV_CONFIG_PATH] = "/proc/env/config.json"
            result = _assert_app_settings(load_settings(None))
            self.assertEqual(result.index_workers, 11)
            self.assertEqual(result.query_workers, 13)
            self.assertEqual(result.config_path, Path("/proc/env/config.json"))

    def test_ut16_none_defaults_when_process_env_empty(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = _assert_app_settings(load_settings(None))
            self.assertEqual(result.index_workers, 2)
            self.assertEqual(result.query_workers, 4)
            self.assertIsNone(result.config_path)

    def test_ut17_does_not_mutate_injected_mapping(self) -> None:
        environ = {
            ENV_INDEX_WORKERS: "4",
            ENV_QUERY_WORKERS: "6",
            ENV_CONFIG_PATH: "/tmp/cfg.json",
        }
        snapshot = dict(environ)
        _ = load_settings(environ)
        self.assertEqual(environ, snapshot)


class TestLoadSettingsProtocolAndOsAgnostic(unittest.TestCase):
    """UT-18, UT-22 — Protocol e semântica OS-agnostic."""

    def test_ut18_return_satisfies_app_settings_protocol(self) -> None:
        result = _assert_app_settings(
            load_settings(
                {
                    ENV_INDEX_WORKERS: "2",
                    ENV_QUERY_WORKERS: "4",
                }
            )
        )
        self.assertIsInstance(result, AppSettings)
        self.assertIsInstance(result.index_workers, int)
        self.assertIsInstance(result.query_workers, int)
        self.assertTrue(
            result.config_path is None or isinstance(result.config_path, Path)
        )

    def test_ut22_same_semantics_regardless_of_os_name(self) -> None:
        environ = {
            ENV_INDEX_WORKERS: "9",
            ENV_QUERY_WORKERS: "3",
            ENV_CONFIG_PATH: "relative/config.json",
        }
        results = []
        for fake_os in ("posix", "nt"):
            with mock.patch("os.name", fake_os):
                results.append(_assert_app_settings(load_settings(environ)))
        self.assertEqual(results[0].index_workers, results[1].index_workers)
        self.assertEqual(results[0].query_workers, results[1].query_workers)
        self.assertEqual(results[0].config_path, results[1].config_path)
        self.assertEqual(results[0].index_workers, 9)
        self.assertEqual(results[0].query_workers, 3)
        self.assertEqual(results[0].config_path, Path("relative/config.json"))


class TestNoDomainAndPathlib(unittest.TestCase):
    """UT-19, UT-20 — sem domínio; pathlib sem hardcode de separadores."""

    def test_ut19_module_has_no_domain_logic(self) -> None:
        source = SETTINGS_SOURCE.read_text(encoding="utf-8")
        for pattern in DOMAIN_FORBIDDEN:
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNone(
                    pattern.search(source),
                    f"padrão de domínio proibido encontrado: {pattern.pattern}",
                )

    def test_ut19_load_settings_does_not_open_config_file(self) -> None:
        raw = "/tmp/github_rag_unit_test_should_not_open.json"
        path = Path(raw)
        if path.exists():
            path.unlink()
        # Mesmo se a implementação existir, não deve criar/abrir o arquivo.
        try:
            load_settings({ENV_CONFIG_PATH: raw})
        except SettingsBootstrapError:
            self.fail("CONFIG_PATH não deve falhar por tipagem de path")
        except Exception:
            # Stub / NotImplemented — aceitável em red; arquivo ainda não deve existir
            pass
        self.assertFalse(
            path.exists(),
            "load_settings não deve criar nem exigir o arquivo de CONFIG_PATH",
        )

    def test_ut20_settings_uses_pathlib_without_separator_hardcode(self) -> None:
        source = SETTINGS_SOURCE.read_text(encoding="utf-8")
        self.assertIn("pathlib", source)
        self.assertIn("Path", source)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = node.value
                # Literais de documentação/docstring podem citar \\ ; bloquear
                # apenas construções de path com separador único hardcoded em
                # expressões (não em docstrings de módulo já longas).
                if node.col_offset == 0:
                    continue
            if isinstance(node, ast.JoinedStr):
                continue
        # Proibição de hardcode operacional: nenhum join manual com "\\" ou "/"
        # como separador de path na lógica (excluindo docstrings do módulo).
        module = ast.parse(source)
        docstring = ast.get_docstring(module) or ""
        body_without_module_doc = source
        if docstring:
            # Remove só a docstring de módulo para varrer o restante
            body_without_module_doc = source.replace(docstring, "", 1)
        # Em corpos de função/classe (exceto docstrings internas longas),
        # proibir padrões típicos de hardcode de separador em lógica.
        forbidden_logic = (
            re.compile(r'''["']\\\\["']'''),  # "\\"
            re.compile(r'''os\.path\.join'''),
            re.compile(r'''["']/["']\s*\+|\+\s*["']/["']'''),
        )
        # Limitar à função load_settings e propriedades (não docstrings)
        load_fn_match = re.search(
            r"def load_settings\([\s\S]*?(?=\ndef |\Z)",
            body_without_module_doc,
        )
        self.assertIsNotNone(load_fn_match)
        load_body = load_fn_match.group(0)
        # Stub atual é "..."; quando implementado, não pode hardcodar separadores
        for pattern in forbidden_logic:
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNone(
                    pattern.search(load_body),
                    f"hardcode de separador/path proibido em load_settings: {pattern.pattern}",
                )


if __name__ == "__main__":
    unittest.main()
