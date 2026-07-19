# Design — T17-mcp-evidence-server

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T17-mcp-evidence-server` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T17-mcp-evidence-server` |
| Base | `feature/github-etl-mcp-rag-T16-query-services` (depende de T04/T07/T16) |
| Rastreabilidade | REQ-003, REQ-028–033; BR-008, BR-011, BR-023; DEC-008, DEC-015; BDD-011–015; BDD-024; ENG-007, ENG-013 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Design inicial: `McpEvidenceServer` sobre SDK oficial `mcp` (`FastMCP`); 5 tools; catálogo + `QueryService`; `QUERY_WORKERS`/`WorkerLimiter`; sem SLM/narrativa. |

## 1. Contexto

A onda W7 entrega a superfície **MCP de evidências** consumida pelo agente no Cursor (REQ-003, BDD-015). Consulta compartilhada (T16), catálogo ativo (T07/T03) e pool de workers de consulta (T04) já existem:

| Dependência | Porta / artefato | Uso em T17 |
|---|---|---|
| T16 | `QueryService` + `DetailFields` + DTOs (`QueryHits`, `FileContent`, `TreeListing`) | `search_code`, `semantic_search`, `read_file`, `list_tree` |
| T07/T03 | `CatalogRepository.list_active_catalog` + `CatalogEntry` | `list_repos` (estados REQ-020) |
| T04 | `WorkerLimiter` / `create_query_limiter` / `QUERY_WORKERS` | Paralelismo BDD-013 / REQ-029 / BR-006 |
| DEC-015 / ENG-013 | SDK oficial Python **`mcp`** (`mcp.server.fastmcp.FastMCP`) | Único transporte/protocolo MCP |

O placeholder `github_rag.mcp` (T01) torna-se o módulo de superfície desta task. Indexação, UI e compose ficam fora — T19 só recebe o processo/entrypoint.

## 2. Problema

O agente no Cursor precisa das cinco operações aprovadas (REQ-028) sem:

1. reinventar protocolo MCP ou cliente HTTP caseiro (BR-023 / DEC-015 / BDD-024);
2. acoplar narrativa ou SLM ao caminho MCP (DEC-008, BR-011, REQ-031/032, BR-010);
3. vazar campos opcionais quando o agente não os pediu (REQ-030 / BDD-012);
4. saturizar backends sem limite de paralelismo (REQ-029 / BDD-013);
5. expor token GitHub em respostas, erros ou logs da superfície (BR-008 / BDD-014);
6. duplicar clientes Zoekt/Qdrant/Git fora de `QueryService` (ENG-007 / D-T16-002).

## 3. Solução proposta

Pacote `github_rag.mcp` com **uma** porta pública `McpEvidenceServer` que:

1. registra **somente** as cinco tools aprovadas no SDK oficial `mcp` (`FastMCP`);
2. delega busca/browse a `QueryService` (nunca `reformulate=True`, nunca `QueryReformulator` / `MetadataGenerator`);
3. implementa `list_repos` via `CatalogRepository.list_active_catalog` (fora de `QueryService`, alinhado a D-T16-009);
4. envolve cada invocação de tool com `WorkerLimiter.acquire()` do pool **query**;
5. projeta args opcionais → `DetailFields` e serializa evidências omitindo `null` dos quatro campos BDD-012.

