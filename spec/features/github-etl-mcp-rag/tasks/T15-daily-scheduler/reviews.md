# Reviews — T15-daily-scheduler

## Revisão 1 — Tech Lead Architect — `design.md` v0.1.0 → v0.2.0

- **Revisor:** Tech Lead Architect
- **Artefato:** `spec/features/github-etl-mcp-rag/tasks/T15-daily-scheduler/design.md`
- **Data:** 2026-07-18

### Achados

| ID | Severidade | Evidência | Descrição | Correção esperada |
|---|---|---|---|---|
| M-T15-01 | MAJOR | `design.md` v0.1.0 §3.3 (`on_tick(): StartupIndexReconcile.run() + run_until_idle()`) | `StartupIndexReconcile.run()` (T14, `spec/.../T14-indexing-orchestrator/design.md` §3.2) reclassifica `indexing`/`queued` órfãos assumindo perda da fila em memória por reinício de processo (ENG-011). Reutilizar esse método em **todo tick periódico**, sem guarda de concorrência, é seguro apenas enquanto nada mais chamar o orquestrador em paralelo. T18 (UI, disparo sob demanda) depende de T14/T15/T16/T07 e deve compartilhar a mesma instância de `IndexingOrchestrator`; sem serialização explícita, um disparo sob demanda concorrente a um tick teria sua execução `indexing` legítima incorretamente marcada como órfã, reenfileirada e reprocessada em duplicidade. | Introduzir guarda de execução única (`run_tick_once` com lock de instância) e registrar handoff de contrato obrigatório para T18 reutilizar o mesmo guard antes de chamar o orquestrador. |
| M-T15-02 | MAJOR | `design.md` v0.1.0 §4.2 ("não obrigatório estender `AppSettings` em T01... factory lê env/`os.environ`") | Contradiz o próprio design de T01 (`spec/.../T01-project-foundation/design.md` §2.5, tabela de variáveis: `INDEX_CRON` já reservada com "dono futuro: T15") e o padrão estabelecido por T04 (`spec/.../T04-worker-limiter/design.md` §2.1 item 4: "não reparsear env no limiter"; consome `AppSettings.index_workers`/`query_workers`). Ler `os.environ` ad-hoc no pacote `schedule` duplica a fonte de verdade de configuração e quebra a convenção de settings centralizados. | Estender `AppSettings`/`load_settings` (T01) com `index_cron: str`; pacote `schedule` consome `AppSettings`, nunca `os.environ` diretamente. |

### Verificação dos demais critérios (sem achados)

- ENG-004 (env default; preferência UI PG prevalece): D-T15-001/002 conformes.
- ENG-010 (só cron, sem segundo modelo de config): §1/§2 conformes.
- DEC-015/BDD-024 (APScheduler; SDK confinado ao adaptador): D-T15-003/004/010 conformes.
- Persistência de preferência sem CRUD de conexões (BR-017) e via SQLAlchemy (BR-024): D-T15-006, tabela `scheduler_preference` isolada de `CatalogRepository`, adaptador `SqlAlchemyCronPreferenceStore`.
- Expressão inválida → erro tipado, sem aplicação parcial: D-T15-003/008, §3.5.
- Escopo: sem UI, sem compose — §11 conforme.
- Ambiguidade menor identificada e corrigida no mesmo ciclo: §3.4 citava dois métodos alternativos (`notify_preference_changed` | `set_cron`) para o mesmo efeito; unificado em `set_cron` como único ponto de escrita.

### Resultado

`CHANGES_REQUIRED` na v0.1.0 (M-T15-01, M-T15-02) → correções aplicadas pelo próprio Architect no `design.md` (§3.1 D-T15-011/012, §3.6, §4.2, §5, §10, §12) → **`APPROVED_BY_ARCHITECT`** na v0.2.0. Sem achados BLOCKING ou MAJOR abertos.

## Revisão 2 — Tech Lead Architect — `bdd.md` v0.1.0 → v0.2.0

- **Revisor:** Tech Lead Architect
- **Artefato:** `spec/features/github-etl-mcp-rag/tasks/T15-daily-scheduler/bdd.md`
- **Data:** 2026-07-18

### Achados

