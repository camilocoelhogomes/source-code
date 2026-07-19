# Refatoração Blue — T15-daily-scheduler

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T15-daily-scheduler` |
| Autor | Implementation Task Runner |
| Data | 2026-07-18 |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Branch | `feature/github-etl-mcp-rag-T15-daily-scheduler` |

## Baseline (pré-Blue)

| Métrica | Valor |
|---|---|
| Suíte | 813+ passed (unit/BDD; integration skip sem Docker) |
| Cobertura global | ≥98.5% (`fail_under=95`) |
| Pacote `schedule` | ~100% linhas (omit `postgres.py` no gate padrão) |

Comando:

```bash
PYTHONPATH=src python -m pytest -q
```

## Mudanças Blue (sem alteração de contrato)

1. `DefaultDailyScheduler`: extrair `_cron_trigger` e `_add_cron_job` para
   eliminar duplicação entre `start()` e `_reschedule` (JobLookupError path).
2. `active_cron`: expressão condicional direta (mesma semântica ENG-004).

Nenhuma mudança de API pública, precedência, lock ou validação.

## Resultados (pós-Blue)

| Métrica | Valor |
|---|---|
| Comportamento | Inalterado (mesmos testes verdes) |
| Contratos | Preservados (interfaces 0.2.0) |

## Gate Architect

Reexecução nesta revisão (venv isolado, worktree): `PYTHONPATH=src python -m pytest -q`
→ **813 passed, 2 skipped**, cobertura total **98.85%** (gate 95%); `schedule/scheduler.py`
**100%** linhas+branches (0 missing), idêntico ao baseline pré-Blue. `_cron_trigger`/
`_add_cron_job` preservam trigger (`CronTrigger.from_crontab(..., timezone=_UTC)`),
`_JOB_ID`, `replace_existing`, `max_instances`, `coalesce` e o tratamento de
`JobLookupError` em `_reschedule`; `active_cron()` mantém a mesma precedência
ENG-004 (preferência > default), só reescrita como expressão condicional. Sem
mudança de assinatura pública, contrato (`interfaces.md` 0.2.0) ou comportamento.

**`BLUE_APPROVED_BY_ARCHITECT`** — Tech Lead Architect, 2026-07-18. Sem achados
BLOCKING/MAJOR.
