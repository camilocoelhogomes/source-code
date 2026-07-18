# Interfaces — T16-query-services

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T16-query-services` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T16-query-services` |
| Escopo desta etapa | Contratos de comunicação T16 **somente** (stubs sem comportamento completo) |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Contratos alinhados a design §4 e BDD QS-01..QS-12. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `DetailFields` | `query/types.py` | Flags de projeção BDD-012 |
| `ExactSearchRequest` | `query/types.py` | Pedido de busca exata |
| `SemanticSearchRequest` | `query/types.py` | Pedido de busca semântica |
| `ReadFileRequest` | `query/types.py` | Pedido de leitura de arquivo |
| `ListTreeRequest` | `query/types.py` | Pedido de listagem de árvore |
| `QueryHit` / `QueryHits` | `query/types.py` | Evidências projetadas |
| `FileContent` / `TreeListing` | `query/types.py` | Resultados de browse |
| `QueryError` (+ subclasses) | `query/errors.py` | Falhas tipadas de consulta |
| `QueryService` | `query/ports.py` | Porta pública (4 operações) |
| `QueryReformulator` | `query/ports.py` | Porta opcional REQ-027 |
| `SnapshotSourceResolver` | `query/ports.py` | `CatalogEntry` → `SnapshotSource` |
| `DefaultQueryService` | `query/service.py` | Orquestração das portas T07/T08/T10/T13 |
| `project_exact` / `project_semantic` | `query/projection.py` | Projeção pura BDD-012 |
| Fakes de apoio | `query/fake.py` | Doubles injetáveis BDD/unit |

Dependências de contrato externo (não redefinidas aqui):

| Origem | Símbolos |
|---|---|
| T10 | `ExactCodeIndex`, `ExactMatch`, `ExactSearchQuery`, `ExactCodeIndexError` |
| T13 | `VectorStore`, `Embedder`, `SemanticHit`, `VectorStoreError`, `EmbeddingError` |
| T08 | `MainSnapshotProvider`, `SnapshotSource`, `SnapshotError`, `FileNotFoundInCommitError` |
| T03/T07 | `CatalogRepository`, `CatalogEntry` |
| T02 | `SecretResolver` (composition root do resolver GitHub; não API de `query/`) |

### Fora de escopo

| Item | Dono |
|---|---|
| Tools MCP / envelope JSON / SDK `mcp` | T17 |
| Telas UI / FastAPI / WorkerLimiter | T18 |
| Adaptador SLM real de `QueryReformulator` | T18 (ou task UI) |
| `list_repos` como método de `QueryService` | Catálogo / T17 |
| Indexação / orquestrador | T14 |
| Client Zoekt/Qdrant/Git paralelo | Proibido (BR-023 / BDD-024) |
| Alterar contratos T07/T08/T10/T13 | Fora |

