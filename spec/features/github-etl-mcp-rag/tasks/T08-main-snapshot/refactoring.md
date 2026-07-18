# Refactoring — T08-main-snapshot (Blue)

| Campo | Valor |
|---|---|
| Task | `T08-main-snapshot` |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Data | 2026-07-18 |
| Cobertura pós-Blue | `97.35%` |

## Baseline (pós-implementação Green / pós M-IMP-01)

| Métrica | Valor |
|---|---|
| Testes | 373 passed, 1 skipped |
| Cobertura global | 97.36%–98.11% |
| `snapshot/clone.py` | ~100% (após testes de clone) |
| `snapshot/local.py` | 97% |
| `snapshot/github.py` | 98% |
| `snapshot/provider.py` | 100% |

## Análise

Nenhum gargalo de performance medido: operações são I/O Git síncronas (tip/diff/read) sobre um repo por chamada; clone GitHub é porta injetável e fora do hot path de testes unitários. Sem otimização prematura.

## Mudanças Blue aplicadas

| ID | Mudança | Motivo |
|---|---|---|
| B-01 | Removido `_ = SnapshotError` morto em `provider.py` (S-IMP-01) | Clareza; import morto |
| B-02 | Simplificado `_main_commit` / `_resolve_commit` em `local.py` | Menos ramos defensivos duplicados sem mudar contratos |
| B-03 | Clone: auth até o fetch + scrub no `finally` (já na review de impl) | BR-008 + D-T08-008 |

## Resultado pós-Blue

| Métrica | Valor |
|---|---|
| Testes | 373 passed, 1 skipped, 161 subtests |
| Cobertura global | 97.35% |
| Comportamento | Contratos aprovados inalterados |

## Rollback

Reverter commits Blue desta branch; módulo isolado em `snapshot/`.
