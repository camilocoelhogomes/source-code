# Interfaces — T15-daily-scheduler

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T15-daily-scheduler` |
| Autor | Tech Lead Architect (candidato via Implementation Task Runner) |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.2.0` |
| Design base | `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T15-daily-scheduler` |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | `0.1.0` | MAJOR M-I-T15-01 (Protocols sem `@runtime_checkable`); MAJOR M-I-T15-02 (docstrings de classe/método sem Responsabilidade+Motivo em `CronPreferenceStore`/`DailyScheduler`, `stop`/`active_cron` sem comentário algum); MAJOR M-I-T15-03 (tabela ENG-013 §8 não distingue explicitamente que `sqlalchemy` é proibido em `cron_expr.py`/`scheduler.py` e `apscheduler` proibido em `postgres.py`, divergindo da granularidade exigida por SCH-13) |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.2.0` | M-I-T15-01/02/03 fechados pelo próprio Architect (§6 `@runtime_checkable` + docstrings completos; §7 docstrings de módulo `postgres.py`/`memory.py` + nota de naming convention; §8 tabela reescrita por módulo); sem BLOCKING/MAJOR abertos |

## 1. Escopo

| Contrato | Módulo | Papel |
|---|---|---|
| Constantes env cron | `settings.py` (T01) | `ENV_INDEX_CRON`, `DEFAULT_INDEX_CRON`, `AppSettings.index_cron` |
| Erros tipados | `schedule/errors.py` | `InvalidCronExpressionError`, `SchedulerConfigError` |
| Validação cron | `schedule/cron_expr.py` | `validate_cron_expression` via APScheduler |
| Portas | `schedule/ports.py` | `CronPreferenceStore`, `DailyScheduler` |
| Fake preferência | `schedule/memory.py` | `InMemoryCronPreferenceStore` |
| Adaptador PG | `schedule/postgres.py` | `SqlAlchemyCronPreferenceStore` + modelo ORM |
| Scheduler | `schedule/scheduler.py` | `DefaultDailyScheduler` (APScheduler) |
| Migration | `migrations/versions/0002_scheduler_preference.py` | Tabela singleton |

## 2. Decisões de interface

| ID | Decisão |
|---|---|
| I-T15-001 | Portas `CronPreferenceStore` e `DailyScheduler` distintas |
| I-T15-002 | `DailyScheduler.set_cron` é o único caminho de escrita para consumidores (persiste + reschedule) |
| I-T15-003 | `run_tick_once` é o único ponto síncrono reconcile+drain (lock D-T15-011) |
| I-T15-004 | Construtores keyword-only; `default_cron: str` injetado (de `AppSettings.index_cron`) |
| I-T15-005 | Pacote `schedule`: APScheduler/SQLAlchemy só em `cron_expr`/`scheduler`/`postgres`; `ports`/`errors`/`memory` sem SDK |
| I-T15-006 | Extensão T01: `ENV_INDEX_CRON="INDEX_CRON"`, `DEFAULT_INDEX_CRON="0 2 * * *"`, `AppSettings.index_cron: str` |
| I-T15-007 | `CronPreferenceStore.clear()` remove override; scheduler volta a `default_cron` |
| I-T15-008 | Timezone do trigger: UTC |
| I-T15-009 | `CronPreferenceStore` e `DailyScheduler` decoradas com `@runtime_checkable` (convenção de todos os Protocols do produto — T01/T03/T04/T14) |

## 3. Extensão T01 — `AppSettings`

```python
ENV_INDEX_CRON = "INDEX_CRON"
DEFAULT_INDEX_CRON = "0 2 * * *"

