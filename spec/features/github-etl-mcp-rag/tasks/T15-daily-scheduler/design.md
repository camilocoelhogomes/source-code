# Design — T15-daily-scheduler

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T15-daily-scheduler` |
| Autor | Implementation Task Runner + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.2.0` |
| Branch | `feature/github-etl-mcp-rag-T15-daily-scheduler` |
| Base | `feature/github-etl-mcp-rag-T14-indexing-orchestrator` |
| Rastreabilidade | REQ-017; BR-017, BR-023, BR-024; DEC-015; BDD-003, BDD-024; ENG-004, ENG-010, ENG-013 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | `0.1.0` | MAJOR M-T15-01 (reuso de `StartupIndexReconcile.run()` no tick sem guarda de concorrência frente a disparo sob demanda futuro/T18); MAJOR M-T15-02 (`INDEX_CRON` lido ad-hoc via `os.environ`, contrariando convenção `AppSettings` já reservada em T01 e seguida por T04) |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.2.0` | M-T15-01 fechado (§3.6 lock de execução único via `run_tick_once`; handoff explícito para T18); M-T15-02 fechado (§4.2/D-T15-001: `AppSettings.index_cron` extendido em T01, sem leitura direta de env no pacote `schedule`); sem BLOCKING/MAJOR abertos |

## 1. Contexto

T14 entrega `IndexingOrchestrator` e `StartupIndexReconcile`: fila, estados REQ-020, skip quando tip == último processado, e reconcile de boot (ENG-011). T15 agenda disparos periódicos por **expressão cron** (ENG-010): o caso “uma vez ao dia” de REQ-017/BDD-003 é uma expressão cron diária (ex.: `0 2 * * *`), não um segundo modelo de configuração.

Dependências já na base:

| Componente | Task | Papel para T15 |
|---|---|---|
| `IndexingOrchestrator` | T14 | Recebe enqueue + `run_until_idle` no tick |
| `StartupIndexReconcile` | T14 | Mesma política tip × processado; T15 reutiliza ou espelha no tick |
| `CatalogRepository` | T03 | Catálogo ativo / estados |
| `AppSettings` / `load_settings` | T01 | T15 estende com `index_cron: str` (env já reservada como "dono futuro: T15" no design T01 §2.5); resolução de env segue o mesmo padrão de T04 |
| PostgreSQL + SQLAlchemy/Alembic | T03 | Persistência da preferência de cron (BR-024) |

Consumidores futuros: T18 (UI lê/grava expressão cron), T19 (boot: start scheduler). Fora de escopo: telas UI, CRUD de conexões, edição de `CONFIG_PATH`, compose.

## 2. Problema

1. Agendar indexação por **cron** maduro (APScheduler — DEC-015 / BR-023 / BDD-024), sem reinventar parser/cron.
2. Default de boot via env `INDEX_CRON`; preferência UI persistida em PostgreSQL **prevalece** em runtime (ENG-004).
3. Expressão inválida → erro tipado; sem aplicar parcialmente; sem silent no-op sem registro.
4. No tick: enfileirar elegíveis (`not_indexed` / `error` / tip ≠ processado) e disparar o orquestrador; **não** reprocessar `up_to_date` com mesmo commit.
5. API de preferência de cron legível/gravável pela UI (T18), sem CRUD de conexões (BR-017).

## 3. Solução proposta

Pacote `github_rag.schedule` (placeholder T01 → materialização):

| Componente | Módulo | Papel |
|---|---|---|
| Erros tipados | `schedule/errors.py` | `InvalidCronExpressionError`, `SchedulerConfigError` |
| Validação cron | `schedule/cron_expr.py` | Valida sintaxe via APScheduler/`CronTrigger`; puro quanto ao domínio |
| `CronPreferenceStore` | `schedule/ports.py` + impl | Porta get/set da expressão persistida (PostgreSQL) |
| `InMemoryCronPreferenceStore` | `schedule/memory.py` | Fake para testes |
| `SqlAlchemyCronPreferenceStore` | `schedule/postgres.py` | Adaptador ORM (BR-024) |
| `DailyScheduler` | `schedule/ports.py` + `scheduler.py` | Porta + impl APScheduler: start/stop, resolve expressão ativa, tick |
| Migration | `migrations/versions/0002_scheduler_preference.py` | Tabela singleton de preferência |

### 3.1 Decisões

| ID | Decisão | Motivo |
|---|---|---|
| D-T15-001 | Env canônica `INDEX_CRON`; default de produto `0 2 * * *` (02:00 UTC diário) se env ausente/blank; resolvido via `AppSettings.index_cron` (T01), **não** por leitura ad-hoc de `os.environ` no pacote `schedule` | ENG-004; fecha nome; “uma vez ao dia” = caso especial; conformidade com I-T01 (T01 já reserva `INDEX_CRON` como “dono futuro: T15”) e com o padrão T04 (`WorkerLimiter` consome `AppSettings.index_workers`/`query_workers`, proibido reparsear env no consumidor) |
| D-T15-002 | Precedência runtime: preferência persistida (não-nula) > default de env/boot | ENG-004 |
| D-T15-003 | Validação com `apscheduler.triggers.cron.CronTrigger.from_crontab` (5 campos) | DEC-015; rejeita inválido com `InvalidCronExpressionError` |
| D-T15-004 | APScheduler `BackgroundScheduler` com job id fixo `index_cron_tick` | SDK maduro; replace job ao mudar cron |
| D-T15-005 | Tick = `StartupIndexReconcile.run()` + `orchestrator.run_until_idle()` | Reutiliza elegibilidade T14; evita duplicar tip×processado |
| D-T15-006 | Preferência em tabela própria `scheduler_preference` (singleton row id=1), **fora** de `CatalogRepository` | BR-017: não é CRUD de conexões; separa SoT de agenda do catálogo de repos |
| D-T15-007 | `CronPreferenceStore.get() → str \| None`; `None` = sem override UI | ENG-004 |
| D-T15-008 | `set(expression)` valida **antes** de persistir; inválido não grava | Sem aplicação parcial |
| D-T15-009 | `DailyScheduler.set_cron` / preferência: ao gravar válida, reschedule job em runtime (sem restart processo) | Aceite T15 |
| D-T15-010 | Adaptador APScheduler isolado; domínio não importa PyGithub/etc.; APScheduler só no adaptador de schedule (ENG-013) | BR-023 |
| D-T15-011 | `on_tick()` e qualquer disparo sob demanda (T18, futuro) que compartilhe a mesma instância de `DailyScheduler`/`IndexingOrchestrator` **devem** serializar o ciclo reconcile+drain via um lock de processo único, exposto como o único ponto de entrada síncrono `DailyScheduler.run_tick_once()` | M-T15-01; evita que `StartupIndexReconcile.run()` reclassifique como órfã uma execução `indexing`/`queued` legitimamente em andamento por outro chamador concorrente |
| D-T15-012 | Recover órfão de `indexing`/`queued` (herdado de T14 `StartupIndexReconcile`) permanece semanticamente válido em runtime **somente** porque o lock de D-T15-011 garante que, ao iniciar um novo ciclo, o ciclo anterior já drenou (`run_until_idle` retornou) — nunca concorrente com outro `run_tick_once` | M-T15-01; preserva contrato T14 sem alterá-lo |

### 3.2 Fluxo — boot

```text
env INDEX_CRON (ou DEFAULT_INDEX_CRON) ──► default_cron
CronPreferenceStore.get() ──► persisted | None
active = persisted if persisted else default_cron
validate(active) ──► InvalidCronExpressionError se inválido
DailyScheduler.start():
  BackgroundScheduler.add_job(tick, CronTrigger.from_crontab(active), id=...)
  scheduler.start()
