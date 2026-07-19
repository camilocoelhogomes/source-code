# Índice de backlog — mvp-local-e2e-green / T02

| Run | Data | Exit | Tasks abertas/atualizadas |
|---|---|---|---|
| `e2e-run-20260719.md` | 2026-07-19 | 3 | T28, T29 (novas); T22–T27 (pendentes herdadas) |
| `e2e-run-20260719-w2.md` | 2026-07-19 | 3 | T31 (nova); T22–T30 (pendentes herdadas) |
| `e2e-run-20260719-r3.md` | 2026-07-19 | 18 | T33 (nova); T32 (pendente); T22 → mergeado |

## Tasks pai para orquestrador (T03)

| Task ID | Superfície | Origem | Estado |
|---|---|---|---|
| T22-fix-tooling-e2e-compose-zoekt | tooling-e2e | auditoria | **MERGED** |
| T23-gap-ui-browser | ui | auditoria | READY_FOR_IMPLEMENTATION |
| T24-gap-catalog-indexing-integral | catalog_indexing | auditoria | READY_FOR_IMPLEMENTATION |
| T25-gap-negative-integral | negative | auditoria | READY_FOR_IMPLEMENTATION |
| T26-gap-mcp-parallel-slo | mcp | auditoria | PR_OPENED |
| T27-gap-sdk-dec015-conformity | sdk | auditoria | READY_FOR_IMPLEMENTATION |
| T28-fix-github-user-org-discovery | catalog_indexing | run T01 F-T01-002 | READY_FOR_IMPLEMENTATION |
| T29-fix-e2e-env-loader-failfast | tooling-e2e | run T01 F-T01-001/003 | **MERGED** |
| T30-container-delivery-compose-local-image | container-delivery | REQ-006/007 | READY_FOR_IMPLEMENTATION |
| T31-fix-healthz-static-mount-order | health + container-delivery | run W1 F-W1-001 | **MERGED** |
| T32-fix-e2e-robot-venv-executable | tooling-e2e | W1 pós-T31 F-W1-robot | **MERGED** |
| T33-fix-e2e-zoekt-index-host-bin | tooling-e2e + catalog wiring | run r3 F-W1-007 | **MERGED** |
| T34-fix-host-local-repos-path-resolution | catalog_indexing | run r5 F-W1-008 | READY_FOR_IMPLEMENTATION |

## Ordem de merge sugerida

1. T29 (tooling — desbloqueia run e2e) — **mergeado**
2. T28 (boot/catalog sync) — **mergeado**
3. T31 (healthz antes de static mount) — **mergeado**
4. T22 (zoekt webserver compose) — **mergeado**
5. **T32** (robot do `.venv/bin` — launcher e2e)
6. **T33** (zoekt-index no host app — F-W1-007; depende T22 mergeado)
7. T24, T25, T23, T26, T27 (gaps)
8. T30 (imagem local + compose end-user)

## Notas r3

- Compose/healthy verdes pós T22+T31; falha dominante nova de tooling = `zoekt-index` ausente no host (≠ T22 webserver).
- T32 e T33 podem implementar em paralelo (ondas distintas); merge sugerido T32 → T33 por estabilizar launcher antes de re-run catalog completo.