class AppSettings(Protocol):
    @property
    def index_workers(self) -> int: ...
    @property
    def query_workers(self) -> int: ...
    @property
    def config_path(self) -> Path | None: ...
    @property
    def index_cron(self) -> str:
        """Expressão cron default de boot (env INDEX_CRON ou DEFAULT_INDEX_CRON).

        Responsabilidade: expor a string já resolvida (ausente/blank → default).
        Motivo da separação: schedule consome AppSettings; não relê os.environ (D-T15-001).
        Invariantes: sempre str não-vazia após strip; sem validação de sintaxe cron aqui.
        Erros: nenhum na propriedade; sintaxe inválida falha em schedule/cron_expr.
        Compatibilidade: string OS-agnostic; nenhuma diferença de formato entre
        Windows, macOS, Linux ou runtime T19 (não é path, não usa separador de SO).
        """
        ...
```

- `load_settings`: lê `INDEX_CRON`; blank/ausente → `DEFAULT_INDEX_CRON`.
- **Não** valida sintaxe cron em T01 (só em `validate_cron_expression`).

## 4. Erros

```python
class InvalidCronExpressionError(ValueError):
    """Expressão cron inválida (sintaxe/campo).

    Responsabilidade: rejeitar cron inválido sem aplicar parcialmente.
    Motivo da separação: distinto de misconfig de wiring (SchedulerConfigError).
    Mensagem: cita a expressão (truncada se > 200 chars); nunca segredos.
    """

class SchedulerConfigError(RuntimeError):
    """Misconfiguração do scheduler (deps ausentes, start inválido).

    Responsabilidade: falhas de wiring/boot do DailyScheduler.
    Motivo da separação: não confundir com erro de sintaxe cron.
    """
```

## 5. Validação

```python
def validate_cron_expression(expression: str) -> str:
    """Valida expressão cron de 5 campos via CronTrigger.from_crontab.

    Responsabilidade: único validador de sintaxe do produto.
    Motivo da separação: isola APScheduler da porta DailyScheduler/store.
    Retorno: expressão stripada se válida.
    Erros: InvalidCronExpressionError.
    """
    ...
```

## 6. Portas

```python
from typing import Protocol, runtime_checkable
```

- Ambas as portas são decoradas com `@runtime_checkable` (I-T15-009), seguindo a convenção já aplicada em **todos** os Protocols do produto (`AppSettings` T01, `CatalogRepository` T03, `WorkerLimiter` T04, `IndexingOrchestrator`/`StartupIndexReconcile` T14, `VectorStore`/`MetadataGenerator` etc.). Habilita `isinstance(fake_ou_adapter, Porta)` nos testes unitários (padrão já exercido em `tests/unit/test_settings.py::isinstance(result, AppSettings)` e `tests/unit/index/metadata/test_ports.py::test_ut_p01_runtime_checkable_implementations`), sem o que o Developer/QA não conseguiriam validar conformidade estrutural de fakes e adaptadores sem duplicar checagem manual de atributos.

### `CronPreferenceStore`

```python
@runtime_checkable
class CronPreferenceStore(Protocol):
    """Porta da preferência de cron persistida pela UI (BR-017, BR-024).

    Responsabilidade: SoT (PostgreSQL) da expressão cron escolhida pelo
    operador via T18; get/set/clear puros de I/O de preferência — sem
    lifecycle de job nem acesso ao catálogo de repositórios.

    Motivo da separação (I-T15-001): a preferência é um dado de configuração
    de agenda, não uma operação de scheduling. Separar de `DailyScheduler`
    permite testar a semântica de persistência (validar-antes-de-gravar,
    `clear` ≠ `set("")`) sem instanciar APScheduler, e mantém `set`/`clear`
    fora do alcance direto de consumidores (T18 só deve escrever via
    `DailyScheduler.set_cron`, nunca diretamente nesta porta — D-T15-009).
    """

    def get(self) -> str | None:
        """Lê preferência UI persistida, ou None se ausente.

        Responsabilidade: leitura pura da SoT (PostgreSQL); não resolve
        default nem consulta `AppSettings` (isso é `DailyScheduler.active_cron`).
        Motivo da separação: preferência ≠ catálogo de repos (BR-017).
        Erros: nenhum; ausência é representada por `None`, não por exceção.
        """
        ...

    def set(self, cron_expression: str) -> str:
        """Valida e persiste. Retorna expressão normalizada.

        Responsabilidade: escrita validada; inválido não grava.
        Motivo da separação: store não reagenda jobs (DailyScheduler.set_cron faz isso).
        Erros: InvalidCronExpressionError.
        """
        ...

    def clear(self) -> None:
        """Remove override; runtime volta ao default_cron de settings.

        Responsabilidade: apagar singleton / marcar ausência.
        Motivo da separação: clear ≠ set("") (vazio é inválido).
        Erros: nenhum; idempotente se já ausente.
        """
        ...