```

### 3.3 Fluxo — tick (BDD-003)

```text
on_tick():                       # corpo de run_tick_once() — ver §3.6 (lock)
  StartupIndexReconcile.run()   # tip, reconcile, enqueue elegíveis
  IndexingOrchestrator.run_until_idle()
  # up_to_date com tip==processado: reconcile não enfileira; skip (BDD-004)
```

Não enfileira `up_to_date` com tip igual — comportamento de T14/`StartupIndexReconcile`.

`on_tick()` só executa dentro do lock de `run_tick_once()` (§3.6); nunca chamado diretamente pelo job APScheduler sem o guard.

### 3.4 Fluxo — preferência UI (T18)

```text
DailyScheduler.set_cron("0 */6 * * *")
  → CronPreferenceStore.set(...)   # valida + persiste (único caminho de escrita)
  → remove/replace job com nova expressão
  → próximos ticks usam a nova cron sem editar CONFIG_PATH
```

`set_cron` é o **único** ponto de entrada para alterar a preferência a partir de consumidores (T18); `CronPreferenceStore.set/clear` não são chamados diretamente pela UI, evitando persistir sem reagendar.

### 3.5 Expressão inválida

| Entrada | Resultado |
|---|---|
| `0 2 * * *` | OK |
| `0 */6 * * *` (a cada 6h) | OK |
| `0 0,12 * * *` (2×/dia) | OK |
| `not-a-cron`, `60 * * * *`, campos a menos | `InvalidCronExpressionError` |
| set com inválido | não persiste; store anterior intacto |
| boot com env inválida e sem preferência | falha tipada no start (não sobe job silent) |

### 3.6 Concorrência tick × disparo sob demanda (D-T15-011/012)

`StartupIndexReconcile.run()` reclassifica `indexing`/`queued` órfãos assumindo que a fila em memória do orquestrador foi perdida (reinício de processo — ENG-011). Essa suposição só é verdadeira se **nenhum outro chamador** estiver processando a fila no mesmo momento. Sem uma guarda explícita, um disparo sob demanda futuro (T18, mesma instância de `IndexingOrchestrator`) rodando em paralelo a um tick teria sua execução `indexing` incorretamente marcada como órfã, reenfileirada e reprocessada em duplicidade.

Mitigação nesta task:

```text
DailyScheduler.run_tick_once():
  with self._run_lock:            # threading.Lock, escopo da instância
      on_tick()                   # StartupIndexReconcile.run() + run_until_idle()

