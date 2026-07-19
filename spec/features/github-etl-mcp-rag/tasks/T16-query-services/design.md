# Design — T16-query-services

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T16-query-services` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T16-query-services` |
| Base | `main` (atualizada; depende de T07/T08/T10/T13 já mergeados) |
| Rastreabilidade | REQ-002, REQ-026–027, REQ-030; BR-011, BR-023; BDD-009, BDD-010, BDD-012, BDD-024; ENG-007 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Design inicial: fachada `QueryService` sobre portas T10/T13/T08/T07; projeção BDD-012; porta opcional de reformulação UI; sem client paralelo. |

## 1. Contexto

A onda W6 entrega a camada de **consulta compartilhada** consumida por T17 (MCP) e T18 (UI). Indexação (Zoekt, Tree-sitter→SLM→Qdrant) e snapshot já existem atrás das portas:

| Dependência | Porta / artefato | Uso em T16 |
|---|---|---|
| T10 | `ExactCodeIndex` + `ExactMatch` / `ExactSearchQuery` | Busca exata (BDD-009) |
| T13 | `VectorStore` + `Embedder` + `SemanticHit` | Busca semântica (BDD-010) |
| T08 | `MainSnapshotProvider` + `SnapshotSource` | `read_file` / `list_tree` |
| T07/T03 | `CatalogRepository` + `CatalogEntry` | Resolver repo ativo → origem/commit |

O placeholder `github_rag.query` (T01) torna-se o módulo de domínio desta task. Superfícies (tools MCP, rotas FastAPI, WorkerLimiter de consulta) ficam fora — só consomem a fachada.

## 2. Problema

UI e MCP precisam das mesmas operações de evidência (exact, semantic, read, tree) sem:

1. duplicar clientes Zoekt/Qdrant/Git (BR-023 / BDD-024);
2. acoplar narrativa SLM ao caminho de recuperação (BR-011);
3. vazar campos opcionais (repositório, caminho, commit, trecho) quando o caller não os pediu (REQ-030 / BDD-012);
4. inventar evidência a partir do modelo local (BR-011; REQ-027 permite apoio só na UI, não na geração de hits).

## 3. Solução proposta

Pacote `github_rag.query` com **uma** porta pública `QueryService` e implementação default que **somente** orquestra portas já aprovadas — zero HTTP/CLI/SDK novo nesta task.

| Componente | Papel |
|---|---|
| `types` | DTOs de pedido/resposta + flags de projeção (BDD-012) |
| `errors` | Hierarquia tipada de falhas de consulta |
| `ports` | `QueryService` (+ `QueryReformulator` opcional) |
| `service` | `DefaultQueryService` — composição das portas T07/T08/T10/T13 |
| `projection` | Aplica `DetailFields` → omite campos não solicitados |
| `resolve` | `CatalogEntry` → `SnapshotSource` / `repo_key` / commit indexado |
| fakes | Doubles injetáveis para BDD/unit sem backends reais |