```

### `DailyScheduler`

```python
@runtime_checkable
class DailyScheduler(Protocol):
    """Porta de lifecycle e agendamento cron da indexação periódica (BDD-003/024).

    Responsabilidade: iniciar/parar o job cron, resolver a expressão ativa
    (precedência preferência > default — ENG-004), expor o único caminho de
    escrita (`set_cron`) e o único ponto síncrono de execução do ciclo
    reconcile+drain (`run_tick_once`, lock D-T15-011).

    Motivo da separação (I-T15-001): distinta de `CronPreferenceStore` porque
    concentra as regras que dependem de *estado em runtime* (job ativo,
    lock de execução) e de orquestração (T14), enquanto a store é só
    persistência da preferência; evita que `set`/`clear` da store apliquem
    efeito colateral de reagendamento sem o caller pedir.
    """

    def start(self) -> None:
        """Inicia BackgroundScheduler com job CronTrigger (UTC).

        Responsabilidade: registrar job id=index_cron_tick; max_instances=1; coalesce=True.
        Motivo da separação: único ponto que materializa o job APScheduler;
        `active_cron()`/`set_cron()` não iniciam o scheduler implicitamente.
        Erros: InvalidCronExpressionError se active_cron inválido; SchedulerConfigError.
        """
        ...

    def stop(self) -> None:
        """Para o scheduler de forma idempotente.

        Responsabilidade: encerrar o `BackgroundScheduler` sem lançar se já parado.
        Motivo da separação: simétrico a `start()`; evita que consumidores
        (T19, testes) precisem checar estado antes de parar.
        Erros: nenhum; chamar sem `start()` prévio é no-op.
        """
        ...

    def active_cron(self) -> str:
        """Expressão efetiva: preference se não-None else default_cron.

        Responsabilidade: única fonte de leitura da expressão em vigor,
        aplicando a precedência ENG-004 (D-T15-002) sem reler `os.environ`.
        Motivo da separação: consumidores (T18 leitura, testes) não devem
        reimplementar a precedência preferência × default.
        Erros: nenhum.
        """
        ...

    def set_cron(self, cron_expression: str) -> str:
        """Valida, persiste via store, reschedule job se running.

        Responsabilidade: único caminho de escrita para T18.
        Motivo da separação: evita persistir sem reagendar.
        Erros: InvalidCronExpressionError (store intacto se inválido).
        """
        ...

    def run_tick_once(self) -> None:
        """Ciclo reconcile+drain sob lock de instância.

        Responsabilidade: StartupIndexReconcile.run() + IndexingOrchestrator.run_until_idle().
        Motivo da separação: único ponto síncrono (D-T15-011); job cron chama só isto.
        Erros: propaga falhas de `StartupIndexReconcile`/`IndexingOrchestrator`; lock é sempre liberado (context manager) mesmo em exceção.
        """
        ...
