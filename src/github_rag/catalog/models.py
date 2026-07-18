"""Modelo de domínio do catálogo — contratos T03 (enums + read models).

Responsabilidade deste módulo
    Declarar os enums fechados (`RepoOrigin`, `RepoState`, `FileStage`,
    `ExecutionStatus`) e as dataclasses imutáveis de leitura (`Progress`,
    `CatalogEntry`, `IndexingExecution`, `FileProgress`) que compõem a superfície
    de dados devolvida pela porta ``CatalogRepository``.

Motivo da separação
    Concentrar a *forma dos dados* (o "quê") separada das *regras de transição*
    (`transitions.py`, o "como muda") e da *porta de persistência*
    (`repository.py`, o "onde persiste"). Isso permite testar o domínio sem PG
    (design §3.1) e congela a forma de leitura consumida por T07/T14/T17/T18 e
    pelos testes BDD (resolve SUGGESTION B-3: forma de `CatalogEntry`/`Progress`).

Decisão de valores de enum (design §4.1, D-T03-004)
    Os valores são slugs ASCII estáveis em inglês; o rótulo em português de
    REQ-020 é responsabilidade de apresentação (T18). Herdam de ``str`` para que
    ``RepoState("not_indexed")`` e ``member.value`` funcionem (contrato exercido
    pelo BDD, CP-09).

Imutabilidade
    Todas as dataclasses são ``frozen=True``: são *snapshots de leitura*, não
    entidades mutáveis. Mutação de estado só ocorre via operações da porta, que
    devolvem um novo snapshot. Evita que consumidores alterem o catálogo por
    engano.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RepoOrigin(str, Enum):
    """Origem do repositório do catálogo (design §4.1).

    Responsabilidade
        Enumerar, de forma fechada, de onde o repositório provém.

    Motivo da separação
        Origem determina quais campos de identificação são obrigatórios
        (`github_org` para ``github``; `local_path` para ``local``) — invariante
        de integridade validado no adaptador via ``CHECK`` (design §5.1).
    """

    GITHUB = "github"
    LOCAL = "local"


class RepoState(str, Enum):
    """Estado de indexação do repositório (REQ-020 — exatamente 5, sem extras).

    Responsabilidade
        Enumerar o conjunto fechado de estados possíveis do repositório.

    Motivo da separação
        REQ-020 é fechado: qualquer outro valor é proibido. Concentrar aqui a
        definição evita reintroduzir `desatualizado`/`indisponível` (proibidos —
        D-T03-004; BDD CP-09). "Desatualizado" é derivado por comparação de
        commit + reconcile; "ausente da config" é soft-delete (`active=False`),
        não um estado.
    """

    NOT_INDEXED = "not_indexed"
    QUEUED = "queued"
    INDEXING = "indexing"
    UP_TO_DATE = "up_to_date"
    ERROR = "error"


class FileStage(str, Enum):
    """Etapa de processamento por arquivo (REQ-022; design §4.1).

    Responsabilidade
        Enumerar as etapas rastreadas por arquivo dentro de uma execução.

    Motivo da separação
        O enfileiramento/pipeline (T14) registra a passagem de cada arquivo por
        estas etapas; manter o enum no domínio mantém a API ``record_file_stage``
        tipada mesmo com o schema usando coluna-por-etapa (D-T03-009).
    """

    ZOEKT = "zoekt"
    TREE_SITTER = "tree_sitter"
    METADATA_PERSISTED = "metadata_persisted"


class ExecutionStatus(str, Enum):
    """Status de uma execução de indexação (design §5.1; resolve SUGGESTION S-2).

    Responsabilidade
        Enumerar o ciclo de vida de um registro de `IndexingExecution`.

    Motivo da separação
        Status de execução é DISTINTO de `RepoState` (REQ-020): uma execução pode
        estar ``failed`` enquanto o repositório está ``error`` ou já ``queued`` de
        novo (nova tentativa — BR-005). Separar evita colapsar histórico de
        execução com o estado corrente do repositório (BDD CP-06/CP-07).
    """

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class Progress:
    """Progresso da execução corrente de um repositório (REQ-021; BDD CP-04).

    Responsabilidade
        Expor, de forma imutável, o progresso legível: percentual, arquivos
        processados/total e a etapa corrente (texto livre exibível).

    Motivo da separação
        Congela a *forma* do progresso como objeto agregado exposto em
        ``CatalogEntry.progress`` (resolve SUGGESTION B-3): o BDD lê
        ``entry.progress.percent`` etc. Manter em objeto próprio (em vez de
        campos planos no `CatalogEntry`) mantém a leitura coesa e permite
        ``None`` quando não há execução corrente.

    Invariantes
        - ``percent`` ∈ [0, 100] quando presente (REQ-021).
        - ``current_stage`` é texto livre exibível (não é `FileStage`; REQ-021).
        - Campos podem ser ``None`` quando ainda não há progresso registrado.
    """

    percent: int | None
    files_processed: int | None
    files_total: int | None
    current_stage: str | None


@dataclass(frozen=True)
class CatalogEntry:
    """Snapshot de leitura de um repositório do catálogo (SoT; design §4.3).

    Responsabilidade
        Representar uma linha do catálogo ativo/histórico como devolvida pela
        porta: identidade, origem, estado (REQ-020), commits de comparação
        (BR-004), progresso agregado (REQ-021), flags de soft-delete e a versão
        de lock otimista.

    Motivo da separação
        É a *view* imutável consumida por T07/T14/T17/T18. Não expõe detalhes de
        persistência (SQLAlchemy/linhas); o adaptador PG e o fake produzem o
        mesmo tipo, garantindo paridade semântica (contrato da porta).

    Invariantes (design §4.1/§4.3/§5.1)
        - ``origin == GITHUB`` ⇒ ``github_org`` preenchido; ``origin == LOCAL``
          ⇒ ``local_path`` preenchido (validado no adaptador via ``CHECK``).
        - ``last_processed_commit is None`` ⇔ nunca foi processado (BR-004).
        - Estado ``up_to_date`` só é válido com
          ``last_processed_commit == current_main_commit`` (regra de domínio;
          ver `transitions.is_up_to_date`).
        - ``row_version`` é usado como ``expected_version`` em
          ``transition_state`` (lock otimista — D-T03-008).
        - ``active is False`` ⇒ fora do catálogo ativo (soft-delete); histórico
          preservado (T07).
    """

    id: int
    connection_name: str
    origin: RepoOrigin
    repo_identifier: str
    state: RepoState
    active: bool
    row_version: int
    github_org: str | None = None
    local_path: str | None = None
    last_processed_commit: str | None = None
    current_main_commit: str | None = None
    progress: Progress | None = None
    current_execution_id: int | None = None
    deactivated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class IndexingExecution:
    """Registro do histórico de execuções (REQ-023; BDD-008; design §5.1).

    Responsabilidade
        Representar uma execução de indexação: alvo (commit), status, início/fim
        e, em caso de falha, mensagem e horário do erro.

    Motivo da separação
        O histórico é a trilha de auditoria (design §10) e é retido mesmo após
        soft-delete do repositório (T07). Separado do `CatalogEntry` porque um
        repositório tem N execuções (BDD CP-07: falha + nova tentativa coexistem).

    Invariantes
        - ``status == FAILED`` ⇒ ``error_message`` e ``error_at`` preenchidos
          (REQ-023; BDD CP-06).
        - ``status == SUCCEEDED`` ⇒ ``finished_at`` preenchido.
        - ``commit_target`` é o commit alvo/processado desta execução.
    """

    id: int
    repository_id: int
    status: ExecutionStatus
    started_at: datetime
    finished_at: datetime | None = None
    commit_target: str | None = None
    error_message: str | None = None
    error_at: datetime | None = None


@dataclass(frozen=True)
class FileProgress:
    """Progresso por arquivo dentro de uma execução (REQ-022; design §5.1).

    Responsabilidade
        Representar a passagem de UM arquivo pelas etapas `zoekt`,
        `tree_sitter` e `metadata_persisted`, cada uma marcada por seu timestamp.

    Motivo da separação
        Modela a decisão D-T03-009 (coluna-por-etapa): registrar uma etapa =
        setar o timestamp correspondente, de forma idempotente e sem duplicar a
        linha do arquivo (BDD CP-05). Um timestamp ``None`` significa etapa ainda
        não concluída.

    Invariantes
        - Único por ``(execution_id, file_path)`` (BDD CP-05: sem duplicação).
        - Registrar etapa já registrada é no-op idempotente (mantém o timestamp).
    """

    id: int
    execution_id: int
    file_path: str
    zoekt_at: datetime | None = None
    tree_sitter_at: datetime | None = None
    metadata_persisted_at: datetime | None = None