```text
Caller (T17/T18)
  → QueryService.search_exact / search_semantic / read_file / list_tree
       │
       ├─ CatalogRepository.get_repository / list_active_catalog
       ├─ ExactCodeIndex.search                    (T10)
       ├─ [opcional] QueryReformulator.reformulate (só UI; texto de query)
       ├─ Embedder.embed → VectorStore.search      (T13)
       └─ MainSnapshotProvider.read_file|list_tree (T08)
  → QueryResult / FileContent / TreeListing  (campos opcionais projetados)
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T16 (camada serviço) | Fora de T16 |
|---|---|---|
| BDD-009 | `search_exact` devolve correspondências do `ExactCodeIndex` | UI/HTML (T18); tools MCP (T17) |
| BDD-010 | `search_semantic` via Embedder+VectorStore; hits = evidências | Render UI; apoio SLM na UI (usa porta opcional, não gera hits) |
| BDD-012 | Projeção: sem `repository`/`path`/`commit`/`snippet` se não solicitados | Envelope MCP/JSON das tools (T17 aplica o mesmo contrato) |
| BDD-024 | Nenhum client paralelo; só portas T10/T13/T08 (+ catálogo ORM T03) | Demais SDKs; DT-001 |
| BR-011 | Caminho semântico **nunca** chama SLM para prosa/evidência | MCP narrative ban (T17) |
| REQ-027 | Porta `QueryReformulator` opcional: só reformula texto da query na UI | Chat livre / respostas MCP |

## 4. Componentes

### 4.1 Identidade de repositório (`repo_key`)

| Decisão | Valor |
|---|---|
| Chave pública de consulta | `CatalogEntry.repo_identifier` (`str`) |
| Alinhamento Zoekt | `ExactSearchQuery.repository` / `ExactMatch.repository` = `repo_key` (I-T10-003) |
| Alinhamento Qdrant | `SemanticHit.repo_id` / filtro `repo_ids` = `repo_key` (string opaca T13) |
| Resolução por id numérico | Métodos aceitam `repository_id: int` **ou** `repo_key: str`; lookup via `CatalogRepository` |

Motivo: uma única chave estável entre índices e catálogo; evita UUID paralelo inventado em T16.

### 4.2 `DetailFields` (BDD-012 / REQ-030)

```python
@dataclass(frozen=True)
class DetailFields:
    repository: bool = False
    path: bool = False
    commit: bool = False
    snippet: bool = False  # trecho
```

- **Responsabilidade:** declarar quais campos opcionais o caller deseja na resposta.
- **Motivo da separação:** isola a política “só sob demanda” da forma crua dos hits Zoekt/Qdrant; T17/T18 montam flags a partir dos args da tool/UI.
- **Default:** todos `False` — resultado mínimo (score/ordenação/ids opacos internos se necessário, sem os quatro campos de evidência).
- **Invariante:** se um campo for `False`, o DTO de saída **não** inclui o atributo populado (usar `None` omitido na serialização futura, ou campos `Optional` sempre `None` quando não pedidos — ver D-T16-004).

### 4.3 Pedidos de consulta

```python
@dataclass(frozen=True)
class ExactSearchRequest:
    pattern: str
    details: DetailFields = DetailFields()
    repo_key: str | None = None
    repository_id: int | None = None
    path_prefix: str | None = None
    max_matches: int | None = None
    context_lines: int = 2

@dataclass(frozen=True)
class SemanticSearchRequest:
    query: str
    details: DetailFields = DetailFields()
    repo_key: str | None = None
    repository_id: int | None = None
    limit: int = 10
    reformulate: bool = False  # só efetivo se QueryReformulator injetado

@dataclass(frozen=True)
class ReadFileRequest:
    repo_key: str | None = None
    repository_id: int | None = None
    path: str
    commit_sha: str | None = None  # default: last_processed_commit
    details: DetailFields = DetailFields()

@dataclass(frozen=True)
class ListTreeRequest:
    repo_key: str | None = None
    repository_id: int | None = None
    commit_sha: str | None = None
    path_prefix: str | None = None
    details: DetailFields = DetailFields()
```

Regras:

| Regra | Comportamento |
|---|---|
| `repo_key` e `repository_id` ambos ausentes | Escopo multi-repo (busca); browse exige um dos dois → `QueryValidationError` |
| Ambos presentes e conflitantes | `QueryValidationError` |
| Repo inativo / inexistente | `QueryRepositoryNotFoundError` |
| `pattern` / `query` vazio (só whitespace) | Exact → `()` (espelha T10); Semantic → `QueryValidationError` |
| `commit_sha is None` em browse | Usa `CatalogEntry.last_processed_commit`; se `None` (nunca indexado) → `QueryCommitUnavailableError` |

### 4.4 Resultados projetados

```python
@dataclass(frozen=True)
class QueryHit:
    """Evidência mínima + campos opcionais sob demanda."""
    # sempre presentes para ordenação/estabilidade interna (não são os 4 de BDD-012)
    kind: Literal["exact", "semantic"]
    score: float | None  # semantic; None em exact
    # opcionais (None se DetailFields.* == False)
    repository: str | None = None
    path: str | None = None
    commit: str | None = None
    snippet: str | None = None
    # metadados semânticos opcionais (não entram em BDD-012; default omitidos)
    chunk_metadata_summary: str | None = None
    line_number: int | None = None

