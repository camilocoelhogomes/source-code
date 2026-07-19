# Task T34 — fix-host-local-repos-path-resolution

| Campo | Valor |
|---|---|
| Task ID | `T34-fix-host-local-repos-path-resolution` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Superfície | `catalog_indexing` + `tooling-e2e` |
| Origem | run r5 F-W1-008 |
| Evidência | `e2e-run-20260719-r5.md` |

## Objetivo

Remapear `file:///repos/*` para `HOST_REPOS` quando app roda no host (e2e T21), registrando repos locais no catálogo.

## Evidência

`/api/catalog/issues`: `local volume path is inaccessible: /repos`  
Fixture em `e2e/fixtures/repos/sample-local`; `HOST_REPOS` setado mas não consumido pelo discovery.

## Escopo

- `sources/local/git_fs.py` / `discovery.py`: prefixo `/repos` → `HOST_REPOS` via env
- `delivery/wiring.py`: passar `environ` ao discovery
- Testes unitários + BDD local discovery
- **Não** alterar `e2e/robot/**` nem `e2e/fixtures/**`

## Critérios de aceite

- [ ] BDD-016: ≥1 repo `origin=local` no catálogo após boot e2e
- [ ] Issue `local-e2e-fixture` ausente ou resolvida
- [ ] Cobertura ≥95% módulos alterados
