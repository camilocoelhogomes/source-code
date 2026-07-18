# Design — T13-qdrant-vector-store

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T13-qdrant-vector-store` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T13-qdrant-vector-store` |
| Base | `feature/github-etl-mcp-rag-T11-treesitter-chunker` |
| Rastreabilidade | DEC-003, DEC-004, DEC-015; BR-010, BR-011, BR-023; REQ-002; ENG-008, ENG-013; BDD-010, BDD-024 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Design inicial sólido: contratos `EnrichedChunk`/`ChunkMetadata`, ports `VectorStore`/`Embedder`, payload Qdrant, reindex por commit, testes via `:memory:` + fake Embedder. |

## 1. Contexto

O pipeline RAG (T14) produz, por arquivo elegível: chunks Tree-sitter (T11) → metadados SLM por chunk (T12) → persistência vetorial (T13). T13 entrega o pacote `github_rag.index.vector` com:

- porta `VectorStore` + adaptador `qdrant-client` (DEC-004, DEC-015, BR-023, ENG-013);
- porta `Embedder` + adaptador SDK OpenAI-compatible `openai` para **embeddings** (distinto de `MetadataGenerator` / T12);
- tipos de chunk enriquecido consumíveis sem gerar metadados (T12 ainda pode estar ausente nesta branch).

Consumidores: T14 (upsert/replace na indexação), T16 (search semântico → UI/MCP). Fora de escopo: narrativa SLM, Zoekt, chunking, geração de metadados, UI/MCP.

## 2. Problema

É preciso persistir e recuperar no Qdrant **cada** unidade RAG como vetor + payload (chunk Tree-sitter + metadados SLM), sem redefinir a unidade de chunk (DEC-003), sem client HTTP caseiro (BR-023 / BDD-024), e com política de reindexação que **substitui** vetores do commit anterior do repositório. Embeddings e metadados SLM compartilham o ecossistema OpenAI-compatible, mas **não** a mesma porta de domínio.

## 3. Solução proposta

Módulo `github_rag.index.vector` (placeholder T01 → implementação nesta task):

| Componente | Papel |
|---|---|
| `types` | `ChunkMetadata`, `EnrichedChunk`, `RepoCommitScope`, `VectorRecord`, `SemanticHit` |
| `errors` | `VectorStoreError` / `EmbeddingError` e subclasses tipadas |
| `ports` | Protocols `VectorStore`, `Embedder` |
| `qdrant_store` | `QdrantVectorStore` — adaptador oficial `qdrant-client` |
| `embedder` | `OpenAICompatibleEmbedder` — adaptador oficial `openai` (embeddings only) |

Fluxo feliz (orquestrado por T14; T13 expõe as peças):

```text
EnrichedChunk (SemanticChunk + ChunkMetadata)
  → Embedder.embed([chunk.text, ...]) → vetores
  → VectorRecord(enriched, vector)
  → VectorStore.replace_repo_commit(scope, records)
       1) upsert pontos (repo_id, commit_sha, payload, vector)
       2) delete pontos do mesmo repo_id com commit_sha ≠ atual
  → Search: Embedder.embed([query]) → VectorStore.search(vector) → SemanticHit[]
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T13 | Fora de T13 |
|---|---|---|
| BDD-010 | Persistência chunk+metadados; upsert+search devolvem hits semanticamente relacionados (score/payload) | UI, apoio SLM na interação (T16/T18) |
| BDD-024 | Integração Qdrant via `qdrant-client`; embeddings via `openai` | Demais SDKs; DT-001 |
| DEC-003 / ENG-008 | Consome só `SemanticChunk` / `EnrichedChunk`; sem chunk por tamanho/linhas | Produção de chunks (T11) |
| BR-010 / BR-011 | Payload inclui metadados SLM; search não chama SLM | Geração de metadados (T12); prosa MCP |

## 4. Componentes

### 4.1 `ChunkMetadata` (contrato mínimo estável T12↔T13)

T12 ainda não está nesta branch. T13 define o contrato **mínimo serializável** que o payload Qdrant exige; T12 deve produzir exatamente este tipo (ou subtype compatível sem quebrar chaves).

```python
@dataclass(frozen=True)
class ChunkMetadata:
    summary: str
    keywords: tuple[str, ...]
    symbols: tuple[str, ...] = ()