@dataclass(frozen=True)
class QueryHits:
    hits: tuple[QueryHit, ...]

@dataclass(frozen=True)
class FileContent:
    content: bytes
    repository: str | None = None
    path: str | None = None
    commit: str | None = None
    # snippet N/A

@dataclass(frozen=True)
class TreeListing:
    paths: tuple[str, ...]
    repository: str | None = None
    commit: str | None = None
```

- **Responsabilidade:** forma estável de evidência para T17/T18 após projeção.
- **Motivo da separação:** callers não recebem `ExactMatch`/`SemanticHit` crus (evita vazar campos e acoplar superfícies aos DTOs de índice).
- **Snippet (trecho):** exact ← `ExactMatch.snippet`; semantic ← `SemanticHit.chunk.text` (ou recorte documentado); só se `details.snippet`.
- **Proibido:** preencher `snippet`/`path`/etc. com texto gerado por SLM.

### 4.5 `QueryService` (Protocol)

```python
class QueryService(Protocol):
    def search_exact(self, request: ExactSearchRequest) -> QueryHits: ...
    def search_semantic(self, request: SemanticSearchRequest) -> QueryHits: ...
    def read_file(self, request: ReadFileRequest) -> FileContent: ...
    def list_tree(self, request: ListTreeRequest) -> TreeListing: ...
```

- **Responsabilidade:** fachada única de consulta compartilhada (exact, semantic, read, tree).
- **Motivo da separação:** ENG-007 — UI e MCP não tocam Zoekt/Qdrant/Git; evita client paralelo (BR-023); centraliza BDD-012.
- **Não faz:** `list_repos` (fica em `CatalogRepository` / T17); indexação; WorkerLimiter (T04/T17/T18); narrativa MCP.

### 4.6 `QueryReformulator` (Protocol opcional — REQ-027)

```python
class QueryReformulator(Protocol):
    def reformulate(self, query: str) -> str: ...
```

- **Responsabilidade:** transformar o texto da query do usuário (UI) antes do embedding — ex. expandir termos.
- **Motivo da separação:** REQ-027 / BR-010 (SLM na UI) **sem** misturar com `MetadataGenerator` (T12) nem com recuperação MCP; BR-011 exige que evidências venham só de Embedder+VectorStore.
- **Regras:**
  - Injetado opcionalmente no `DefaultQueryService`; se ausente, `reformulate=True` é ignorado (no-op, usa `query` original) ou levanta `QueryReformulatorUnavailableError` — **D-T16-007: no-op**.
  - Saída é **somente** string de query; nunca vira hit/snippet.
  - Falha tipada `QueryReformulatorError`; caller UI decide fallback (recomendado: usar query original — documentar em T18).
  - **Proibido** no caminho MCP (T17 não passa `reformulate=True` / não injeta reformulador).

Implementação default desta task: **não** entregar adaptador SLM real (fica T18 ou task de UI); apenas o Protocol + fake nos testes. T16 valida o gancho.

### 4.7 `DefaultQueryService`

Construtor (injeção):

| Dependência | Tipo | Obrigatório |
|---|---|---|
| `exact_index` | `ExactCodeIndex` | sim |
| `vector_store` | `VectorStore` | sim |
| `embedder` | `Embedder` | sim |
| `snapshot` | `MainSnapshotProvider` | sim |
| `catalog` | `CatalogRepository` | sim |
| `source_resolver` | `SnapshotSourceResolver` (função/Protocol interno) | sim |
| `reformulator` | `QueryReformulator \| None` | não |

`SnapshotSourceResolver`:

```python
class SnapshotSourceResolver(Protocol):
    def resolve(self, entry: CatalogEntry) -> SnapshotSource: ...
