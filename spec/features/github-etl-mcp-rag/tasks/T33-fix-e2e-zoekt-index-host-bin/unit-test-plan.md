# Unit test plan — T33-fix-e2e-zoekt-index-host-bin

| Campo | Valor |
|---|---|
| Task | `T33-fix-e2e-zoekt-index-host-bin` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Cobertura alvo | ≥ 95% global; módulos alterados 100% branches críticos |

## UT-P08 — zoekt_bin + host_env + launcher

| ID | Módulo | Cenário | Tipo |
|---|---|---|---|
| UT-P08-01 | `zoekt_bin` | `default_wrapper_dir` e2e vs dev | positivo |
| UT-P08-02 | `zoekt_bin` | `find_zoekt_container_id` retorna CID | positivo |
| UT-P08-03 | `zoekt_bin` | container ausente → `E2eStackError` | negativo |
| UT-P08-04 | `zoekt_bin` | `exec_zoekt_index_cli` traduz `-index` → `/data/index` | positivo |
| UT-P08-05 | `zoekt_bin` | `exec_zoekt_index_cli` podman cp + exec + cleanup | positivo |
| UT-P08-06 | `zoekt_bin` | `materialize_zoekt_index_wrapper` cria executável | positivo |
| UT-P08-07 | `zoekt_bin` | `resolve` com override explícito preserva path | positivo |
| UT-P08-08 | `zoekt_bin` | `resolve` materializa wrapper quando default | positivo |
| UT-P08-09 | `host_env` | `build_host_delivery_env` inclui `ZOEKT_INDEX_BIN` | positivo |
| UT-P08-10 | `launcher` | `_start_host_app` propaga bin resolvido (mock) | positivo |

Arquivo novo: `tests/unit/e2e/test_zoekt_bin_resolver.py`  
Delta: `tests/unit/e2e/test_host_env.py`, `tests/unit/e2e/test_launcher.py`
