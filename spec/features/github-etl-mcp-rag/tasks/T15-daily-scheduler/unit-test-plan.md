# Unit test plan — T15-daily-scheduler

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T15-daily-scheduler` |
| Autor | Implementation Task Runner (QA) |
| Data | 2026-07-18 |
| Estado | `CANDIDATE` |
| Versão | `0.1.0` |
| Interfaces | `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T15-daily-scheduler` |

## Objetivo

Cobrir contratos, extremos e corner cases de `DailyScheduler`, `CronPreferenceStore`, validação cron e extensão `AppSettings.index_cron`, alinhados a BDD SCH-01..13.

## Matriz

| ID | Área | Cenário | Esperado | BDD / iface |
|---|---|---|---|---|
| UT-S01 | settings | `INDEX_CRON` ausente/blank → default | `DEFAULT_INDEX_CRON` | I-T15-006 |
| UT-S02 | settings | `INDEX_CRON="0 3 * * *"` | `index_cron` igual | SCH-03 |
| UT-S03 | cron_expr | válidas diária/horária/2× | retorna stripada | SCH-02 |
| UT-S04 | cron_expr | inválidas | `InvalidCronExpressionError` | SCH-07 |
| UT-S05 | memory store | get None inicial; set/get; clear | semântica ENG-004 | SCH-03/04 |
| UT-S06 | memory store | set inválido não grava | store intacto | SCH-07 |
| UT-S07 | scheduler | active_cron sem pref = default | string default | SCH-03 |
| UT-S08 | scheduler | pref prevalece | active = pref | SCH-04 |
| UT-S09 | scheduler | set_cron inválido | erro; active inalterado | SCH-07 |
| UT-S10 | scheduler | set_cron válido muda active | reschedule path | SCH-08 |
| UT-S11 | tick | not_indexed → up_to_date | via reconcile+orch | SCH-01 |
| UT-S12 | tick | up_to_date tip==proc skip | sem index calls | SCH-05 |
| UT-S13 | tick | tip≠proc indexa | up_to_date C2 | SCH-06 |
| UT-S14 | lock | reentrância run_tick_once | serializado | SCH-11 |
| UT-S15 | ENG-013 | ports/errors/memory sem apscheduler/sqlalchemy | AST | SCH-13 |
| UT-S16 | BDD-024 | scheduler/cron_expr usam apscheduler | import/source | SCH-10 |
| UT-S17 | BR-017 | schedule sem API de conexões | dir/attrs | SCH-09 |
| UT-S18 | start inválido | default_cron inválido no start | InvalidCron… | SCH-07 |
| UT-S19 | clear | após set+clear volta default | active=default | I-T15-007 |
| UT-S20 | runtime_checkable | isinstance fake/impl | True | I-T15-009 |

## Extremos / corner

- Expressão só whitespace → inválida.
- Expressão >200 chars na mensagem truncada.
- `stop()` sem `start()` = idempotente.
- `set_cron` com scheduler não iniciado: persiste; active atualiza; start usa nova.
- Concorrência: segundo `run_tick_once` espera o primeiro.

## Evidência de falha (pré-impl)

```bash
python -m pytest tests/unit/schedule tests/bdd/test_daily_scheduler.py -q
# Esperado: ImportError / falhas — módulos schedule ainda não implementados
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `tests/unit/schedule/test_settings_cron.py` | UT-S01/S02 |
| `tests/unit/schedule/test_cron_expr.py` | UT-S03/S04 |
| `tests/unit/schedule/test_memory_store.py` | UT-S05/S06 |
| `tests/unit/schedule/test_scheduler.py` | UT-S07..S14, S18/S19/S20 |
| `tests/unit/schedule/test_eng013.py` | UT-S15/S16/S17 |
| `tests/bdd/test_daily_scheduler.py` | SCH-01..13 |
| `tests/unit/schedule/helpers.py` | harness |

## Cobertura alvo

≥95% global e do pacote `github_rag.schedule` (+ linhas tocadas em `settings.py`).