## 2. Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T16-001 | `repo_key` = `CatalogEntry.repo_identifier` (`str`); mesma string em Zoekt `repository` e Qdrant `repo_id` | Uma chave estável; sem UUID paralelo | D-T16-001; QS-01/02/10 |
| I-T16-002 | Porta única `QueryService` com exatamente 4 métodos | ENG-007; BR-023; sem client paralelo | D-T16-002; QS-05 |
| I-T16-003 | `DetailFields` default tudo `False`; campos omitidos → `None` no DTO | REQ-030; BDD-012 | D-T16-003; QS-03/04/06 |
| I-T16-004 | DTOs de saída próprios (`QueryHit`…); não reexportar `ExactMatch`/`SemanticHit` | Evita vazamento e acoplamento de superfície | D-T16-004; QS-03/04 |
| I-T16-005 | Browse default `commit_sha` = `CatalogEntry.last_processed_commit` | Evidência alinhada ao índice (BR-015) | D-T16-005; QS-06/07/11 |
| I-T16-006 | `QueryReformulator` opcional; só devolve `str`; nunca gera hits | REQ-027; BR-011 | D-T16-006; QS-02/09 |
| I-T16-007 | Sem reformulador + `reformulate=True` → no-op (query original); sem `QueryReformulatorUnavailableError` | Evita acoplar T16 a T18 | D-T16-007; QS-09 |
| I-T16-008 | Hierarquia `QueryError` por família de backend + validation | Aceite tipado; superfícies mapeiam sem `except Exception` | D-T16-008; QS-08/10/11/12 |
| I-T16-009 | Exact `pattern` vazio/whitespace → `QueryHits(hits=())`; semantic `query` vazia → `QueryValidationError` | Paridade T10; evita embed de whitespace | D-T16-012; QS-12 |
| I-T16-010 | `SnapshotSourceResolver` Protocol separado; token só no composition root | BR-008; T16 não importa PyGithub/GitPython | D-T16-011; QS-05 |
| I-T16-011 | Projeção via funções puras `project_exact` / `project_semantic` | Isola política BDD-012 da orquestração | D-T16-003; QS-03/04 |
| I-T16-012 | Resolução de escopo: `repo_key` **ou** `repository_id`; ambos conflitantes / browse sem escopo → `QueryValidationError`; inativo/ausente → `QueryRepositoryNotFoundError` | Regras design §4.3 | D-T16-008; QS-10 |
| I-T16-013 | `FileNotFoundInCommitError` (e demais `SnapshotError`) → `QuerySnapshotError` com `__cause__` | Sem subtipo obrigatório no MVP | D-T16-008; QS-08 |
| I-T16-014 | Pacote `github_rag.query` sem imports de `qdrant_client`/`openai`/Zoekt HTTP/CLI/`PyGithub`/`git`/`httpx`/`requests` | BDD-024 / BR-023 | D-T16-010; QS-05 |
| I-T16-015 | Fakes em `query/fake.py` para Embedder/VectorStore/Snapshot/Reformulator/Resolver; Exact via `FakeExactCodeIndex` (T10); catálogo via `InMemoryCatalogRepository` (T03) | BDD sem backends reais | design §11; QS-01..12 |
| I-T16-016 | Tipos frozen (`dataclass(frozen=True)`) | Contrato estável T17/T18; sem mutação pós-construção | D-T16-004 |

## 3. Contratos detalhados

### 3.1 `DetailFields`

Módulo: `github_rag.query.types`

```python
@dataclass(frozen=True)
class DetailFields:
    repository: bool = False
    path: bool = False
    commit: bool = False
    snippet: bool = False  # trecho
```

- **Responsabilidade:** declarar quais dos quatro campos opcionais de evidência (BDD-012 / REQ-030) o caller deseja na resposta.
- **Motivo da separação:** isola a política “só sob demanda” da forma crua dos hits Zoekt/Qdrant; T17/T18 montam flags a partir dos args da tool/UI.
- **Invariantes:** default todos `False`; flag `False` ⇒ atributo correspondente `None` no DTO de saída (I-T16-003).
- **Erros:** N/A (valor de pedido).

### 3.2 `ExactSearchRequest`

Módulo: `github_rag.query.types`

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
```

- **Responsabilidade:** descrever intenção de busca exata (BDD-009) sem expor `ExactSearchQuery` Zoekt ao caller de superfície.
- **Motivo da separação:** T17/T18 falam o DTO de produto; só `DefaultQueryService` monta `ExactSearchQuery` (I-T10).
- **Invariantes / regras (I-T16-009, I-T16-012):**
  - `pattern` vazio ou só whitespace → `QueryHits(hits=())` (paridade T10); não levanta.
  - `repo_key` e `repository_id` ambos ausentes → escopo multi-repo permitido.
  - ambos presentes e conflitantes (ids resolvem para entradas distintas) → `QueryValidationError`.
  - repo ausente/`active=False` → `QueryRepositoryNotFoundError` **antes** de chamar o índice (QS-10).
- **Mapeamento interno:** → `ExactSearchQuery(pattern, repository=repo_key?, path_prefix, max_matches, context_lines)`.

### 3.3 `SemanticSearchRequest`

Módulo: `github_rag.query.types`

```python
@dataclass(frozen=True)
class SemanticSearchRequest:
    query: str
    details: DetailFields = DetailFields()
    repo_key: str | None = None
    repository_id: int | None = None
    limit: int = 10
    reformulate: bool = False  # só efetivo se QueryReformulator injetado
