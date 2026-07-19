# Unit Test Plan — T17-mcp-evidence-server

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T17-mcp-evidence-server` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Interfaces | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Cobertura alvo | ≥95% em `github_rag.mcp` e gate global |
| Branch | `feature/github-etl-mcp-rag-T17-mcp-evidence-server` |

## 1. Estratégia

| Camada | Arquivo | Doubles |
|---|---|---|
| Unit serialize | `tests/unit/mcp/test_serialize.py` | `QueryHit` / `FileContent` / `TreeListing` / `CatalogEntry` sintéticos |
| Unit errors | `tests/unit/mcp/test_errors.py` | subclasses `QueryError` + token sentinela |
| Unit tools / server | `tests/unit/mcp/test_tools.py` | `SpyQueryService`, `InMemoryCatalogRepository`, `SemaphoreWorkerLimiter` |
| Unit server lifecycle | `tests/unit/mcp/test_server.py` | fakes T16/T03/T04 + FastMCP real |
| Conformidade | `tests/unit/mcp/test_imports.py` | AST do pacote `github_rag.mcp` |
| Helpers | `tests/unit/mcp/helpers.py` | spy, seed, invoke/list tools |

- Sem Cursor real, sem Zoekt/Qdrant/Git reais, sem protocolo MCP caseiro.
- Stubs atuais: métodos de comportamento → `NotImplementedError` (I-T17-015). Suíte unitária **RED** até o Developer.
- BDD MCP-01..12 permanece a suíte de superfície; unitários cobrem contratos isolados e corners.

## 2. Matriz unitária

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-S01 | `details_from_includes` defaults | `DetailFields()` todos False | I-T17-005; MCP-02 |
| UT-S02 | `details_from_includes` todos True | quatro flags True | I-T17-005; MCP-03 |
| UT-S03 | `details_from_includes` matriz parcial | só `path=True` | I-T17-005 |
| UT-S04 | `omit_nulls` remove `None` top-level | chave ausente (não `null`) | I-T17-005; MCP-02 |
| UT-S05 | `omit_nulls` recursivo em dict aninhado | nulls internos omitidos | I-T17-005 |
| UT-S06 | `omit_nulls` preserva `0`/`False`/`""` | valores falsy não-None mantidos | corner |
| UT-S07 | `hit_to_dict` exact sem detalhes | `kind`; sem repository/path/commit/snippet; score omitido se None | I-T17-005/010 |
| UT-S08 | `hit_to_dict` semantic com score | `kind`+`score`; sem opcionais se None | MCP-02/09 |
| UT-S09 | `hit_to_dict` com includes preenchidos | quatro opcionais presentes | MCP-03 |
| UT-S10 | `hit_to_dict` nunca emite `chunk_metadata_summary` | chave ausente mesmo se DTO tiver | I-T17-010; MCP-09 |
| UT-S11 | `hit_to_dict` `line_number` só se não-None | presente/ausente | I-T17-010 |
| UT-S12 | `file_to_dict` UTF-8 | `content` str + `content_encoding=utf-8` | I-T17-007; MCP-11 |
| UT-S13 | `file_to_dict` bytes inválidos UTF-8 | `content_base64` + `base64`; sem `content` | I-T17-007; MCP-11 |
| UT-S14 | `file_to_dict` omite metadados None | sem repository/path/commit | omit-null |
| UT-S15 | `tree_to_dict` paths + omit nulls | `paths`; opcionais só se não-None | serialize |
| UT-S16 | `repo_entry_to_dict` campos obrigatórios + commits null | chaves I-T17-008; commits podem null | MCP-10 |
| UT-S17 | `repo_entry_to_dict` sem `local_path`/token | chaves proibidas ausentes | I-T17-008; BR-008 |
| UT-E01 | `McpToolError` guarda `message`/`kind` | atributos estáveis | I-T17-012 |
| UT-E02 | `map_query_error` tabela de kinds | subclasses → kind sugerido | interfaces §3.3 |
| UT-E03 | `map_query_error` não ecoa `SECRET_TOKEN` | ausente em message/str/repr | MCP-05/12; BDD-014 |
| UT-E04 | `QueryError` genérico → kind `query` | fallback | I-T17-012 |
| UT-T01 | `register_tools` registra exatamente 5 nomes | set == APPROVED | I-T17-003; MCP-01/08 |
| UT-T02 | sem `ask_codebase` | ausente | MCP-08 |
| UT-T03 | `search_code` → `search_exact` + DetailFields | spy request | I-T17-004/005 |
| UT-T04 | `semantic_search` sempre `reformulate=False` | spy; sem MetadataGenerator/QueryReformulator no pacote | I-T17-009; MCP-09 |
| UT-T05 | `list_repos` via catálogo; não chama QueryService | spy query vazio; repos OK | I-T17-004; MCP-10 |
| UT-T06 | `list_repos` catálogo vazio | `{"repos": []}` sucesso | MCP-12 |
| UT-T07 | `list_repos` omite inactive/`local_path`/token | só ativos; sem segredos | MCP-10 |
| UT-T08 | `read_file` UTF-8 / base64 na superfície | encoding correto | MCP-11 |
| UT-T09 | falha QueryError → `McpToolError`; sem `hits: []` | tipado; sem fallback | MCP-12 |
| UT-T10 | token ausente em sucesso e erro | redaction | MCP-05 |
| UT-L01 | toda tool sob `query_limiter.acquire` | acquire chamado (instrumentado) | I-T17-006; MCP-04 |
| UT-L02 | capacity=1: segunda `search_code` aguarda | waiter bloqueia até release | MCP-04 |
| UT-L03 | capacity=1: segunda `list_repos` aguarda | mesmo pool query | D-T17-006 |
| UT-L04 | pool index não usado | limiter injetado `pool="query"` | MCP-04 |
| UT-V01 | `search_code` pattern vazio/whitespace → `{"hits": []}` | paridade I-T16-009 (não erro) | T16 / entradas |
| UT-V01b | `semantic_search` query vazia → `McpToolError` kind `validation` | paridade I-T16-009 | T16 / map_query_error |
| UT-V02 | `read_file`/`list_tree` sem escopo → erro tipado | kind `validation` | I-T16-012 |
| UT-C01 | calls concorrentes capacity=2 → peak ≤ 2 | paralelismo | MCP-04 |
| UT-C02 | duas invocações idênticas `search_code` → resultados estáveis | idempotência observacional | corner |
| UT-B01 | `DefaultMcpEvidenceServer.build` → `FastMCP` | isinstance | I-T17-001/002; MCP-07 |
| UT-B02 | `run` callable; transport default stdio | capacidade | I-T17-011; MCP-06 |
| UT-B03 | `server_name` default `github-rag-evidence` | constante | I-T17-014 |
| UT-B04 | Protocol `McpEvidenceServer` runtime | isinstance | I-T17-002 |
| UT-X01 | import ban pacote mcp | sem qdrant/openai/github/git/httpx/requests/fastmcp | I-T17-013; MCP-07 |
| UT-X02 | SDK `mcp` / `FastMCP` presente + pin pyproject | importável; `mcp>=1.27,<2` | I-T17-001; MCP-07 |
| UT-X03 | sem `MetadataGenerator`/`QueryReformulator` no fonte mcp | AST/texto | I-T17-009 |
| UT-F01 | `FakeMcpEvidenceServer` existe como double | símbolo importável | interfaces §3.6 |

## 3. Demonstração RED (TDD)

```bash
.venv/bin/python -m pytest tests/unit/mcp/ -q --no-cov
```

Falhas esperadas pré-implementação:

| Área | Razão |
|---|---|
| serialize / `map_query_error` / `register_tools` / `build`/`run` | `NotImplementedError` (stubs I-T17-015) |
| tools/limiter via `build()` | comportamento incompleto dos stubs |
| Conformidade UT-X* / `McpToolError` / constantes | podem passar (estrutura já presente) |

Após implementação Developer: verde + cobertura ≥95% em `github_rag.mcp`.

## 4. Fora de escopo unitário

- Cursor E2E / stdio real
- Implementação de `DefaultMcpEvidenceServer` (Developer)
- T15 scheduler
- Alterar contratos T16/T07/T04

## 5. Architect Review

| Decisão | Status | Autor | Data |
|---|---|---|---|
| APPROVED_BY_ARCHITECT | aprovado | tech-lead-architect | 2026-07-18 |
