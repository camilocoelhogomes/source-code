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