```text
Cursor (MCP host)
  → SDK mcp (stdio) / FastMCP
       → tool handler (1 das 5)
            → with query_limiter.acquire():
                 ├─ list_repos     → CatalogRepository.list_active_catalog
                 ├─ search_code    → QueryService.search_exact
                 ├─ semantic_search→ QueryService.search_semantic (reformulate=False)
                 ├─ read_file      → QueryService.read_file
                 └─ list_tree      → QueryService.list_tree
  → JSON estruturado de evidência (sem prosa gerada)
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T17 (superfície MCP) | Fora de T17 |
|---|---|---|
| BDD-011 | Tools retornam evidências; zero narrativa/SLM no caminho | Validação humana Discovery completa no Cursor |
| BDD-012 | Args → `DetailFields`; JSON omite campos não pedidos | Projeção interna T16 (já coberta) |
| BDD-013 | `QUERY_WORKERS` / `create_query_limiter`; excedentes aguardam | Pool de indexação |
| BDD-014 | Respostas/erros/logs MCP sem token | Indexação/UI (outras tasks) |
| BDD-015 | Tools utilizáveis pelo agente (capacidade) | E2E Discovery humano completo |
| BDD-024 | Só pacote `mcp` oficial; zero protocolo caseiro | Demais SDKs (já em adaptadores) |
| BR-011 | `semantic_search` sem SLM/reformulador | UI `QueryReformulator` (T18) |

## 4. Componentes

### 4.1 Dependência SDK (`mcp`)

| Decisão | Valor |
|---|---|
| Pacote | **`mcp`** (PyPI oficial Model Context Protocol Python SDK) |
| Pin | `mcp>=1.27,<2` (linha estável v1.x; v2 é pre-release — não usar) |
| API | `from mcp.server.fastmcp import FastMCP` |
| Proibido | Pacote standalone `fastmcp` (Prefect/legado); JSON-RPC/HTTP MCP reinventado; framing caseiro |

- **Responsabilidade:** falar o protocolo MCP com o host (Cursor).
- **Motivo da separação:** BR-023 / DEC-015 / BDD-024 / ENG-013 — conformidade de integração fica no adaptador de superfície; domínio permanece em `query`/`catalog`.

### 4.2 `McpEvidenceServer` (porta pública)

```python
class McpEvidenceServer(Protocol):
    def build(self) -> FastMCP: ...
    def run(self, *, transport: Literal["stdio"] = "stdio") -> None: ...
```

Implementação default (composition):

| Dependência | Tipo | Obrigatório |
|---|---|---|
| `catalog` | `CatalogRepository` | sim |
| `query` | `QueryService` | sim |
| `query_limiter` | `WorkerLimiter` | sim (pool query; tipicamente `create_query_limiter(settings)`) |
| `server_name` | `str` | não (default `"github-rag-evidence"`) |

- **Responsabilidade:** compor e expor o servidor MCP de evidências (tools + lifecycle).
- **Motivo da separação:** ENG-007 — Cursor/SDK não acoplam a Zoekt/Qdrant/Git/catálogo ORM; T19 só precisa do processo/`run()`.
- **Não faz:** indexação; UI; `ask_codebase`; narrativa; reformulação SLM; composition root completo de adapters (fica no entrypoint/T19).

### 4.3 Tools aprovadas (conjunto fechado)

Somente estas tools são registradas. Nomes MCP = nomes REQ-028.

| Tool | Delegação | Pedido T16 / fonte |
|---|---|---|
| `list_repos` | `CatalogRepository.list_active_catalog` | **não** usa `QueryService` |
| `search_code` | `QueryService.search_exact` | `ExactSearchRequest` |
| `semantic_search` | `QueryService.search_semantic` | `SemanticSearchRequest` com `reformulate=False` sempre |
| `read_file` | `QueryService.read_file` | `ReadFileRequest` |
| `list_tree` | `QueryService.list_tree` | `ListTreeRequest` |

**Proibido registrar:** `ask_codebase`, tools de prosa, tools de indexação, tools de config/token, qualquer tool que chame `MetadataGenerator` ou `QueryReformulator`.

### 4.4 Args comuns → `DetailFields` (BDD-012)

Flags booleanas opcionais nas tools de evidência (default `False`):

| Arg MCP | `DetailFields` |
|---|---|
| `include_repository` | `repository` |
| `include_path` | `path` |
| `include_commit` | `commit` |
| `include_snippet` | `snippet` |

- **Responsabilidade:** traduzir intenção do agente em política T16.
- **Motivo da separação:** superfície MCP não reimplementa projeção; reusa `DetailFields` (D-T16-003).
- **Serialização:** campos com valor `None` **omitidos** do JSON da tool (não emitir `"repository": null`).

`list_repos` não usa `DetailFields` (lista de catálogo, não hits).

### 4.5 Assinaturas lógicas das tools

#### `list_repos`

```text
() → { "repos": [ RepoEvidence, ... ] }