```

- **Responsabilidade:** descrever intenção de busca semântica (BDD-010) + gancho opcional de reformulação de texto (REQ-027).
- **Motivo da separação:** mantém Embedder+VectorStore atrás da fachada; `reformulate` não mistura com geração de evidência/prosa (BR-011).
- **Invariantes / regras (I-T16-007, I-T16-009):**
  - `query` vazio ou só whitespace → `QueryValidationError`; sem `Embedder.embed` / `VectorStore.search` (QS-12).
  - `reformulate=True` sem reformulador → no-op (usa `query` original); **não** levanta `QueryReformulatorUnavailableError`.
  - `reformulate=False` → nunca chama `reformulator.reformulate` (QS-09).
  - escopo de repo: mesmas regras de I-T16-012; filtro `repo_ids=[repo_key]` quando escopo único.
- **Proibido:** preencher hits/snippet com saída do reformulador.

### 3.4 `ReadFileRequest`

Módulo: `github_rag.query.types`

```python
@dataclass(frozen=True)
class ReadFileRequest:
    repo_key: str | None = None
    repository_id: int | None = None
    path: str
    commit_sha: str | None = None  # default: last_processed_commit
    details: DetailFields = DetailFields()
```

- **Responsabilidade:** pedir bytes de um arquivo no commit indexado (ou SHA explícito) via snapshot (T08).
- **Motivo da separação:** browse compartilhado UI/MCP sem acoplar a `SnapshotSource`/`MainSnapshotProvider` nas superfícies.
- **Invariantes / regras (I-T16-005, I-T16-012):**
  - exige `repo_key` **ou** `repository_id` (não multi-repo); ausência de ambos → `QueryValidationError`.
  - `path` vazio/whitespace → `QueryValidationError`.
  - `commit_sha is None` → usa `entry.last_processed_commit`; se também `None` → `QueryCommitUnavailableError` sem chamar snapshot (QS-11).
  - `commit_sha` explícito prossegue mesmo sem `last_processed_commit` (QS-11).
  - projeção: `details` controla `repository`/`path`/`commit` em `FileContent`; `snippet` N/A; `content` sempre presente.

### 3.5 `ListTreeRequest`

Módulo: `github_rag.query.types`

```python
@dataclass(frozen=True)
class ListTreeRequest:
    repo_key: str | None = None
    repository_id: int | None = None
    commit_sha: str | None = None
    path_prefix: str | None = None
    details: DetailFields = DetailFields()
```

- **Responsabilidade:** listar paths do tip/commit via snapshot, com filtro opcional de prefixo.
- **Motivo da separação:** mesma fachada de browse que `read_file`; filtra `path_prefix` na camada serviço (design §4.8).
- **Invariantes / regras:** iguais a browse de `ReadFileRequest` quanto a escopo/commit (I-T16-005/012); `path_prefix=None` → árvore completa do provider; prefixo restringe paths (QS-07).
- **Projeção:** `details` controla `repository`/`commit` em `TreeListing`.

### 3.6 `QueryHit` / `QueryHits`

Módulo: `github_rag.query.types`

```python
@dataclass(frozen=True)
class QueryHit:
    """Evidência mínima + campos opcionais sob demanda."""
    kind: Literal["exact", "semantic"]
    score: float | None  # semantic; None em exact
    repository: str | None = None
    path: str | None = None
    commit: str | None = None
    snippet: str | None = None
    # metadados semânticos opcionais (fora de BDD-012; default omitidos)
    chunk_metadata_summary: str | None = None
    line_number: int | None = None


@dataclass(frozen=True)
class QueryHits:
    hits: tuple[QueryHit, ...]
