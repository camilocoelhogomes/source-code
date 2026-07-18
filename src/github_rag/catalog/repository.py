"""Porta ``CatalogRepository`` — contrato T03 (Protocol, sem implementação).

Responsabilidade deste módulo
    Declarar a porta hexagonal do catálogo: a interface tipada e congelada que
    o adaptador PostgreSQL (`PostgresCatalogRepository`) e o fake in-memory
    (`InMemoryCatalogRepository` — gate de implementação) devem satisfazer, e
    contra a qual os consumidores (T07/T14/T17/T18) programam.

Motivo da separação
    Arquitetura hexagonal (design §3.1): a porta separa o *contrato* de
    persistência da *implementação*. Consumidores dependem deste Protocol, não
    de SQLAlchemy nem de dicionários em memória. Isso permite: (1) testar
    domínio/comportamento com o fake sem PG/Docker (metade da equipe em Windows),
    e (2) validar a semântica PostgreSQL no adaptador via testcontainers, sem que
    o resto do sistema conheça o backend.

Congelamento de nomes (resolve SUGGESTION B-2)
    As assinaturas abaixo são os NOMES CANÔNICOS congelados. O BDD usava listas
    de verbos equivalentes (`_invoke`); a partir deste gate, cada operação tem um
    único nome oficial (ver `interfaces.md`). O helper `_invoke` continua
    aceitando o nome canônico como primeiro candidato — nenhuma quebra no BDD.

Contrato vs. implementação
    Todos os métodos têm corpo ``...``: esta é a definição de interface. Nenhuma
    lógica de persistência é escrita nesta etapa.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol, runtime_checkable

from .models import (
    CatalogEntry,
    FileProgress,
    FileStage,
    IndexingExecution,
    RepoOrigin,
    RepoState,
)


@runtime_checkable
class CatalogRepository(Protocol):
    """Porta de persistência do catálogo (PostgreSQL como SoT; design §6).

    Responsabilidade
        Expor as operações de sincronização (T07), orquestração/indexação (T14)
        e leitura (T17/T18) sobre o catálogo, com semântica de erros de domínio
        (not found, transição inválida, conflito de concorrência) independente do
        backend.

    Motivo da separação
        Uma única porta versionada estabiliza o handoff para T07/T14: mudanças no
        adaptador PG não vazam para os consumidores. O fake e o adaptador PG
        implementam este mesmo contrato, garantindo paridade semântica testável.

    Invariantes gerais
        - Operações sobre ``repository_id``/``execution_id`` inexistente levantam
          ``RepositoryNotFoundError``.
        - Toda mutação devolve o `CatalogEntry` (ou registro) atualizado, com
          ``row_version`` incrementado quando houver escrita na linha do repo.
        - Nenhuma operação apaga histórico; remoção do catálogo é soft-delete.
    """

    # -- Sincronização do catálogo (T07) ------------------------------------

    def upsert_repository(
        self,
        *,
        connection_name: str,
        origin: RepoOrigin,
        repo_identifier: str,
        github_org: str | None = None,
        local_path: str | None = None,
    ) -> CatalogEntry:
        """Insere ou atualiza um repositório do catálogo, preservando progresso.

        Responsabilidade: materializar um repo descoberto (T07) sem sobrescrever
        estado/commit já conhecidos; reativa (``active=True``) se estava
        soft-deleted com a mesma ``(connection_name, repo_identifier)``.
        Motivo da separação: T07 sincroniza a config declarada com o SoT; upsert
        é a operação idempotente dessa sincronização.
        Erros: nenhum de domínio no caminho feliz; ``CatalogPersistenceError`` no
        adaptador PG em falha de infra.
        """
        ...

    def deactivate_repository(self, repository_id: int) -> CatalogEntry:
        """Soft-delete: remove do catálogo ativo sem apagar histórico (BDD CP-08).

        Responsabilidade: marcar ``active=False`` e ``deactivated_at`` quando o
        repo some da config atual (T07); execuções permanecem no histórico.
        Motivo da separação: preservar auditoria (REQ-023) exige remoção lógica,
        não física (D-T03-005).
        Erros: ``RepositoryNotFoundError`` se o id não existir.
        """
        ...

    # -- Leitura (T07/T14/T17/T18) ------------------------------------------

    def list_active_catalog(self) -> Sequence[CatalogEntry]:
        """Lista o catálogo ativo com estado + ``last_processed_commit`` (ENG-011).

        Responsabilidade: retornar apenas ``active=True``, cada item com estado,
        commits de comparação e progresso — base do startup reconcile e das
        superfícies UI/MCP (BDD CP-08, design §5.2).
        Motivo da separação: leitura central e barata do reconcile, distinta da
        leitura pontual ``get_repository``.
        Erros: nenhum; retorna sequência vazia se não houver ativos.
        """
        ...

    def get_repository(self, repository_id: int) -> CatalogEntry:
        """Leitura pontual de um repositório por id (BDD CP-11).

        Responsabilidade: devolver o `CatalogEntry` corrente para inspeção.
        Motivo da separação: ponto único de leitura por id, com erro explícito de
        ausência (evita ``None`` silencioso).
        Erros: ``RepositoryNotFoundError`` se o id não existir.
        """
        ...

    # -- Máquina de estados (T14) -------------------------------------------

    def transition_state(
        self,
        repository_id: int,
        target_state: RepoState,
        *,
        expected_version: int,
    ) -> CatalogEntry:
        """Aplica uma transição validada com lock otimista (BDD CP-10/CP-12).

        Responsabilidade: verificar existência, checar ``expected_version`` contra
        ``row_version`` (conflito ⇒ ``ConcurrencyConflictError``) e validar a
        transição (ilegal ⇒ ``InvalidStateTransitionError``), preservando o estado
        em caso de rejeição.
        Motivo da separação: operação genérica de transição com controle de
        concorrência explícito, separada dos atalhos ``mark_*`` (que não exigem
        ``expected_version``).
        Ordem de checagem (contrato congelado): existência → versão → validade da
        transição (garante CP-12 mesmo quando o destino é válido).
        Erros: ``RepositoryNotFoundError``, ``ConcurrencyConflictError``,
        ``InvalidStateTransitionError``.
        """
        ...

    def mark_queued(self, repository_id: int) -> CatalogEntry:
        """Atalho de transição para ``queued`` (enfileiramento; T14).

        Responsabilidade: transicionar o repo para ``queued`` respeitando a
        máquina de estados (``not_indexed → queued`` ou ``error → queued``;
        ``queued → queued`` é no-op idempotente).
        Motivo da separação: atalho sem ``expected_version`` para o fluxo de
        orquestração; lê a versão corrente internamente.
        Erros: ``RepositoryNotFoundError``, ``InvalidStateTransitionError``.
        """
        ...

    def mark_indexing(self, repository_id: int) -> CatalogEntry:
        """Atalho de transição para ``indexing`` (início da execução; T14).

        Responsabilidade: transicionar ``queued → indexing``.
        Motivo da separação: atalho de fluxo, par de ``start_execution``.
        Erros: ``RepositoryNotFoundError``, ``InvalidStateTransitionError``.
        """
        ...

    def mark_updated(self, repository_id: int, commit: str) -> CatalogEntry:
        """Conclui indexação com sucesso: grava commits e vai a ``up_to_date``.

        Responsabilidade: transicionar ``indexing → up_to_date`` e gravar
        ``last_processed_commit = current_main_commit = commit``; fecha a execução
        corrente como ``SUCCEEDED`` (BDD CP-03). Cumpre o papel de
        "complete_execution_success" com o nome canônico do BDD.
        Motivo da separação: efeito colateral (carimbar commit + fechar execução)
        que a transição genérica não faz.
        Erros: ``RepositoryNotFoundError``, ``InvalidStateTransitionError``.
        """
        ...

    def mark_error(
        self,
        repository_id: int,
        message: str,
        error_at: datetime,
    ) -> CatalogEntry:
        """Registra falha: vai a ``error`` com mensagem + horário (BDD CP-06).

        Responsabilidade: transicionar ``indexing → error``, marcar a execução
        corrente como ``FAILED`` com ``error_message`` e ``error_at`` (REQ-023).
        Cumpre o papel de "fail_execution" com o nome canônico do BDD.
        Motivo da separação: efeito colateral de auditoria de erro no histórico.
        Erros: ``RepositoryNotFoundError``, ``InvalidStateTransitionError``.
        """
        ...

    # -- Comparação de commit / reconcile (T08/T14) -------------------------

    def update_main_commit(self, repository_id: int, commit: str) -> CatalogEntry:
        """Atualiza o tip conhecido da main (``current_main_commit``) — BR-004.

        Responsabilidade: registrar o commit-alvo da main sem, por si só, mudar o
        estado (a decisão de rebaixar fica em ``reconcile_repository``).
        Motivo da separação: separar "descobri um novo tip" (T08) de "reajustar o
        estado com base nele" (reconcile) mantém a comparação pura e testável.
        Erros: ``RepositoryNotFoundError``.
        """
        ...

    def reconcile_repository(self, repository_id: int) -> CatalogEntry:
        """Reajusta o estado comparando commit processado × tip (ENG-011).

        Responsabilidade: se ``state == up_to_date`` e
        ``not is_up_to_date(last_processed_commit, current_main_commit)``,
        rebaixar ``up_to_date → not_indexed`` preservando
        ``last_processed_commit`` como base de comparação (BDD CP-02); caso os
        commits sejam iguais, permanecer ``up_to_date`` (BDD CP-01). Para os
        demais estados, é no-op idempotente.
        Motivo da separação: concentra a política de reconcile do startup num
        único ponto, usando o helper puro ``transitions.is_up_to_date``.
        Erros: ``RepositoryNotFoundError``.
        """
        ...

    # -- Progresso da execução corrente (REQ-021; T14) ----------------------

    def update_progress(
        self,
        repository_id: int,
        percent: int,
        files_processed: int,
        files_total: int,
        current_stage: str,
    ) -> CatalogEntry:
        """Atualiza o progresso legível da execução corrente (BDD CP-04).

        Responsabilidade: persistir percentual, arquivos processados/total e a
        etapa corrente (texto livre), expostos em ``CatalogEntry.progress``
        (REQ-021).
        Motivo da separação: progresso é leitura de UI/MCP distinta do histórico
        de execução e das etapas por arquivo.
        Erros: ``RepositoryNotFoundError``.
        """
        ...

    # -- Execuções / histórico (REQ-023; T14/T18) ---------------------------

    def start_execution(
        self,
        repository_id: int,
        commit_target: str,
    ) -> IndexingExecution:
        """Abre uma nova execução para o commit alvo (BDD CP-03/CP-07).

        Responsabilidade: criar um `IndexingExecution` ``RUNNING`` e vinculá-lo
        como execução corrente do repositório, alimentando o histórico.
        Motivo da separação: o ciclo de vida da execução é separado da transição
        de estado do repo; uma nova tentativa (BR-005) abre nova execução sem
        apagar as anteriores.
        Erros: ``RepositoryNotFoundError``.
        """
        ...

    def list_executions(self, repository_id: int) -> Sequence[IndexingExecution]:
        """Lista o histórico de execuções do repositório (BDD CP-06/CP-07).

        Responsabilidade: retornar todas as execuções (inclusive falhas, com
        ``error_message``/``error_at``), retidas entre tentativas e após
        soft-delete (REQ-023).
        Motivo da separação: leitura de auditoria distinta do estado corrente.
        Erros: ``RepositoryNotFoundError`` se o repositório não existir.
        """
        ...

    # -- Etapas por arquivo (REQ-022; T14) ----------------------------------

    def record_file_stage(
        self,
        execution_id: int,
        file_path: str,
        stage: FileStage,
    ) -> FileProgress:
        """Registra (idempotente) a etapa de um arquivo na execução (BDD CP-05).

        Responsabilidade: setar o timestamp da etapa (`zoekt`/`tree_sitter`/
        `metadata_persisted`) para ``(execution_id, file_path)``, sem duplicar a
        linha do arquivo; re-registrar a mesma etapa é no-op idempotente
        (D-T03-009).
        Motivo da separação: rastreio granular por arquivo, separado do progresso
        agregado (`update_progress`).
        Erros: ``RepositoryNotFoundError`` se a execução não existir.
        """
        ...

    def list_file_progress(self, execution_id: int) -> Sequence[FileProgress]:
        """Lista o progresso por arquivo de uma execução (BDD CP-05).

        Responsabilidade: retornar um `FileProgress` por arquivo, com os
        timestamps de etapa preenchidos (ou ``None`` se ainda não concluída).
        Motivo da separação: leitura granular consumida pela UI/diagnóstico.
        Erros: ``RepositoryNotFoundError`` se a execução não existir.
        """
        ...