RepoEvidence:
  repo_key: str          # CatalogEntry.repo_identifier
  repository_id: int
  origin: str            # RepoOrigin value ("github" | "local")
  connection_name: str
  state: str             # RepoState value (REQ-020: not_indexed|queued|indexing|up_to_date|error)
  last_processed_commit: str | null
  current_main_commit: str | null
  # progress opcional agregado (files_processed/files_total/current_stage) se presente
```

Regras:

- Fonte = `list_active_catalog()` → apenas `active=True` (repos soft-deleted fora).
- Inclui todos os estados REQ-020 (não só `up_to_date`) — “indexados” no produto = catálogo ativo gerenciado.
- Sem token, sem `local_path` absoluto se puder vazar montagens sensíveis? **D-T17-008:** `local_path` **não** entra na resposta MCP (evidência de identidade = `repo_key` + `origin` + estados/commits). `github_org` pode aparecer só se necessário para distinção — MVP: omitir; `repo_key` basta.

#### `search_code`

```text
(
  pattern: str,
  repo_key: str | None = None,
  repository_id: int | None = None,
  path_prefix: str | None = None,
  max_matches: int | None = None,
  context_lines: int = 2,
  include_repository: bool = False,
  include_path: bool = False,
  include_commit: bool = False,
  include_snippet: bool = False,
) → { "hits": [ HitEvidence, ... ] }
```

#### `semantic_search`

```text
(
  query: str,
  repo_key: str | None = None,
  repository_id: int | None = None,
  limit: int = 10,
  include_repository: bool = False,
  include_path: bool = False,
  include_commit: bool = False,
  include_snippet: bool = False,
) → { "hits": [ HitEvidence, ... ] }
```

Invariantes:

- Nunca passa `reformulate=True`.
- Composition root de T17 **não** injeta `QueryReformulator` no `QueryService` usado pelo MCP.
- Resposta **não** inclui `chunk_metadata_summary` (evita superfície narrativa/SLM-flavored no MCP; evidência = hit projetado BDD-012 + `kind`/`score`/`line_number` quando presente).

#### `read_file`

```text
(
  path: str,
  repo_key: str | None = None,
  repository_id: int | None = None,
  commit_sha: str | None = None,
  include_repository: bool = False,
  include_path: bool = False,
  include_commit: bool = False,
) → FileEvidence
```

`include_snippet` N/A (corpo = evidência). Conteúdo: ver D-T17-007.

#### `list_tree`

```text
(
  repo_key: str | None = None,
  repository_id: int | None = None,
  commit_sha: str | None = None,
  path_prefix: str | None = None,
  include_repository: bool = False,
  include_commit: bool = False,
) → { "paths": [...], ...campos opcionais }
```

### 4.6 Forma de evidência serializada

```python
# HitEvidence (search_code / semantic_search)
{
  "kind": "exact" | "semantic",
  "score": float | null,       # null em exact
  "line_number": int | null,   # omitir se null
  # opcionais — só se include_* e valor não-None:
  "repository": str,
  "path": str,
  "commit": str,
  "snippet": str,
}
```

- **Responsabilidade:** envelope estável para o agente (BDD-011/015).
- **Motivo da separação:** não vazar DTOs crus T10/T13; alinhar omissão BDD-012 na borda MCP.
- **Proibido:** texto gerado por modelo; frases “explicativas”; campos de token/env.

### 4.7 Conteúdo de arquivo (D-T17-007)

| Caso | Serialização |
|---|---|
| `content` decodifica como UTF-8 | `"content": "<text>"`, `"content_encoding": "utf-8"` |
| inválido como UTF-8 | `"content_base64": "<b64>"`, `"content_encoding": "base64"` (sem campo `content` texto) |

Nunca logar o corpo em INFO.

### 4.8 Paralelismo (BDD-013 / REQ-029)

```text
tool_call
  → with query_limiter.acquire():   # bloqueia se slots esgotados
       executar delegação síncrona
