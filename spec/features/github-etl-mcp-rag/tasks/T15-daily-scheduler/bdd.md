# BDD — T15-daily-scheduler

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T15-daily-scheduler` |
| Autor | Implementation Task Runner (QA step) |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão BDD | `0.2.0` |
| Design base | `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T15-daily-scheduler` |
| Rastreabilidade | REQ-017; BR-017, BR-023, BR-024; DEC-015; BDD-003, BDD-024; ENG-004, ENG-010, ENG-013; D-T15-001..012 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | `0.1.0` | MAJOR M-BDD-T15-01 (sem cenário de confinamento de SDK ao adaptador — ENG-013/BDD-024 — divergindo do padrão já aplicado em T14 `IO-14` e T16 `QS-05`); MAJOR M-BDD-T15-02 (SCH-03 usa o mesmo valor literal do default de produto (`0 2 * * *`) tanto para `AppSettings.index_cron` quanto para o resultado esperado, não distinguindo "lido de `AppSettings`" de "constante hardcoded" — não reverifica D-T15-001/M-T15-02 do `design.md`) |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.2.0` | M-BDD-T15-01 fechado (novo cenário `SCH-13`); M-BDD-T15-02 fechado (`SCH-03` reescrito com valor de `AppSettings.index_cron` distinto do default literal); sem BLOCKING/MAJOR abertos |

## Rastreabilidade

| Cenário | Aceite / requisito |
|---|---|
| SCH-01 | BDD-003 — tick com cron diário indexa elegíveis (`not_indexed`) |
| SCH-02 | BDD-003 / ENG-010 — expressões horárias / 2× dia / a cada N horas aceitas |
| SCH-03 | ENG-004 — sem preferência UI → usa `AppSettings.index_cron` (env/`INDEX_CRON`) |
| SCH-04 | ENG-004 — preferência persistida prevalece sobre env em runtime |
| SCH-05 | BDD-003 / BDD-004 — `up_to_date` com tip == processado **não** é reprocessado no tick |
| SCH-06 | BDD-003 — tip ≠ processado no tick → enfileira e indexa |
| SCH-07 | Expressão inválida → `InvalidCronExpressionError`; sem persistir; sem silent no-op |
| SCH-08 | `set_cron` válido reschedule sem editar `CONFIG_PATH` / conexões |
| SCH-09 | BR-017 — superfície de preferência **não** expõe CRUD de conexões/repos |
| SCH-10 | BDD-024 / DEC-015 — scheduling via APScheduler (`CronTrigger` / `BackgroundScheduler`) |
| SCH-11 | D-T15-011 — `run_tick_once` serializa ciclo (lock); reentrância bloqueia até fim |
| SCH-12 | BR-024 — preferência persistida via SQLAlchemy (adaptador / migration 0002) |
| SCH-13 | BDD-024 / ENG-013 / D-T15-010 — SDK (APScheduler/SQLAlchemy) confinado aos módulos adaptadores; `ports`/`errors`/`memory` não importam SDK |

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Steps / asserts | `tests/bdd/test_daily_scheduler.py` |
| Fakes / harness | `tests/unit/schedule/helpers.py` (após interfaces) |

## Como executar

```bash
python -m pytest tests/bdd/test_daily_scheduler.py -q
```

## Escopo e exclusões

### Em escopo

- `DailyScheduler` + cron APScheduler
- `CronPreferenceStore` (memória + contrato PG)
- Precedência ENG-004; validação tipada
- Tick via `StartupIndexReconcile` + `run_until_idle`
- Extensão `AppSettings.index_cron`

### Fora de escopo

| Item | Dono |
|---|---|
| UI / FastAPI de cron | T18 |
| Compose boot wiring | T19 |
| CRUD conexões | proibido (BR-017) |
| Pipeline de indexação interno | T14 |

## Cenários

### SCH-01 — Tick indexa elegíveis (BDD-003)

**Dado** repositórios ativos em `not_indexed` e scheduler com cron válido  
**Quando** `run_tick_once()`  
**Então** elegíveis passam a `up_to_date` (via orquestrador)  
**E** tip processado é carimbado.

### SCH-02 — Variedade de expressões cron (ENG-010)

**Dado** expressões `0 2 * * *`, `0 */6 * * *`, `0 0,12 * * *`  
**Quando** validadas / aplicadas via `set_cron`  
**Então** são aceitas sem erro  
**E** `active_cron()` reflete a expressão aplicada.

### SCH-03 — Default de env via `AppSettings` (ENG-004 / D-T15-001)

