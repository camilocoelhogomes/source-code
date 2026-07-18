# Interfaces — T13-qdrant-vector-store

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T13-qdrant-vector-store` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T13-qdrant-vector-store` |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Contratos alinhados a design §4 e BDD VS-01..VS-14. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `ChunkMetadata` | `index/vector/types.py` | Metadados SLM serializáveis (mínimo T12↔T13) |
| `EnrichedChunk` | `index/vector/types.py` | Chunk Tree-sitter + metadata |
| `RepoCommitScope` | `index/vector/types.py` | Escopo repo + commit |
| `VectorRecord` | `index/vector/types.py` | Enriched + vetor |
| `SemanticHit` | `index/vector/types.py` | Evidência de search |
| `VectorStoreError` (+ subclasses) | `index/vector/errors.py` | Falhas tipadas do store |
| `EmbeddingError` (+ subclasses) | `index/vector/errors.py` | Falhas tipadas do embedder |
| `VectorStore` | `index/vector/ports.py` | Porta de persistência/busca |
| `Embedder` | `index/vector/ports.py` | Porta de embeddings |
| `QdrantVectorStore` | `index/vector/qdrant_store.py` | Adaptador `qdrant-client` |
| `OpenAICompatibleEmbedder` | `index/vector/embedder.py` | Adaptador `openai` (embeddings only) |

Dependência de contrato externo (não redefinida aqui): `SemanticChunk`, `SourceLanguage` de `github_rag.index.chunk.types` (T11).

### Fora de escopo

| Item | Dono |
|---|---|
| Geração de metadados SLM / chat | T12 (`MetadataGenerator`) |
| Produção de chunks Tree-sitter | T11 |
| Orquestração / BR-005 restart | T14 |
| UI / QueryService / MCP | T16 / T18 / T17 |
| Client HTTP caseiro Qdrant/embeddings | Proibido (BR-023) |

## 2. Decisões de contrato

| ID | Decisão | Motivo |
|---|---|---|
| I-T13-001 | Portas `VectorStore` e `Embedder` como `Protocol` distintos | T14/T16 injetam fakes; embeddings ≠ metadados SLM (BR-010); ENG-007 |
| I-T13-002 | Tipos frozen (`ChunkMetadata`, `EnrichedChunk`, …) | Contrato estável T12/T14/T16; sem mutação pós-construção |
| I-T13-003 | `ChunkMetadata` mínimo: `summary`, `keywords`, `symbols` | Payload Qdrant tipado sem T12 na branch; serialização estável |
| I-T13-004 | `VectorStore` recebe `VectorRecord` (já embutido) | Store não embute; orquestrador usa `Embedder` à parte |
| I-T13-005 | `replace_repo_commit` = upsert + purge outros commits do repo | Critério reindex/restart; BDD VS-03/VS-08 |
| I-T13-006 | Erros tipados sob `VectorStoreError` / `EmbeddingError` | Corners BDD; T14 mapeia falha de etapa (BR-005) |
| I-T13-007 | Sem parâmetros de chunking nas ports/adaptadores | DEC-003 / ENG-008 / BDD VS-14 |
| I-T13-008 | Adaptadores só via `qdrant-client` e `openai` | DEC-015, BR-023, BDD-024, VS-05/VS-06 |
| I-T13-009 | `OpenAICompatibleEmbedder` não expõe chat/completions | Separação rígida de T12; VS-06 |
| I-T13-010 | Point id UUID v5(`repo_id`, `commit_sha`, `chunk_id`) | Idempotência VS-13; design §4.7 |
| I-T13-011 | Payload §4.8 com chunk completo + `metadata` aninhado | BDD-010 / VS-01 reidratação |
| I-T13-012 | `search` retorna `SemanticHit` (evidência); sem SLM | BR-011 |

## 3. Contratos detalhados

### 3.1 `ChunkMetadata`

Módulo: `github_rag.index.vector.types`

```python
@dataclass(frozen=True)
class ChunkMetadata:
    summary: str
    keywords: tuple[str, ...]
    symbols: tuple[str, ...] = ()
```

- **Responsabilidade:** carregar metadados contextuais SLM serializáveis associados a **um** chunk Tree-sitter.
- **Motivo da separação:** desacopla T13 da geração SLM (T12); estabiliza chaves do payload Qdrant; impede dict livre sem invariantes.
- **Invariantes no upsert (VS-04):** `summary.strip()` não vazio; `keywords`/`symbols` são tuples (podem ser `()`).
- **Serialização payload:** `{"summary": str, "keywords": list[str], "symbols": list[str]}`.