```

- **Responsabilidade:** forma estável de evidência para T17/T18 após projeção (BDD-009/010/012).
- **Motivo da separação:** callers não recebem `ExactMatch`/`SemanticHit` crus (I-T16-004); evita vazar campos e acoplar superfícies aos DTOs de índice.
- **Invariantes:**
  - `kind` e (em semantic) `score` sempre presentes conforme tipo; **não** são os quatro campos BDD-012 (QS-03).
  - exact: `score is None` (QS-01).
  - semantic: `score` numérico (`float`) (QS-02).
  - flag `DetailFields.* == False` ⇒ atributo correspondente `None` (QS-03/04).
  - **Proibido:** preencher `snippet`/`path`/etc. com texto gerado por SLM/reformulador.
- **Erros:** N/A (valor de retorno).

### 3.7 `FileContent` / `TreeListing`

Módulo: `github_rag.query.types`

```python
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

- **Responsabilidade:** resultados de browse tipados após projeção; `content`/`paths` são evidência do snapshot.
- **Motivo da separação:** superfícies não lidam com `bytes` crus + metadados misturados às portas T08; encoding UTF-8 fica a cargo de T17/T18.
- **Invariantes:** `content` sempre presente em `FileContent` mesmo com `DetailFields` default (QS-06); campos opcionais seguem I-T16-003.

### 3.8 Erros — hierarquia `QueryError`

Módulo: `github_rag.query.errors`

```python
class QueryError(Exception):
    """Base das falhas de consulta compartilhada."""

    def __init__(self, message: str = "") -> None: ...


class QueryValidationError(QueryError):
    """Pedido inválido: repo ambíguo, path/query vazios, escopo browse ausente, etc."""


class QueryRepositoryNotFoundError(QueryError):
    """Catálogo: id/key ausente ou active=False."""


class QueryCommitUnavailableError(QueryError):
    """Browse sem commit_sha e sem last_processed_commit."""


class QueryExactIndexError(QueryError):
    """Falha Zoekt na busca; envolve ExactCodeIndexError em __cause__."""


class QueryVectorError(QueryError):
    """Falha Qdrant search; envolve VectorStoreError em __cause__."""


class QueryEmbeddingError(QueryError):
    """Falha Embedder; envolve EmbeddingError em __cause__."""


class QuerySnapshotError(QueryError):
    """Falha read/tree; envolve SnapshotError (+ subclasses) em __cause__."""


class QueryReformulatorError(QueryError):
    """Falha da porta opcional QueryReformulator (quando injetada e falha)."""


# QueryReformulatorUnavailableError — NÃO definido / NÃO usado (I-T16-007 / D-T16-007)
```

- **Responsabilidade:** sinalizar falhas de consulta por família, sem fallback silencioso para hits vazios quando o backend falhou (QS-08).
- **Motivo da separação:** distinto dos erros T10/T13/T08 crus; T17/T18 mapeiam um tipo estável (I-T16-008).
- **Quando (mapeamento):**

| Tipo | Quando | BDD |
|---|---|---|
| `QueryValidationError` | Pedido inválido (repo ambíguo, path vazio, query semântica vazia, browse sem escopo) | QS-12 (+ unit) |
| `QueryRepositoryNotFoundError` | id/key ausente ou `active=False`; backends **não** chamados | QS-10 |
| `QueryCommitUnavailableError` | browse sem SHA e sem `last_processed_commit`; snapshot **não** chamado | QS-11 |
| `QueryExactIndexError` | envolve `ExactCodeIndexError` | QS-08 |
| `QueryVectorError` | envolve `VectorStoreError` | QS-08 |
| `QueryEmbeddingError` | envolve `EmbeddingError` | QS-08 |
| `QuerySnapshotError` | envolve `SnapshotError` / `FileNotFoundInCommitError` (I-T16-013) | QS-08 |
| `QueryReformulatorError` | reformulador injetado falhou | unit / QS-09 extensão |

- **Invariantes:** `str(exc)` / mensagens **sem** token/segredos (BR-008); `__cause__` preserva exceção original quando houver envelopamento.

### 3.9 `QueryService` (Protocol)

