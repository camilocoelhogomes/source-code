# Design — T36-fix-zoekt-index-cli-binary-e2e

| Campo | Valor |
|---|---|
| Task | `T36-fix-zoekt-index-cli-binary-e2e` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Decisão | Sidecar `zoekt-cli` + shebang `sys.executable` + filtro `name=_zoekt-cli_` |

## Problema

`sourcegraph/zoekt:latest` não contém `zoekt-index`. T33 `podman exec zoekt-index` falha. Wrapper `#/usr/bin/env python3` quebra com `ModuleNotFoundError: github_rag`.

## Solução

1. Serviço compose `zoekt-cli` (`docker/zoekt-cli/Dockerfile`) builda `zoekt-index` from source (linux/amd64).
2. `find_zoekt_container_id` filtra `name=_zoekt-cli_` (override `ZOEKT_CLI_CONTAINER_FILTER`).
3. `exec_zoekt_index_cli` invoca binário configurável (`ZOEKT_CONTAINER_INDEX_BIN`, default `zoekt-index`).
4. `materialize_zoekt_index_wrapper` usa `sys.executable` no shebang.

## Compatibilidade

- Contrato T10 (`-index`, `-name`, tree path) preservado.
- `E2E_DEFER_STARTUP_INDEX` já no launcher dev+e2e (68875fa) — sem alteração.
- `e2e/robot/**` congelado.

## Rollback

Remover serviço `zoekt-cli` e reverter filtro T33 (não recomendado — regressão F-W1-007).