### 3.2 `EnrichedChunk`

Módulo: `github_rag.index.vector.types`

```python
@dataclass(frozen=True)
class EnrichedChunk:
    chunk: SemanticChunk  # github_rag.index.chunk.types
    metadata: ChunkMetadata
```

- **Responsabilidade:** unidade de entrada do VectorStore — chunk Tree-sitter + metadados SLM já gerados.
- **Motivo da separação:** T13 não redefine a unidade de chunk nem gera metadados; só consome o par imutável (DEC-003).
- **Invariantes no upsert:** `chunk.text` não vazio; `chunk.chunk_id` não vazio; `metadata.summary` não vazio (strip).

### 3.3 `RepoCommitScope`

Módulo: `github_rag.index.vector.types`

```python
@dataclass(frozen=True)
class RepoCommitScope:
    repo_id: str
    commit_sha: str
```

- **Responsabilidade:** identificar o escopo de indexação vetorial (repositório + tip `main` processado).
- **Motivo da separação:** concentra filtros de purge/replace/delete sem acoplar T13 ao schema PostgreSQL do catálogo.
- **Invariantes:** ambos não vazios (strip); valores opacos para T13.

### 3.4 `VectorRecord`

Módulo: `github_rag.index.vector.types`

```python
@dataclass(frozen=True)
class VectorRecord:
    enriched: EnrichedChunk
    vector: tuple[float, ...]
```

- **Responsabilidade:** transportar um chunk enriquecido já embutido para persistência.
- **Motivo da separação:** deixa explícito que o store não chama `Embedder`; dimensão validada contra `vector_size` (VS-09).

### 3.5 `SemanticHit`

Módulo: `github_rag.index.vector.types`

```python
@dataclass(frozen=True)
class SemanticHit:
    score: float
    repo_id: str
    commit_sha: str
    chunk: SemanticChunk
    metadata: ChunkMetadata
```

- **Responsabilidade:** evidência semântica reidratada para T16/UI/MCP (score + chunk + metadata).
- **Motivo da separação:** search devolve evidências tipadas sem prosa SLM (BR-011); contrato estável de reidratação (VS-01).

### 3.6 Erros — VectorStore

Módulo: `github_rag.index.vector.errors`

```python
class VectorStoreError(Exception):
    """Base das falhas de persistência/busca vetorial."""

    def __init__(self, message: str = "") -> None: ...

class VectorValidationError(VectorStoreError):
    """Record inválido: summary/text/chunk_id vazios (VS-04)."""

class VectorDimensionError(VectorStoreError):
    """len(vector) != vector_size da collection (VS-09)."""
```

- **Responsabilidade:** sinalizar falhas do store sem fallback silencioso nem payload parcial.
- **Motivo da separação:** distinto de `EmbeddingError` e de erros de chunk/metadata; T14 mapeia para falha de etapa.
- **Quando:**
  - `VectorValidationError` — `metadata.summary` vazio/whitespace; `chunk.text` vazio; `chunk_id` vazio
  - `VectorDimensionError` — dimensão do vetor ≠ `vector_size`
  - `VectorStoreError` — falhas SDK Qdrant/config (mensagem sem secrets)

### 3.7 Erros — Embedder

Módulo: `github_rag.index.vector.errors`

```python
class EmbeddingError(Exception):
    """Base das falhas de embedding."""

    def __init__(self, message: str = "") -> None: ...

class EmbeddingValidationError(EmbeddingError):
    """Texto vazio/whitespace ou dimensões inconsistentes no retorno (VS-12)."""
```

- **Responsabilidade:** sinalizar falhas de embedding sem enviar input inválido ao runtime.
- **Motivo da separação:** falhas de embedding ≠ falhas de Qdrant; permite retry/restart distintos em T14.
- **Quando:**
  - `EmbeddingValidationError` — texto vazio/só whitespace; retorno com dim ≠ `dimensions`
  - `EmbeddingError` — falhas SDK/rede/modelo

### 3.8 `Embedder` (Protocol)

Módulo: `github_rag.index.vector.ports`

```python
@runtime_checkable
class Embedder(Protocol):
    @property
    def dimensions(self) -> int:
        """Dimensionalidade dos vetores produzidos."""
        ...

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """Produz embeddings densos para uma sequência de textos.

        Responsabilidade
            Única porta de produção de vetores a partir de textos.

        Motivo da separação
            Isola o SDK ``openai`` / runtime local de embeddings da porta
            ``MetadataGenerator`` (T12) e do ``VectorStore``.
        """
        ...
```