```

### `DefaultDailyScheduler` deps (keyword-only)

```python
DefaultDailyScheduler(
    *,
    preference_store: CronPreferenceStore,
    reconcile: StartupIndexReconcile,
    orchestrator: IndexingOrchestrator,
    default_cron: str,  # tipicamente settings.index_cron
)
```

## 7. Persistência PostgreSQL

### `schedule/postgres.py`

```python
"""Adaptador PostgreSQL da preferência de cron (BR-024).

Responsabilidade deste módulo
    Implementar `SqlAlchemyCronPreferenceStore` (satisfaz `CronPreferenceStore`)
    e o modelo ORM da tabela singleton `scheduler_preference`.

Motivo da separação
    Único ponto onde `sqlalchemy` é importado no pacote `schedule` (ENG-013 /
    D-T15-010); `ports.py`/`memory.py` permanecem testáveis sem PostgreSQL.
"""
```

Tabela `scheduler_preference`:

| Coluna | Tipo |
|---|---|
| `id` | SmallInteger PK (=1) |
| `cron_expression` | Text NOT NULL |
| `updated_at` | DateTime(timezone=True) |

- `SqlAlchemyCronPreferenceStore(session_factory)` — SQLAlchemy 2.x; mesma forma de injeção de `session_factory` já usada em `PostgresCatalogRepository` (T03, `catalog/postgres/factory.py`).
- Migration Alembic `0002_scheduler_preference` (`down_revision = 0001_initial_catalog`).
- `Base(DeclarativeBase)` própria no pacote `schedule`, apontando ao mesmo `DATABASE_URL` / `session_factory` injetada (não reabre `catalog/postgres/models.py`). **Deve reutilizar a mesma `_NAMING_CONVENTION`** (`ix`/`uq`/`ck`/`fk`/`pk`) definida em `catalog/postgres/models.py`, para que os nomes de constraints da tabela `scheduler_preference` sigam o mesmo padrão determinístico do catálogo (evita `pk`/`uq` com nomes default do dialeto divergentes entre tabelas do mesmo banco).

### `schedule/memory.py`

```python
"""Fake em memória da preferência de cron — implementação de referência.

Responsabilidade deste módulo
    Implementar `InMemoryCronPreferenceStore`: mesma semântica get/set/clear
    de `SqlAlchemyCronPreferenceStore`, sem PostgreSQL.

Motivo da separação
    Permite testar `DailyScheduler` e os cenários SCH-01..SCH-11 em qualquer
    SO sem Docker/PG (paridade com o padrão `InMemoryCatalogRepository`, T03);
    não importa `sqlalchemy` (ENG-013).
"""
```

- Dict/atributo em memória; mesma semântica get/set/clear + validação via `validate_cron_expression`.

## 8. ENG-013 / BDD-024 — confinamento de SDK (SCH-13)

| Módulo | SDK permitido | Proibido |
|---|---|---|
| `ports.py` | nenhum | `apscheduler`, `sqlalchemy`, PyGithub, GitPython |
| `errors.py` | nenhum | `apscheduler`, `sqlalchemy`, PyGithub, GitPython |
| `memory.py` | nenhum | `apscheduler`, `sqlalchemy`, PyGithub, GitPython |
| `cron_expr.py` | `apscheduler` (só `CronTrigger.from_crontab`, D-T15-003) | `sqlalchemy`, PyGithub, GitPython |
| `scheduler.py` | `apscheduler` (`BackgroundScheduler`, D-T15-004) | `sqlalchemy`, PyGithub, GitPython |
| `postgres.py` | `sqlalchemy` (ORM, D-T15-010) | `apscheduler`, PyGithub, GitPython, SQL ad hoc fora do ORM |

Cada SDK aparece em exatamente um adaptador; nenhum módulo importa os dois SDKs. Verificação: inspeção AST de imports (SCH-13), a mesma técnica de `IO-14` (T14) e `QS-05` (T16).

Import estático de `apscheduler` / `sqlalchemy` restrito aos adaptadores listados.

## 9. Fora de escopo da interface

- Rotas FastAPI / UI (T18)
- Wiring compose (T19)
- Métodos de CRUD de conexões
- Alteração da porta `CatalogRepository`
