# Refatoração Blue — T18-management-ui

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T18-management-ui` |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Data | 2026-07-18 |

## Baseline

| Métrica | Antes Blue | Depois |
|---|---|---|
| Suíte UI | 29 passed | 33 passed |
| Cobertura global | ~98.4% | ≥98% |
| `ui/app.py` | handlers duplicavam payload hits + `_raise_http` + `raise` morto | `_http` + `_hits_payload`; `raise ... from exc` |

## Mudanças

1. Extrair `_hits_payload` — remove duplicação exact/semantic.
2. Trocar `_raise_http` + `raise` inalcançável por `raise _http(exc) from exc`.
3. Catch-all `/api/{path}` 404 antes do StaticFiles (já na impl; preservado).

## Não feito (sem medição de gargalo)

- Async drain com background tasks
- SPA framework
- Compressão de assets

## Decisão Architect

`BLUE_APPROVED_BY_ARCHITECT` — sem alteração de contrato; estrutura simplificada.