```

| Campo | Tipo | Descrição |
|---|---|---|
| `summary` | `str` | Resumo contextual do chunk (obrigatório; não vazio no upsert) |
| `keywords` | `tuple[str, ...]` | Termos/tópicos; pode ser `()` |
| `symbols` | `tuple[str, ...]` | Símbolos/nomes estruturais citados; default `()` |

- **Responsabilidade:** carregar metadados contextuais SLM serializáveis associados a **um** chunk.
- **Motivo da separação:** desacopla T13 da geração SLM; estabiliza chaves do payload Qdrant antes de T12; impede dict livre sem invariantes.
- **Proibido em T13:** chamar SLM ou preencher estes campos a partir de heurísticas locais.

Serialização no payload: objeto aninhado `metadata: { "summary", "keywords", "symbols" }` (listas JSON para as tuples).

### 4.2 `EnrichedChunk`

```python
@dataclass(frozen=True)
class EnrichedChunk:
    chunk: SemanticChunk  # de github_rag.index.chunk.types (T11)
    metadata: ChunkMetadata
```

- **Responsabilidade:** unidade de entrada do VectorStore — chunk Tree-sitter + metadados SLM já gerados.
- **Motivo da separação:** T13 não redefine chunk nem gera metadados; só consome o par imutável.
- **Invariantes no upsert:** `chunk.text` não vazio; `metadata.summary` não vazio (strip); `chunk.chunk_id` não vazio.

### 4.3 `RepoCommitScope`

```python
@dataclass(frozen=True)
class RepoCommitScope:
    repo_id: str
    commit_sha: str
```

Identifica o escopo de indexação vetorial. `repo_id` é o identificador estável do catálogo (string opaca para T13; T14/T07 definem o valor). `commit_sha` é o tip `main` processado.

### 4.4 `VectorRecord` e `SemanticHit`

```python
@dataclass(frozen=True)
class VectorRecord:
    enriched: EnrichedChunk
    vector: tuple[float, ...]

@dataclass(frozen=True)
class SemanticHit:
    score: float
    repo_id: str
    commit_sha: str
    chunk: SemanticChunk
    metadata: ChunkMetadata
```

- `VectorRecord`: entrada já embutida (orquestrador ou helper embute via `Embedder`).
- `SemanticHit`: evidência semântica para T16 (BR-011 — sem prosa).

### 4.5 `Embedder` (Protocol)

Responsabilidade: produzir embeddings densos a partir de textos. Separação: isola o SDK `openai` e o runtime local de embeddings da porta `MetadataGenerator` (T12) e do `VectorStore`.

```python
class Embedder(Protocol):
    @property
    def dimensions(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]: ...
```

| Regra | Comportamento |
|---|---|
| Entrada vazia `()` | Retorna `()` |
| Texto vazio / só whitespace | `EmbeddingError` (não envia ao runtime) |
| Sucesso | `len(result) == len(texts)`; cada vetor com `len == dimensions` |
| Falha SDK/rede/modelo | `EmbeddingError` (subclasse tipada se útil) |

Implementação default: `OpenAICompatibleEmbedder` — cliente `openai.OpenAI` (ou async equivalente se o projeto padronizar sync) apontando a `base_url` local + `api_key` configurável; método `embeddings.create(model=..., input=...)`. **Proibido** client HTTP inventado.

Config (construtor / env documentada para T19; defaults no design):

| Parâmetro | Default sugerido | Notas |
|---|---|---|
| `base_url` | obrigatório injetado | Runtime local (Ollama/vLLM/etc. — aberto em requisitos) |
| `api_key` | `"local"` ou env | Sem logar valor |
| `model` | configurável | Modelo de **embedding**, não Qwen chat de metadados |
| `dimensions` | obrigatório alinhado ao modelo | Usado para criar collection Qdrant |

### 4.6 `VectorStore` (Protocol)

Responsabilidade: persistir e buscar vetores + payload RAG no Qdrant. Separação: não chunka, não embute, não gera metadados; só I/O vetorial atrás de porta estável para T14/T16.

```python
class VectorStore(Protocol):
    def upsert(self, scope: RepoCommitScope, records: Sequence[VectorRecord]) -> None: ...

    def purge_other_commits(self, scope: RepoCommitScope) -> None: ...

    def replace_repo_commit(
        self, scope: RepoCommitScope, records: Sequence[VectorRecord]
    ) -> None: ...

    def delete_repo(self, repo_id: str) -> None: ...

    def delete_paths(self, scope: RepoCommitScope, paths: Sequence[str]) -> None: ...

    def search(
        self,
        query_vector: Sequence[float],
        *,
        limit: int,
        repo_ids: Sequence[str] | None = None,
    ) -> tuple[SemanticHit, ...]: ...