```

| Regra | Comportamento |
|---|---|
| Capacidade | `settings.query_workers` via `create_query_limiter` (default ENG-003 = 4) |
| Escopo do slot | Toda a tool (inclui `list_repos`) — consultas MCP contam no pool query |
| Pool index | Isolado; MCP **não** usa `create_index_limiter` |
| Concorrência SDK | FastMCP pode aceitar calls concorrentes; o semáforo garante teto |
| Sync vs async | Handlers síncronos preferidos; se o SDK exigir coroutine, `to_thread` da delegação **dentro** do `acquire` |

### 4.9 Registro FastMCP

```python
mcp = FastMCP(server_name)

@mcp.tool(name="list_repos")
def list_repos() -> dict: ...

@mcp.tool(name="search_code")
def search_code(...) -> dict: ...
# idem semantic_search, read_file, list_tree
```

Docstrings curtas descrevem evidência (não pedem narrativa ao modelo). Tools são funções puras de superfície sobre deps injetadas (closure / bound methods do server).

### 4.10 Transport e processo

| Item | Decisão |
|---|---|
| Transport MVP | **stdio** (padrão Cursor MCP) |
| Entry | `McpEvidenceServer.run(transport="stdio")` e/ou `__main__` / console script |
| Handoff T19 | Processo na imagem chama o mesmo entry; compose/env já existentes |

SSE/HTTP Streamable fora do MVP T17 (podem ser adicionados depois sem mudar tools).

### 4.11 Módulos previstos

```text
src/github_rag/mcp/
  __init__.py          # exporta McpEvidenceServer / DefaultMcpEvidenceServer
  ports.py             # Protocol McpEvidenceServer
  server.py            # DefaultMcpEvidenceServer + build FastMCP
  tools.py             # handlers / registro das 5 tools
  serialize.py         # DetailFields mapping + JSON omit-null + file encoding
  errors.py            # McpToolError / mapeamento QueryError → mensagem segura
  fake.py              # doubles para BDD/unit sem SDK real se necessário
```

## 5. Fluxo de dados

```text
┌────────────┐   stdio    ┌───────────────────┐
│ Cursor MCP │◄──────────►│ FastMCP (sdk mcp) │
└────────────┘            └─────────┬─────────┘
                                    │ tool dispatch
                          ┌─────────▼─────────┐
                          │ McpEvidenceServer │
                          │  + serialize      │
                          └─────────┬─────────┘
                                    │ acquire
                          ┌─────────▼─────────┐
                          │ WorkerLimiter     │
                          │ (query pool)      │
                          └─────────┬─────────┘
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
         CatalogRepository    QueryService         (sem SLM)
         list_active_catalog  exact/semantic/read/tree
