"""Tipos e funções puras do chunking Tree-sitter (T11).

Responsabilidade deste módulo
    Declarar ``SourceLanguage``, ``ChunkSourceFile``, ``SemanticChunk`` e as
    funções puras ``compute_chunk_id`` / ``language_from_path``.

Motivo da separação
    Contratos estáveis para T12/T13/T14 sem acoplar a grammars ou ao parser.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class SourceLanguage(StrEnum):
    """Linguagens com grammar oficial no MVP.

    Responsabilidade
        Enumerar o conjunto fechado de linguagens e o valor estável usado em
        ``chunk_id`` / payload.

    Motivo da separação
        Evita strings mágicas; extensão fora do mapa → ``None`` (caller levanta).
    """

    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    MARKDOWN = "markdown"
    YAML = "yaml"
    JSON = "json"
    XML = "xml"
    TOML = "toml"


@dataclass(frozen=True)
class ChunkSourceFile:
    """Arquivo-fonte imutável a chunkar.

    Responsabilidade
        Carregar path + bytes + override opcional de linguagem.

    Motivo da separação
        Desacopla o chunker de como T08/T14 obtêm bytes do snapshot.
    """

    path: str
    content: bytes
    language: SourceLanguage | None = None


@dataclass(frozen=True)
class SemanticChunk:
    """Unidade exclusiva de chunk semântico/RAG.

    Responsabilidade
        Transportar texto, ranges e ``chunk_id`` estável para T12/T13.

    Motivo da separação
        Estabiliza o contrato entre Tree-sitter e o restante do pipeline.
    """

    chunk_id: str
    path: str
    language: SourceLanguage
    kind: str
    text: str
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]
    end_point: tuple[int, int]


_EXTENSION_TO_LANGUAGE: dict[str, SourceLanguage] = {
    ".py": SourceLanguage.PYTHON,
    ".pyi": SourceLanguage.PYTHON,
    ".java": SourceLanguage.JAVA,
    ".js": SourceLanguage.JAVASCRIPT,
    ".mjs": SourceLanguage.JAVASCRIPT,
    ".cjs": SourceLanguage.JAVASCRIPT,
    ".ts": SourceLanguage.TYPESCRIPT,
    ".tsx": SourceLanguage.TYPESCRIPT,
    ".md": SourceLanguage.MARKDOWN,
    ".markdown": SourceLanguage.MARKDOWN,
    ".yaml": SourceLanguage.YAML,
    ".yml": SourceLanguage.YAML,
    ".json": SourceLanguage.JSON,
    ".xml": SourceLanguage.XML,
    ".toml": SourceLanguage.TOML,
}


def compute_chunk_id(
    *,
    path: str,
    start_byte: int,
    end_byte: int,
    language: SourceLanguage,
    kind: str,
) -> str:
    """SHA-256 hex canônico (design §4.3.1)."""
    payload = (
        f"{path}\0{start_byte}\0{end_byte}\0{language.value}\0{kind}".encode("utf-8")
    )
    return hashlib.sha256(payload).hexdigest()


def language_from_path(path: str) -> SourceLanguage | None:
    """Mapear extensão do path para ``SourceLanguage`` MVP (sem I/O)."""
    if not path:
        return None
    ext = Path(path).suffix.lower()
    return _EXTENSION_TO_LANGUAGE.get(ext)