```

- Local: `LocalSnapshotSource(local_path=entry.local_path)`.
- GitHub: `GitHubSnapshotSource(full_name=entry.repo_identifier, token=...)` — token via `SecretResolver` no composition root (nunca logado; BR-008).
- **Motivo da separação:** T16 não importa PyGithub/GitPython; só monta `SnapshotSource` e delega a T08.

### 4.8 Fluxos por operação

#### `search_exact`

```text
ExactSearchRequest
  → validar pattern / escopo repo
  → montar ExactSearchQuery(pattern, repository=repo_key?, path_prefix, max_matches, context_lines)
  → ExactCodeIndex.search
  → map ExactMatch → QueryHit(kind="exact") + projection(details)
  → QueryHits
```

#### `search_semantic`

```text
SemanticSearchRequest
  → validar query / escopo
  → text = reformulator.reformulate(query) se reformulate e reformulator else query
  → vector = Embedder.embed([text])[0]
  → VectorStore.search(vector, limit=..., repo_ids=[repo_key] ou None)
  → map SemanticHit → QueryHit(kind="semantic", score=...) + projection(details)
  → QueryHits
```

#### `read_file` / `list_tree`

```text
Request
  → resolver CatalogEntry (id ou repo_key)
  → commit = request.commit_sha or entry.last_processed_commit
  → SnapshotSource via resolver
  → MainSnapshotProvider.read_file | list_tree
  → (list_tree) filtrar path_prefix se pedido
  → FileContent | TreeListing + projection
```

Conteúdo de `read_file` é sempre o bytes do snapshot (evidência); encoding/UTF-8 fica a cargo de T17/T18.

### 4.9 Projeção (`projection`)

Função pura:

```python
def project_exact(match: ExactMatch, details: DetailFields) -> QueryHit: ...
def project_semantic(hit: SemanticHit, details: DetailFields) -> QueryHit: ...
```

| Flag | Exact | Semantic |
|---|---|---|
| `repository` | `match.repository` | `hit.repo_id` |
| `path` | `match.path` | `hit.chunk.path` |
| `commit` | `match.commit` | `hit.commit_sha` |
| `snippet` | `match.snippet` | `hit.chunk.text` |

Campos com flag `False` → `None` no `QueryHit` (serializadores futuros omitem `null` se desejarem; contrato de serviço usa `None`).

## 5. Fluxo de dados

```text
                    ┌────────────────────┐
                    │ CatalogRepository  │
                    └─────────┬──────────┘
                              │ repo_key / SnapshotSource inputs
┌─────────────┐     ┌─────────▼──────────┐     ┌──────────────────┐
│ ExactCode   │◄────│ DefaultQueryService│────►│ MainSnapshot     │
│ Index (T10) │     │                    │     │ Provider (T08)   │
└─────────────┘     │  (+ projection)    │     └──────────────────┘
                    │  (+ optional       │
┌─────────────┐     │   reformulator)    │
│ Embedder    │◄────┤                    │
└──────┬──────┘     └─────────▲──────────┘
       │                      │
