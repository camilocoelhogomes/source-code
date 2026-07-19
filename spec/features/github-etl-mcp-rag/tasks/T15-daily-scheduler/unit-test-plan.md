# Unit test plan — T15-daily-scheduler

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T15-daily-scheduler` |
| Autor | Implementation Task Runner (QA) + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.2.0` |
| Interfaces | `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T15-daily-scheduler` |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | `0.1.0` | MAJOR M-UT-T15-01 (SCH-08/UT-S10 declaravam cobertura de "reschedule path"/"scheduler iniciado com cron A", mas `tests/unit/schedule/test_scheduler.py::TestSetCron` e `tests/bdd/test_daily_scheduler.py::TestSCH08SetCronNoConfigPath` nunca chamavam `start()` antes de `set_cron`, deixando o "Dado" do cenário e D-T15-009 — reschedule em runtime sem restart de processo — sem qualquer verificação, mesmo indireta); MAJOR M-UT-T15-02 (`apscheduler`, exigido por D-T15-003/004 e pelos módulos `cron_expr.py`/`scheduler.py` do escopo desta task, não estava declarado em `[project].dependencies` do `pyproject.toml` — apesar de já presente no `.venv` local — risco de ambiente não reprodutível em CI/outro dev ao implementar); MAJOR M-UT-T15-03 (gate de cobertura `[tool.coverage.report] fail_under = 95` sem `omit` para `schedule/postgres.py`, divergindo do padrão já aplicado a `catalog/postgres/*` (T03, design §3.3/D-T03-010) para adaptador só exercível contra PostgreSQL real; sem a exclusão, o pacote `schedule` dificilmente atinge 95% sem testes de integração com Docker) |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.2.0` | M-UT-T15-01 fechado (novo teste `test_valid_reschedules_while_running_without_restart` em `test_scheduler.py`; `TestSCH08SetCronNoConfigPath` corrigido para chamar `start()`/`stop()` conforme o "Dado" do cenário); M-UT-T15-02 fechado (`apscheduler>=3.10,<4` adicionado a `pyproject.toml`); M-UT-T15-03 fechado (`*/schedule/postgres.py` adicionado a `[tool.coverage.run] omit`); evidência de falha RED reconfirmada após as correções (`ModuleNotFoundError`/`ImportError` nos mesmos 5 módulos de teste — nenhuma regressão introduzida); sem achados BLOCKING ou MAJOR abertos |

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

≥95% global e do pacote `github_rag.schedule` (+ linhas tocadas em `settings.py`). `schedule/postgres.py` excluído do gate (`[tool.coverage.run] omit`), mesmo padrão de `catalog/postgres/*` (T03) — adaptador só exercível contra PostgreSQL real (`tests/integration`).