Módulo: `github_rag.query.ports`

```python
@runtime_checkable
class QueryService(Protocol):
    def search_exact(self, request: ExactSearchRequest) -> QueryHits:
        """Busca exata via ExactCodeIndex; retorna hits projetados.

        Responsabilidade
            Expor BDD-009 na fachada compartilhada.

        Motivo da separação
            UI/MCP não tocam Zoekt; centraliza projeção BDD-012.
        """
        ...

    def search_semantic(self, request: SemanticSearchRequest) -> QueryHits:
        """Busca semântica via Embedder+VectorStore; hits = evidências.

        Responsabilidade
            Expor BDD-010 sem prosa SLM (BR-011).

        Motivo da separação
            Isola Qdrant/embeddings e o gancho opcional de reformulação.
        """
        ...

    def read_file(self, request: ReadFileRequest) -> FileContent:
        """Lê bytes do snapshot no commit resolvido.

        Responsabilidade
            Browse de arquivo alinhado ao índice (I-T16-005).

        Motivo da separação
            Superfícies não montam SnapshotSource nem falam com Git.
        """
        ...

    def list_tree(self, request: ListTreeRequest) -> TreeListing:
        """Lista paths do snapshot; aplica path_prefix se pedido.

        Responsabilidade
            Browse de árvore compartilhado UI/MCP.

        Motivo da separação
            Mesma fachada que read_file; filtro de prefixo na camada serviço.
        """
        ...
```

- **Responsabilidade:** fachada única de consulta compartilhada (exact, semantic, read, tree) — ENG-007.
- **Motivo da separação:** UI e MCP não tocam Zoekt/Qdrant/Git; evita client paralelo (BR-023 / BDD-024 / QS-05); centraliza BDD-012.
- **Não faz:** `list_repos` (fica em `CatalogRepository` / T17); indexação; WorkerLimiter; narrativa MCP; SDK `mcp`/FastAPI.
- **Erros:** hierarquia §3.8 conforme operação.

### 3.10 `QueryReformulator` (Protocol)

Módulo: `github_rag.query.ports`

```python
@runtime_checkable
class QueryReformulator(Protocol):
    def reformulate(self, query: str) -> str:
        """Transforma o texto da query do usuário (UI) antes do embedding.

        Responsabilidade
            Expandir/reescrever somente a string de consulta (REQ-027).

        Motivo da separação
            REQ-027 / BR-010 (SLM na UI) sem misturar com MetadataGenerator (T12)
            nem com recuperação MCP; BR-011 exige evidências só de Embedder+VectorStore.
        """
        ...
```

- **Responsabilidade:** transformar o texto da query antes do embedding — saída **somente** `str`.
- **Motivo da separação:** gancho UI sem gerar hits/snippet; MCP (T17) **não** injeta esta porta e não passa `reformulate=True`.
- **Regras (I-T16-006/007):**
  - injetada opcionalmente em `DefaultQueryService`;
  - ausente + `reformulate=True` → no-op;
  - falha tipada → `QueryReformulatorError` (caller UI decide fallback — recomendado: query original, documentar em T18);
  - implementação SLM real **fora** de T16 (só Protocol + fake).
- **Erros:** implementação pode levantar qualquer exceção; serviço envelopa em `QueryReformulatorError`.

### 3.11 `SnapshotSourceResolver` (Protocol)

Módulo: `github_rag.query.ports`

```python
@runtime_checkable
class SnapshotSourceResolver(Protocol):
    def resolve(self, entry: CatalogEntry) -> SnapshotSource:
        """Monta SnapshotSource a partir do CatalogEntry.

        Responsabilidade
            Mapear origem local/GitHub do catálogo para o DTO T08.

        Motivo da separação
            T16 não importa PyGithub/GitPython; token fica no composition root (BR-008).
        """
        ...
```