| Regra | Comportamento | BDD |
|---|---|---|
| `texts == ()` | Retorna `()`; sem I/O | VS-12 |
| Texto vazio / whitespace | `EmbeddingValidationError`; sem chamada ao runtime | VS-12 |
| Sucesso | `len(result) == len(texts)`; cada `len(v) == dimensions` | design §4.5 |
| Falha SDK | `EmbeddingError` | design §6 |

- **Proibido na assinatura:** `max_chars`, `chunk_size`, `overlap`, `max_lines` (VS-14).

### 3.9 `VectorStore` (Protocol)

Módulo: `github_rag.index.vector.ports`

```python
@runtime_checkable
class VectorStore(Protocol):
    def upsert(
        self,
        scope: RepoCommitScope,
        records: Sequence[VectorRecord],
    ) -> None:
        """Insere/atualiza pontos do scope (idempotente por point id).

        Responsabilidade
            Persistir vetor + payload (chunk Tree-sitter + metadata SLM).

        Motivo da separação
            Isola Qdrant dos consumidores; não remove commits antigos.
        """
        ...

    def purge_other_commits(self, scope: RepoCommitScope) -> None:
        """Remove pontos do mesmo ``repo_id`` com ``commit_sha`` ≠ scope.

        Responsabilidade
            Limpar commits anteriores do repositório.

        Motivo da separação
            Permite testar purge isolado de upsert (VS-07).
        """
        ...

    def replace_repo_commit(
        self,
        scope: RepoCommitScope,
        records: Sequence[VectorRecord],
    ) -> None:
        """Upsert + purge_other_commits (reindex / restart total por commit).

        Responsabilidade
            Substituir o índice vetorial do repo pelo commit atual.

        Motivo da separação
            API conveniente e semântica explícita para T14 (VS-03, VS-08).
        """
        ...

    def delete_repo(self, repo_id: str) -> None:
        """Remove todos os pontos do ``repo_id``.

        Responsabilidade
            Wipe vetorial de um repositório.

        Motivo da separação
            Operação de catálogo/remoção distinta de reindex por commit.
        """
        ...

    def delete_paths(
        self,
        scope: RepoCommitScope,
        paths: Sequence[str],
    ) -> None:
        """Remove pontos do scope cujo payload.path ∈ paths.

        Responsabilidade
            Limpar paths removidos (ENG-012) sem rebuild total obrigatório.

        Motivo da separação
            Handoff T14; escopo por commit evita apagar path de outro tip.
        """
        ...

    def search(
        self,
        query_vector: Sequence[float],
        *,
        limit: int,
        repo_ids: Sequence[str] | None = None,
    ) -> tuple[SemanticHit, ...]:
        """Busca k-NN; reidrata SemanticHit a partir do payload.

        Responsabilidade
            Recuperar evidências semanticamente relacionadas (BDD-010).

        Motivo da separação
            Search não gera prosa nem chama SLM (BR-011).
        """
        ...
```

| Método | Semântica | BDD |
|---|---|---|
| `upsert` | Idempotente; valida records; não purge | VS-01, VS-04, VS-09, VS-13 |
| `purge_other_commits` | Só outros commits do mesmo `repo_id` | VS-07 |
| `replace_repo_commit` | `upsert` + `purge_other_commits`; `records==()` limpa | VS-03, VS-08 |
| `delete_paths` | Path ∈ lista no scope | VS-10 |
| `delete_repo` | Todos os pontos do repo | VS-10 |
| `search` | k-NN Cosine; filtro `repo_ids`; `limit` | VS-01, VS-02, VS-11 |

- **Proibido na assinatura:** parâmetros de chunking (VS-14).
- **Payload persistido:** design §4.8 (campos do `SemanticChunk` + `metadata`).

### 3.10 `QdrantVectorStore`

Módulo: `github_rag.index.vector.qdrant_store`

