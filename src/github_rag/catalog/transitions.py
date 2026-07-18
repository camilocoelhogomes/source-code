"""Máquina de estados e regras puras de commit — contratos T03 (sem I/O).

Responsabilidade deste módulo
    Congelar a máquina de estados fechada de `RepoState` (REQ-020), a política
    de reentrância idempotente e o helper puro de comparação de commit
    (BR-002/004). Formaliza o conjunto de transições que estava apenas em prosa
    no design (resolve SUGGESTION S-1).

Motivo da separação
    Isolar as *regras que mudam o estado* dos *dados* (`models.py`) e da *porta*
    (`repository.py`). Estas regras são domínio puro, sem PostgreSQL nem I/O —
    100% testáveis em qualquer OS sem Docker (design §3.1/§3.3), carregando o
    grosso da cobertura ≥95%. O adaptador PG e o fake in-memory devem ambos
    respeitar esta mesma tabela, garantindo paridade semântica.

Contrato vs. implementação
    ``ALLOWED_TRANSITIONS`` e ``IDEMPOTENT_SELF_STATES`` são o *contrato*
    declarativo (dados congelados). As funções são apenas assinaturas (``...``)
    nesta etapa de interfaces; o comportamento é fixado pelos unit tests e
    escrito no gate de implementação.
"""

from __future__ import annotations

from typing import Final

from .errors import InvalidStateTransitionError
from .models import RepoState

# ---------------------------------------------------------------------------
# Contrato declarativo da máquina de estados (REQ-020; design §4.2; S-1)
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: Final[dict[RepoState, frozenset[RepoState]]] = {
    RepoState.NOT_INDEXED: frozenset({RepoState.QUEUED}),
    RepoState.QUEUED: frozenset({RepoState.INDEXING}),
    RepoState.INDEXING: frozenset({RepoState.UP_TO_DATE, RepoState.ERROR}),
    RepoState.UP_TO_DATE: frozenset({RepoState.NOT_INDEXED}),
    RepoState.ERROR: frozenset({RepoState.QUEUED, RepoState.NOT_INDEXED}),
}
"""Conjunto FECHADO de transições válidas (origem → destinos permitidos).

Responsabilidade
    Ser a única fonte de verdade das transições de `RepoState` (REQ-020).

Motivo da separação
    Declarar a tabela como dado congelado (não espalhada em ``if`` de callers)
    permite testes negativos exaustivos (BDD CP-10) e paridade fake × PG.

Semântica das transições (design §4.2)
    - ``not_indexed → queued``: enfileiramento.
    - ``queued → indexing``: início da execução.
    - ``indexing → up_to_date``: sucesso; grava ``last_processed_commit``.
    - ``indexing → error``: falha; grava mensagem + horário (REQ-023).
    - ``error → queued``: nova tentativa reinicia o repo inteiro (BR-005).
    - ``error → not_indexed``: reconcile/limpeza.
    - ``up_to_date → not_indexed``: novo commit em main ≠ processado (ENG-011).

Qualquer par ausente desta tabela é ilegal ⇒ ``InvalidStateTransitionError``.
"""

IDEMPOTENT_SELF_STATES: Final[frozenset[RepoState]] = frozenset(
    {RepoState.NOT_INDEXED, RepoState.QUEUED}
)
"""Estados cuja auto-transição (destino == atual) é no-op idempotente.

Responsabilidade
    Formalizar a política de reentrância pedida em S-1: reconcile/enfileiramento
    repetidos não devem falhar.

Motivo da separação
    ``not_indexed`` e ``queued`` são pontos de reconcile onde repetição é
    esperada (idempotência de startup — ENG-011). Auto-transição para qualquer
    OUTRO estado (``indexing``/``up_to_date``/``error``) é ilegal e levanta
    ``InvalidStateTransitionError`` — evita mascarar reprocessamento indevido.
"""


def is_transition_allowed(current: RepoState, target: RepoState) -> bool:
    """Indica se ``current → target`` é permitido pela máquina de estados.

    Responsabilidade
        Decidir, sem I/O, se a transição consta em ``ALLOWED_TRANSITIONS`` ou é
        uma auto-transição idempotente (``target == current`` e ``current`` em
        ``IDEMPOTENT_SELF_STATES``).

    Motivo da separação
        Predicado puro reutilizado pela porta (fake e adaptador PG) e por testes;
        centraliza a regra REQ-020 em um único ponto.

    Retorno
        ``True`` se permitida (incluindo no-op idempotente); ``False`` caso
        contrário. Não levanta.
    """
    if target == current:
        return current in IDEMPOTENT_SELF_STATES
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def ensure_transition_allowed(current: RepoState, target: RepoState) -> None:
    """Valida a transição ou levanta ``InvalidStateTransitionError``.

    Responsabilidade
        Guardar a máquina de estados na fronteira de escrita: se
        ``is_transition_allowed(current, target)`` for falso, levanta
        ``InvalidStateTransitionError`` sem mutar nada (BDD CP-10).

    Motivo da separação
        Concentrar a conversão "regra violada → erro tipado" num único helper
        evita divergência entre fake e adaptador PG e mantém o estado preservado
        em caso de rejeição.
    """
    if not is_transition_allowed(current, target):
        raise InvalidStateTransitionError(
            f"transição ilegal: {current.value} → {target.value}"
        )


def is_up_to_date(
    last_processed_commit: str | None,
    current_main_commit: str | None,
) -> bool:
    """Compara commit processado × tip da main (BR-002/004; ENG-011).

    Responsabilidade
        Decidir, de forma pura, se o repositório está "atualizado": há commit
        processado e ele é igual ao tip conhecido da main.

    Motivo da separação
        A comparação de commit é a regra central do reconcile (BDD CP-01/CP-02) e
        deve ser testável sem PG. Um repo com ``last_processed_commit is None``
        (nunca processado) ou com tip diferente NÃO está atualizado.

    Retorno
        ``True`` se ambos não-nulos e iguais; ``False`` caso contrário. Não
        levanta. Não decide transição — apenas informa a comparação; o
        rebaixamento ``up_to_date → not_indexed`` é aplicado por
        ``CatalogRepository.reconcile_repository``.
    """
    return (
        last_processed_commit is not None
        and current_main_commit is not None
        and last_processed_commit == current_main_commit
    )
