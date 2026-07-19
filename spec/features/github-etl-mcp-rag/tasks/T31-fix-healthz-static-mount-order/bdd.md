# BDD — T31 fix-healthz-static-mount-order

| Campo | Valor |
|---|---|
| Task | `T31-fix-healthz-static-mount-order` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Rastreabilidade | BDD-HSM-001, CD-01, I-T19-007 |

## BDD-HSM-001 — `/healthz` alcançável com UI estática montada

**Dado** app FastAPI montado com `web_root` válido e readiness UI+MCP true  
**Quando** cliente HTTP faz `GET /healthz`  
**Então** resposta HTTP **200**  
**E** corpo JSON contém `status=ok`, `ui=ready`, `mcp=ready`  
**E** corpo não contém segredos  

**E** `GET /` continua HTTP **200** (static intacto)  
**E** `GET /api/repos` continua HTTP **200**

### Implementação pytest

| ID | Arquivo | Teste |
|---|---|---|
| BDD-HSM-001 | `tests/unit/delivery/test_health.py` | `test_ut_h03_healthz_200_with_static_mount` |
| BDD-HSM-001 | `tests/unit/ui/test_app_health_mount.py` | `test_create_app_healthz_before_static_mount` |
