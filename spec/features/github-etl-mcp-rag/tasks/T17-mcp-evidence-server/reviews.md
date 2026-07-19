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

---

## Review — BDD (v0.1.0) — QA → Architect

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Artefato | `bdd.md` + `tests/bdd/test_mcp_evidence_server.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `READY_FOR_ARCHITECT_REVIEW` |

### Entrega QA

| Item | Detalhe |
|---|---|
| Cenários | MCP-01..MCP-12 |
| Produto | BDD-011, BDD-012, BDD-013, BDD-014, BDD-015 (capacidade), BDD-024 |
| Extras | sem `ask_codebase`; `reformulate=False`; `list_repos` sem `local_path`/token; encoding read_file; erros tipados |
| Fixtures | `FakeQueryService`+spy, `InMemoryCatalogRepository`, `SemaphoreWorkerLimiter` |
| Estado testes | **RED** — import de `DefaultMcpEvidenceServer` / `McpToolError` falha (produção T17 ainda ausente) |
| Comando | `python -m pytest tests/bdd/test_mcp_evidence_server.py -q` |

### Pedido ao Architect

Revisar alinhamento design §4 / D-T17-* e aprovar ou devolver com achados. QA **não** auto-aprova.

---

## Review — BDD (v0.1.0) — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `tests/bdd/test_mcp_evidence_server.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário; aprovação Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| BDD-011 — 5 tools / evidências / sem narrativa-SLM | OK | MCP-01, MCP-08 |
| BDD-012 — omit/include `DetailFields` na superfície | OK | MCP-02, MCP-03 (exact+semantic) |
| BDD-013 — pool query / excedentes aguardam / list_repos incluso | OK | MCP-04 (+ `list_repos`) |
| BDD-014 — token ausente | OK | MCP-05, MCP-12 |
| BDD-015 — capacidade list/call/`run` | OK | MCP-06 |
| BDD-024 — SDK `mcp`/`FastMCP`; ban imports | OK | MCP-07 |
| D-T17-009/010 — `reformulate=False`; sem `chunk_metadata_summary` | OK | MCP-09 |
| D-T17-008 — `list_repos` sem `local_path`; commits §4.5 | OK | MCP-10 |
| D-T17-007 — UTF-8 / base64 | OK | MCP-11 |
| Fixtures fakes; sem Cursor/Zoekt/Qdrant | OK | § Fixtures; testes |

### Achados (corrigidos nesta review)

| Severidade | Achado | Evidência | Correção | Status |
|---|---|---|---|---|
| `MAJOR` | MCP-03 não exercitava `semantic_search` com todos `include_*=True` | design §4.4; bdd MCP-03 | Teste + critérios atualizados | Corrigido |
| `MAJOR` | MCP-04 não proveava `list_repos` sob `query_limiter` | D-T17-006 | `test_list_repos_also_respects_query_limiter` | Corrigido |
| `MAJOR` | MCP-10 omitia `last_processed_commit` / `current_main_commit` | design §4.5 | Critérios + asserts | Corrigido |
| `SUGGESTION` | Verificação explícita “pool index não usado” é fraca | MCP-04 texto | Aceito — construção injeta só query limiter; unit opcional | Aceito |
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — bdd.md v0.1.0 + testes alinhados ao design APPROVED. Prosseguir para interfaces.

---

## Review — Interfaces (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` + stubs `src/github_rag/mcp/*` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| I-T17-001 — SDK `mcp`/`FastMCP`; pin `<2` | OK | interfaces §2; `pyproject.toml`; `server.py`/`ports.py` import |
| I-T17-002/014 — `McpEvidenceServer` / `DefaultMcpEvidenceServer` | OK | `ports.py`, `server.py` |
| I-T17-003 — 5 tools fechadas | OK | `tools.APPROVED_TOOL_NAMES`; §3.4 |
| I-T17-004..013 — catálogo/QueryService/DetailFields/limiter/encoding/erros/bans | OK | §2–§5 |
| Comentários responsabilidade + motivo em cada contrato | OK | interfaces §3 + docstrings nos stubs |
| Stubs sem comportamento completo (`NotImplementedError`) | OK | `build`/`run`/`register_tools`/serialize/`map_query_error` |
| Alinhamento BDD MCP-01..12 | OK | interfaces §6 |
| Símbolos BDD importáveis | OK | `DefaultMcpEvidenceServer`, `McpToolError` |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING`, `MAJOR` ou `SUGGESTION` | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces v0.1.0 + stubs. Prosseguir para unit-test plan / implementação.
