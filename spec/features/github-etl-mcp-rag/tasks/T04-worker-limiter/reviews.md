# Reviews — T04-worker-limiter

## Review — Design (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Escopo estrito (sem jobs reais, MCP, UI) | OK | `design.md` §1, §5; fora de escopo explícito |
| Isolamento index vs query | OK | D-T04-001; factories distintas; §2.3 |
| Fila/espera quando limite atingido | OK | `acquire` bloqueante; §2.3; mapeamento aceite §3 |
| Tratamento explícito de valores inválidos | OK | D-T04-003; `capacity < 1` → `WorkerLimiterError`; sem fallback silencioso; §2.5 |
| Compatibilidade com T01 `AppSettings` | OK | Usa `index_workers`/`query_workers` já tipados; não reparseia env; política min em T04 (alinha I-T01-008 / `settings.py` sem min/max) |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |
| `SUGGESTION` | API opcional (`try_acquire`, `active_count`/`available_permits`) ainda ambígua | `design.md` D-T04-004 | Na etapa de interfaces, fechar contrato mínimo: preferir só `capacity` + `acquire()` context manager; omitir métricas da porta pública |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.1. Prosseguir para interfaces/BDD (QA) sem alteração de escopo.

## Review — BDD (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `tests/bdd/test_worker_limiter.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Cobertura dos critérios de aceite da task | OK | WL-01..WL-08 mapeiam paralelismo, espera, inválidos, corners; WL-09 fronteira T01 |
| Alinhamento design: capacity + acquire CM | OK | WL-01 factories/`capacity`; WL-02..WL-07 usam `with limiter.acquire()` |
| Alinhamento design: isolamento index × query | OK | WL-04; duas instâncias `SemaphoreWorkerLimiter` |
| Alinhamento design: rejeição `capacity < 1` | OK | WL-08 → `WorkerLimiterError`; sem fallback silencioso |
| Cenários executáveis e corner cases | OK | limite 1 (WL-05), rajada (WL-06), release após exceção (WL-07), espera (WL-03) |
| Sem extrapolar escopo | OK | Sem jobs reais, MCP, UI, asyncio, reparse de env no limiter |
| Red pré-implementação | OK | Relatado: 9 failed (`ModuleNotFoundError` concurrency), 1 passed (WL-09 T01) |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |
| `SUGGESTION` | WL-04 no `bdd.md` afirma o inverso (query cheia não bloqueia index), mas o executável só cobre index→query | `bdd.md` WL-04; `tests/bdd/test_worker_limiter.py` `TestWL04Isolation` | Na etapa unitária ou ajuste menor do BDD: adicionar o inverso simétrico, ou restringir o texto ao sentido já testado (instâncias independentes já bastam para o aceite) |

### Decisão

`APPROVED_BY_ARCHITECT` — BDD v0.1.0. Prosseguir para interfaces.

## Review — Interfaces (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md`, `src/github_rag/concurrency/limiter.py`, `src/github_rag/concurrency/__init__.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `APPROVED_BY_ARCHITECT` |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Comentários de responsabilidade e motivo da separação em cada contrato | OK | Docstrings em `WorkerLimiterError`, `WorkerLimiter`, `SemaphoreWorkerLimiter`, factories, `MIN_WORKERS`; espelhados em `interfaces.md` §3 |
| API mínima: `capacity` + `acquire()` CM | OK | Protocol L74–L94; I-T04-001; sem `try_acquire`/métricas (I-T04-007 fecha SUGGESTION do design) |
| Dois factories isolados | OK | `create_index_limiter` / `create_query_limiter`; I-T04-002; mapa §4 |
| `capacity < 1` → `WorkerLimiterError` | OK | I-T04-004; construtor e factories; `MIN_WORKERS = 1` |
| Alinhamento design (sync semaphore, sem reparse env) | OK | I-T04-003, I-T04-005; D-T04-001..004 |
| Sem extrapolar escopo | OK | Fora de escopo §1: T14/T16/T17/T18, asyncio, métricas |
| Protocol + stubs nesta etapa | OK | `...` em construtor/factories; reexports em `__init__.py` |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |
| `SUGGESTION` | Imports `Iterator` e `contextmanager` ainda não usados no stub | `limiter.py` L15–L16 | Remover ou usar na implementação (etapa Developer); não bloqueia gate de interfaces |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces v0.1.0. Prosseguir para unit-test-plan / TDD.

