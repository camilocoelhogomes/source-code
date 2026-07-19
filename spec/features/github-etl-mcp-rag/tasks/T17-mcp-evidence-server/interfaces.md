# Interfaces — T17-mcp-evidence-server

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T17-mcp-evidence-server` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T17-mcp-evidence-server` |
| Escopo desta etapa | Contratos de comunicação T17 **somente** (stubs sem comportamento completo) |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Contratos alinhados a design §4 e BDD MCP-01..MCP-12. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `McpEvidenceServer` | `mcp/ports.py` | Porta pública (`build` / `run`) |
| `DefaultMcpEvidenceServer` | `mcp/server.py` | Composition + registro FastMCP |
| `McpToolError` | `mcp/errors.py` | Falha tipada da superfície |
| `map_query_error` | `mcp/errors.py` | `QueryError` → mensagem segura |
| `register_tools` | `mcp/tools.py` | Registro das 5 tools REQ-028 |
| `details_from_includes` | `mcp/serialize.py` | Args `include_*` → `DetailFields` |
| `hit_to_dict` / `file_to_dict` / `tree_to_dict` / `repo_entry_to_dict` | `mcp/serialize.py` | Envelope JSON BDD-012 / D-T17-* |
| `omit_nulls` | `mcp/serialize.py` | Omitir chaves `None` no JSON |
| Fakes de apoio | `mcp/fake.py` | Doubles opcionais BDD/unit |

Dependências de contrato externo (não redefinidas aqui):

| Origem | Símbolos |
|---|---|
| T16 | `QueryService`, `DetailFields`, requests/DTOs, `QueryError` (+ subclasses) |
| T03/T07 | `CatalogRepository`, `CatalogEntry`, `RepoOrigin`, `RepoState` |
| T04 | `WorkerLimiter`, `create_query_limiter` |
| DEC-015 | SDK `mcp` — `FastMCP` em `mcp.server.fastmcp` |

### Fora de escopo

| Item | Dono |
|---|---|
| Comportamento completo das tools / acquire / serialize | Developer (pós unit plan) |
| UI / FastAPI / `QueryReformulator` | T18 |
| Compose / entrypoint de imagem | T19 |
| Alterar contratos T16/T07/T04 | Fora |
| Pacote Prefect `fastmcp` / `mcp` v2 / protocolo caseiro | Proibido |

## 2. Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T17-001 | SDK `mcp>=1.27,<2`; API `from mcp.server.fastmcp import FastMCP`; proibido `fastmcp` Prefect e framing caseiro | DEC-015; BR-023; BDD-024 | D-T17-001; MCP-07 |
| I-T17-002 | Porta única `McpEvidenceServer` com `build() -> FastMCP` e `run(transport="stdio")` | ENG-007; handoff T19 | D-T17-002; MCP-06 |
| I-T17-003 | Exatamente 5 tools: `list_repos`, `search_code`, `semantic_search`, `read_file`, `list_tree`; sem `ask_codebase` | REQ-028; DEC-008 | D-T17-003; MCP-01/08 |
| I-T17-004 | `list_repos` → `CatalogRepository.list_active_catalog`; demais → `QueryService` | D-T16-009; ENG-007 | D-T17-004; MCP-01/10 |
| I-T17-005 | Args `include_*` → `DetailFields`; JSON omite chaves `None` (não `"x": null`) | REQ-030; BDD-012 | D-T17-005; MCP-02/03 |
| I-T17-006 | Toda tool sob `query_limiter.acquire()` (inclui `list_repos`); pool query apenas | BDD-013; BR-006 | D-T17-006; MCP-04 |
| I-T17-007 | `read_file`: UTF-8 → `content`+`content_encoding=utf-8`; senão `content_base64`+`base64` sem `content` | Evidência sem assumir encoding | D-T17-007; MCP-11 |
| I-T17-008 | `list_repos` item: `repo_key`, `repository_id`, `origin`, `connection_name`, `state`, `last_processed_commit`, `current_main_commit`; sem `local_path`/token | BR-008; REQ-020 | D-T17-008; MCP-10 |
| I-T17-009 | `semantic_search` sempre monta `SemanticSearchRequest(reformulate=False)`; sem `QueryReformulator`/`MetadataGenerator` no pacote | BR-011; DEC-008 | D-T17-009; MCP-09 |
| I-T17-010 | Serialização de hits **omite** `chunk_metadata_summary`; pode incluir `line_number` se não-None | Reduz prosa SLM-flavored | D-T17-010; MCP-09 |
| I-T17-011 | Transport MVP = `"stdio"` em `run` | Cursor MCP; T19 | D-T17-011; MCP-06 |
| I-T17-012 | `McpToolError` (+ `map_query_error`); mensagens sem segredo; sem fallback `hits: []` em falha | BDD-014; BR-008 | D-T17-012; MCP-05/12 |
| I-T17-013 | Pacote `github_rag.mcp` sem imports de `qdrant_client`/`openai`/`github`/`git`/`httpx`/`requests`/cliente Zoekt/`fastmcp` | BDD-024 | D-T17-013; MCP-07 |
| I-T17-014 | `DefaultMcpEvidenceServer` injeta `catalog`, `query`, `query_limiter`; `server_name` default `"github-rag-evidence"` | Composition testável | design §4.2 |
| I-T17-015 | Stubs desta etapa: símbolos importáveis; métodos de comportamento levantam `NotImplementedError` até o Developer | Gate interfaces ≠ implementação | escopo etapa |