┌──────▼──────┐               │
│ VectorStore │───────────────┘
│ (T13)       │
└─────────────┘
```

## 6. Erros tipados

| Tipo | Quando | Mapeamento de backends |
|---|---|---|
| `QueryError` | Base | — |
| `QueryValidationError` | Pedido inválido (repo ambíguo, path vazio, query semântica vazia, etc.) | — |
| `QueryRepositoryNotFoundError` | Catálogo: id/key ausente ou `active=False` | `RepositoryNotFoundError` / ausência em list |
| `QueryCommitUnavailableError` | Browse sem `last_processed_commit` e sem `commit_sha` | — |
| `QueryExactIndexError` | Falha Zoekt na busca | envolve `ExactCodeIndexError` |
| `QueryVectorError` | Falha Qdrant search | envolve `VectorStoreError` |
| `QueryEmbeddingError` | Falha Embedder | envolve `EmbeddingError` |
| `QuerySnapshotError` | Falha read/tree | envolve `SnapshotError` (+ subclasses preservadas em `__cause__`) |
| `QueryReformulatorError` | Falha da porta opcional | — |
| `QueryReformulatorUnavailableError` | (não usado — D-T16-007 no-op) | — |

Regras:

- Mensagens **sem** token/segredos (BR-008 / BDD-014).
- Sem fallback silencioso que invente hits vazios quando o backend falhou.
- `FileNotFoundInCommitError` → `QuerySnapshotError` (ou subtipo `QueryFileNotFoundError` se QA preferir no interfaces.md).

## 7. Segurança

- Token GitHub só no `SnapshotSourceResolver` / memória; nunca em `QueryHit`, logs INFO, nem `str(error)`.
- Conteúdo de arquivo e snippets podem conter código privado — aceito como evidência; não logar corpo em INFO.
- SLM/reformulador: se algum dia logar prompts, redaction igual às outras camadas; MVP T16 sem logger obrigatório.
- BDD-012 reduz superfície de dados expostos ao agente quando flags estão off.

## 8. Compatibilidade

| Item | Ação |
|---|---|
| Deps novas | Nenhuma SDK de integração; só código de domínio sobre portas existentes |
| Python | 3.12+ |
| T10/T13/T08/T07 | Consumo read-only das ports; sem alterar contratos |
| T17/T18 | Única fachada de consulta; MCP não injeta reformulador |
| `list_repos` | Fora — `CatalogRepository.list_active_catalog` |
| WorkerLimiter | Fora — T04 aplicado nas superfícies (BDD-013) |
| Placeholder | Substituir stub `github_rag.query` |

## 9. Observabilidade

- Sem métricas obrigatórias no MVP T16.
- Erros tipados + `__cause__` bastam para T17/T18/UI.
- Opcional futuro: contagem de hits / latência por operação — fora do escopo.

## 10. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Divergência `repo_key` Zoekt vs Qdrant vs catálogo | D-T16-001; contrato documentado; testes com mesma string nos três fakes |
| UI/MCP reimplementarem clientes | Handoff explícito; review T17/T18 bloqueia imports de `index.zoekt.client` / `qdrant_client` fora de adaptadores |
| Reformulador gerar “evidência” | Protocol só devolve `str`; projection nunca lê SLM; BR-011 nos testes |
| Browse no tip live ≠ índice | Default `last_processed_commit` (commit indexado); tip live só se caller passar SHA |
| GitHub token ausente no browse | `SnapshotSourceResolver` falha tipada; mensagem sem segredo |
| Vazamento de campos opcionais | Unitários de projection com matriz de flags; BDD-012 na camada serviço |

## 11. Estratégia de teste (orientação para QA)

| Camada | Estratégia |
|---|---|
| BDD serviço | Cenários BDD-009/010/012/024 com fakes T10/T13/T08/T07 |
| Unit | Projection matriz; validação de pedidos; mapeamento de erros; reformulate no-op vs chamado; semantic nunca chama SLM de evidência |
| Cobertura | ≥95% no pacote `github_rag.query` |
| Proibido | Subir Zoekt/Qdrant reais no gate unit; client HTTP inventado |

## 12. Rollback

Reverter o pacote `github_rag.query` ao placeholder T01 e testes associados. Sem migration SQL, sem novos volumes. T17/T18 não devem ter sido mergeados dependendo da fachada, ou revertem junto.

## 13. Decisões de design

| ID | Decisão | Motivo |
|---|---|---|
| D-T16-001 | `repo_key` = `CatalogEntry.repo_identifier`; mesma string em Zoekt `repository` e Qdrant `repo_id` | Uma chave; alinha I-T10-003 e opacidade T13 |
| D-T16-002 | Porta única `QueryService` (4 operações); sem client paralelo | ENG-007; BR-023; BDD-024; handoff T17/T18 |
| D-T16-003 | `DetailFields` default tudo `False`; projeção para `None` | REQ-030; BDD-012 |
| D-T16-004 | DTOs de saída próprios (`QueryHit`…), não reexportar `ExactMatch`/`SemanticHit` | Evita vazamento de campos e acoplamento de superfície |
| D-T16-005 | Browse default = `last_processed_commit` | Evidência alinhada ao índice; BR-015 |
| D-T16-006 | `QueryReformulator` opcional; só texto de query; nunca gera hits | REQ-027; BR-011 |
| D-T16-007 | Sem reformulador + `reformulate=True` → no-op (query original) | Evita acoplar T16 a T18; falha só se reformulador existir e errar |
| D-T16-008 | Erros tipados por família de backend + validation | Critério de aceite; superfícies mapeiam sem `except Exception` |
| D-T16-009 | `list_repos` e WorkerLimiter fora de T16 | Escopo da task; catálogo/T04 já cobrem |
| D-T16-010 | Sem narrativa MCP / sem SDK `mcp` / sem FastAPI nesta task | Escopo; T17/T18 |
| D-T16-011 | `SnapshotSourceResolver` separado + `SecretResolver` no composition root | BR-008; T16 não fala com PyGithub |
| D-T16-012 | Exact pattern vazio → hits vazios (paridade T10); semantic query vazia → validation error | Consistência com portas; evita embed de whitespace |

## 14. Arquivos previstos

```text
src/github_rag/query/
  __init__.py
  types.py
  errors.py
  ports.py
  service.py
  projection.py
  resolve.py
  fake.py
