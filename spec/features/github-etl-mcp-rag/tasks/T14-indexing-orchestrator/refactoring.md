# Refatoração Blue — T14-indexing-orchestrator

| Campo | Valor |
|---|---|
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Evidência pós-Blue | `769 passed`; coverage global **98.79%**; indexing orchestrator ~98%, demais 100% |

## Baseline

- Suíte: `pytest -q --ignore=tests/integration` → 760+ passed; coverage global ≥95%.
- Pacote `github_rag.indexing`: orchestrator ~98%, pipeline/startup/types/progress 100%.

## Medições

Sem gargalo reproduzível exigindo mudança estrutural: `run_until_idle` usa `ThreadPoolExecutor` + `WorkerLimiter`; pipeline e helpers já separados. Nenhuma otimização especulativa solicitada.

## Mudanças Blue aplicadas

| ID | Mudança | Motivo | Impacto comportamental |
|---|---|---|---|
| B-01 | Handler de erro unifica transição `up_to_date`→`not_indexed`→`queued`→`indexing`→`error` | Cobrir falha antes de entrar em `indexing` sem alterar contratos | Nenhum — ainda `mark_error` no boundary; testes IO-07 / unit corners verdes |
| B-02 | Removido `else: return` inalcançável no match de estados | Simplificação (enum fechado REQ-020) | Nenhum — dead code |

## Resultado

- Comportamento e contratos I-T14 preservados.
- Cobertura do pacote indexing ≥95%; global **98.79%**.
- Decisão Architect: `BLUE_APPROVED_BY_ARCHITECT`.