| ID | Severidade | Evidência | Descrição | Correção esperada |
|---|---|---|---|---|
| M-BDD-T15-01 | MAJOR | `bdd.md` v0.1.0, cenários SCH-01..SCH-12 (sem cenário de confinamento de SDK) | `design.md` §3.1 D-T15-010 exige que APScheduler fique confinado ao adaptador de scheduling (ENG-013), e BDD-024 exige conformidade de integrações com SDK oficial só nos adaptadores. As tasks-irmãs já estabelecem esse cenário como parte do gate BDD-024: T14 `bdd.md` `IO-14` ("Sem SDKs no pacote indexing") e T16 `bdd.md` `QS-05` ("nenhum client paralelo ad-hoc em `github_rag.query`"). O candidato de T15 cobria o **uso** de APScheduler/SQLAlchemy (SCH-10, SCH-12) mas não a **ausência** de import desses SDKs fora dos módulos adaptadores (`ports.py`, `errors.py`, `memory.py`), deixando D-T15-010 sem verificação behavioral/AST equivalente à dos pares. | Adicionar cenário de inspeção de imports (AST) confirmando que `ports.py`/`errors.py`/`memory.py` não importam `apscheduler`/`sqlalchemy`, e que esses SDKs só aparecem nos módulos adaptadores (`cron_expr.py`/`scheduler.py` para APScheduler; `postgres.py` para SQLAlchemy). |
| M-BDD-T15-02 | MAJOR | `bdd.md` v0.1.0, cenário SCH-03 ("`AppSettings.index_cron == "0 2 * * *"`" ... "`active_cron()` == default de settings") | O valor de entrada (`AppSettings.index_cron`) e o valor esperado de saída eram o mesmo literal do default de produto (`0 2 * * *`) definido em `design.md` §4.2/D-T15-001. Um teste derivado desse cenário passaria mesmo se a implementação ignorasse `AppSettings.index_cron` e apenas retornasse uma constante hardcoded local igual ao default — não distingue "lido de `AppSettings`" de "hardcoded coincidente". Isso reabre, no nível de BDD, o risco já registrado como MAJOR M-T15-02 no `design.md` (leitura ad-hoc de env), sem uma verificação que de fato force a dependência em `AppSettings.index_cron`. | Reescrever SCH-03 usando um valor de `AppSettings.index_cron` distinto do literal default de produto (ex.: `"0 3 * * *"`) como caso principal, comprovando que `active_cron()` reflete exatamente o campo de settings; manter o caso do default literal (`0 2 * * *`, ausência de env) como segundo caso, agora não ambíguo por já haver o caso discriminante. |

### Verificação dos demais critérios (sem achados)

- Cobertura dos critérios de aceite da task (T15-daily-scheduler.md): cron UI/env (SCH-03/04), tick elegíveis (SCH-01/06), sem reprocessar `up_to_date` (SCH-05), inválido tipado (SCH-07), APScheduler (SCH-10), BR-017 (SCH-09) — todos presentes e rastreados.
- Alinhamento ao `design.md` 0.2.0: `AppSettings.index_cron` (SCH-03, corrigido), `run_tick_once` com lock (SCH-11, D-T15-011), tick = `StartupIndexReconcile` + `run_until_idle` (SCH-01/05/06, §3.3).
- Sem antecipação de UI T18: cenários exercitam `DailyScheduler`/`CronPreferenceStore` diretamente (fakes/contratos), sem simular telas ou rotas FastAPI; seção "Fora de escopo" explicita UI/FastAPI como T18.
- BR-024 (SQLAlchemy/Alembic) e BR-017 (sem CRUD de conexões): SCH-12 e SCH-09 conformes.
- Rastreabilidade e escopo/exclusões coerentes com `T15-daily-scheduler.md` e `design.md` §11.

### Resultado

`CHANGES_REQUIRED` na v0.1.0 (M-BDD-T15-01, M-BDD-T15-02) → correções aplicadas pelo próprio Architect no `bdd.md` (SCH-03 reescrito; novo SCH-13; tabela de rastreabilidade e histórico atualizados) → **`APPROVED_BY_ARCHITECT`** na v0.2.0. Sem achados BLOCKING ou MAJOR abertos.

## Revisão 3 — Tech Lead Architect — `interfaces.md` v0.1.0 → v0.2.0

