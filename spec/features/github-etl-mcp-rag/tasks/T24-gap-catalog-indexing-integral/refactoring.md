# Refatoração Blue — T24-gap-catalog-indexing-integral

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T24-gap-catalog-indexing-integral` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Pipeline | autonomous |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |

## 1. Baseline (pré-Blue)

| Métrica | Valor | Comando / nota |
|---|---|---|
| Unitários T24 helpers + seed | **40 passed** | `PYTHONPATH=<wt-T24>/src python -m pytest tests/unit/e2e/test_catalog_indexing_keywords.py tests/unit/e2e/test_coverage_gaps.py --no-cov` |
| Escopo produção | e2e Robot + `github_rag.e2e.launcher` seed | Sem domínio ETL/UI |
| Performance | N/A nesta etapa | Sem alegação de ganho de latência; stack Robot e2e fora do gate unitário |

**Nota:** o editable install do `.venv` do repo principal pode apontar outro worktree; baseline exige `PYTHONPATH` do worktree T24.

## 2. Metas Blue

| ID | Meta | Tipo |
|---|---|---|
| B-T24-01 | Remover imports Robot mortos no resource (complexidade desnecessária óbvia) | Simplificação |
| B-T24-02 | Manter contratos I-T24-* e comportamento dos 40 unitários | Não-regressão |
| B-T24-03 | Sem otimização especulativa de cron/poll/git | Política Blue |

## 3. Mudanças aplicadas

| Arquivo | Mudança | Impacto comportamental |
|---|---|---|
| `e2e/robot/resources/catalog_indexing.resource` | Removidas libraries `OperatingSystem` e `String` (não referenciadas) | Nenhum — só Settings |

## 4. Pós-Blue (verificação)

| Métrica | Valor |
|---|---|
| Unitários | **40 passed** (mesmo comando do baseline) |
| Contratos Robot | Inalterados (keywords/cenários) |

## 5. Decisão Architect

`BLUE_APPROVED_BY_ARCHITECT` — baseline registrada; simplificação mínima sem alteração de comportamento; sem BLOCKING/MAJOR abertos na etapa Blue.