## Review — Unit test plan + unitários (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` + `tests/unit/concurrency/test_worker_limiter.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Interfaces base | `APPROVED_BY_ARCHITECT` |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Contratos (`capacity`, `acquire`, Protocol, factories) | OK | U-01, U-02, U-09, U-10, U-13 |
| Extremos / corners (cap=1, rajada, reentrada) | OK | U-04, U-05, U-14 |
| Bloqueio até release | OK | U-03 |
| Liberação após falha no CM | OK | U-06 |
| Inválidos (`0`, negativo, factory sem fallback) | OK | U-07, U-08, U-12, U-15 |
| Isolamento index × query (ambos sentidos) | OK | U-11, U-16 (fecha SUGGESTION BDD WL-04) |
| Sem enfraquecer requisitos / escopo | OK | WL-01/WL-09 fora do unit (BDD/T01); matriz alinhada a I-T04-001..006 |
| Red pré-implementação | OK | 15 failed, 1 passed (`test_u13_protocol_runtime`); stubs `...` |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |
| `SUGGESTION` | U-15 exige pool + valor, não substring de razão | `interfaces.md` §3.1; `test_u15_error_message_cites_pool_and_value` | Opcional na implementação: incluir razão na mensagem; unitário já cobre pool/valor |

### Decisão

`APPROVED_BY_ARCHITECT` — unit-test-plan v0.1.0 e testes unitários em RED. Prosseguir para implementação (Developer / green).

## Review — Implementação (green)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `src/github_rag/concurrency/limiter.py`, `src/github_rag/concurrency/__init__.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Contratos base | design `0.1.1`, interfaces `0.1.0`, BDD e unit-test-plan `APPROVED_BY_ARCHITECT` |
| Evidência | 64 passed (suite); coverage 100%; T04 BDD+unit verdes |
| Resultado | `APPROVED_BY_ARCHITECT` |
| Próximo | Pronto para etapa Blue (refactor) |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Fidelidade ao Protocol (`capacity` + `acquire` CM) | OK | `SemaphoreWorkerLimiter` L123–L142; reexports em `__init__.py` |
| Semáforo sync + release em `finally` | OK | `threading.Semaphore`; `try/finally` + `release` em `_slot` L136–L140 |
| Isolamento index × query | OK | factories distintas L162–L187; testes U-11/U-16 e WL-04 ambos sentidos |
| `capacity < 1` → `WorkerLimiterError` sem fallback | OK | `_validate_capacity` L98–L102; U-07/U-08/U-12; WL-08 |
| Mensagem cita pool + valor + razão | OK | `f"{pool}: capacity must be >= {MIN_WORKERS}, got {capacity}"`; U-15 |
| Escopo (sem jobs/MCP/UI/asyncio/reparse env) | OK | só `concurrency/`; factories leem `AppSettings` |
| Testes não enfraquecidos no green | OK | diff red→green: +WL-04 inverso; +assert `">="` em U-15 |
| Cobertura ≥ 95% | OK | 100% em `concurrency` e suite completa |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |
| `SUGGESTION` | `@contextmanager` aninhado recria closure a cada `acquire()` | `limiter.py` L133–L142 | Blue: avaliar CM dedicado/reuso se baseline mostrar alocação relevante; não alterar contrato |
| `SUGGESTION` | `self._pool` guardado e não lido após construção | `limiter.py` L126 | Blue: remover atributo se não usado, ou documentar retenção para debug |

### Decisão

`APPROVED_BY_ARCHITECT` — implementação green aceita. Pronto para Blue refactor (sem mudança de comportamento/contratos).

## Review — Blue refactor

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `refactoring.md` + `src/github_rag/concurrency/limiter.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Implementação base | `APPROVED_BY_ARCHITECT` |
| Evidência | 64 passed, 36 subtests; coverage 100% (TOTAL 81 stmts; `limiter.py` 35 stmts) |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Sem mudança de comportamento/contratos | OK | Mesma API `capacity` + `acquire()` CM; `try/finally` + `release`; factories e Protocol intactos |
| Só simplificação | OK | `@contextmanager` no método (não nested); removido `self._pool` não lido; pool só em `_validate_capacity` |
| Baseline e resultados registrados | OK | `refactoring.md`: pré 64/100%/38 stmts → pós 64/100%/35 stmts |
| SUGGESTIONs green endereçadas | OK | Closure aninhada eliminada; atributo `_pool` removido |
| Cobertura mantida ≥ 95% | OK | 100%; `limiter.py` 35 stmts, 0 miss |
| Fora de escopo Blue respeitado | OK | Sem asyncio/Dockerfile/consumidores T14/T17 |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING`, `MAJOR` ou `SUGGESTION` | — | — |

### Decisão

`BLUE_APPROVED_BY_ARCHITECT` — refatoração Blue aceita. Prosseguir para documentação/changelog e gate humano (PR).
