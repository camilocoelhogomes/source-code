# BDD — T17-mcp-evidence-server

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T17-mcp-evidence-server` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Rastreabilidade | BDD-011–015; BDD-024; REQ-003, REQ-028–033; BR-008, BR-011, BR-023; DEC-008, DEC-015; ENG-007, ENG-013; D-T17-001–013 |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `READY_FOR_ARCHITECT_REVIEW` | `0.1.0` | MCP-01..MCP-12: superfície MCP com fakes T16/T03/T04 (sem Cursor/Zoekt/Qdrant reais). |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Alinhado ao design; correções MAJOR: MCP-03 semantic+includes; MCP-04 list_repos no limiter; MCP-10 commits. |

## Escopo

Superfície `McpEvidenceServer` / `DefaultMcpEvidenceServer` (pacote `github_rag.mcp`): registra exatamente 5 tools no SDK oficial `mcp` (`FastMCP`), delega a `CatalogRepository` + `QueryService`, limita paralelismo com `WorkerLimiter` do pool query, serializa evidências sem narrativa/SLM.

## Fixtures de teste (design §11)

| Double | Origem | Uso |
|---|---|---|
| `FakeQueryService` (+ spy no teste) | `github_rag.query.fake` | exact/semantic/read/tree sem backends reais |
| `InMemoryCatalogRepository` | `github_rag.catalog.memory` | `list_repos` / estados REQ-020 |
| `SemaphoreWorkerLimiter` / `create_query_limiter` | `github_rag.concurrency` | BDD-013 / `QUERY_WORKERS` |
| Token sentinela | constante de teste | BDD-014 |

- Sem Cursor real, sem Zoekt/Qdrant/Git reais, sem protocolo MCP caseiro.
- Tools invocadas via `McpEvidenceServer.build()` → FastMCP (list/call), não via stdio no gate BDD.

## Cenários executáveis

### MCP-01 — BDD-011: cinco tools retornam evidências; sem SLM/narrativa

**Rastreabilidade:** BDD-011; REQ-028; REQ-031/032; DEC-008; D-T17-003

**Dado** um `DefaultMcpEvidenceServer` com `FakeQueryService` pré-carregado (hits exact/semantic, `FileContent`, `TreeListing`) e `InMemoryCatalogRepository` com ao menos um repo ativo  
**E** `query_limiter` = `SemaphoreWorkerLimiter(capacity=4, pool="query")`  
**Quando** as tools `list_repos`, `search_code`, `semantic_search`, `read_file` e `list_tree` são invocadas via o `FastMCP` retornado por `build()`  
**Então** cada uma devolve evidência estruturada correspondente (`repos` / `hits` / conteúdo / `paths`)  
**E** nenhuma resposta contém prosa narrativa gerada (sem campos de “answer”/“explanation”/“summary” gerados)  
**E** o grafo de dependências do servidor **não** inclui `MetadataGenerator`, `QueryReformulator` nem cliente SLM/`openai`  
**E** `ask_codebase` **não** está registrada

**Critérios de verificação**
- `assert set(tool_names) == {"list_repos", "search_code", "semantic_search", "read_file", "list_tree"}`
- Respostas JSON com chaves de evidência; ausência de chaves narrativas
- AST/import do pacote `github_rag.mcp`: sem `openai`, `MetadataGenerator`, `QueryReformulator`

---

### MCP-02 — BDD-012: detalhes omitidos quando `include_*` default (False)

**Rastreabilidade:** BDD-012; REQ-030; D-T17-005

**Dado** `FakeQueryService` que, ao receber `DetailFields` default, devolve hits com `repository`/`path`/`commit`/`snippet` em `None` (ou o servidor omite nulls)  
**E** chamadas a `search_code` / `semantic_search` **sem** `include_repository`/`include_path`/`include_commit`/`include_snippet`  
**Quando** as tools retornam JSON  
**Então** cada hit **não** contém as chaves `repository`, `path`, `commit`, `snippet` (omitidas — não `"repository": null`)  
**E** `kind` permanece presente; em semantic, `score` permanece quando aplicável  
**E** o `QueryService` foi chamado com `DetailFields` todos `False`

**Critérios de verificação**
- Para cada hit dict: `assert "repository" not in hit and "path" not in hit and "commit" not in hit and "snippet" not in hit`
- `assert hit["kind"] in {"exact", "semantic"}`
- Spy: `request.details == DetailFields()`

---

### MCP-03 — BDD-012: detalhes incluídos quando solicitados

**Rastreabilidade:** BDD-012; REQ-030; D-T17-005

**Dado** backends fake com evidências conhecidas (`repo=acme/api`, `path=src/auth.py`, `commit=abc123`, snippet com `authenticate`)  
**E** `search_code` / `semantic_search` com todos `include_*=True`  
**Quando** as tools são invocadas  
**Então** os hits JSON incluem os quatro campos com valores vindos do `QueryService`  
**E** matriz parcial: só `include_path=True` → só `path` presente; demais três chaves ausentes

**Critérios de verificação**
- `search_code` e `semantic_search` com todos True: chaves presentes com valores esperados; spy `DetailFields` espelha os `include_*` em ambas
- Só path (`search_code`): `assert "path" in hit and "repository" not in hit and "commit" not in hit and "snippet" not in hit`

---

### MCP-04 — BDD-013: paralelismo ≤ `QUERY_WORKERS`; excedentes aguardam

**Rastreabilidade:** BDD-013; REQ-029; BR-006; D-T17-006

**Dado** `SemaphoreWorkerLimiter(capacity=2, pool="query")` (ou `create_query_limiter` com `query_workers=2`)  
**E** um spy de `QueryService` que bloqueia dentro da delegação até sinal de release  
**Quando** 4 invocações concorrentes de `search_code` são disparadas  
**Então** o pico de execuções simultâneas na delegação é `<= 2`  
**E** as excedentes só entram após liberação de slot (aguardam capacidade)  
**E** com capacity=1, a segunda `search_code` permanece pendente até release da primeira  
**E** `list_repos` também consome o mesmo pool query (capacity=1: segunda call aguarda; D-T17-006)  
**E** o pool de indexação **não** é usado

**Critérios de verificação**
- `assert peak <= 2` (search_code ×4, capacity=2)
- Com capacity=1: segunda `search_code` pendente até release
- Com capacity=1: segunda `list_repos` pendente até release (catálogo instrumentado)
- Limiter injetado é o de query (`pool="query"`)

---

### MCP-05 — BDD-014: token ausente de respostas e erros MCP

**Rastreabilidade:** BDD-014; BR-008; D-T17-012; D-T17-008

**Dado** token sentinela `SECRET_TOKEN = "ghp_should_never_appear_in_mcp_9f3a2"` presente apenas no ambiente de teste (não passado às tools)  
**E** `FakeQueryService` configurado para falhar com `QueryError` cuja causa interna poderia ecoar o token  
**Quando** uma tool MCP falha e/ou sucede (`list_repos`, `search_code`, …)  
**Então** o corpo JSON de sucesso **não** contém o token  
**E** a mensagem de erro exposta (`McpToolError` / payload de erro da tool) **não** contém o token  
**E** `str(exc)` / `repr(exc)` da superfície MCP não contém o token

**Critérios de verificação**
- `assert SECRET_TOKEN not in json.dumps(success_payload)`
- `assert SECRET_TOKEN not in error_message`
- `assert SECRET_TOKEN not in str(exc) and SECRET_TOKEN not in repr(exc)`

---

### MCP-06 — BDD-015: tools listáveis e utilizáveis (capacidade)

**Rastreabilidade:** BDD-015; REQ-003; REQ-033; D-T17-002

**Dado** um `DefaultMcpEvidenceServer` construído com fakes válidos  
**Quando** `build()` é chamado  
**Então** o host MCP (FastMCP) lista exatamente as 5 tools aprovadas com nomes REQ-028  
**E** cada tool pode ser invocada com argumentos mínimos válidos e retorna evidência utilizável (não stub vazio obrigatório quando há dados no fake)  
**E** `run(transport="stdio")` existe na porta (capacidade de processo; sem abrir stdio real no gate)

**Critérios de verificação**
- `list_tools` → 5 nomes
- Invocação bem-sucedida de cada tool
- `assert callable(server.run)`

---

### MCP-07 — BDD-024: SDK oficial `mcp` / FastMCP; sem protocolo caseiro

**Rastreabilidade:** BDD-024; BR-023; DEC-015; ENG-013; D-T17-001; D-T17-013

**Dado** o pacote de produção `github_rag.mcp`  
**Quando** `build()` é executado e as importações de produção são inspecionadas  
**Então** o servidor é instância / produto de `mcp.server.fastmcp.FastMCP`  
**E** existe `import mcp` / uso de `from mcp.server.fastmcp import FastMCP`  
**E** AST do pacote **não** implementa framing JSON-RPC/HTTP MCP caseiro nem usa pacote standalone `fastmcp` (Prefect)  
**E** não há import de `qdrant_client`, cliente Zoekt HTTP, `PyGithub`/`github`, `openai` dentro de `github_rag.mcp`

**Critérios de verificação**
- `from mcp.server.fastmcp import FastMCP` e `isinstance(app, FastMCP)` (ou type name/module `mcp.server.fastmcp`)
- AST: ausência de módulos proibidos; presença de import `mcp`
- Sem módulo/protocolo caseiro paralelo

---

### MCP-08 — Sem `ask_codebase`; conjunto fechado de 5 tools

**Rastreabilidade:** DEC-008; REQ-028; D-T17-003

**Dado** o `FastMCP` de `build()`  
**Quando** a lista de tools é inspecionada  
**Então** `ask_codebase` está ausente  
**E** não há tools além das cinco aprovadas

**Critérios de verificação**
- `assert "ask_codebase" not in tool_names`
- `assert len(tool_names) == 5`

---

### MCP-09 — `semantic_search` sempre com `reformulate=False`

**Rastreabilidade:** BR-011; DEC-008; D-T17-009; D-T17-010

**Dado** spy de `QueryService` registrando `SemanticSearchRequest`  
**Quando** `semantic_search` é invocada com query qualquer  
**Então** a única chamada a `search_semantic` usa `reformulate=False`  
**E** a resposta JSON de hits **não** inclui `chunk_metadata_summary`  
**E** o servidor MCP **não** recebe `QueryReformulator` no composition root de teste

**Critérios de verificação**
- `assert all(r.reformulate is False for r in spy.semantic_requests)`
- `assert "chunk_metadata_summary" not in hit` para cada hit

---

### MCP-10 — `list_repos` sem `local_path`/token; estados REQ-020

**Rastreabilidade:** D-T17-008; BR-008; REQ-020

**Dado** catálogo com repo GitHub ativo e repo local ativo com `local_path="/secret/mount/repo"`  
**E** entradas em estados distintos do conjunto REQ-020 quando aplicável  
**Quando** `list_repos` é invocada  
**Então** cada item tem `repo_key`, `repository_id`, `origin`, `connection_name`, `state`, `last_processed_commit`, `current_main_commit` (commits podem ser `null`)  
**E** **nenhum** item contém `local_path` nem token  
**E** `state` ∈ `{not_indexed, queued, indexing, up_to_date, error}`  
**E** repos `active=False` não aparecem

**Critérios de verificação**
- Chaves obrigatórias do design §4.5 presentes em cada item
- `assert "local_path" not in repo_item` para todos
- `assert SECRET_TOKEN not in json.dumps(payload)`
- Soft-deleted ausente da lista

---

### MCP-11 — `read_file`: UTF-8 texto ou `content_base64`

**Rastreabilidade:** D-T17-007

**Dado** `FakeQueryService` com `FileContent(content=b"hello\n")`  
**Quando** `read_file` é invocada  
**Então** resposta tem `"content": "hello\n"` e `"content_encoding": "utf-8"`  

**Dado** conteúdo inválido como UTF-8 (`b"\xff\xfe"`)  
**Quando** `read_file` é invocada  
**Então** resposta tem `"content_base64"` e `"content_encoding": "base64"`  
**E** **não** tem campo texto `content`

**Critérios de verificação**
- UTF-8: `content` str + encoding utf-8
- Binary: `content_base64` presente; `content` ausente

---

### MCP-12 — Erro tipado de tool sem eco de segredo; lista vazia é sucesso

**Rastreabilidade:** design §6; D-T17-012; BDD-014

**Dado** catálogo vazio  
**Quando** `list_repos` é invocada  
**Então** sucesso com `{"repos": []}` (não erro)

**Dado** `FakeQueryService` que levanta `QueryRepositoryNotFoundError`  
**Quando** `search_code` / `read_file` falha  
**Então** a falha é tipada na superfície (`McpToolError` ou erro de tool com tipo lógico estável)  
**E** mensagem sem token sentinela  
**E** não há fallback silencioso para `hits: []` quando o backend falhou

**Critérios de verificação**
- Lista vazia: `assert payload == {"repos": []}` (ou equivalente com chave `repos`)
- Falha: erro tipado; `SECRET_TOKEN not in message`; não retorna hits inventados

## Fora de escopo destes BDD

- Validação humana Discovery E2E no Cursor (produto amplo BDD-015)
- UI / FastAPI / `QueryReformulator` real (T18)
- Compose/Dockerfile (T19)
- Transport SSE/HTTP Streamable
- Zoekt/Qdrant/Git reais
- Pacote Prefect `fastmcp` / `mcp` v2

## Execução

```bash
python -m pytest tests/bdd/test_mcp_evidence_server.py -q
```

## Architect Review

| Decisão | Status | Autor | Data |
|---|---|---|---|
| APPROVED_BY_ARCHITECT | aprovado | tech-lead-architect | 2026-07-18 |