on_tick() do job APScheduler == run_tick_once()
```

- `run_tick_once()` é o **único** ponto de entrada síncrono que executa o ciclo reconcile+drain; o job cron chama exclusivamente `run_tick_once()`.
- `max_instances=1` + `coalesce=True` (APScheduler) evita reentrância do próprio job; o lock evita reentrância **entre** o job e qualquer chamador externo que compartilhe a mesma instância de `DailyScheduler`.
- **Handoff obrigatório para T18:** disparo de indexação sob demanda pela UI deve invocar `DailyScheduler.run_tick_once()` (ou adquirir o mesmo lock antes de chamar `IndexingOrchestrator.enqueue`/`run_until_idle` diretamente) — nunca chamar o orquestrador em paralelo ao scheduler sem essa serialização. Registrado como pré-condição de design para T18; não implementado nesta task (fora de escopo de UI).

## 4. Dados

### 4.1 Tabela `scheduler_preference`

| Coluna | Tipo | Notas |
|---|---|---|
| `id` | `SMALLINT` PK | Sempre `1` (singleton) |
| `cron_expression` | `TEXT` NOT NULL | Expressão validada |
| `updated_at` | `TIMESTAMPTZ` | now() |

Ausência de linha = sem preferência UI → usa env/default.

### 4.2 Env

| Nome | Default | Papel |
|---|---|---|
| `INDEX_CRON` | `0 2 * * *` | Default de boot (ENG-004) |

T01 já reserva `INDEX_CRON` em `settings.py` com "dono futuro: T15" (design T01 §2.5). Esta task **estende** `AppSettings`/`load_settings` (T01) com a propriedade `index_cron: str` (env `INDEX_CRON`; default `0 2 * * *` se ausente/blank; sem validação de sintaxe cron em T01 — só em `schedule/cron_expr.py`), seguindo o mesmo padrão de T04 (`WorkerLimiter` consome `AppSettings.index_workers`/`query_workers`; proibido reparsear env no consumidor). O pacote `schedule` recebe `AppSettings` (ou `default_cron: str` explícito nos testes) — **nunca** lê `os.environ` diretamente. Constantes `ENV_INDEX_CRON` / `DEFAULT_INDEX_CRON` residem em `settings.py` (T01), não duplicadas em `schedule`.

## 5. API pública (esboço; detalhe em interfaces.md)

```python
class CronPreferenceStore(Protocol):
    def get(self) -> str | None: ...
    def set(self, cron_expression: str) -> str: ...
    def clear(self) -> None: ...  # remove override; volta ao env

