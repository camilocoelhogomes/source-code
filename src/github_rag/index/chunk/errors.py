"""Hierarquia de erros tipados do chunking Tree-sitter (T11).

Responsabilidade deste módulo
    Sinalizar falhas de chunking sem fallback genérico (vazio, binário,
    grammar, parse).

Motivo da separação
    Distinto de elegibilidade/catálogo; T14 mapeia qualquer ``ChunkingError``
    para falha da etapa ``tree_sitter`` (BR-005).
"""

from __future__ import annotations

from github_rag.index.chunk.types import SourceLanguage


class ChunkingError(Exception):
    """Raiz das falhas de chunking semântico.

    Responsabilidade
        Tipo-base único com ``path`` / ``language`` opcionais para observabilidade.

    Motivo da separação
        Permite ``except ChunkingError`` amplo sem capturar Exception genérica.
    """

    path: str | None
    language: SourceLanguage | None

    def __init__(
        self,
        message: str = "",
        *,
        path: str | None = None,
        language: SourceLanguage | None = None,
    ) -> None:
        self.path = path
        self.language = language
        parts: list[str] = []
        if message:
            parts.append(message)
        if path is not None and path not in message:
            parts.append(f"path={path}")
        if language is not None:
            parts.append(f"language={language.value}")
        super().__init__(" ".join(parts) if parts else "")


class EmptySourceError(ChunkingError):
    """Conteúdo vazio (`len(content) == 0`)."""


class BinarySourceError(ChunkingError):
    """Conteúdo binário (NUL) ou não decodificável como UTF-8 strict."""


class GrammarUnavailableError(ChunkingError):
    """Extensão/linguagem sem grammar MVP ou registry sem pacote/variante."""


class ParseFailureError(ChunkingError):
    """Exceção do parser/grammar ou impossível materializar chunk com texto."""
