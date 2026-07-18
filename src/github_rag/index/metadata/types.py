"""Tipos de saída da geração de metadados SLM (T12).

Responsabilidade deste módulo
    Declarar ``ChunkMetadata`` imutável e serializável para payload Qdrant (T13).

Motivo da separação
    Desacopla o formato de saída SLM do adaptador OpenAI e do VectorStore.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkMetadata:
    """Metadados contextuais imutáveis associados a um ``chunk_id``.

    Responsabilidade
        Transportar summary/symbols/keywords/intent/extra e serializá-los
        via ``to_payload()`` para o contrato T13.

    Motivo da separação
        Evita mutação pós-geração e containers mutáveis em dataclass frozen.
    """

    chunk_id: str
    summary: str
    symbols: tuple[str, ...]
    keywords: tuple[str, ...]
    intent: str
    extra: tuple[tuple[str, str | int | float | bool | None], ...]

    def to_payload(self) -> dict[str, object]:
        """Serializa para dict JSON-safe (listas e extra plano)."""
        return {
            "chunk_id": self.chunk_id,
            "summary": self.summary,
            "symbols": list(self.symbols),
            "keywords": list(self.keywords),
            "intent": self.intent,
            "extra": dict(self.extra),
        }
