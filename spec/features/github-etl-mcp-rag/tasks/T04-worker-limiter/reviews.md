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
