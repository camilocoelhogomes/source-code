"""Testes unitários — GrammarRegistry / OfficialGrammarRegistry (T11)."""

from __future__ import annotations

import unittest

from github_rag.index.chunk.errors import GrammarUnavailableError
from github_rag.index.chunk.grammar_registry import OfficialGrammarRegistry
from github_rag.index.chunk.types import SourceLanguage


class FakeUnavailableRegistry:
    """Registry que sempre falha — fronteira injetável (I-T11-005)."""

    def resolve(self, language: SourceLanguage, *, path_extension: str):
        raise GrammarUnavailableError(
            "grammar ausente (fake)",
            path=None,
            language=language,
        )


class TestOfficialGrammarRegistry(unittest.TestCase):
    """UT-G01, UT-G02."""

    def test_ut_g01_resolve_python(self) -> None:
        registry = OfficialGrammarRegistry()
        language = registry.resolve(SourceLanguage.PYTHON, path_extension=".py")
        self.assertIsNotNone(language)

    def test_ut_g02_typescript_vs_tsx_variants(self) -> None:
        registry = OfficialGrammarRegistry()
        ts = registry.resolve(SourceLanguage.TYPESCRIPT, path_extension=".ts")
        tsx = registry.resolve(SourceLanguage.TYPESCRIPT, path_extension=".tsx")
        self.assertIsNotNone(ts)
        self.assertIsNotNone(tsx)
        # Variantes distintas quando a API do pacote as expõe.
        self.assertIsNot(ts, tsx)


class TestGrammarRegistryFailures(unittest.TestCase):
    """UT-G03."""

    def test_ut_g03_fake_registry_raises_grammar_unavailable(self) -> None:
        registry = FakeUnavailableRegistry()
        with self.assertRaises(GrammarUnavailableError):
            registry.resolve(SourceLanguage.PYTHON, path_extension=".py")


if __name__ == "__main__":
    unittest.main()
