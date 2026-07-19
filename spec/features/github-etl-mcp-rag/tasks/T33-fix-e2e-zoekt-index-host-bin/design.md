# Design — T33-fix-e2e-zoekt-index-host-bin

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T33-fix-e2e-zoekt-index-host-bin` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T33-fix-e2e-zoekt-index-host-bin` |
| Base | `main` @ `57bcdb4` |
| Rastreabilidade | F-W1-007; REQ-ZIH-*; D-T33-001..004; T10; T22; T21 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Wrapper podman exec; volume compartilhado; fail-fast; fallback env explícito |

## 1. Contexto

Modelo e2e: infra em compose (zoekt webserver saudável pós-T22) + app `github_rag.delivery` no host. `ZoektExactCodeIndex` (T10) invoca `ZOEKT_INDEX_BIN` (default `zoekt-index`) via `SubprocessZoektIndexRunner`. Binário ausente no host → `FileNotFoundError`.

## 2. Problema

`build_host_delivery_env` define `ZOEKT_URL` e `ZOEKT_INDEX_DIR` mas não `ZOEKT_INDEX_BIN`. Indexação falha antes de materializar shards.

## 3. Solução

### 3.1 Módulo `github_rag.e2e.zoekt_bin`

| Componente | Responsabilidade |
|---|---|
| `find_zoekt_container_id` | `podman compose -f <file> ps -q zoekt` → CID ou erro |
| `exec_zoekt_index_cli` | Parse argv T10; `podman cp` árvore host → container; `podman exec zoekt-index -index /data/index`; cleanup |
| `materialize_zoekt_index_wrapper` | Escreve script executável em `.data/{e2e\|dev}-zoekt-index-bin/zoekt-index` com compose path baked |
| `resolve_zoekt_index_bin` | Orquestra materialização pós-compose; respeita override explícito em env |

### 3.2 Wiring launcher

Após `compose up` bem-sucedido, `_start_host_app` chama `resolve_zoekt_index_bin` e passa path a `build_host_delivery_env(extra={"ZOEKT_INDEX_BIN": ...})`.

### 3.3 Fallback D-T33-003

Se `ZOEKT_INDEX_BIN` já definido no env do operador e ≠ `zoekt-index`, não sobrescrever.

### 3.4 Fail-fast

Container zoekt ausente após `up` → `E2eStackError` clara (sem FileNotFound silencioso no app).

## 4. Compatibilidade

- Sem alteração em `ZoektExactCodeIndex` / `SubprocessZoektIndexRunner` (D-T33-004).
- Sem alteração em `e2e/robot/**`.
- Volume `ZOEKT_INDEX_HOST` ↔ `/data/index` inalterado (D-T33-002).

## 5. Segurança

Wrapper não loga tokens; stderr redigido via contratos existentes.

## 6. Rollback

Remover wiring T33; operador define `ZOEKT_INDEX_BIN` manual ou instala zoekt no host.
