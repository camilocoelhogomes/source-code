# Reviews — T17-mcp-evidence-server

## Review — Design (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Escopo T17 (MCP evidências; sem UI/indexação/compose) | OK | §1, §16, handoff §17 |
| DEC-015 / BR-023 / BDD-024 — só SDK oficial `mcp` (`FastMCP`); pin `<2`; sem `fastmcp` Prefect | OK | §4.1, D-T17-001, D-T17-013 |
| Tools fechadas REQ-028 (5); sem `ask_codebase`/narrativa/SLM | OK | §4.3, D-T17-003, D-T17-009 |
| `list_repos` via catálogo; demais via `QueryService` | OK | §4.3–4.5, D-T17-004 |
| BDD-012 — `include_*` → `DetailFields` + omit-null | OK | §4.4, D-T17-005 |
| BDD-013 — `QUERY_WORKERS` / `create_query_limiter` / `acquire` | OK | §4.8, D-T17-006 |
| BDD-014 / BR-008 — sem token em respostas/erros/logs | OK | §6, §7, D-T17-008, D-T17-012 |
| BR-011 / DEC-008 — semantic sem reformulate/MetadataGenerator | OK | §3.1, D-T17-009, D-T17-010 |
| ENG-007 — superfície consome portas; sem client paralelo | OK | §3, D-T17-002, D-T17-013 |
| Handoff T19 (processo stdio) | OK | §4.10, §17, D-T17-011 |
| Alinhamento handoff T16 | OK | consome `QueryService`/`DetailFields`; sem reformulador |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING`, `MAJOR` ou `SUGGESTION` | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.0. Prosseguir para BDD e interfaces.