**Dado** `CronPreferenceStore` vazio (sem preferência persistida)  
**E** `AppSettings` construído com `index_cron == "0 3 * * *"` — valor **distinto** do literal default de produto (`0 2 * * *`), para provar que a fonte é o campo `AppSettings.index_cron` e não uma constante hardcoded no pacote `schedule`  
**Quando** o scheduler resolve a expressão ativa a partir desse `AppSettings`  
**Então** `active_cron()` == `"0 3 * * *"`  
**E** a fonte efetiva é env/default (não preference)  
**E** nenhuma leitura de `os.environ` ocorre dentro do pacote `schedule` (resolução via `AppSettings`, D-T15-001).

**Dado** (segundo caso) `AppSettings` construído sem `INDEX_CRON` em env (default de `AppSettings.index_cron` == `"0 2 * * *"`, T01)  
**Quando** o scheduler resolve a expressão ativa  
**Então** `active_cron()` == `"0 2 * * *"` — mesmo valor, mas obtido via `AppSettings.index_cron`, não via leitura própria de env pelo `schedule`.

### SCH-04 — Preferência UI prevalece (ENG-004)

**Dado** settings com `index_cron == "0 2 * * *"`  
**E** preferência persistida `"0 */6 * * *"`  
**Quando** o scheduler resolve / está em runtime  
**Então** `active_cron()` == `"0 */6 * * *"`.

### SCH-05 — Não reprocessa atualizado (BDD-004)

**Dado** repo `up_to_date` com tip == `last_processed_commit`  
**Quando** `run_tick_once()`  
**Então** portas de indexação (Zoekt/vector) **não** processam conteúdo novo  
**E** estado permanece `up_to_date`.

### SCH-06 — Novo commit no tick (BDD-003 + tip≠processado)

**Dado** repo `up_to_date` com `last_processed == C1` e tip atual `C2`  
**Quando** `run_tick_once()`  
**Então** o repo é indexado e fica `up_to_date` com `C2`.

### SCH-07 — Cron inválido tipado

**Dado** expressão inválida (`"not-a-cron"`, `"60 * * * *"`, campos a menos)  
**Quando** `set_cron` / validação / start com default inválido  
**Então** levanta `InvalidCronExpressionError`  
**E** preferência anterior (se houver) permanece intacta  
**E** não há silent no-op.

### SCH-08 — set_cron reagenda sem tocar CONFIG_PATH

**Dado** scheduler iniciado com cron A  
**Quando** `set_cron(B)` válido  
**Então** `active_cron()` == B  
**E** nenhuma API de conexões/CONFIG_PATH é usada.

### SCH-09 — Sem CRUD de conexões (BR-017)

**Dado** o pacote `github_rag.schedule`  
**Quando** inspecionada a superfície pública  
**Então** não expõe create/update/delete de conexões ou definições de repositório  
**E** só preferência de cron + lifecycle do scheduler.

### SCH-10 — APScheduler (BDD-024 / DEC-015)

**Dado** a implementação default do scheduler  
**Quando** inspecionado o módulo de scheduling  
**Então** usa APScheduler (`BackgroundScheduler` e/ou `CronTrigger`)  
**E** não implementa parser cron caseiro.

### SCH-11 — Lock de tick (D-T15-011)

**Dado** um `run_tick_once` em andamento (simulado com bloqueio controlado)  
**Quando** outro thread chama `run_tick_once`  
**Então** a segunda chamada espera o lock  
**E** os ciclos não se sobrepõem.

### SCH-12 — Persistência ORM (BR-024)

**Dado** o adaptador PostgreSQL de preferência  
**Quando** inspecionado  
**Então** usa SQLAlchemy / migration Alembic `0002_scheduler_preference`  
**E** não usa SQL ad hoc paralelo fora do ORM.

### SCH-13 — Confinamento de SDK aos adaptadores (BDD-024 / ENG-013 / D-T15-010)

**Dado** o pacote de produção `github_rag.schedule` (módulos `errors`, `ports`, `memory`, `cron_expr`, `scheduler`, `postgres`)  
**Quando** os imports de produção são inspecionados (AST) e `DailyScheduler`/`CronPreferenceStore` são exercidos só com fakes injetados  
**Então** `ports.py`, `errors.py` e `memory.py` **não** importam `apscheduler` nem `sqlalchemy`  
**E** `apscheduler` só aparece em `cron_expr.py` (validação via `CronTrigger.from_crontab`, D-T15-003) e `scheduler.py` (adaptador `BackgroundScheduler`, D-T15-004)  
**E** `sqlalchemy` só aparece em `postgres.py` (adaptador ORM, BR-024)  
**E** o domínio (`ports.py`) expõe apenas os `Protocol`s `CronPreferenceStore`/`DailyScheduler`, sem instanciar adaptadores concretos.
