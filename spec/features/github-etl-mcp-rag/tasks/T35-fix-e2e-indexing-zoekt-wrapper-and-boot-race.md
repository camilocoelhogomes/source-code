# Task T35 — fix-e2e-indexing-zoekt-wrapper-and-boot-race

| Campo | Valor |
|---|---|
| Task ID | `T35-fix-e2e-indexing-zoekt-wrapper-and-boot-race` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Superfície | `catalog_indexing` + `tooling-e2e` |
| Origem | run r6 pós-T34 |
| Evidência | `e2e-run-20260719-r6.md` (pendente) |

## Objetivo

Desbloquear BDD-002: indexação conclui `up_to_date` em ≤900s; local deixa de ir para `error` no boot.

## Causa raiz

1. Boot reconcile enfileira indexação antes do Robot; BDD-002 POST é no-op em repo já `indexing`.
2. Wrapper T33: `podman cp` sem mkdir, sem timeout; GitHub repo grande trava >15min.

## Escopo

- `zoekt_bin.py`: mkdir antes cp, timeout cp/exec, stderr propagado
- Política e2e: `E2E_DEFER_STARTUP_INDEX` ou aguardar idle antes Robot (launcher/host_env)
- `orchestrator.enqueue`: re-enqueue ou retry quando INDEXING órfão
- Testes UT + cobertura ≥95%
- **Não** alterar `e2e/robot/**`

## Critérios

- [ ] BDD-002 pass
- [ ] Local indexável (desbloqueia BDD-003+)
- [ ] Re-run e2e catalog_indexing melhora vs r6 (3/10)
