"""Tipos de contrato do índice vetorial (T13).

Responsabilidade deste módulo
    Declarar ``ChunkMetadata``, ``EnrichedChunk``, ``RepoCommitScope``,
    ``VectorRecord`` e ``SemanticHit`` — contratos frozen T12/T13/T14/T16.

Motivo da separação
    Estabiliza payload Qdrant e evidências de search sem acoplar à geração SLM
    (T12) nem ao SDK Qdrant.
"""

from __future__ import annotations

from dataclasses import dataclass

from github_rag.index.chunk.types import SemanticChunk


@dataclass(frozen=True)
class ChunkMetadata:
    """Metadados contextuais SLM serializáveis associados a um chunk.

    Responsabilidade
        Carregar summary/keywords/symbols para o payload Qdrant.

    Motivo da separação
        Desacopla T13 da geração SLM; impede dict livre sem invariantes.
    """

    summary: str
    keywords: tuple[str, ...]
    symbols: tuple[str, ...] = ()


@dataclass(frozen=True)
class EnrichedChunk:
    """Unidade de entrada do VectorStore: chunk Tree-sitter + metadata SLM.

    Responsabilidade
        Transportar o par imutável consumido no upsert.

    Motivo da separação
        T13 não redefine chunk nem gera metadados (DEC-003).
    """

    chunk: SemanticChunk
    metadata: ChunkMetadata


@dataclass(frozen=True)
class RepoCommitScope:
    """Escopo de indexação vetorial (repositório + tip main).

    Responsabilidade
        Identificar filtros de purge/replace/delete sem acoplar ao catálogo SQL.

    Motivo da separação
        Concentra o par ``repo_id``/``commit_sha`` opaco para T13.
    """

    repo_id: str
    commit_sha: str


@dataclass(frozen=True)
class VectorRecord:
    """Chunk enriquecido já embutido para persistência.

    Responsabilidade
        Transportar ``EnrichedChunk`` + vetor denso.

    Motivo da separação
        Deixa explícito que o store não chama ``Embedder``.
    """

    enriched: EnrichedChunk
    vector: tuple[float, ...]


@dataclass(frozen=True)
class SemanticHit:
    """Evidência semântica reidratada (score + chunk + metadata).

    Responsabilidade
        Devolver evidências tipadas para T16/UI/MCP sem prosa SLM (BR-011).

    Motivo da separação
        Contrato estável de reidratação do payload Qdrant.
    """

    score: float
    repo_id: str
    commit_sha: str
    chunk: SemanticChunk
    metadata: ChunkMetadata
