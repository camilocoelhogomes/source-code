# Design — T31 fix-healthz-static-mount-order

| Campo | Valor |
|---|---|
| Task | `T31-fix-healthz-static-mount-order` |
| Feature | `github-etl-mcp-rag` |
| Versão | `0.1.0` |
| Estado | `APPROVED_BY_ARCHITECT` |

## Contexto

`GET /healthz` retorna **404** após boot com `web_root` presente. `create_app` monta `StaticFiles` em `/` antes que `register_health_routes` (em `_materialize_surfaces`) adicione a rota explícita — o mount captura `/healthz`.

Evidência: `spec/features/mvp-local-e2e-green/runs/e2e-run-20260719-w2.md` (F-W1-001).

## Solução

### D-T31-001 — Health antes do mount estático

`create_app` aceita callback opcional `get_state`. Quando presente, chama `register_health_routes` **antes** de `app.mount("/", StaticFiles(...))`.

### D-T31-002 — Builder pattern em wire_ui_app

`wire_ui_app` retorna `DefaultManagementUiApi` (não built). `_materialize_surfaces` chama `build(get_state=...)` passando readiness do runtime.

### D-T31-003 — Remover registro tardio

`_materialize_surfaces` deixa de chamar `register_health_routes` após `build()` quando `get_state` já foi injetado via builder. Fallback mantido para apps ASGI injetados diretamente (test doubles).

## Componentes

| Componente | Arquivo | Mudança |
|---|---|---|
| UI app | `src/github_rag/ui/app.py` | `get_state` opcional; health antes static |
| UI API | `src/github_rag/ui/api.py` | `build(get_state=...)` |
| Wiring | `src/github_rag/delivery/wiring.py` | retorna builder |
| Runtime | `src/github_rag/delivery/runtime.py` | `build(get_state=...)` |
| Tests | `tests/unit/delivery/test_health.py` | UT-H03 mount order |
| Tests | `tests/unit/ui/test_app_health_mount.py` | ordem create_app |

## Fluxo

```
wire_ui_app → DefaultManagementUiApi
_materialize_surfaces → build(get_state=lambda readiness)
create_app → register_health_routes → /api/* → StaticFiles mount
```

## Erros / compatibilidade

- `create_app` sem `get_state`: comportamento T18 inalterado (sem `/healthz`).
- Payload `/healthz` inalterado (I-T19-007).
- `GET /` e `/api/*` preservados.

## Riscos

| Risco | Mitigação |
|---|---|
| Test doubles injetam FastAPI pronto | Fallback `register_health_routes` em `_materialize_surfaces` |
| Regressão T18 static | Teste GET `/` com web_root |

## Rollback

Reverter branch; health volta 404 com static mount (F-W1-001).
