# Reviews — T19-container-delivery

## Design `0.1.0`

| Severidade | Achado | Evidência | Correção esperada | Resultado |
|---|---|---|---|---|
| — | Nenhum BLOCKING/MAJOR | design.md | — | `APPROVED_BY_ARCHITECT` |

---

## Review — BDD (v0.1.0 → v0.1.1) — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `tests/bdd/test_container_delivery.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário; aprovação Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| BDD-020 — UI + MCP disponíveis | OK | CD-01 (`/healthz` ui/mcp ready); CD-09 volumes/env |
| BDD-021 smoke — config válida + sync | OK | CD-02 conexões nomeadas + sync 1× |
| BDD-022 smoke — fail-fast sem parcial | OK | CD-03: missing/blank/missing-file/invalid JSON + doubles; token leak; `run_container_boot` exit 1 |
| BDD-024 / DEC-015 — SDKs + grammars + uvicorn + git | OK | CD-05 pyproject + grammars + Dockerfile `pip install .` / `git` |
| ENG-011 — reconcile no boot | OK | CD-04 `StartupIndexReconcile.run()` 1× |
| D-T19-003 — ordem sync → reconcile → scheduler → bind | OK | CD-04 ordem completa (v0.1.1) |
| ContainerRuntime / entrypoint | OK | CD-10 exports + `python -m github_rag.delivery` |
| Dockerfile/compose asserts (ENG-002/005/006/009) | OK | CD-06..CD-09 |
| Sem domínio fora do escopo | OK | doubles de sync/reconcile; sem tip×estado / discovery / index pipeline |

### Achados (v0.1.0) — corrigidos em v0.1.1

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | CD-03 `test_missing_config_path_*` chamava `run_container_boot` sem injetar doubles; asserts de “sem sync/bind” eram vacuosos | `test_container_delivery.py` (v0.1.0 L262–296) | Fail-fast com `DefaultContainerRuntime` + doubles; entrypoint em teste separado | Corrigido |
| `MAJOR` | CD-03 listava blank `CONFIG_PATH` / arquivo inexistente sem cobertura executável alinhada ao design §5 | `bdd.md` CD-03; design §5 [1] | Testes `blank` + `missing_config_file` | Corrigido |
| `MAJOR` | CD-04 só assertava sync→reconcile; D-T19-003 exige scheduler e bind depois | `test_container_delivery.py` CD-04; design D-T19-003 | Ordem sync → reconcile → scheduler → bind_ui/bind_mcp | Corrigido |
| `MAJOR` | CD-05/BDD-024 citava grammars tree-sitter sem assert no pyproject | `bdd.md` CD-05; `DEC015_RUNTIME_PACKAGES` só `tree-sitter` | Assert do conjunto de grammars pinadas | Corrigido |
| `SUGGESTION` | Regex MCP no compose (`8001\|MCP_PORT\|mcp`) é ampla | CD-08 | Aceito no smoke de manifesto; interfaces/unit podem endurecer | Aceito |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — bdd.md v0.1.1 + `tests/bdd/test_container_delivery.py` alinhados ao design 0.1.0. Prosseguir para interfaces.

---

## Review — Interfaces `0.1.0` — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (aprovação Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Porta `ContainerRuntime.boot()` | OK | I-T19-002; §4 |
| `run_container_boot` + `DefaultContainerRuntime` keyword-only | OK | I-T19-003/004; §5; alinha CD-01..04 |
| Ordem D-T19-003 + fail-fast BDD-022 | OK | I-T19-005/006/014 |
| Wiring helpers + env sem reabrir T01 | OK | I-T19-008/009; §6/§10 |
| Health `/healthz` | OK | I-T19-007; §7; CD-01 |
| `__main__` + `mcp_stdio` | OK | I-T19-010/015; §8 |
| Exports públicos CD-10 | OK | I-T19-016; §9 |
| Manifesto separado (Dockerfile/compose asserts) | OK | I-T19-017; M-T19-*; §11 |
| Comentários responsabilidade/motivo em cada contrato | OK | §§4–9 |
| Sem domínio / sem implementação produção | OK | I-T19-018/020 |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces.md v0.1.0 sólidas e alinhadas a design 0.1.0 + BDD 0.1.1. Prosseguir para unit plan / stubs.

---

## Review — Unit test plan `0.1.0` — QA (pendente Architect)

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Artefato | `unit-test-plan.md` + `tests/unit/delivery/` |
| Data | 2026-07-18 |
| Resultado | `TESTS_READY_FOR_REVIEW` |

### Suíte

| Path | IDs |
|---|---|
| `tests/unit/delivery/test_runtime_boot.py` | UT-B01..B14 |
| `tests/unit/delivery/test_health.py` | UT-H01..H05 |
| `tests/unit/delivery/test_wiring.py` | UT-W01..W04 |
| `tests/unit/delivery/test_manifest.py` | UT-M01..M06 |
| `tests/unit/delivery/test_imports.py` | UT-X01..X04 |

### Demonstração RED

```bash
cd /private/tmp/github_rag_T19
PYTHONPATH=src /Users/camilocoelhogomes/projects/github_rag/.venv/bin/python -m pytest tests/unit/delivery/ -q --no-cov
```

Resultado QA: **33 failed**, 0 passed — `ImportError`/`ModuleNotFoundError` (`delivery` sem superfície) e `AssertionError` (Dockerfile/compose/`.env.example`/`uvicorn` ausentes). Sem commits nesta etapa.

---

