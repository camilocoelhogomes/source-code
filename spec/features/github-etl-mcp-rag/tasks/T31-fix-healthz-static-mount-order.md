# Task T31 — fix-healthz-static-mount-order

| Campo | Valor |
|---|---|
| Task ID | `T31-fix-healthz-static-mount-order` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Superfície | `health` + `container-delivery` |
| Origem | `mvp-local-e2e-green` / W1 pós T28/T29 (`F-W1-001`) |
| Evidência | `spec/features/mvp-local-e2e-green/runs/e2e-run-20260719-w2.md` |
| Revisão PO | `PENDING_PO_REVIEW` |

## Classificação

| ID | Classificação | Motivo |
|---|---|---|
| F-W1-001 | `produto` | `GET /healthz` → 404; StaticFiles em `/` intercepta rota registrada depois |
| F-W1-002 | `produto` (colateral) | Launcher e2e timeout 600s em `healthy` — efeito de F-W1-001 |

## Objetivo

Garantir que `GET /healthz` responde HTTP 200 com `status=ok`, `ui=ready` e `mcp=ready` quando UI+MCP estão prontos (**I-T19-007**, cenário **CD-01**).

## Evidência (sanitizada)

Run `e2e-run-20260719-w2.md` (commit `d4aab4b`, pós merge T28/T29):

| Check | Resultado |
|---|---|
| compose dev infra | ok |
| host app (`github_rag.delivery`) | running (~60s+) |
| `GET /healthz` | **404 Not Found** (Uvicorn log) |
| `GET /` | 200 |
| `GET /docs` | 200 |
| fase e2e | `healthy` — `healthz timeout` (exit 3) |

Causa raiz: `register_health_routes` em `_materialize_surfaces` (`delivery/runtime.py`) registra `/healthz` **depois** que `create_app` (`ui/app.py`) monta `StaticFiles` em `/`; o mount captura `/healthz` antes da rota explícita.

## Escopo

- Corrigir ordem de registro: `/healthz` deve ser alcançável quando runtime marca UI+MCP ready.
- Superfícies prováveis:
  - `src/github_rag/ui/app.py` — registrar health **antes** do mount static, **ou** adiar mount static para fase pós-health;
  - `src/github_rag/delivery/runtime.py` / `wire_ui_app` — builder pattern ou callback `get_state` injetado em `create_app` para health antes do static;
  - `src/github_rag/delivery/health.py` — manter contrato `I-T19-007` (sem alterar payload).
- Testes unitários: rota `/healthz` responde 200 pós-boot com app que inclui static root (UT-H03, I-T19-013).
- BDD CD-01 permanece fonte de verdade de superfície.

## Fora de escopo

- `e2e/robot/**` — sem alteração de contrato GREEN_PATH ou keywords Robot.
- Mudança de payload/contrato `/healthz` além de I-T19-007.
- T22–T30 (zoekt, env loader, imagem local, gaps) — não cobrem ordem health/static.

## Critérios de aceite

- [ ] `GET /healthz` → HTTP 200 com `{ "status": "ok", "ui": "ready", "mcp": "ready" }` após boot completo (CD-01 / I-T19-007).
- [ ] Com `web_root` presente, `/healthz` **não** retorna 404 (regressão F-W1-001).
- [ ] `GET /` e rotas `/api/*` continuam funcionando (static + API intactos).
- [ ] Testes unitários delivery/health + UI cobrem ordem mount vs health (UT-H03/H04).
- [ ] Cobertura ≥ 95% nos módulos alterados.
- [ ] `python -m github_rag.e2e` avança além da fase `healthy` (validação manual pós-merge; não alterar Robot).

## Dependências

| Tipo | Task | Motivo |
|---|---|---|
| Hard | — | independente |
| Soft | T28, T29 | run W1 já mergeou; T31 desbloqueia fase `healthy` do loop e2e |

## Rastreabilidade

| Artefato | Referência |
|---|---|
| Interface | I-T19-007, I-T19-013 |
| BDD | CD-01 (BDD-020) |
| Unit | UT-H03, UT-H04 |
| Falha | F-W1-001 |