## 3. Contratos detalhados

### 3.1 `McpEvidenceServer` (Protocol)

Módulo: `github_rag.mcp.ports`

```python
@runtime_checkable
class McpEvidenceServer(Protocol):
    def build(self) -> FastMCP:
        """Monta FastMCP com as 5 tools registradas.

        Responsabilidade
            Produzir o app MCP pronto para list/call pelo host.

        Motivo da separação
            Isola lifecycle SDK do composition root e do domínio query/catalog.
        """
        ...

    def run(self, *, transport: Literal["stdio"] = "stdio") -> None:
        """Executa o servidor MCP (stdio no MVP).

        Responsabilidade
            Expor o processo consumido por Cursor/T19.

        Motivo da separação
            Handoff de delivery sem acoplar compose à lógica das tools.
        """
        ...
```

- **Responsabilidade:** porta pública da superfície MCP de evidências.
- **Motivo da separação:** ENG-007 — host/Cursor não acoplam a Zoekt/Qdrant/Git/ORM; T19 só chama `run()`.
- **Não faz:** indexação; UI; narrativa; reformulação SLM; composition completa de adapters de índice.
- **Erros:** falhas de tool → `McpToolError` (I-T17-012); boot/limiter inválido pode propagar `WorkerLimiterError` no composition root.

### 3.2 `DefaultMcpEvidenceServer`

Módulo: `github_rag.mcp.server`

```python
class DefaultMcpEvidenceServer:
    def __init__(
        self,
        *,
        catalog: CatalogRepository,
        query: QueryService,
        query_limiter: WorkerLimiter,
        server_name: str = "github-rag-evidence",
    ) -> None: ...

    def build(self) -> FastMCP: ...
    def run(self, *, transport: Literal["stdio"] = "stdio") -> None: ...
```

- **Responsabilidade:** implementação default que compõe catálogo + `QueryService` + limiter e registra tools no `FastMCP`.
- **Motivo da separação:** materializa I-T17-002/014 sem espalhar registro SDK pelo domínio.
- **Invariantes (comportamento completo — Developer):**
  - `build()` devolve instância de `mcp.server.fastmcp.FastMCP`;
  - registra **somente** as 5 tools (I-T17-003);
  - cada handler envolve delegação com `with query_limiter.acquire():` (I-T17-006);
  - `semantic_search` → `reformulate=False` (I-T17-009);
  - sem injeção de `QueryReformulator` / `MetadataGenerator`.
- **Stub atual:** `__init__` armazena deps; `build`/`run` → `NotImplementedError` (I-T17-015).

### 3.3 `McpToolError` / `map_query_error`

Módulo: `github_rag.mcp.errors`

```python
class McpToolError(Exception):
    """Falha tipada exposta pela superfície MCP.

    Responsabilidade
        Sinalizar falha de tool com mensagem estável sem segredos.

    Motivo da separação
        Distingue erros de superfície de QueryError crus; evita eco de token
        em str/repr (BDD-014 / BR-008).
    """

    def __init__(self, message: str = "", *, kind: str = "error") -> None:
        self.message = message
        self.kind = kind  # ex.: validation, repository_not_found, ...
        super().__init__(message)


def map_query_error(exc: QueryError) -> McpToolError:
    """Mapeia QueryError → McpToolError sem vazar segredos.

    Responsabilidade
        Traduzir família T16 em kind/message seguros para o host MCP.

    Motivo da separação
        Centraliza política BDD-014; handlers não montam str(exc) bruto.
    """
    ...
```

