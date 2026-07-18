"""Portas de domínio do índice vetorial (T13).

Responsabilidade deste módulo
    Declarar Protocols ``VectorStore`` e ``Embedder``.

Motivo da separação
    Isola Qdrant e o runtime de embeddings dos consumidores (T14/T16);
    embeddings ≠ metadados SLM (BR-010).
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from github_rag.index.vector.types import RepoCommitScope, SemanticHit, VectorRecord


@runtime_checkable
class Embedder(Protocol):
    @property
    def dimensions(self) -> int:
        """Dimensionalidade dos vetores produzidos."""
        ...

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """Produz embeddings densos para uma sequência de textos.

        Responsabilidade
            Única porta de produção de vetores a partir de textos.

        Motivo da separação
            Isola o SDK openai / runtime local de embeddings da porta
            MetadataGenerator (T12) e do VectorStore.
        """
        ...


@runtime_checkable
class VectorStore(Protocol):
    def upsert(
        self,
        scope: RepoCommitScope,
        records: Sequence[VectorRecord],
    ) -> None:
        """Insere/atualiza pontos do scope (idempotente por point id).

        Responsabilidade
            Persistir vetor + payload (chunk Tree-sitter + metadata SLM).

        Motivo da separação
            Isola Qdrant dos consumidores; não remove commits antigos.
        """
        ...

    def purge_other_commits(self, scope: RepoCommitScope) -> None:
        """Remove pontos do mesmo ``repo_id`` com ``commit_sha`` ≠ scope.

        Responsabilidade
            Limpar commits anteriores do repositório.

        Motivo da separação
            Permite testar purge isolado de upsert.
        """
        ...

    def replace_repo_commit(
        self,
        scope: RepoCommitScope,
        records: Sequence[VectorRecord],
    ) -> None:
        """Upsert + purge_other_commits (reindex / restart total por commit).

        Responsabilidade
            Substituir o índice vetorial do repo pelo commit atual.

        Motivo da separação
            API conveniente e semântica explícita para T14.
        """
        ...

    def delete_repo(self, repo_id: str) -> None:
        """Remove todos os pontos do ``repo_id``.

        Responsabilidade
            Wipe vetorial de um repositório.

        Motivo da separação
            Operação de catálogo/remoção distinta de reindex por commit.
        """
        ...

    def delete_paths(
        self,
        scope: RepoCommitScope,
        paths: Sequence[str],
    ) -> None:
        """Remove pontos do scope cujo payload.path ∈ paths.

        Responsabilidade
            Limpar paths removidos (ENG-012) sem rebuild total obrigatório.

        Motivo da separação
            Handoff T14; escopo por commit evita apagar path de outro tip.
        """
        ...

    def search(
        self,
        query_vector: Sequence[float],
        *,
        limit: int,
        repo_ids: Sequence[str] | None = None,
    ) -> tuple[SemanticHit, ...]:
        """Busca k-NN; reidrata SemanticHit a partir do payload.

        Responsabilidade
            Recuperar evidências semanticamente relacionadas (BDD-010).

        Motivo da separação
            Search não gera prosa nem chama SLM (BR-011).
        """
        ...
