"""Avaliação de SLO de paralelismo sob limite de workers (T26 / BDD-013).

Responsabilidade deste módulo
    Calcular ondas mínimas ``ceil(N/capacity)`` e aceitar/rejeitar evidência
    de wall-clock que prove paralelismo sob limite + fila de excedentes.

Motivo da separação
    Isola a regra de aceite BDD-013 (D-T26-002) para reuso por pytest e
    keywords Robot, sem acoplar a transporte MCP nem a ``threading``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ParallelSloResult:
    """Resultado tipado da avaliação de SLO paralelo.

    Responsabilidade
        Comunicar ok/falha com diagnóstico sem secrets.

    Motivo da separação
        Evita booleans opacos e mensagens ad-hoc espalhadas em Robot/pytest.
    """

    ok: bool
    reason: str
    min_waves: int


def min_waves(n_calls: int, capacity: int) -> int:
    """Retorna ``ceil(n_calls / capacity)``.

    Responsabilidade
        Onda mínima teórica sob limite configurado.

    Motivo da separação
        Aritmética isolada do avaliador e das keywords (I-T26-002).

    Erros
        ``ValueError`` se ``n_calls < 1`` ou ``capacity < 1``.
    """
    if n_calls < 1:
        raise ValueError(f"n_calls must be >= 1, got {n_calls}")
    if capacity < 1:
        raise ValueError(f"capacity must be >= 1, got {capacity}")
    return int(math.ceil(n_calls / capacity))


def evaluate_parallel_slo(
    *,
    capacity: int,
    n_calls: int,
    wall_seconds: float,
    single_seconds: float,
    tol_low: float = 0.35,
    tol_serial: float = 0.85,
) -> ParallelSloResult:
    """Avalia se wall-clock prova paralelismo sob limite + fila/excedentes.

    Responsabilidade
        Aplicar as regras I-T26-003 / D-T26-002 de forma pura.

    Motivo da separação
        Uma regra compartilhada Robot↔pytest; sem I/O nem secrets.

    Regras
        1. Entradas inválidas → ``ok=False``.
        2. Se ``n_calls > capacity``: ``wall >= single * (min_waves - tol_low)``.
        3. Se ``capacity > 1`` e ``n_calls > capacity``:
           ``wall < single * n_calls * tol_serial``.
        4. Se ``n_calls > 1`` e ``n_calls <= capacity``:
           ``wall < single * n_calls * tol_serial``.
        5. Se ``n_calls == 1``: aceita quando entradas válidas.
    """
    if capacity < 1:
        return ParallelSloResult(
            ok=False,
            reason=f"invalid capacity={capacity}",
            min_waves=0,
        )
    if n_calls < 1:
        return ParallelSloResult(
            ok=False,
            reason=f"invalid n_calls={n_calls}",
            min_waves=0,
        )
    if single_seconds <= 0:
        return ParallelSloResult(
            ok=False,
            reason=f"invalid single_seconds={single_seconds}",
            min_waves=0,
        )
    if wall_seconds < 0:
        return ParallelSloResult(
            ok=False,
            reason=f"invalid wall_seconds={wall_seconds}",
            min_waves=0,
        )

    waves = min_waves(n_calls, capacity)

    if n_calls > capacity:
        min_wall = single_seconds * max(waves - tol_low, 0.0)
        if wall_seconds < min_wall:
            return ParallelSloResult(
                ok=False,
                reason=(
                    f"wall_seconds={wall_seconds:.4f} < min_wall={min_wall:.4f} "
                    f"(capacity={capacity}, n_calls={n_calls}, waves={waves}); "
                    "excess queue / waves not evidenced"
                ),
                min_waves=waves,
            )
        if capacity > 1:
            max_wall = single_seconds * n_calls * tol_serial
            if wall_seconds >= max_wall:
                return ParallelSloResult(
                    ok=False,
                    reason=(
                        f"wall_seconds={wall_seconds:.4f} >= max_serialish="
                        f"{max_wall:.4f} (capacity={capacity}, n_calls={n_calls}); "
                        "looks fully serial — no parallelism under limit"
                    ),
                    min_waves=waves,
                )
    elif n_calls > 1:
        max_wall = single_seconds * n_calls * tol_serial
        if wall_seconds >= max_wall:
            return ParallelSloResult(
                ok=False,
                reason=(
                    f"wall_seconds={wall_seconds:.4f} >= max_serialish="
                    f"{max_wall:.4f} (capacity={capacity}, n_calls={n_calls}); "
                    "expected parallelism when n_calls<=capacity"
                ),
                min_waves=waves,
            )

    return ParallelSloResult(ok=True, reason="", min_waves=waves)
