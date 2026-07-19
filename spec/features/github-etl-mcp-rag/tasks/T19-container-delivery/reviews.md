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
