"""Erros tipados da geração de metadados SLM (T12).

Responsabilidade deste módulo
    Hierarquia sob ``MetadataGenerationError`` sem fallback silencioso.

Motivo da separação
    Distinto de ``ChunkingError`` (T11) e erros de VectorStore (T13);
    T14 trata qualquer ``MetadataGenerationError`` como falha da etapa.
"""

from __future__ import annotations


class MetadataGenerationError(Exception):
    """Falha tipada na geração de metadados (base).

    Responsabilidade
        Carregar ``chunk_id``/``path`` quando conhecidos e expor mensagem
        sem secrets (``api_key`` nunca é atributo da classe).

    Motivo da separação
        Observabilidade para T14 / BR-005 sem acoplar ao adaptador OpenAI.
    """

    def __init__(
        self,
        message: str = "",
        *,
        chunk_id: str | None = None,
        path: str | None = None,
    ) -> None:
        super().__init__(message)
        self.chunk_id = chunk_id
        self.path = path

    def __str__(self) -> str:
        base = super().__str__()
        parts: list[str] = []
        if base:
            parts.append(base)
        if self.chunk_id is not None:
            parts.append(f"chunk_id={self.chunk_id}")
        if self.path is not None:
            parts.append(f"path={self.path}")
        return " ".join(parts) if parts else ""


class MetadataConfigError(MetadataGenerationError):
    """Config inválida (base_url/model/timeout) na construção do adaptador."""


class MetadataModelError(MetadataGenerationError):
    """Falha de rede/SDK/runtime/timeout/HTTP/API ou resposta vazia do modelo."""


class MetadataResponseParseError(MetadataGenerationError):
    """Content não-JSON, schema inválido ou ``summary`` vazio."""
