# Design — T35-fix-e2e-indexing-zoekt-wrapper-and-boot-race

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T35-fix-e2e-indexing-zoekt-wrapper-and-boot-race` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T35-fix-e2e-indexing-zoekt-wrapper-and-boot-race` |
| Base | `main` |
| Rastreabilidade | BDD-002; F-W1-007; T33; T14; T21 |

## 1. Contexto

Run e2e r6: BDD-016 ok (T34); BDD-002 falha — repo permanece `indexing` >900s.
Boot reconcile enfileira todos os repos antes do Robot; POST BDD-002 é no-op em
repo já `indexing`. Wrapper zoekt (T33) faz `podman cp` sem `mkdir -p` e sem
timeout — falha local (`error`) ou hang GitHub (>15min).

## 2. Solução

### 2.1 `zoekt_bin.py`

1. Antes de `podman cp`: `podman exec <cid> mkdir -p <tree_container>`.
2. `_default_run_command`: timeouts via env (`ZOEKT_CP_TIMEOUT_SECONDS`,
   `ZOEKT_EXEC_TIMEOUT_SECONDS`, `ZOEKT_MKDIR_TIMEOUT_SECONDS`); timeout →
   `E2eStackError`.
3. Falha de mkdir/cp levanta `E2eStackError` com stderr (já existente em cp).

### 2.2 `E2E_DEFER_STARTUP_INDEX`

Launcher e2e injeta `E2E_DEFER_STARTUP_INDEX=1` no env do host app.
`DefaultStartupIndexReconcile` recebe `defer_enqueue` de wiring; quando true,
atualiza tip/reconcile mas **não** chama `orchestrator.enqueue`.
Robot controla indexação via POST (BDD-002).

### 2.3 `orchestrator.enqueue`

Repos em `indexing` entram na fila interna (dedupe) **sem** `mark_queued`
(transição ilegal). Permite re-disparo via POST quando boot deixou job órfão.

## 3. Compatibilidade

- Produção sem `E2E_DEFER_STARTUP_INDEX`: comportamento T14 inalterado.
- Wrapper timeouts default generosos (cp 300s, exec 900s).
- Sem alteração em `e2e/robot/**`.

## 4. Rollback

Remover env defer; reverter enqueue INDEXING; remover mkdir/timeouts do wrapper.

## 5. Riscos

| Risco | Mitigação |
|---|---|
| Re-enqueue INDEXING duplica trabalho | Dedupe na fila; index idempotente no mesmo tip |
| Defer esquecido em prod | Env só setado pelo launcher e2e |