- **Revisor:** Tech Lead Architect
- **Artefato:** `spec/features/github-etl-mcp-rag/tasks/T15-daily-scheduler/interfaces.md`
- **Data:** 2026-07-18

### Achados

| ID | Severidade | Evidência | Descrição | Correção esperada |
|---|---|---|---|---|
| M-I-T15-01 | MAJOR | `interfaces.md` v0.1.0 §6 (`class CronPreferenceStore(Protocol):` / `class DailyScheduler(Protocol):`, sem `@runtime_checkable`) | Todos os demais Protocols do produto são decorados com `@runtime_checkable` — `AppSettings` (`src/github_rag/settings.py:120`), `CatalogRepository` (`src/github_rag/catalog/repository.py:44`), `WorkerLimiter` (`src/github_rag/concurrency/limiter.py:51`), `IndexingOrchestrator`/`StartupIndexReconcile` (`src/github_rag/indexing/ports.py:17,43`), entre outros — e há teste dedicado ao padrão (`tests/unit/index/metadata/test_ports.py::test_ut_p01_runtime_checkable_implementations`, `tests/unit/test_settings.py:65`). Sem o decorator, `isinstance(fake_ou_adapter, Porta)` levanta `TypeError` em runtime, impedindo o QA de escrever o UT análogo para T15 e quebrando a convenção estrutural do pacote. | Decorar `CronPreferenceStore` e `DailyScheduler` com `@runtime_checkable`. |
| M-I-T15-02 | MAJOR | `interfaces.md` v0.1.0 §6 (`CronPreferenceStore`/`DailyScheduler` sem docstring de classe; `stop()`/`active_cron()` sem nenhum comentário de Responsabilidade/Motivo) | Regra do usuário exige que toda interface tenha comentário de responsabilidade e do motivo da separação. O candidato documentava a separação I-T15-001 só na tabela de decisões (§2), fora do código da interface, e dois métodos da porta `DailyScheduler` (`stop`, `active_cron`) não tinham nenhum comentário, divergindo do padrão de `AppSettings` (T01) e `WorkerLimiter`/`WorkerLimiterError` (T04), que documentam Responsabilidade+Motivo na própria classe/Protocol. | Adicionar docstring de classe (Responsabilidade + Motivo da separação, referenciando I-T15-001) em `CronPreferenceStore` e `DailyScheduler`; completar `stop()`/`active_cron()`/`start()` com Responsabilidade/Motivo/Erros. |
| M-I-T15-03 | MAJOR | `interfaces.md` v0.1.0 §8 (tabela `Permitido no módulo` / `Proibido` com 3 linhas genéricas) | BDD `SCH-13` (v0.2.0, `APPROVED_BY_ARCHITECT`) exige que `apscheduler` só apareça em `cron_expr.py`/`scheduler.py` **e** `sqlalchemy` só em `postgres.py` — isto é, proibição cruzada entre adaptadores, não apenas a proibição de SDK nos módulos de domínio. A tabela do candidato não declarava que `sqlalchemy` é proibido em `cron_expr.py`/`scheduler.py`, nem que `apscheduler` é proibido em `postgres.py`, deixando a granularidade do gate ENG-013/BDD-024 menos estrita que o cenário já aprovado que a interface deveria refletir. | Reescrever a tabela §8 por módulo, listando explicitamente o SDK permitido e todos os proibidos (incluindo o SDK do adaptador "irmão"). |

### Verificação dos demais critérios (sem achados)

- Alinhamento com `design.md` 0.2.0: `AppSettings.index_cron` (§3, D-T15-001), `run_tick_once` com lock de instância (§6, D-T15-011), `set_cron` como único caminho de escrita (§6, D-T15-002/D-T15-009), timezone UTC (I-T15-008).
- Sem CRUD de conexões (BR-017): superfície de `CronPreferenceStore`/`DailyScheduler` restrita a preferência de cron + lifecycle do scheduler; §9 explicita exclusão de CRUD/`CatalogRepository`.
- APScheduler confinado a `cron_expr.py`/`scheduler.py`; SQLAlchemy confinado a `postgres.py` (corrigido em §8, M-I-T15-03).
- Migration `0002_scheduler_preference` com `down_revision = "0001_initial_catalog"` confere com a revisão real (`migrations/versions/0001_initial_catalog_schema.py:18-19`).
- `SqlAlchemyCronPreferenceStore(session_factory)` alinhado ao padrão de injeção de `PostgresCatalogRepository` (T03, `catalog/postgres/factory.py:52`).
- Construtores keyword-only (I-T15-004) conforme padrão T14 (I-T14-008).