- **Responsabilidade:** `CatalogEntry` → `SnapshotSource` (`LocalSnapshotSource` / `GitHubSnapshotSource`).
- **Motivo da separação:** I-T16-010 / D-T16-011 — resolve paths/full_name/token fora da orquestração de busca; T16 só delega a T08.
- **Comportamento esperado (composition root, não corpo de `query/`):**
  - Local: `LocalSnapshotSource(local_path=entry.local_path)`.
  - GitHub: `GitHubSnapshotSource(full_name=entry.repo_identifier, token=...)` via `SecretResolver`; token nunca logado nem em `str(error)`.
- **Erros:** falha tipada do resolver (ex. token ausente) → serviço mapeia para `QuerySnapshotError` ou `QueryValidationError` conforme causa; mensagem sem segredo.

### 3.12 Funções de projeção

Módulo: `github_rag.query.projection`

```python
def project_exact(match: ExactMatch, details: DetailFields) -> QueryHit: ...

def project_semantic(hit: SemanticHit, details: DetailFields) -> QueryHit: ...
```

| Flag | Exact (`ExactMatch`) | Semantic (`SemanticHit`) |
|---|---|---|
| `repository` | `match.repository` | `hit.repo_id` |
| `path` | `match.path` | `hit.chunk.path` |
| `commit` | `match.commit` | `hit.commit_sha` |
| `snippet` | `match.snippet` | `hit.chunk.text` |

- **Responsabilidade:** aplicar `DetailFields` → `QueryHit` com campos não solicitados em `None` (I-T16-003/011).
- **Motivo da separação:** política BDD-012 testável em isolamento (matriz de flags) sem backends.
- **Invariantes:**
  - `project_exact` → `kind="exact"`, `score=None`; `line_number` só se útil/disponível (opcional; default `None` se não pedido por contrato de superfície).
  - `project_semantic` → `kind="semantic"`, `score=hit.score`; `chunk_metadata_summary` default `None` no MVP (não faz parte dos quatro campos BDD-012; pode preencher só se contrato futuro pedir — **não** ligado a `DetailFields.snippet`).
  - funções puras: sem I/O, sem SLM.
- **BDD:** QS-03, QS-04.

### 3.13 `DefaultQueryService`

Módulo: `github_rag.query.service`

```python
class DefaultQueryService:
    def __init__(
        self,
        *,
        exact_index: ExactCodeIndex,
        vector_store: VectorStore,
        embedder: Embedder,
        snapshot: MainSnapshotProvider,
        catalog: CatalogRepository,
        source_resolver: SnapshotSourceResolver,
        reformulator: QueryReformulator | None = None,
    ) -> None: ...

    def search_exact(self, request: ExactSearchRequest) -> QueryHits: ...
    def search_semantic(self, request: SemanticSearchRequest) -> QueryHits: ...
    def read_file(self, request: ReadFileRequest) -> FileContent: ...
    def list_tree(self, request: ListTreeRequest) -> TreeListing: ...
```

- **Responsabilidade:** implementação default que **somente** orquestra portas T07/T08/T10/T13 (+ reformulador opcional); zero HTTP/CLI/SDK novo.
- **Motivo da separação:** composição injetável para T17/T18 e testes; satisfaz `QueryService` sem acoplar superfícies a adaptadores concretos (QS-05).
- **Construtor (congelado):** todos os parâmetros **keyword-only**; dependências obrigatórias conforme tabela; `reformulator` opcional (`None`).

| Dependência | Tipo | Obrigatório |
|---|---|---|
| `exact_index` | `ExactCodeIndex` | sim |
| `vector_store` | `VectorStore` | sim |
| `embedder` | `Embedder` | sim |
| `snapshot` | `MainSnapshotProvider` | sim |
| `catalog` | `CatalogRepository` | sim |
| `source_resolver` | `SnapshotSourceResolver` | sim |
| `reformulator` | `QueryReformulator \| None` | não |

- **Resolução de catálogo (comportamento contratado):**
  - por `repository_id` → `catalog.get_repository(id)`;
  - por `repo_key` → localizar em `list_active_catalog()` (ou equivalente read-only) onde `entry.repo_identifier == repo_key`;
  - entrada inexistente ou `active=False` → `QueryRepositoryNotFoundError` (QS-10).