```

| Método | Semântica |
|---|---|
| `upsert` | Insere/atualiza pontos do `scope` (idempotente por point id). Não remove commits antigos. |
| `purge_other_commits` | Apaga pontos com `repo_id` igual e `commit_sha` ≠ `scope.commit_sha`. |
| `replace_repo_commit` | `upsert` + `purge_other_commits` — **política de reindex / restart total por commit** (critério T13). |
| `delete_repo` | Remove todos os pontos do `repo_id`. |
| `delete_paths` | Remove pontos do `scope` cujo payload.`path` ∈ `paths` (ENG-012 paths removidos; T14). |
| `search` | k-NN por vetor; filtro opcional por `repo_ids`; retorna hits com payload reidratado. |

`replace_repo_commit` com `records == ()` é válido: equivale a limpar o repo após purge (útil se tip sem arquivos elegíveis — decisão de T14 se chama ou não).

Implementação default: `QdrantVectorStore`.

### 4.7 Collection e point id

| Item | Decisão |
|---|---|
| Collection | Nome configurável; default `github_rag_chunks` |
| Distance | Cosine |
| Vector size | `embedder.dimensions` (ou valor injetado no store na criação) |
| Criação | Idempotente no primeiro uso (`get_collection` / `create_collection`) |
| Point id | UUID v5: namespace fixo do produto + `f"{repo_id}\0{commit_sha}\0{chunk_id}"` |

Motivo do point id: estável entre retries do mesmo commit/chunk; muda se commit ou chunk_id muda; compatível com IDs UUID do Qdrant.

### 4.8 Payload Qdrant (schema)

Payload **flat + objeto metadata** (tipos JSON-compatíveis do Qdrant):

| Chave | Tipo JSON | Origem |
|---|---|---|
| `repo_id` | string | `RepoCommitScope` |
| `commit_sha` | string | `RepoCommitScope` |
| `chunk_id` | string | `SemanticChunk.chunk_id` |
| `path` | string | `SemanticChunk.path` |
| `language` | string | `SemanticChunk.language.value` |
| `kind` | string | `SemanticChunk.kind` |
| `text` | string | `SemanticChunk.text` |
| `start_byte` | int | `SemanticChunk` |
| `end_byte` | int | `SemanticChunk` |
| `start_point` | `[row, col]` | `SemanticChunk` |
| `end_point` | `[row, col]` | `SemanticChunk` |
| `metadata` | object | `ChunkMetadata` → `{summary, keywords, symbols}` |

Índices de payload recomendados (criação da collection / `create_payload_index`): `repo_id`, `commit_sha`, `path` — para filtros de purge/delete/search.

**Invariante de aceite:** nenhum upsert sem `metadata.summary` não vazio e campos do chunk Tree-sitter presentes.

### 4.9 `QdrantVectorStore`

- Construtor recebe `qdrant_client.QdrantClient` (injetável) + `collection_name` + `vector_size`.
- Toda comunicação Qdrant exclusivamente via SDK `qdrant-client` (DEC-015 / BR-023 / BDD-024).
- Mapeia exceções do SDK → `VectorStoreError` (mensagem sem secrets).
- `search` reidrata `SemanticChunk` + `ChunkMetadata` a partir do payload; `language` via `SourceLanguage(value)`.

### 4.10 `OpenAICompatibleEmbedder`

- Construtor: `client: openai.OpenAI` (ou factory url/key/model) + `model` + `dimensions`.
- Chama apenas a API de embeddings do SDK; **não** chama chat/completions (isso é T12).
- Batch: uma chamada `embeddings.create` com lista de inputs quando o runtime permitir; preserva ordem.

## 5. Fluxo de dados

```text
T11 SemanticChunk → T12 ChunkMetadata → EnrichedChunk
  → T13 Embedder.embed(texts)
  → T13 VectorStore.replace_repo_commit(scope, VectorRecord[])
  → Qdrant points

