# Índice de backlog — mvp-local-e2e-green / T02

| Run | Data | Exit | Tasks abertas/atualizadas |
|---|---|---|---|
| `e2e-run-20260719.md` | 2026-07-19 | 3 | T28, T29 (novas); T22–T27 (pendentes herdadas) |

## Tasks pai para orquestrador (T03)

| Task ID | Superfície | Origem | Estado |
|---|---|---|---|
| T22-fix-tooling-e2e-compose-zoekt | tooling-e2e | auditoria | READY_FOR_IMPLEMENTATION |
| T23-gap-ui-browser | ui | auditoria | READY_FOR_IMPLEMENTATION |
| T24-gap-catalog-indexing-integral | catalog_indexing | auditoria | READY_FOR_IMPLEMENTATION |
| T25-gap-negative-integral | negative | auditoria | READY_FOR_IMPLEMENTATION |
| T26-gap-mcp-parallel-slo | mcp | auditoria | PR_OPENED |
| T27-gap-sdk-dec015-conformity | sdk | auditoria | READY_FOR_IMPLEMENTATION |
| T28-fix-github-user-org-discovery | catalog_indexing | run T01 F-T01-002 | READY_FOR_IMPLEMENTATION |
| T29-fix-e2e-env-loader-failfast | tooling-e2e | run T01 F-T01-001/003 | READY_FOR_IMPLEMENTATION |
| T30-container-delivery-compose-local-image | container-delivery | REQ-006/007 | READY_FOR_IMPLEMENTATION |

## Ordem de merge sugerida

1. T29 (tooling — desbloqueia run e2e)
2. T28 (boot/catalog sync)
3. T22 (zoekt e2e compose — se ainda aplicável)
4. T24, T25, T23, T26, T27 (gaps)
5. T30 (imagem local + compose end-user)