```python
class QdrantVectorStore:
    def __init__(
        self,
        *,
        client: Any,  # qdrant_client.QdrantClient
        collection_name: str = "github_rag_chunks",
        vector_size: int,
    ) -> None: ...

    def upsert(
        self, scope: RepoCommitScope, records: Sequence[VectorRecord]
    ) -> None: ...

    def purge_other_commits(self, scope: RepoCommitScope) -> None: ...

    def replace_repo_commit(
        self, scope: RepoCommitScope, records: Sequence[VectorRecord]
    ) -> None: ...

    def delete_repo(self, repo_id: str) -> None: ...

    def delete_paths(
        self, scope: RepoCommitScope, paths: Sequence[str]
    ) -> None: ...

    def search(
        self,
        query_vector: Sequence[float],
        *,
        limit: int,
        repo_ids: Sequence[str] | None = None,
    ) -> tuple[SemanticHit, ...]: ...
```

- **Responsabilidade:** implementar `VectorStore` via SDK oficial `qdrant-client` (DEC-004, DEC-015).
- **Motivo da separação:** concentra binding Qdrant; T14 depende só da porta.
- **Collection:** Cosine; criação idempotente; `vector_size` obrigatório.
- **Point id:** UUID v5, namespace fixo do produto, nome `f"{repo_id}\0{commit_sha}\0{chunk_id}"` (I-T13-010).
- **Proibido:** client HTTP/REST caseiro (`requests`/`httpx`/`urllib` para Qdrant) — VS-05.
- **Erros SDK:** mapear para `VectorStoreError` (sem secrets na mensagem).

### 3.11 `OpenAICompatibleEmbedder`

Módulo: `github_rag.index.vector.embedder`

```python
class OpenAICompatibleEmbedder:
    def __init__(
        self,
        *,
        client: Any,  # openai.OpenAI
        model: str,
        dimensions: int,
    ) -> None: ...

    @property
    def dimensions(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]: ...
```

- **Responsabilidade:** implementar `Embedder` via SDK oficial `openai` (`embeddings.create` apenas).
- **Motivo da separação:** adaptador de embeddings distinto de T12 chat/completions; injetável para testes (VS-12).
- **Regras:** validação de texto antes de qualquer chamada ao client; batch preserva ordem; `len(vector) == dimensions`.
- **Proibido:** client HTTP inventado; `chat.completions` / superfícies de chat — VS-06.
- **Construtor (BDD):** keyword-only `client`, `model`, `dimensions` (alinha `_make_embedder` dos testes).

## 4. Payload Qdrant (contrato de dados)

Chaves obrigatórias no ponto (design §4.8 / VS-01):

| Chave | Tipo | Origem |
|---|---|---|
| `repo_id` | string | `RepoCommitScope` |
| `commit_sha` | string | `RepoCommitScope` |
| `chunk_id` | string | `SemanticChunk` |
| `path` | string | `SemanticChunk` |
| `language` | string | `SemanticChunk.language.value` |
| `kind` | string | `SemanticChunk` |
| `text` | string | `SemanticChunk` |
| `start_byte` | int | `SemanticChunk` |
| `end_byte` | int | `SemanticChunk` |
| `start_point` | `[row, col]` | `SemanticChunk` |
| `end_point` | `[row, col]` | `SemanticChunk` |
| `metadata` | object | `ChunkMetadata` → summary/keywords/symbols |

Índices de payload recomendados: `repo_id`, `commit_sha`, `path`.

## 5. Reexports (`index/vector/__init__.py`)

```python
from github_rag.index.vector.errors import (
    EmbeddingError,
    EmbeddingValidationError,
    VectorDimensionError,
    VectorStoreError,
    VectorValidationError,
)
from github_rag.index.vector.ports import Embedder, VectorStore
from github_rag.index.vector.types import (
    ChunkMetadata,
    EnrichedChunk,
    RepoCommitScope,
    SemanticHit,
    VectorRecord,
)
from github_rag.index.vector.qdrant_store import QdrantVectorStore
from github_rag.index.vector.embedder import OpenAICompatibleEmbedder
```

## 6. Handoff T12 / T14 / T16

| Consumidor | Usa |
|---|---|
| T12 `MetadataGenerator` | Deve emitir `ChunkMetadata` compatível (§3.1) |
| T14 orquestrador | `EnrichedChunk` → `Embedder.embed` → `VectorRecord` → `VectorStore.replace_repo_commit` / `delete_paths`; captura erros tipados |
| T16 query | `Embedder` + `VectorStore.search` → `SemanticHit[]` |

Contrato congelado nesta task: campos dos tipos §3.1–3.5, semântica de `replace_repo_commit`, schema de payload §4 e hierarquia de erros — mudanças exigem `SCOPE_CHANGE_REQUIRED`.