- **Fluxos:** design §4.8 (`search_exact` / `search_semantic` / `read_file` / `list_tree`).
- **Proibido (I-T16-014):** importar/instanciar clients Zoekt/Qdrant/openai/PyGithub/GitPython/`httpx`/`requests` dentro de `github_rag.query`.
- **Erros:** hierarquia §3.8; sem fallback silencioso para `QueryHits(hits=())` quando backend falhou (QS-08).

### 3.14 Fakes de apoio

Módulo: `github_rag.query.fake`

```python
class FakeEmbedder:
    """Double de Embedder: textos → vetores controlados; instrumentação de calls."""

    def __init__(
        self,
        *,
        vectors_by_text: Mapping[str, tuple[float, ...]] | None = None,
        dimensions: int = 8,
        fail: bool = False,
    ) -> None: ...

    @property
    def dimensions(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]: ...
    # expõe call_count / last_texts para QS-02/09/12


class FakeVectorStore:
    """Double de VectorStore focado em search; upsert mínimo para pré-carga de hits."""

    def __init__(
        self,
        *,
        hits_by_vector: Mapping[tuple[float, ...], tuple[SemanticHit, ...]] | None = None,
        fail_search: bool = False,
    ) -> None: ...

    def search(
        self,
        query_vector: Sequence[float],
        *,
        limit: int,
        repo_ids: Sequence[str] | None = None,
    ) -> tuple[SemanticHit, ...]: ...
    # demais métodos VectorStore: stubs no-op ou NotImplemented conforme necessidade do Protocol
    # expõe search_call_count para QS-02/08/12


class FakeMainSnapshotProvider:
    """Double de MainSnapshotProvider para read_file/list_tree sem Git."""

    def __init__(
        self,
        *,
        files: Mapping[tuple[str, str], bytes] | None = None,  # (commit_sha, path) -> content
        trees: Mapping[str, tuple[str, ...]] | None = None,  # commit_sha -> paths
        fail: bool = False,
    ) -> None: ...

    def read_file(
        self, source: SnapshotSource, *, commit_sha: str, path: str
    ) -> bytes: ...

    def list_tree(
        self, source: SnapshotSource, *, commit_sha: str
    ) -> tuple[str, ...]: ...
    # get_main_tip / diff_files: stubs compatíveis com o Protocol se exigido pelo type-check
    # expõe read_file_calls / call_count para QS-06/07/11


class FakeSnapshotSourceResolver:
    """Double: CatalogEntry → SnapshotSource estável (local path sintético)."""

    def resolve(self, entry: CatalogEntry) -> SnapshotSource: ...


class FakeQueryReformulator:
    """Double: mapping query → reformulated; nunca produz hits."""

    def __init__(
        self,
        *,
        mapping: Mapping[str, str] | None = None,
        fail: bool = False,
    ) -> None: ...

    def reformulate(self, query: str) -> str: ...
    # expõe call_count para QS-09


class FakeQueryService:
    """Double completo de QueryService para T17/T18 sem DefaultQueryService."""

    def __init__(
        self,
        *,
        exact_hits: QueryHits | None = None,
        semantic_hits: QueryHits | None = None,
        file_content: FileContent | None = None,
        tree: TreeListing | None = None,
        fail: type[QueryError] | None = None,
    ) -> None: ...

    def search_exact(self, request: ExactSearchRequest) -> QueryHits: ...
    def search_semantic(self, request: SemanticSearchRequest) -> QueryHits: ...
    def read_file(self, request: ReadFileRequest) -> FileContent: ...
    def list_tree(self, request: ListTreeRequest) -> TreeListing: ...
```

- **Responsabilidade:** doubles injetáveis para BDD/unit da camada `query` e para consumidores T17/T18 sem backends reais.
- **Motivo da separação:** I-T16-015 — valida contratos e QS-* sem Zoekt/Qdrant/Git; `FakeQueryService` desacopla superfícies de `DefaultQueryService` em testes de T17/T18.
- **Reuso externo (não redefinir em T16):**
  - `FakeExactCodeIndex` — `github_rag.index.zoekt.fake` (T10);
  - `InMemoryCatalogRepository` — `github_rag.catalog.memory` (T03).
