"""Registry de grammars oficiais Tree-sitter (T11).

Responsabilidade deste módulo
    Resolver ``SourceLanguage`` (+ extensão) para ``tree_sitter.Language``
    oficial, incluindo variantes TS vs TSX.

Motivo da separação
    Permite injetar fake em testes de erro sem acoplar o chunker aos pacotes
    nativos (I-T11-005 / D-T11-007).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from github_rag.index.chunk.errors import GrammarUnavailableError
from github_rag.index.chunk.types import SourceLanguage


@runtime_checkable
class GrammarRegistry(Protocol):
    def resolve(
        self,
        language: SourceLanguage,
        *,
        path_extension: str,
    ) -> Any:
        """Resolve a Language oficial para a linguagem/extensão.

        Responsabilidade
            Carregar grammar oficial (incl. variante TS vs TSX).

        Motivo da separação
            Permite injetar fake em testes de erro (grammar ausente) sem
            acoplar o chunker aos pacotes nativos.
        """
        ...


def _language_ptr(language: SourceLanguage, *, path_extension: str) -> Any:
    """Retorna o ponteiro C da grammar oficial para ``Language(...)``."""
    if language is SourceLanguage.PYTHON:
        import tree_sitter_python as pkg

        return pkg.language()
    if language is SourceLanguage.JAVA:
        import tree_sitter_java as pkg

        return pkg.language()
    if language is SourceLanguage.JAVASCRIPT:
        import tree_sitter_javascript as pkg

        return pkg.language()
    if language is SourceLanguage.TYPESCRIPT:
        import tree_sitter_typescript as pkg

        if path_extension.lower() == ".tsx":
            return pkg.language_tsx()
        return pkg.language_typescript()
    if language is SourceLanguage.MARKDOWN:
        import tree_sitter_markdown as pkg

        return pkg.language()
    if language is SourceLanguage.YAML:
        import tree_sitter_yaml as pkg

        return pkg.language()
    if language is SourceLanguage.JSON:
        import tree_sitter_json as pkg

        return pkg.language()
    if language is SourceLanguage.XML:
        import tree_sitter_xml as pkg

        return pkg.language_xml()
    if language is SourceLanguage.TOML:
        import tree_sitter_toml as pkg

        return pkg.language()
    # Enum fechado MVP: ramo só para defesa se SourceLanguage crescer sem update.
    raise GrammarUnavailableError(  # pragma: no cover
        f"linguagem sem grammar MVP: {language.value}",
        language=language,
    )


class OfficialGrammarRegistry:
    """Implementação default com pacotes oficiais ``tree-sitter-*``.

    Responsabilidade
        Concentrar binding nativo/import dos pacotes; variantes TS/TSX por
        ``path_extension``.

    Motivo da separação
        O chunker depende só de ``GrammarRegistry``.
    """

    def __init__(self) -> None:
        # Garante que todos os bindings MVP carregam (JS incluso; sem fixture .js).
        for lang, ext in (
            (SourceLanguage.PYTHON, ".py"),
            (SourceLanguage.JAVA, ".java"),
            (SourceLanguage.JAVASCRIPT, ".js"),
            (SourceLanguage.TYPESCRIPT, ".ts"),
            (SourceLanguage.TYPESCRIPT, ".tsx"),
            (SourceLanguage.MARKDOWN, ".md"),
            (SourceLanguage.YAML, ".yaml"),
            (SourceLanguage.JSON, ".json"),
            (SourceLanguage.XML, ".xml"),
            (SourceLanguage.TOML, ".toml"),
        ):
            self.resolve(lang, path_extension=ext)

    def resolve(
        self,
        language: SourceLanguage,
        *,
        path_extension: str,
    ) -> Any:
        from tree_sitter import Language

        try:
            return Language(_language_ptr(language, path_extension=path_extension))
        except GrammarUnavailableError:
            raise
        except Exception as exc:
            raise GrammarUnavailableError(
                f"falha ao carregar grammar: {exc}",
                language=language,
            ) from exc
