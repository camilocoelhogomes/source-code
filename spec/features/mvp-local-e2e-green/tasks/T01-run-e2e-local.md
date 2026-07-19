# Task T01 — run-e2e-local

| Campo | Valor |
|---|---|
| Task ID | `T01-run-e2e-local` |
| Feature | `mvp-local-e2e-green` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W1 |
| Plano | v0.1.0 |

## Objetivo

Executar a prova e2e local canônica via `python -m github_rag.e2e` (Podman + stack real + GitHub real) e registrar exit code, suítes/cenários falhos e artefatos observáveis.

## Escopo

- Pré-reqs: `.env` com token válido (não versionado), Podman + compose provider, `pip install -e ".[e2e]"`, `rfbrowser init` — conforme `e2e/README.md` e checklist `mvp-e2e-audit-hardening`.
- Comando: `python -m github_rag.e2e`.
- Suítes green path REQ-002: `health`, `catalog_indexing`, `ui`, `ui_browser`, `mcp`, `negative` (`--exclude bdd015`).
- Registrar por execução: exit code, fase (compose/healthy/robot), suítes/cenários falhos, timeouts/rate-limit, paths de artefatos em `e2e/results/` (gitignored).
- Versionar **somente** resumo sanitizado em `spec/features/mvp-local-e2e-green/runs/`.
- Classificar falhas por superfície para handoff T02 (`health` | `catalog_indexing` | `ui` | `mcp` | `negative` | `tooling-e2e` | `container-delivery`).
- Falha de token/stack/timeout/rate limit **vira achado registrado** — não abortar sem evidência (REQ-014).

## Fora de escopo

- Abrir tasks no pai (T02).
- Disparar orquestrador autônomo (T03).
- Build imagem `github-rag:local` / alterar `docker-compose.yml` (T04).
- Corrigir produto ou expandir suíte Robot.
- Merge de PRs (T05).

## Dependências

- Pré-reqs HITL (`.env`, Podman, deps e2e).
- Consumo: T19 (`docker-compose.e2e.yml`), T21 (`src/github_rag/e2e/**`, `e2e/robot/**`).

## Critérios de aceite

- `python -m github_rag.e2e` executado; resultado observável documentado (BDD-001, REQ-013).
- Cada falha mapeada a superfície + classificação preliminar (`produto` | `flakiness` | `gap-teste` | `tooling-e2e`).
- Nenhum segredo no artefato versionado (BDD-008, BR-004).
- Handoff explícito para T02.

## Arquivos prováveis

- `spec/features/mvp-local-e2e-green/runs/e2e-run-YYYYMMDD.md`
- Consumo: `docker-compose.e2e.yml`, `e2e/README.md`, `src/github_rag/e2e/**`
- Locais gitignored: `e2e/results/`

## Rastreabilidade

- REQ-001, REQ-011–014; DEC-002; BDD-001, BDD-008.

## Handoff

- Achados runtime → T02 (`open-bug-tasks-parent`).
- Se exit 0: registrar verde e ainda passar por T02 (dedup/confirm zero falhas novas vs T22–T27).
