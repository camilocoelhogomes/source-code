# Orquestração T03 — onda 1

| Campo | Valor |
|---|---|
| Feature | `mvp-local-e2e-green` |
| Task | `T03-orchestrate-bugfix-loop` |
| Data | 2026-07-19 |
| Base main | `1d3f023` |

## Onda 1 (paralelo, base `main`)

| Task | Branch | Motivo |
|---|---|---|
| T29-fix-e2e-env-loader-failfast | `feature/github-etl-mcp-rag-T29-fix-e2e-env-loader-failfast` | Desbloqueia run e2e (fail-fast + env) |
| T28-fix-github-user-org-discovery | `feature/github-etl-mcp-rag-T28-fix-github-user-org-discovery` | Delivery boot catalog sync |

## Onda 2 (após onda 1)

T22, T23, T24, T25, T27, T30

## T26

Estado `PR_OPENED` — incluir na ordem de merge se aplicável.

## Critério de parada

`python -m github_rag.e2e` exit 0 → merge auto PRs (DEC-005 operador).
