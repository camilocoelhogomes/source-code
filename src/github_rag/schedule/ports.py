"""Portas públicas do agendamento (T15).

Responsabilidade deste módulo
    Declarar ``CronPreferenceStore`` e ``DailyScheduler`` (Protocols).

Motivo da separação
    Contratos sem APScheduler/SQLAlchemy (ENG-013 / SCH-13).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CronPreferenceStore(Protocol):
    """SoT da preferência de expressão cron da UI (PostgreSQL).

    Responsabilidade
        Persistir/ler override de cron sem tocar catálogo de conexões (BR-017).

    Motivo da separação
        Preferência de agenda ≠ ``CatalogRepository`` (I-T15-001 / D-T15-006).
    """

    def get(self) -> str | None:
        """Lê preferência UI persistida, ou ``None`` se ausente.

        Responsabilidade: SoT da override de cron.
        Motivo da separação: leitura distinta de escrita validada.
        """
        ...

    def set(self, cron_expression: str) -> str:
        """Valida e persiste. Retorna expressão normalizada.

        Responsabilidade: escrita validada; inválido não grava.
        Motivo da separação: store não reagenda jobs (``DailyScheduler.set_cron``).
        Erros: ``InvalidCronExpressionError``.
        """
        ...

    def clear(self) -> None:
        """Remove override; runtime volta ao ``default_cron`` de settings.

        Responsabilidade: apagar singleton / marcar ausência.
        Motivo da separação: ``clear`` ≠ ``set("")`` (vazio é inválido).
        """
        ...


@runtime_checkable
class DailyScheduler(Protocol):
    """Agenda indexação periódica por cron e dispara o orquestrador.

    Responsabilidade
        Resolver expressão ativa (ENG-004), gerir job APScheduler e serializar
        o ciclo reconcile+drain via ``run_tick_once`` (D-T15-011).

    Motivo da separação
        Único dono do lifecycle de agenda; distinto do store de preferência
        (I-T15-001) e do orquestrador T14.
    """

    def start(self) -> None:
        """Inicia ``BackgroundScheduler`` com job ``CronTrigger`` (UTC).

        Responsabilidade: registrar job ``index_cron_tick``; ``max_instances=1``;
        ``coalesce=True``. Idempotente se já rodando: reaplica ``active_cron()``
        via reschedule (mesmo caminho de ``set_cron``) em vez de duplicar o job
        ou lançar erro — evita que um segundo ``start()`` acidental (ex.: wiring
        de boot, T19) derrube o job em vigor.
        Erros: ``InvalidCronExpressionError``; ``SchedulerConfigError``.
        """
        ...

    def stop(self) -> None:
        """Para o scheduler de forma idempotente.

        Responsabilidade: encerrar o ``BackgroundScheduler`` se estiver ativo.
        Motivo da separação: lifecycle distinto de ``start`` / ``run_tick_once``.
        """
        ...

    def active_cron(self) -> str:
        """Expressão efetiva: preference se não-``None`` else ``default_cron``.

        Responsabilidade: expor a cron usada pelo job (ENG-004 / D-T15-002).
        Motivo da separação: leitura sem efeito colateral de persistência.
        """
        ...

    def set_cron(self, cron_expression: str) -> str:
        """Valida, persiste via store, reschedule job se running.

        Responsabilidade: único caminho de escrita para T18 (I-T15-002).
        Motivo da separação: evita persistir sem reagendar.
        Erros: ``InvalidCronExpressionError`` (store intacto se inválido).
        """
        ...

    def run_tick_once(self) -> None:
        """Ciclo reconcile+drain sob lock de instância.

        Responsabilidade: ``StartupIndexReconcile.run()`` +
        ``IndexingOrchestrator.run_until_idle()``.
        Motivo da separação: único ponto síncrono (D-T15-011); job cron chama só isto.
        """
        ...