| `QueryError` | `kind` sugerido |
|---|---|
| `QueryValidationError` | `validation` |
| `QueryRepositoryNotFoundError` | `repository_not_found` |
| `QueryCommitUnavailableError` | `commit_unavailable` |
| `QueryExactIndexError` | `exact_index` |
| `QueryVectorError` | `vector` |
| `QueryEmbeddingError` | `embedding` |
| `QuerySnapshotError` | `snapshot` |
| demais `QueryError` | `query` |

- **Invariantes:** `SECRET_TOKEN` / valores de env **nunca** em `message`/`str`/`repr`; falha de backend **não** vira `{"hits": []}` silencioso (MCP-12).
- **Stub atual:** classe real; `map_query_error` → `NotImplementedError`.

### 3.4 `register_tools`

Módulo: `github_rag.mcp.tools`

```python
def register_tools(
    app: FastMCP,
    *,
    catalog: CatalogRepository,
    query: QueryService,
    query_limiter: WorkerLimiter,
) -> None:
    """Registra as 5 tools aprovadas no FastMCP.

    Responsabilidade
        Único ponto de binding nome MCP → handler (REQ-028).

    Motivo da separação
        Isola decorators/SDK do lifecycle `build`/`run` e da serialização.
    """
    ...
```

Assinaturas lógicas dos handlers (nomes MCP = nomes Python das tools):

#### `list_repos`

```text
() -> dict  # {"repos": [RepoEvidence, ...]}
```

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
) -> dict  # {"hits": [...]}
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
) -> dict  # {"hits": [...]}
```

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
) -> dict  # FileEvidence
```

#### `list_tree`

```text
(
  repo_key: str | None = None,
  repository_id: int | None = None,
  commit_sha: str | None = None,
  path_prefix: str | None = None,
  include_repository: bool = False,
  include_commit: bool = False,
) -> dict  # {"paths": [...], ...}
```

- **Invariantes:** conjunto fechado (I-T17-003); cada handler sob `acquire` (I-T17-006); `list_repos` não chama `QueryService`.
- **Stub atual:** `register_tools` → `NotImplementedError`.

### 3.5 Serialização

Módulo: `github_rag.mcp.serialize`

```python
def details_from_includes(
    *,
    include_repository: bool = False,
    include_path: bool = False,
    include_commit: bool = False,
    include_snippet: bool = False,
) -> DetailFields:
    """Args MCP include_* → DetailFields T16.

    Responsabilidade
        Traduzir intenção do agente na política BDD-012.

    Motivo da separação
        Handlers não montam DetailFields ad hoc; um único mapeamento.
    """
    ...


def omit_nulls(data: dict[str, Any]) -> dict[str, Any]:
    """Remove chaves cujo valor é None (e recursivo em dicts aninhados de hits).

    Responsabilidade
        Garantir omissão BDD-012 na borda JSON (não emitir null).

    Motivo da separação
        Política de envelope isolada da lógica de tool.
    """
    ...


def repo_entry_to_dict(entry: CatalogEntry) -> dict[str, Any]:
    """CatalogEntry → RepoEvidence MCP (I-T17-008).

    Responsabilidade
        Projetar catálogo ativo sem local_path/token.

    Motivo da separação
        list_repos não vaza montagens/segredos (BR-008).
    """
    ...


def hit_to_dict(hit: QueryHit) -> dict[str, Any]:
    """QueryHit → HitEvidence JSON (I-T17-005/010).

    Responsabilidade
        Envelope de hit: kind/score/line_number + quatro opcionais se não-None;
        nunca chunk_metadata_summary.

    Motivo da separação
        Não vazar DTOs T10/T13; alinha omissão BDD-012.
    """
    ...


def file_to_dict(content: FileContent) -> dict[str, Any]:
    """FileContent → FileEvidence (I-T17-007).

    Responsabilidade
        UTF-8 texto ou content_base64; metadados opcionais omitidos se None.

    Motivo da separação
        Encoding fica na superfície MCP (T16 devolve bytes).
    """
    ...


def tree_to_dict(tree: TreeListing) -> dict[str, Any]:
    """TreeListing → JSON de list_tree.

    Responsabilidade
        paths + repository/commit opcionais omitidos se None.

    Motivo da separação
        Mesmo envelope omit-null das demais tools.
    """
    ...
```

