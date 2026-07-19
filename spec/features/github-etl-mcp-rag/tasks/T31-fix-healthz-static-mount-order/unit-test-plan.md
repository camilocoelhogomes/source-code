# Unit test plan — T31 fix-healthz-static-mount-order

| Campo | Valor |
|---|---|
| Task | `T31-fix-healthz-static-mount-order` |
| Estado | `APPROVED_BY_ARCHITECT` |

## UT-H03 — health 200 pós-boot com static mount

| Caso | Entrada | Esperado |
|---|---|---|
| UT-H03a | `create_app` + `web_root` + `get_state` ready | `GET /healthz` → 200 ok |
| UT-H03b | `DefaultContainerRuntime.boot()` com web | `GET /healthz` → 200 ok |
| UT-H03c | ordem invertida (health após mount) | reproduz 404 (regressão guard) |

## UT-H04 — payload sem segredos

| Caso | Entrada | Esperado |
|---|---|---|
| UT-H04 | boot + `GET /healthz` | keys `{status,ui,mcp}`; sem token |

## Arquivos

- `tests/unit/ui/test_app_health_mount.py` (novo)
- `tests/unit/delivery/test_health.py` (UT-H03b reforçado)
- `tests/unit/delivery/test_wiring.py` (wire retorna builder)
