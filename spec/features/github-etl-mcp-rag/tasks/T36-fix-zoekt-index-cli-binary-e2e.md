# Task T36 — fix-zoekt-index-cli-binary-e2e

| Campo | Valor |
|---|---|
| Task ID | `T36-fix-zoekt-index-cli-binary-e2e` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Superfície | `tooling-e2e` + `catalog_indexing` |

## Problema

`sourcegraph/zoekt:latest` **não contém** binário `zoekt-index` (só webserver/archive-index). Wrapper T33 falha: `executable file zoekt-index not found in $PATH`. Shebang wrapper usa `python3` sem venv → `ModuleNotFoundError`.

## Escopo

- Imagem zoekt com CLI de indexação **ou** serviço sidecar/indexer no compose dev+e2e
- Wrapper: shebang `sys.executable`; invocar binário correto (`zoekt-index` ou equivalente documentado T10)
- Testes + e2e/README
- Sem alterar `e2e/robot/**`

## Aceite

- [ ] Indexação local sample-local conclui sem erro Zoekt CLI
- [ ] BDD-002 pass (ref repo up_to_date)
