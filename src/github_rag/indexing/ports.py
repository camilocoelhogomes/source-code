"""Portas públicas do orquestrador de indexação (T14).

Responsabilidade deste módulo
    Declarar ``IndexingOrchestrator`` e ``StartupIndexReconcile``.

Motivo da separação
    T15/T18/T19 programam contra Protocols; reconcile de boot ≠ fila/workers
    (D-T14-003 / I-T14-001).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class IndexingOrchestrator(Protocol):
    """Porta de orquestração de indexação (fila + pipeline + estados REQ-020).

    Responsabilidade
        Enfileirar repositórios, drenar a fila com ``WorkerLimiter`` e indexar
        um repo (Zoekt conjunto tip → RAG → Qdrant) com política BR-005.

    Motivo da separação
        Único dono da sequência de indexação; não faz reconcile de boot
        (isso é ``StartupIndexReconcile``).
    """

    def enqueue(self, repository_ids: Sequence[int]) -> None:
        """Marca elegíveis como ``queued`` e coloca na fila interna (dedupe)."""
        ...

    def run_until_idle(self) -> None:
        """Drena a fila respeitando ``WorkerLimiter`` até vazia."""
        ...

    def index_repository(self, repository_id: int) -> None:
        """Indexa um repositório de forma síncrona."""
        ...


@runtime_checkable
class StartupIndexReconcile(Protocol):
    """Porta de reconcile de indexação no startup (ENG-011).

    Responsabilidade
        Após sync de catálogo: tip × processado, recover órfãos, enqueue stale.

    Motivo da separação
        T07 é sync-only; T19 chama esta porta — não duplicar no orquestrador.
    """

    def run(self) -> None:
        """Atualiza tip, ``reconcile_repository``, recover e enqueue."""
        ...
