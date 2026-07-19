# Task T28 — fix-github-user-org-discovery

| Campo | Valor |
|---|---|
| Task ID | `T28-fix-github-user-org-discovery` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Superfície | `catalog_indexing` |
| Origem | `mvp-local-e2e-green` / T02 (`F-T01-002`) |
| Evidência | `spec/features/mvp-local-e2e-green/runs/e2e-run-20260719.md` |

## Classificação

| ID | Classificação | Motivo |
|---|---|---|
| F-T01-002 | `produto` | Delivery boot falha: `get_organization('camilocoelhogomes')` → HTTP 404; conta é usuário, não org |

## Objetivo

Permitir descoberta GitHub para contas de **usuário** (não só orgs) ou ajustar config e2e/fixtures para o modelo correto, de modo que `python -m github_rag.delivery` complete `catalog_sync` no green path local.

## Evidência (sanitizada)

```
GitHubDiscoveryError: erro HTTP 404 ao listar repositórios da org 'camilocoelhogomes'
CatalogSyncError: falha na descoberta GitHub durante sync do catálogo
```

Config: `e2e/fixtures/config.e2e.json` → `"orgs": ["camilocoelhogomes"]`, `"repos": ["camilocoelhogomes/source-*"]`.

## Escopo

- Suportar discovery por usuário (`/users/{login}/repos`) quando `orgs` contém login de usuário, **ou** schema de config que distingue `users` vs `orgs`.
- Atualizar `e2e/fixtures/config.e2e.json` se necessário.
- Boot delivery passa sync sem abortar e2e.

## Critérios de aceite

- `DefaultContainerRuntime().boot()` com fixture e2e + token válido não falha em catalog sync por 404 de org.
- Testes unitários/BDD cobrindo user vs org discovery.
- Cobertura ≥ 95%.

## Dependências

- Nenhuma dura; recomendado após T29 (env/runner estável).
