"""Limitação de paralelismo de indexação e consulta.

Responsabilidade deste módulo
    Expor a porta ``WorkerLimiter`` e factories isoladas para os pools de
    indexação e consulta, com política de capacidade mínima.

Motivo da separação
    Isolar semáforos de concorrência do bootstrap de env (T01), da orquestração
    de indexação (T14) e das tools MCP/query (T17), permitindo trocar a
    implementação sem alterar consumidores.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import Protocol, runtime_checkable

from github_rag.settings import AppSettings

MIN_WORKERS = 1
"""Menor capacidade aceita para um pool de workers (política T04).

Responsabilidade: literal de validação compartilhado por construtor e factories.
Motivo da separação: evita espalhar ``1`` mágico nos callers.
Invariantes: literal ``1``; capacidade efetiva deve ser ``>= MIN_WORKERS``.
Erros: nenhum nesta constante.
"""


class WorkerLimiterError(Exception):
    """Falha ao construir ou usar um limiter de workers.

    Responsabilidade
        Sinalizar capacidade inválida (``capacity < MIN_WORKERS``) de forma
        explícita, sem fallback silencioso para defaults de engenharia.

    Motivo da separação
        Distinguir erros de política de paralelismo (T04) de erros de tipagem
        de env em ``SettingsBootstrapError`` (T01).

    Invariantes
        Mensagem cita o pool (quando conhecido), o valor e a razão; sem segredos.

    Erros
        Esta classe **é** o tipo de erro.
    """


@runtime_checkable
class WorkerLimiter(Protocol):
    """Porta de limitação de paralelismo por pool.

    Responsabilidade
        Garantir que no máximo ``capacity`` seções críticas entrem
        simultaneamente via ``acquire()``; excedentes aguardam slot.

    Motivo da separação
        Contrato estável para orquestrador de indexação (T14) e consulta/MCP
        (T17) sem acoplar a ``threading.Semaphore`` nem a ``os.environ``.

    Invariantes
        - ``capacity >= MIN_WORKERS`` em instância válida.
        - Pico de entradas ativas no context manager ``<= capacity``.
        - Liberação do slot no exit do CM, inclusive com exceção.
        - Limiters de pools distintos não compartilham slots.

    Erros
        O Protocol não levanta após construção ok; construção inválida usa
        ``WorkerLimiterError``.
    """

    @property
    def capacity(self) -> int:
        """Capacidade máxima de slots simultâneos deste pool.

        Responsabilidade: expor o limite configurado (já validado).
        Motivo da separação: atributo tipado distinto do nome de env.
        Invariantes: ``int >= MIN_WORKERS``.
        Erros: nenhum na propriedade.
        """
        ...

    def acquire(self) -> AbstractContextManager[None]:
        """Adquire um slot, bloqueando até haver capacidade.

        Responsabilidade: enfileirar/aguardar quando o limite está saturado;
        liberar o slot ao sair do context manager.
        Motivo da separação: única API de entrada na seção crítica (sem
        ``try_acquire``/métricas na porta pública).
        Invariantes: libera no ``__exit__`` mesmo com exceção.
        Erros: nenhum na aquisição após construção ok.
        """
        ...


class SemaphoreWorkerLimiter:
    """Implementação de ``WorkerLimiter`` baseada em ``threading.Semaphore``.

    Responsabilidade
        Materializar o contrato síncrono de aquisição/liberação com a
        capacidade informada.

    Motivo da separação
        Isola o mecanismo de sincronização da porta, permitindo testes e
        substituição futura sem mudar T14/T17.

    Invariantes
        ``capacity >= MIN_WORKERS``; pool usado só em mensagens de erro.

    Erros
        ``WorkerLimiterError`` se ``capacity < MIN_WORKERS``.
    """

    def __init__(self, *, capacity: int, pool: str) -> None:
        ...

    @property
    def capacity(self) -> int:
        ...

    def acquire(self) -> AbstractContextManager[None]:
        ...


def create_index_limiter(settings: AppSettings) -> WorkerLimiter:
    """Cria limiter isolado para o pool de indexação.

    Responsabilidade
        Ler ``settings.index_workers`` e devolver ``WorkerLimiter`` com
        ``pool="index"``.

    Motivo da separação
        Garante isolamento do pool de indexação em relação ao de query;
        callers não escolhem a classe concreta nem o label do pool.

    Invariantes
        Capacidade = ``settings.index_workers`` após validação ``>= 1``.

    Erros
        ``WorkerLimiterError`` se a capacidade do snapshot for ``< 1``.
    """
    ...


def create_query_limiter(settings: AppSettings) -> WorkerLimiter:
    """Cria limiter isolado para o pool de consulta.

    Responsabilidade
        Ler ``settings.query_workers`` e devolver ``WorkerLimiter`` com
        ``pool="query"``.

    Motivo da separação
        Mesmo motivo de ``create_index_limiter``, para o pool de query/MCP.

    Invariantes
        Capacidade = ``settings.query_workers`` após validação ``>= 1``.

    Erros
        ``WorkerLimiterError`` se a capacidade do snapshot for ``< 1``.
    """
    ...