```

## 6. Erros tipados

| Tipo superfície | Quando | Origem |
|---|---|---|
| `McpToolError` | Base de falha exposta à tool | — |
| Mensagem de validação | Args inválidos / `QueryValidationError` | T16 |
| Repo não encontrado | `QueryRepositoryNotFoundError` | T16 |
| Commit indisponível | `QueryCommitUnavailableError` | T16 |
| Falha de índice/vetor/embed/snapshot | subclasses `Query*Error` | T16 |
| Falha de limiter (construção) | `WorkerLimiterError` no boot — **não** no happy-path da tool | T04 |

Regras:

- Mapear `QueryError` → erro de tool com `message` estável **sem** token/segredo (BR-008 / BDD-014).
- Preservar tipo lógico na mensagem (`validation`, `repository_not_found`, …) sem `str(exception)` bruto de backends que possam ecoar headers/URLs com credenciais.
- Sem fallback que invente hits vazios quando o backend falhou.
- `list_repos` falhas de catálogo → erro tipado; lista vazia é sucesso (`repos: []`).

## 7. Segurança

- Token GitHub nunca entra em args, respostas, docstrings, logs INFO nem `McpToolError.message`.
- Composition root resolve segredos para `SnapshotSourceResolver` **antes** do MCP; tools não recebem token.
- Redaction: se logar exceção, filtrar padrões de bearer/token; preferir mensagens tipadas.
- BDD-012 reduz superfície de código privado exposta ao agente quando flags off.
- Conteúdo/`snippet` podem ser código privado (evidência aceita); não logar corpos.

## 8. Compatibilidade

| Item | Ação |
|---|---|
| Deps | Adicionar `mcp>=1.27,<2` em `pyproject.toml` |
| Python | 3.12+ |
| T16 | Consumo read-only de `QueryService` / DTOs; sem alterar contratos |
| T07/T03 | `list_active_catalog` / `CatalogEntry` / `RepoState` |
| T04 | `create_query_limiter` / `QUERY_WORKERS` |
| T18 | Não compartilham processo; compartilham `QueryService` |
| Placeholder | Substituir stub `github_rag.mcp` |
| Pacote `fastmcp` standalone | **Não** adicionar |

## 9. Observabilidade

- Sem métricas obrigatórias no MVP T17.
- Erros tipados + (opcional) log de nome da tool / latência sem payloads.
- Pico de paralelismo verificável nos testes via limiter fake/instrumentado.

## 10. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Usar `fastmcp` Prefect ou `mcp` v2 pre-release | D-T17-001; pin `<2`; review de `pyproject` |
| Tool narrativa / SLM escondida | Conjunto fechado de 5 tools; testes de import graph; `reformulate=False` |
| Vazamento BDD-012 | Unitários de serialize + BDD-012 na superfície |
| Bypass do limiter | Todo handler passa por `acquire`; teste de saturação BDD-013 |
| Token em `str(error)` | Mensagens tipadas; testes BDD-014 com token sentinela |
| Duplicar clientes de índice | Import ban em `mcp/` para `qdrant_client` / Zoekt HTTP / PyGithub / `openai` |
| FastMCP async vs sync QueryService | D-T17-006; `to_thread` dentro do slot se necessário |
| Discovery E2E (BDD-015) | Task entrega capacidade das tools; validação humana fica fora |

## 11. Estratégia de teste (orientação para QA)

| Camada | Estratégia |
|---|---|
| BDD superfície | BDD-011..014 (+ suporte 015/024) com `FakeQueryService` / catálogo in-memory / limiter real ou fake |
| Unit | serialize DetailFields; mapeamento erros; `reformulate` nunca True; registro exatamente 5 tools; pin/import `mcp.server.fastmcp` |
| Paralelismo | N calls concorrentes com `QUERY_WORKERS=k` → pico ≤ k |
| Cobertura | ≥95% no pacote `github_rag.mcp` |
| Proibido | Subir Cursor real no gate unit; protocolo MCP caseiro; backends Zoekt/Qdrant reais |

## 12. Rollback

Reverter pacote `github_rag.mcp` ao placeholder T01, remover dep `mcp` e testes associados. Sem migration SQL. T19 deixa de expor o processo até reintroduzir.

## 13. Decisões de design

| ID | Decisão | Motivo |
|---|---|---|
| D-T17-001 | SDK oficial `mcp` v1.x (`mcp>=1.27,<2`) via `FastMCP` em `mcp.server.fastmcp`; proibido standalone `fastmcp` e protocolo caseiro | DEC-015; BR-023; BDD-024; ENG-013 |
| D-T17-002 | Porta pública única `McpEvidenceServer` (`build`/`run`) | ENG-007; handoff T19 |
| D-T17-003 | Exatamente 5 tools REQ-028; sem `ask_codebase`/narrativa | DEC-008; REQ-031/032; BR-011 |
| D-T17-004 | `list_repos` → `list_active_catalog`; demais → `QueryService` | D-T16-009; ENG-007 |
| D-T17-005 | Args `include_*` → `DetailFields`; JSON omite nulls BDD-012 | REQ-030; BDD-012 |
| D-T17-006 | Cada tool sob `query_limiter.acquire()` (`QUERY_WORKERS`) | BDD-013; REQ-029; BR-006; T04 |
| D-T17-007 | `read_file`: UTF-8 texto ou `content_base64` | Evidência estruturada sem assumir encoding |
| D-T17-008 | Resposta `list_repos` sem `local_path`/token; estados REQ-020 | BR-008; identidade via `repo_key` |
| D-T17-009 | `semantic_search` sempre `reformulate=False`; sem `QueryReformulator`/`MetadataGenerator` | BR-011; DEC-008; handoff T16 |
| D-T17-010 | Omitir `chunk_metadata_summary` na serialização MCP | Reduz superfície prosa/metadado SLM no agente |
| D-T17-011 | Transport MVP = stdio | Integração Cursor; T19 empacota processo |
| D-T17-012 | Erros tipados sem eco de segredos | BDD-014; BR-008 |
| D-T17-013 | Import ban de clientes de índice/SLM dentro de `github_rag.mcp` | BDD-024; BR-023 |

## 14. Arquivos previstos

```text
src/github_rag/mcp/
  __init__.py
  ports.py
  server.py
  tools.py
  serialize.py
  errors.py
  fake.py