- **Invariantes:** fakes **não** importam SDKs proibidos; falhas configuráveis levantam erros tipados das portas de origem (`ExactCodeIndexError`, `VectorStoreError`, `EmbeddingError`, `SnapshotError`) para o serviço envelopar (QS-08).

## 4. Reexports (`github_rag.query.__init__`)

```python
from github_rag.query.errors import (
    QueryCommitUnavailableError,
    QueryEmbeddingError,
    QueryError,
    QueryExactIndexError,
    QueryReformulatorError,
    QueryRepositoryNotFoundError,
    QuerySnapshotError,
    QueryValidationError,
    QueryVectorError,
)
from github_rag.query.ports import (
    QueryReformulator,
    QueryService,
    SnapshotSourceResolver,
)
from github_rag.query.projection import project_exact, project_semantic
from github_rag.query.service import DefaultQueryService
from github_rag.query.types import (
    DetailFields,
    ExactSearchRequest,
    FileContent,
    ListTreeRequest,
    QueryHit,
    QueryHits,
    ReadFileRequest,
    SemanticSearchRequest,
    TreeListing,
)
```

Fakes podem ser importados de `github_rag.query.fake` (export opcional no `__init__` se QA preferir superfície mínima).

## 5. Mapeamento I-T16-* ↔ D-T16-* ↔ BDD QS-*

| Decisão interface | Design | Cenários BDD |
|---|---|---|
| I-T16-001 | D-T16-001 | QS-01, QS-02, QS-10 |
| I-T16-002 | D-T16-002 | QS-01..QS-07, QS-05 |
| I-T16-003 | D-T16-003 | QS-03, QS-04, QS-06 |
| I-T16-004 | D-T16-004 | QS-03, QS-04 |
| I-T16-005 | D-T16-005 | QS-06, QS-07, QS-11 |
| I-T16-006 | D-T16-006 | QS-02, QS-09 |
| I-T16-007 | D-T16-007 | QS-09 |
| I-T16-008 | D-T16-008 | QS-08, QS-10, QS-11, QS-12 |
| I-T16-009 | D-T16-012 | QS-12 |
| I-T16-010 | D-T16-011 | QS-05, QS-06/07 |
| I-T16-011 | D-T16-003 | QS-03, QS-04 |
| I-T16-012 | D-T16-008 / §4.3 | QS-10 (+ unit validation) |
| I-T16-013 | D-T16-008 / §6 | QS-08 |
| I-T16-014 | D-T16-010 / BR-023 | QS-05 |
| I-T16-015 | §11 / fakes | QS-01..QS-12 |
| I-T16-016 | D-T16-004 | todos os DTOs |

## 6. Handoff T17 / T18 / QA

| Consumidor | Usa |
|---|---|
| T17 MCP | `QueryService` para exact/semantic/read/tree; monta `DetailFields` dos args; **não** injeta `QueryReformulator`; `list_repos` via catálogo |
| T18 UI | Mesmo `QueryService`; pode injetar `QueryReformulator` + `reformulate=True` |
| QA | Unitários de projection/validação/erros + BDD QS-* com fakes; cobertura ≥95% em `github_rag.query` |
| Developer | Stubs dos Protocols/DTOs primeiro; implementação até verde |

Contrato congelado nesta task: assinaturas de `QueryService`, forma de `DetailFields`/`QueryHit`/`FileContent`/`TreeListing`, semântica de defaults de commit, política I-T16-007 (no-op), hierarquia de erros e construtor keyword-only de `DefaultQueryService` — mudanças exigem `SCOPE_CHANGE_REQUIRED`.

## Architect Review

| Decisão | Status | Autor | Data |
|---|---|---|---|
| APPROVED_BY_ARCHITECT | aprovado | tech-lead-architect | 2026-07-18 |