tests/unit/query/
tests/bdd/test_query_services.py
spec/features/github-etl-mcp-rag/tasks/T16-query-services/
  design.md
  reviews.md
  bdd.md          # QA (próximo)
  interfaces.md   # Architect (após BDD)
```

## 15. Rastreabilidade (mapeamento BDD / REQ / BR)

| ID | Como T16 atende |
|---|---|
| BDD-009 | `search_exact` → `ExactCodeIndex.search` → `QueryHits` |
| BDD-010 | `search_semantic` → Embedder + `VectorStore.search` → `QueryHits` |
| BDD-012 | `DetailFields` + `projection`; defaults omitidos |
| BDD-024 | Reutiliza adaptadores oficiais atrás das portas; nenhum client ad-hoc em `query/` |
| REQ-002 | Exact + semantic na camada de serviço |
| REQ-026 | Base de serviço para buscas da UI (T18) |
| REQ-027 | Gancho `QueryReformulator`; recuperação continua embeddings/Qdrant |
| REQ-030 | Campos opcionais só quando `DetailFields` true |
| BR-011 | Semantic path sem prosa SLM; reformulador ≠ evidência |
| BR-023 | Sem reinventar cliente; só orquestração de portas |

## 16. Fora de escopo

- Servidor MCP / tools / SDK `mcp` (T17)
- Telas UI / FastAPI / apoio visual SLM completo (T18)
- Indexação, orquestrador, scheduler (T14/T15)
- `list_repos` como método de `QueryService`
- WorkerLimiter / BDD-013 (superfície)
- Adaptador real de `QueryReformulator` (Protocol + fake apenas)
- Alterar contratos T07/T08/T10/T13
- Chunking, metadata SLM de indexação, compose/imagens (T19)

## 17. Handoff

| Consumidor | Usa |
|---|---|
| T17 | `QueryService` para `search_code`, `semantic_search`, `read_file`, `list_tree`; monta `DetailFields` dos args da tool; **não** injeta reformulador; `list_repos` via catálogo |
| T18 | Mesmo `QueryService`; pode injetar `QueryReformulator` e `reformulate=True` na busca semântica |
| QA | BDD de serviço + unit de projection/erros antes da implementação |
| Architect (próximo) | Congelar `interfaces.md` após BDD aprovado |

Contratos a congelar na etapa de interfaces: assinaturas de `QueryService`, forma de `DetailFields`/`QueryHit`, semântica de defaults de commit, e política D-T16-007.

## Architect Review

| Decisão | Status | Autor | Data |
|---|---|---|---|
| APPROVED_BY_ARCHITECT | aprovado | tech-lead-architect | 2026-07-18 |
