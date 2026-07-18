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