class DailyScheduler(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def active_cron(self) -> str: ...
    def set_cron(self, cron_expression: str) -> str: ...  # valida, persiste (via CronPreferenceStore), reschedule
    def run_tick_once(self) -> None: ...  # único ponto síncrono do ciclo reconcile+drain; serializado por lock (§3.6); job cron chama só isto
```

## 6. Erros

| Erro | Quando |
|---|---|
| `InvalidCronExpressionError` | Sintaxe/campo cron inválido |
| `SchedulerConfigError` | Misconfig (ex.: start sem deps; store indisponível no boot se política exigir) |

Mensagens citam a expressão (truncada se enorme); **nunca** token GitHub.

## 7. Segurança

- Preferência não armazena segredos.
- Tick não loga token.
- Sem superfície de CRUD de conexões.

## 8. Compatibilidade

- Windows/macOS/Linux: APScheduler + cron UTC; timezone documentado como **UTC** no MVP (UI/T18 pode expor isso).
- Migration Alembic 0002 após 0001.
- Branch empilhada em T14; merge order: T14 → T15.

## 9. Observabilidade

- Log estruturado no start: expressão ativa + fonte (`env` \| `preference`).
- Log no tick: início/fim + contagem enfileirada (se observável).
- Erro de cron inválido sempre explícito (exception), nunca silent.

## 10. Riscos e rollback

| Risco | Mitigação |
|---|---|
| Tick longo sobrepõe próximo cron | `max_instances=1` + `coalesce=True` no job APScheduler |
| Recover órfão do T14 reclassifica execução concorrente sob demanda (T18 futuro) | Lock de instância em `run_tick_once` (D-T15-011/012, §3.6); handoff obrigatório para T18 reusar o mesmo guard |
| Preferência corrompida/inválida no DB | Validar no `get` path do scheduler start; se inválida, erro tipado (operador corrige via set/clear) |
| Duplicar lógica de elegibilidade | Reusar `StartupIndexReconcile` (D-T15-005) |
| `INDEX_CRON` duplicado entre `settings.py` (T01) e `schedule` | Constantes/parse só em T01 (`AppSettings.index_cron`); `schedule` só consome, nunca lê env (D-T15-001) |
| Rollback | Reverter migration 0002; remover pacote schedule impl e extensão `index_cron` em `AppSettings`; T14 intacto |

## 11. Fora de escopo

- UI visual / FastAPI routes (T18)
- Wiring compose/boot completo (T19)
- Alterar máquina de estados do catálogo
- CRUD conexões / `CONFIG_PATH`

## 12. Decisões abertas fechadas neste design

| Dúvida requisitos | Resolução |
|---|---|
| Precedência UI × env | ENG-004: persistida > env |
| APScheduler vs outro | APScheduler (DEC-015 default) |
| Nome da env | `INDEX_CRON` |
| Onde resolver `INDEX_CRON` (ad-hoc vs `AppSettings`) | `AppSettings.index_cron` (T01), seguindo padrão T04; revisão Architect M-T15-02 |
| Concorrência tick × disparo sob demanda futuro (T18) | Lock de instância em `run_tick_once` + handoff de contrato para T18; revisão Architect M-T15-01 |