Consulta (T16):
  query text → Embedder.embed → VectorStore.search → SemanticHit[]
  → UI/MCP (evidências; sem prosa SLM no caminho MCP — BR-011)
```

Reindexação / BR-005 (T14): em nova tentativa do repositório, T14 chama novamente `replace_repo_commit` com o tip atual; pontos do commit anterior são removidos no `purge_other_commits`.

## 6. Erros

| Tipo | Quando |
|---|---|
| `VectorStoreError` | Base; falhas Qdrant/SDK/config |
| `VectorValidationError` | Record inválido (summary vazio, dim errada, chunk sem texto) |
| `VectorDimensionError` | `len(vector) != vector_size` da collection |
| `EmbeddingError` | Base; falhas do runtime/SDK de embeddings |
| `EmbeddingValidationError` | Texto vazio; dimensions inconsistentes no retorno |

Todos tipados para T14 mapear falha de etapa → restart do repo (BR-005). Sem fallback silencioso nem payload parcial sem metadata.

## 7. Segurança

- Não logar `api_key`, textos completos de arquivos em nível INFO (payload pode conter código — logs de debug opt-in).
- Sem token GitHub nesta camada.
- URL Qdrant / base_url embeddings via config injetada (T19); sem hardcode de secrets.
- Search/MCP consomem apenas evidências já no payload (BR-011).

## 8. Compatibilidade

| Item | Ação |
|---|---|
| Deps novas | `qdrant-client`, `openai` em `pyproject.toml` dependencies |
| Dev/integration | Manter `testcontainers` opcional; ver §11 |
| Python | 3.12+ |
| T11 | Importa `SemanticChunk`, `SourceLanguage` — sem alterar contrato T11 |
| T12 | Deve emitir `ChunkMetadata` compatível; se T12 evoluir campos, versionar payload com cuidado |
| T14/T16 | Consumem ports; não importam SDKs |

## 9. Observabilidade

- Sem logger obrigatório no MVP desta task; erros tipados bastam.
- Contagens (`upsert` N points, `search` K hits) observáveis pelo orquestrador/T16.
- Opcional futuro: métricas de latência Qdrant/embed — fora do MVP T13.

## 10. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| T12 ausente / schema divergente | Contrato `ChunkMetadata` mínimo documentado; testes T13 com fixtures manuais de metadata |
| Dimensão de embedding ≠ collection | `VectorDimensionError` + `dimensions` explícito no Embedder/store |
| Índice parcial visível durante indexação | T14 deve preferir `replace_repo_commit` ao **final** do sucesso do repo; até lá commit anterior permanece |
| Código sensível no payload | Aceito (REQ RAG); volumes locais; sem expor em logs |
| Runtime embeddings distinto da SLM chat | Portas separadas; models/URLs distintos na config |
| API Qdrant/openai mudar | Pin de versões no pyproject; SDKs oficiais apenas |

## 11. Estratégia de teste

| Camada | Estratégia |
|---|---|
| Unit (gate cobertura ≥95%) | `Embedder` fake; `QdrantVectorStore` com `QdrantClient(":memory:")` oficial (exercita SDK sem Docker); validação de payload/purge/search |
| Unit isolado de adaptador | Fakes das ports para consumidores futuros (T14/T16) |
| Integration (marker, opcional) | `testcontainers` Qdrant se necessário validar URL/rede; **não** bloqueia o gate padrão (padrão T03 postgres) |
| Proibido | Client HTTP inventado; assertar contra API REST crua |

Cobertura BDD-010 nesta task: cenários de persistência + search retornando hits com chunk+metadata relacionados (fixtures com vetores controlados / fake embedder determinístico). BDD-024: imports/adaptadores usam `qdrant-client` e `openai`.

## 12. Rollback

Remover implementação de `index.vector` (exceto stub), deps `qdrant-client`/`openai` do pyproject e testes T13. Volume Qdrant é descartável no MVP local. Sem migration SQL.

## 13. Decisões de design

| ID | Decisão | Motivo |
|---|---|---|
| D-T13-001 | Tipos `ChunkMetadata` + `EnrichedChunk` (frozen) como contrato mínimo T12/T13 | T12 ausente na branch; payload exige metadados tipados |
| D-T13-002 | Portas separadas `VectorStore` e `Embedder` | Embeddings ≠ metadados SLM (BR-010); ENG-007/013 |
| D-T13-003 | Adaptadores só via `qdrant-client` e `openai` | DEC-015, BR-023, BDD-024, ENG-013 |
| D-T13-004 | `replace_repo_commit` = upsert + purge outros `commit_sha` do mesmo `repo_id` | Critério reindex/restart total; substitui vetores do commit anterior |
| D-T13-005 | Collection única default `github_rag_chunks` + filtros payload | Simplicidade MVP; escala multi-repo via `repo_id` |
| D-T13-006 | Point id = UUID v5(`repo_id`, `commit_sha`, `chunk_id`) | Idempotência e compatibilidade Qdrant |
| D-T13-007 | Payload inclui campos completos do `SemanticChunk` + objeto `metadata` | Aceite T13 / BDD-010; evidências para T16 |
| D-T13-008 | `delete_paths` na porta | Handoff ENG-012 (arquivos removidos) sem forçar rebuild total sempre |
| D-T13-009 | Testes primários com `QdrantClient(":memory:")` + Embedder fake | SDK real sem Docker no gate; alinhado cobertura 95% |
| D-T13-010 | `OpenAICompatibleEmbedder` não usa chat/completions | Separação rígida de T12 |
| D-T13-011 | Proibido chunking ou geração de metadata em T13 | DEC-003, ENG-008; escopo da task |
| D-T13-012 | Distance Cosine; `dimensions` explícitas na config | Comportamento previsível de search semântico |

## 14. Arquivos previstos

```text
src/github_rag/index/vector/
  __init__.py
  types.py
  errors.py
  ports.py
  qdrant_store.py
  embedder.py
