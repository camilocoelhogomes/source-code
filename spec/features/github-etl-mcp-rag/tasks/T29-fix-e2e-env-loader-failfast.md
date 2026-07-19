# Task T29 — fix-e2e-env-loader-failfast

| Campo | Valor |
|---|---|
| Task ID | `T29-fix-e2e-env-loader-failfast` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Superfície | `tooling-e2e` |
| Origem | `mvp-local-e2e-green` / T02 (`F-T01-001`, `F-T01-003`) |
| Evidência | `spec/features/mvp-local-e2e-green/runs/e2e-run-20260719.md` |

## Classificação

| ID | Classificação | Motivo |
|---|---|---|
| F-T01-001 | `tooling-e2e` | `source .env` quebra em zsh: `INDEX_CRON=0 2 * * *` |
| F-T01-003 | `produto` | Launcher não fail-fast quando `github_rag.delivery` morre (zombie); espera 600s healthz |

## Objetivo

Tornar o fluxo e2e local robusto: carregamento de env seguro e falha rápida quando o app host exit ≠ 0.

## Escopo

- Documentar `.env.example` com `INDEX_CRON="0 2 * * *"` (aspas) e/ou loader Python no entrypoint `github_rag.e2e`.
- `PodmanE2eStackLauncher.wait_healthy`: detectar exit do processo host e levantar `E2eStackError` imediato com stderr sanitizado.
- Atualizar `e2e/README.md` com comando de env seguro.

## Critérios de aceite

- `source .env` ou equivalente documentado não quebra shell.
- Delivery crash → e2e exit ≠ 0 em segundos, não após timeout healthz.
- Testes unitários launcher cobrindo fail-fast.

## Dependências

- Nenhuma (desbloqueia T01/T03 loop).