#### Formas JSON congeladas

**RepoEvidence** (`list_repos`):

| Campo | Tipo | Notas |
|---|---|---|
| `repo_key` | `str` | `CatalogEntry.repo_identifier` |
| `repository_id` | `int` | |
| `origin` | `str` | `RepoOrigin.value` |
| `connection_name` | `str` | |
| `state` | `str` | `RepoState.value` (REQ-020) |
| `last_processed_commit` | `str \| null` | chave presente; valor pode ser null |
| `current_main_commit` | `str \| null` | chave presente; valor pode ser null |

Proibido: `local_path`, `token`, qualquer segredo.

**HitEvidence**:

| Campo | Quando |
|---|---|
| `kind` | sempre |
| `score` | sempre em semantic (`float`); exact pode omitir ou `null` — preferir omitir se `None` |
| `line_number` | só se não-None |
| `repository`/`path`/`commit`/`snippet` | só se não-None (flags include) |
| `chunk_metadata_summary` | **nunca** |

**FileEvidence:** ver I-T17-007.

- **Stub atual:** todas as funções → `NotImplementedError`.

### 3.6 Fakes

Módulo: `github_rag.mcp.fake`

```python
class FakeMcpEvidenceServer:
    """Double opcional de McpEvidenceServer para testes sem SDK.

    Responsabilidade
        Permitir unitários de composition sem FastMCP real quando útil.

    Motivo da separação
        BDD principal usa DefaultMcpEvidenceServer + FastMCP real (MCP-07);
        fake é apoio, não substitui o gate SDK.
    """

    def build(self) -> Any: ...
    def run(self, *, transport: str = "stdio") -> None: ...
```

- BDD MCP-01..12 usam preferencialmente `DefaultMcpEvidenceServer` + fakes T16/T03/T04.
- **Stub atual:** classe com `build`/`run` → `NotImplementedError`.

## 4. Módulos e layout

```text
src/github_rag/mcp/
  __init__.py       # exporta McpEvidenceServer, DefaultMcpEvidenceServer, McpToolError
  ports.py
  server.py
  tools.py
  serialize.py
  errors.py
  fake.py
```

Dependência de projeto: `mcp>=1.27,<2` em `pyproject.toml`.

## 5. Import bans (I-T17-013)

Dentro de `github_rag.mcp/**` é **proibido** importar:

- `qdrant_client`, `openai`, `github`, `git`, `httpx`, `requests`, `fastmcp` (Prefect)
- clientes Zoekt HTTP/CLI diretos
- `MetadataGenerator`, `QueryReformulator` (uso/import)

Permitido: `mcp` / `mcp.server.fastmcp`, stdlib, `github_rag.query`, `github_rag.catalog`, `github_rag.concurrency`.

## 6. Rastreabilidade BDD → contrato

| BDD | Contratos |
|---|---|
| MCP-01 / BDD-011 | I-T17-003; `register_tools`; serialize evidência |
| MCP-02/03 / BDD-012 | I-T17-005; `details_from_includes`; `hit_to_dict`+`omit_nulls` |
| MCP-04 / BDD-013 | I-T17-006; handlers + `WorkerLimiter` |
| MCP-05/12 / BDD-014 | I-T17-012; `McpToolError` |
| MCP-06 / BDD-015 | I-T17-002; `build`/`run` |
| MCP-07 / BDD-024 | I-T17-001/013; `FastMCP` |
| MCP-08 | I-T17-003 |
| MCP-09 | I-T17-009/010 |
| MCP-10 | I-T17-008; `repo_entry_to_dict` |
| MCP-11 | I-T17-007; `file_to_dict` |

## 7. Handoff

| Consumidor | Usa |
|---|---|
| QA (unit plan) | Contratos §3; stubs importáveis; BDD permanece RED até Developer |
| Developer | Implementar `build`/`register_tools`/serialize/map_error sem mudar assinaturas |
| T19 | `DefaultMcpEvidenceServer(...).run(transport="stdio")` |
| T18 | Não consome este pacote; compartilha só `QueryService` |

## Architect Review

| Decisão | Status | Autor | Data |
|---|---|---|---|
| APPROVED_BY_ARCHITECT | aprovado | tech-lead-architect | 2026-07-18 |