## Review — Unit tests `0.1.1` — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` `0.1.1` + `tests/unit/delivery/**` |
| Data | 2026-07-18 |
| Pipeline | autonomous (aprovação Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Contratos I-T19-* / ordem boot | OK | UT-B01 ordem D-T19-003; UT-B08/B12 |
| BDD-022 fail-fast sem parcial | OK | UT-B02..B07, B11, B14, B15, B17; scheduler assertado |
| Extremos / corners / inválidos / vazio | OK | blank/missing/invalid JSON; INDEX_WORKERS; secret ausente; idle não bloqueia |
| Health / segredos | OK | UT-H01..H05; UT-B13 URL+token; pré-boot sem ASGI |
| Wiring env incompleto | OK | UT-W01..W04 |
| Manifesto M-T19-* | OK | UT-M01..M06 (+ UI/MCP env) |
| ENG-013 / entries | OK | UT-X01..X05 (`mcp_stdio`) |
| Sem domínio fora do escopo | OK | doubles; sem tip×estado |

### Achados (v0.1.0) — corrigidos em v0.1.1

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | Sem fail-fast de `wait_for_postgres` no caminho de `boot()` | plan UT-B* vs design §7 / I-T19-006 | UT-B15 | Corrigido |
| `MAJOR` | Sem cobertura de `skip_infra=True` omitindo wait/alembic | I-T19-011 ausente na matriz | UT-B16 | Corrigido |
| `MAJOR` | Sem fail-fast de secret ausente (`GITHUB_TOKEN`) | design §7 ConfigLoadError; BDD-022 | UT-B17 | Corrigido |
| `MAJOR` | Patches só em `wiring.*` — frágeis ao estilo de import do runtime | `test_runtime_boot.py` UT-B01/B06 | `helpers.patch_infra` dual-site | Corrigido |
| `MAJOR` | Fail-fast não assertava `scheduler.started == 0` | UT-B06/B07 / `_assert_exit_no_partial` | scheduler em todos os fail-fast | Corrigido |
| `MAJOR` | UT-B13 só checava token/`ghp_`, não URL completa | I-T19-019 | assert `secret_pass` + `DATABASE_URL` | Corrigido |
| `MAJOR` | Entry `mcp_stdio` (I-T19-010/015) sem unit | só UT-X04 `__main__` | UT-X05 | Corrigido |
| `MAJOR` | UT-H03 não garantia ausência de app pré-boot | plan “só após boot” | assert `ui_app`/`asgi_app` is None pré-boot | Corrigido |
| `SUGGESTION` | UT-W03 só checava `callable` | I-T19-012 | signature com `environ` | Corrigido |
| `SUGGESTION` | `.env.example` sem UI/MCP na matriz unit | I-T19-009 §10 | UT-M06 + `UI_PORT`/`MCP_*` | Corrigido |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — unit-test-plan v0.1.1 + `tests/unit/delivery/**` suficientes vs I-T19-* / design / BDD-022. Prosseguir para implementação (Developer).

---

## Review — Implementation — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `src/github_rag/delivery/**`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `docs/runbook-local.md`, diffs `tests/unit/delivery/test_health.py` / `test_wiring.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (aprovação Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` (após correção BLOCKING/MAJOR) |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Ordem boot ENG-011 / D-T19-003 | OK | `runtime.py` sync → `reconcile.run()` → `scheduler.start()` → surfaces |
| Fail-fast BDD-022 | OK | `SystemExit(1)` pré-bind; CD-03 / UT-B02..B17 |
| SDKs na imagem BDD-024 | OK | `Dockerfile` `pip install .` + `git`; `pyproject` DEC-015 + uvicorn |
| Sem `.venv` host / amd64 / healthz | OK | Dockerfile/compose/runbook; `GET /healthz` |
| Sem domínio novo; reconcile só T14 | OK | só `StartupIndexReconcile.run()`; sem tip×estado |
| Diff testes cobertura | OK | `test_health.py` / `test_wiring.py`: só cenários adicionais (503, factories, binds); sem enfraquecimento |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `BLOCKING` | `default_bind_ui` usa `uvicorn.run` (bloqueante) e `boot()` chamava `bind_ui` → `bind_mcp` em sequência; MCP nunca subia e `_ui_ready`/`_mcp_ready` só eram setados **depois** dos binds — `/healthz` nunca 200 em produção | `wiring.py` L337–348; `runtime.py` (pré-fix) L155–158 | Ready antes dos listeners; MCP em thread daemon no path de produção; UI bloqueia no main | **Corrigido** em `runtime.py` |
| `MAJOR` | Design §4.3/§5[10] exige drain da fila pós-reconcile em background; implementação não drenava (só cron T15) | design §4.3; `runtime.py` ausente `run_until_idle` pós-bind | Thread daemon `run_until_idle` **somente** com binds default (não quebra UT-B10) | **Corrigido** (`_start_background_index_drain`) |
| `SUGGESTION` | `mcp_stdio` sem ENG-011 completo | `mcp_stdio.py`; I-T19 permite path acoplado | Documentar no runbook | **Corrigido** em `docs/runbook-local.md` |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — implementação alinhada a design/interfaces/BDD após correção dos binds produção e drain background. Prosseguir Blue.

---

## Review — Blue — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `refactoring.md` + working tree pós-correção |
| Data | 2026-07-18 |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum | Estrutura já mínima (ports/runtime/wiring/health); sem gargalo de performance medido | N/A |

### Decisão

`BLUE_APPROVED_BY_ARCHITECT` — ver `refactoring.md`. Baseline: 1010 passed, cobertura global 96.38%.
