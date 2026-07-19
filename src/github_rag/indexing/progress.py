"""Helpers puros de progresso de indexação (T14).

Responsabilidade deste módulo
    Calcular percentual legível (REQ-021) sem I/O.

Motivo da separação
    Regra testável isolada do orquestrador e do catálogo.
"""

from __future__ import annotations


def compute_progress_percent(*, files_processed: int, files_total: int) -> int:
    """Retorna int em ``[0, 100]``; ``files_total <= 0`` ⇒ ``0``.

    Responsabilidade: percentual agregado para ``update_progress``.
    Motivo da separação: evita espalhar a fórmula nos callers.
    """
    if files_total <= 0:
        return 0
    raw = (100 * files_processed) // files_total
    return max(0, min(100, raw))