tests/unit/mcp/
tests/bdd/mcp/   # ou tests/bdd/test_mcp_evidence_server.py
pyproject.toml   # + mcp>=1.27,<2
spec/features/github-etl-mcp-rag/tasks/T17-mcp-evidence-server/
  design.md
  reviews.md
  approvals.md
  bdd.md          # QA (próximo)
  interfaces.md   # Architect (após BDD)
```

## 15. Rastreabilidade (mapeamento BDD / REQ / BR)

| ID | Como T17 atende |
|---|---|
| BDD-011 | 5 tools → evidências; sem narrativa/SLM |
| BDD-012 | `include_*` → `DetailFields` + omit-null |
| BDD-013 | `WorkerLimiter` pool query / `QUERY_WORKERS` |
| BDD-014 | Mensagens/respostas/logs sem token |
| BDD-015 | Tools registradas e utilizáveis pelo host MCP |
| BDD-024 | Somente SDK `mcp` oficial na superfície |
| REQ-003 | Servidor MCP conectável ao Cursor |
| REQ-028 | Operações aprovadas expostas |
| REQ-029 | Paralelismo limitado |
| REQ-030 | Detalhes sob demanda |
| REQ-031/032 | Sem narrativa / sem modelo local nas respostas |
| REQ-033 | Agente compõe Discovery (capacidade das tools) |
| BR-008 | Sem vazamento de token |
| BR-011 | Semantic path sem prosa SLM |
| BR-023 / DEC-015 | SDK `mcp` |
| DEC-008 | Só evidências |
| ENG-007 | Consome portas; não toca índices direto |

## 16. Fora de escopo

- UI / FastAPI / `QueryReformulator` real (T18)
- Indexação, orquestrador, scheduler (T14/T15)
- Compose/Dockerfile/imagem (T19) — só handoff do processo
- Validação humana Discovery end-to-end completa (BDD-015 como aceite de produto amplo)
- Transport SSE/HTTP Streamable
- Alterar contratos T16/T07/T04
- Tool `ask_codebase` ou qualquer narrativa
- Pacote Prefect `fastmcp` / `mcp` v2

## 17. Handoff T19

| Consumidor | Usa |
|---|---|
| T19 | Processo: `McpEvidenceServer(...).run(transport="stdio")` (ou entrypoint equivalente) na imagem; env `QUERY_WORKERS` já lida por settings/T04 |
| Cursor | Config MCP apontando ao comando do servidor (documentação de delivery) |
| QA | BDD de tools + paralelismo + anti-vazamento antes da implementação |
| Architect (próximo) | Congelar `interfaces.md` após BDD aprovado |

Contratos a congelar na etapa de interfaces: assinaturas das 5 tools, forma JSON de evidência, política D-T17-005/007/009/010, e garantia de registro exclusivo via `mcp.server.fastmcp`.

## Architect Review

| Decisão | Status | Autor | Data |
|---|---|---|---|
| APPROVED_BY_ARCHITECT | aprovado | tech-lead-architect | 2026-07-18 |
