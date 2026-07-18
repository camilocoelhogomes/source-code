"""Porta de domínio ExactCodeIndex (T10).

Responsabilidade deste módulo
    Declarar o Protocol ``ExactCodeIndex`` consumido por T14/T16.

Motivo da separação
    Orquestração e QueryService não acoplam a Zoekt (HTTP, CLI, shards);
    permite ``FakeExactCodeIndex`` e troca de backend oficial.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from github_rag.index.zoekt.models import ExactMatch, ExactSearchQuery, FileToIndex


@runtime_checkable
class ExactCodeIndex(Protocol):
    """Porta: indexar / buscar / limpar índice de código exato.

    Responsabilidade
        Abstrair indexação e busca exata de código para o produto (T14
        indexa; T16 busca; restart usa ``delete_repository``).

    Motivo da separação
        T14/T16 não acoplam a Zoekt; permite fake e troca de backend sem
        mudar orquestração/UI/MCP (D-T10-002).
    """

    def index(
        self,
        repository: str,
        commit: str,
        files: Sequence[FileToIndex],
    ) -> None:
        """Indexa o conjunto tip do repositório (``files`` vazio = no-op)."""
        ...

    def search(self, query: ExactSearchQuery) -> Sequence[ExactMatch]:
        """Busca literal; ``pattern`` vazio → sequência vazia."""
        ...

    def delete_repository(self, repository: str) -> None:
        """Remove artefatos do repositório; ausência = no-op."""
        ...