### Resultado

`CHANGES_REQUIRED` na v0.1.0 (M-I-T15-01, M-I-T15-02, M-I-T15-03) → correções aplicadas pelo próprio Architect no `interfaces.md` (§6 `@runtime_checkable` + docstrings completos de classe/método; §7 docstrings de módulo `postgres.py`/`memory.py` + nota de naming convention; §8 tabela de confinamento de SDK reescrita por módulo; §2 nova decisão I-T15-009) → **`APPROVED_BY_ARCHITECT`** na v0.2.0. Sem achados BLOCKING ou MAJOR abertos.

## Revisão 4 — Tech Lead Architect — `unit-test-plan.md` v0.1.0 → v0.2.0 + testes (`tests/unit/schedule/*`, `tests/bdd/test_daily_scheduler.py`)

- **Revisor:** Tech Lead Architect
- **Artefatos:** `spec/features/github-etl-mcp-rag/tasks/T15-daily-scheduler/unit-test-plan.md`; `tests/unit/schedule/test_settings_cron.py`; `tests/unit/schedule/test_cron_expr.py`; `tests/unit/schedule/test_memory_store.py`; `tests/unit/schedule/test_scheduler.py`; `tests/unit/schedule/test_eng013.py`; `tests/unit/schedule/helpers.py`; `tests/bdd/test_daily_scheduler.py`; `pyproject.toml`
- **Data:** 2026-07-18

### Achados

| ID | Severidade | Evidência | Descrição | Correção esperada |
|---|---|---|---|---|
| M-UT-T15-01 | MAJOR | `unit-test-plan.md` v0.1.0 (UT-S10 "reschedule path \| SCH-08"); `bdd.md` v0.2.0 SCH-08 ("**Dado** scheduler iniciado com cron A"); `tests/unit/schedule/test_scheduler.py::TestSetCron::test_valid_updates_active_and_store` e `tests/bdd/test_daily_scheduler.py::TestSCH08SetCronNoConfigPath` v0.1.0 (candidatos) | `design.md` §3.1 D-T15-009 exige que `set_cron` "reschedule job em runtime (sem restart processo)" quando o scheduler já está rodando — esse é justamente o cenário que distingue `set_cron` pré-`start()` de `set_cron` com o job ativo. Nenhum teste candidato chamava `sched.start()` antes de `set_cron`; o BDD SCH-08 declarava esse "Dado" no Gherkin mas o step executável o ignorava, testando exatamente o mesmo caminho já cobrido por UT-S09 (sem scheduler iniciado). Resultado: uma implementação que só atualizasse estado interno em `set_cron` sem nunca tocar o job do `BackgroundScheduler` enquanto rodando passaria em 100% dos testes candidatos, sem violar nenhuma assertiva. | Adicionar teste que chama `start()` com cron válido antes de `set_cron()` válido, mantendo as asserções de `active_cron()`/store/ausência de CRUD, e encerra com `stop()` — alinhando o step executável ao "Dado" literal do cenário aprovado. |
| M-UT-T15-02 | MAJOR | `pyproject.toml` (candidato, antes da correção) `[project].dependencies` sem `apscheduler` | `design.md` D-T15-003/004 e `interfaces.md` §8 exigem `apscheduler` em `schedule/cron_expr.py` e `schedule/scheduler.py`; o pacote estava presente apenas por instalação manual prévia no `.venv` local (`pip show apscheduler` → 3.11.3), não declarado no manifesto do projeto. Em CI ou em outra máquina de desenvolvimento (`pip install -e .` limpo), a implementação desta task falharia por `ModuleNotFoundError: No module named 'apscheduler'` mesmo com o código correto — quebrando o requisito de ambiente de testes reprodutível. | Declarar `apscheduler` em `[project].dependencies` do `pyproject.toml` com faixa de versão compatível com a instalada localmente. |
| M-UT-T15-03 | MAJOR | `pyproject.toml` (candidato, antes da correção) `[tool.coverage.run] omit` só com `*/catalog/postgres/*` | O próprio `pyproject.toml` já estabelece o padrão (comentário citando design T03 §3.3/D-T03-010) de excluir do gate `fail_under = 95` adaptadores PostgreSQL só exercíveis contra banco real. `interfaces.md`/`design.md` de T15 definem `schedule/postgres.py` com o mesmo perfil (`SqlAlchemyCronPreferenceStore`, BR-024) e o `unit-test-plan.md`/`bdd.md` só o inspecionam por leitura de código-fonte (SCH-12/UT §Arquivos), nunca o exercitam via unit test. Sem a exclusão, o pacote `schedule` corre risco concreto de não atingir 95% de cobertura no run padrão (sem Docker), obrigando o Developer a criar testes de integração fora do escopo desta task só para satisfazer o gate. | Adicionar `*/schedule/postgres.py` ao `[tool.coverage.run] omit`, mesmo padrão de `catalog/postgres/*`. |

