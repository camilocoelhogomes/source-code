# BDD — T35-fix-e2e-indexing-zoekt-wrapper-and-boot-race

| Campo | Valor |
|---|---|
| Task | `T35-fix-e2e-indexing-zoekt-wrapper-and-boot-race` |
| Estado | `APPROVED_BY_ARCHITECT` |

## Cenários executáveis (unit/BDD Python)

| ID | Critério | Arquivo |
|---|---|---|
| T35-01 | mkdir antes de podman cp | `tests/unit/e2e/test_zoekt_bin_resolver.py` |
| T35-02 | cp timeout → E2eStackError | idem |
| T35-03 | mkdir failure → E2eStackError | idem |
| T35-04 | enqueue INDEXING re-dispara fila | `tests/unit/indexing/test_orchestrator.py` |
| T35-05 | defer startup skip enqueue | `tests/unit/indexing/test_startup.py` |
| T35-06 | launcher e2e seta E2E_DEFER_STARTUP_INDEX | `tests/unit/e2e/test_launcher.py` |

## Robot (não alterado)

BDD-002 em `e2e/robot/catalog_indexing.robot` — validação manual pós-merge.

## Execução

```bash
python -m pytest tests/unit/e2e/test_zoekt_bin_resolver.py tests/unit/indexing/test_orchestrator.py tests/unit/indexing/test_startup.py tests/unit/e2e/test_launcher.py -q
```