tests/unit/index/vector/
tests/bdd/test_qdrant_vector_store.py
spec/features/github-etl-mcp-rag/tasks/T13-qdrant-vector-store/
  design.md
  reviews.md
  bdd.md          # QA (próximo)
  interfaces.md   # Architect (após BDD)
```

## 15. Rastreabilidade

| ID | Como T13 atende |
|---|---|
| BDD-010 | Upsert de chunk+metadata; search retorna `SemanticHit` relacionados |
| BDD-024 | `qdrant-client` + `openai` apenas; sem HTTP caseiro |
| DEC-004 | Qdrant como store vetorial |
| DEC-015 / BR-023 / ENG-013 | SDKs oficiais nos adaptadores |
| DEC-003 / ENG-008 | Consome `SemanticChunk`; não chunka |
| BR-010 | Metadados SLM no payload; Embedder ≠ MetadataGenerator |
| BR-011 | Search devolve evidências; sem prosa SLM |
| REQ-002 | Base da busca semântica |

## 16. Handoff

| Consumidor | Usa |
|---|---|
| T12 | Deve produzir `ChunkMetadata` compatível (§4.1) |
| T14 | `EnrichedChunk` → `Embedder` → `VectorStore.replace_repo_commit` / `delete_paths` |
| T16 | `Embedder` + `VectorStore.search` → evidências |

Contratos a congelar na etapa de interfaces: campos de `ChunkMetadata`/`EnrichedChunk`/`SemanticHit`, semântica de `replace_repo_commit`, schema de payload §4.8.