### Verificação dos demais critérios (sem achados)

- Evidência RED confirmada por execução real (não só citação): `python -m pytest tests/unit/schedule tests/bdd/test_daily_scheduler.py -q` (com `PYTHONPATH` apontando ao `src` do worktree) → 5 erros de coleta, todos `ModuleNotFoundError`/`ImportError` para módulos/símbolos ainda não implementados (`github_rag.schedule.cron_expr`, `github_rag.schedule.errors` ×2, `DEFAULT_INDEX_CRON` de `github_rag.settings` ×2) — razão esperada, sem falha por erro de sintaxe/fixture/dependência faltante nos próprios testes. Reconfirmado idêntico após as correções desta revisão (sem regressão).
- Extremos/corner cases: blank/whitespace em `INDEX_CRON` (UT-S01/02), expressões inválidas variadas + truncamento de mensagem >200 chars (UT-S03/04), `set`/`get`/`clear` + `set` inválido não persiste (UT-S05/06), precedência preferência×default (UT-S07/08), `set_cron` inválido não altera estado (UT-S09), `clear` volta ao default (UT-S19), reentrância de `run_tick_once` sob lock com ordenação determinística via `threading.Event`/`gate` (UT-S14/SCH-11), `stop()` idempotente sem `start()` prévio (UT-S18 implícito) — todos presentes e com asserção específica, não apenas "não lança exceção".
- Alinhamento com `interfaces.md` 0.2.0: assinaturas keyword-only de `DefaultDailyScheduler` (`helpers.py::make_scheduler`) conforme I-T15-004; `@runtime_checkable` exercido via `isinstance` em ambas as portas (UT-S20, `test_memory_store.py`/`test_scheduler.py`); confinamento de SDK verificado por AST real (`test_eng013.py`, `test_daily_scheduler.py::TestSCH13SdkConfinement`), não apenas por regex/string matching ingênuo.
- Sem enfraquecimento de contrato: nenhum teste usa `assertIsNotNone`/`try/except: pass` para mascarar comportamento; `test_invalid_set_does_not_persist` e `test_typed_error_no_partial_apply` (SCH-07) verificam estado do store **depois** da exceção, não só a exceção em si — fecha o requisito "sem aplicação parcial" (D-T15-008).
- Reuso de fakes T14 (`tests/unit/indexing/helpers.py::make_orchestrator`/`seed_repo`) sem duplicar lógica de elegibilidade — conforme D-T15-005.

### Resultado

`CHANGES_REQUIRED` na v0.1.0 (M-UT-T15-01, M-UT-T15-02, M-UT-T15-03) → correções aplicadas pelo próprio Architect: `tests/unit/schedule/test_scheduler.py` (novo `test_valid_reschedules_while_running_without_restart`), `tests/bdd/test_daily_scheduler.py` (`TestSCH08SetCronNoConfigPath` corrigido para chamar `start()`/`stop()`), `pyproject.toml` (`apscheduler>=3.10,<4` adicionado; `*/schedule/postgres.py` incluído em `omit`); evidência RED reexecutada e reconfirmada sem regressão → **`APPROVED_BY_ARCHITECT`** na v0.2.0. Sem achados BLOCKING ou MAJOR abertos.
