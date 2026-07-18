# BDD — T13-qdrant-vector-store

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T13-qdrant-vector-store` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Rastreabilidade | BDD-010, BDD-024; DEC-003, DEC-004, DEC-015; BR-010, BR-011, BR-023; ENG-008, ENG-013 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Correções: VS-01 ranges; VS-12 → `OpenAICompatibleEmbedder`; VS-14 DEC-003. |

## Escopo

Persistência e busca semântica no Qdrant via ports `VectorStore` / `Embedder` (camada T13). UI/MCP (perspectiva BDD-010 completa) ficam em T16/T18; aqui cobrimos a base: upsert de chunk+metadata e search devolvendo `SemanticHit` relacionados.

## Fixtures de teste (design §11)

- `QdrantClient(":memory:")` (SDK oficial; sem Docker no gate).
- Vetores controlados/normalizados nos `VectorRecord` (sem runtime de embedding no happy path do store).
- `OpenAICompatibleEmbedder` com cliente `openai` stub (VS-12); sem runtime real.
- `ChunkMetadata` / `EnrichedChunk` / `SemanticChunk` construídos manualmente (T12 pode estar ausente).

## Cenários executáveis

### VS-01 — BDD-010: upsert persiste chunk Tree-sitter + metadados SLM

**Dado** um `QdrantVectorStore` com `QdrantClient(":memory:")` e `vector_size` conhecido  
**E** um `RepoCommitScope(repo_id="repo-a", commit_sha="aaa111")`  
**E** um `VectorRecord` cujo `EnrichedChunk` tem `SemanticChunk` (path, language, kind, text, `start_byte`/`end_byte`, `start_point`/`end_point`, chunk_id) e `ChunkMetadata(summary` não vazio, keywords, symbols)  
**Quando** `store.upsert(scope, [record])` é executado  
**Então** a operação completa sem erro  
**E** um `search` subsequente com o mesmo vetor (limit≥1) devolve ao menos um `SemanticHit`  
**E** o hit reidrata `chunk` com path, language, kind, text, chunk_id, ranges e points iguais aos do record (design §4.8)  
**E** o hit reidrata `metadata` (summary/keywords/symbols) igual ao do record  
**E** `hit.repo_id` e `hit.commit_sha` batem com o scope  
**E** o hit é evidência tipada (`SemanticHit`); search não invoca SLM/chat (BR-011)

### VS-02 — BDD-010: search retorna hits semanticamente relacionados

**Dado** dois `VectorRecord` no mesmo scope com vetores distintos (Embedder fake / vetores fixos)  
**E** o record A alinhado ao vetor de query Q; o record B ortogonal/distante de Q  
**Quando** `store.search(Q, limit=2)` é executado  
**Então** o primeiro hit (maior score) corresponde ao chunk A  
**E** o payload do hit inclui texto/path do chunk A e `metadata.summary` de A  
**E** o score de A é estritamente maior que o de B (quando ambos retornam)

### VS-03 — Reindex: `replace_repo_commit` substitui vetores do commit anterior

**Dado** pontos indexados para `repo_id="repo-a"` no commit `oldsha`  
**Quando** `replace_repo_commit(RepoCommitScope("repo-a", "newsha"), records_new)` é executado  
**Então** `search` com filtro `repo_ids=["repo-a"]` só devolve hits com `commit_sha == "newsha"`  
**E** nenhum hit com `commit_sha == "oldsha"` permanece  
**E** os payloads dos hits novos refletem `records_new` (chunk + metadata)

### VS-04 — Invariante: upsert exige metadata SLM + chunk Tree-sitter válidos

**Dado** um store válido  
**Quando** `upsert` recebe record com `metadata.summary` vazio ou só whitespace  
**Então** levanta `VectorValidationError` (subclasse de `VectorStoreError`)  
**E** não persiste ponto parcial  

**Quando** `upsert` recebe record com `chunk.text` vazio ou `chunk_id` vazio  
**Então** levanta `VectorValidationError`  
**E** não persiste ponto parcial

### VS-05 — BDD-024: integração Qdrant via `qdrant-client`

**Dado** o módulo de produção `github_rag.index.vector.qdrant_store`  
**Quando** a superfície de `QdrantVectorStore` é inspecionada / exercida  
**Então** a comunicação com Qdrant usa o cliente oficial `qdrant_client.QdrantClient`  
**E** o código de produção não implementa client HTTP/REST caseiro para Qdrant (BR-023 / DEC-015)

### VS-06 — BDD-024: embeddings via SDK `openai`

**Dado** o módulo de produção `github_rag.index.vector.embedder`  
**Quando** a superfície de `OpenAICompatibleEmbedder` é inspecionada  
**Então** embeddings usam o cliente oficial `openai.OpenAI` (método de embeddings)  
**E** não há client HTTP inventado para embeddings  
**E** o adaptador não expõe/chama chat/completions (separação de T12 / BR-010)

### VS-07 — Corner: `purge_other_commits` remove só outros commits do mesmo repo

**Dado** pontos para `(repo-a, oldsha)`, `(repo-a, keepsha)` e `(repo-b, other)`  
**Quando** `purge_other_commits(RepoCommitScope("repo-a", "keepsha"))`  
**Então** pontos de `repo-a`/`oldsha` são removidos  
**E** pontos de `repo-a`/`keepsha` e de `repo-b` permanecem

### VS-08 — Corner: `replace_repo_commit` com `records == ()` limpa o repo

**Dado** pontos existentes para `repo-a` em qualquer commit  
**Quando** `replace_repo_commit(RepoCommitScope("repo-a", "tip"), ())`  
**Então** nenhum hit de `repo-a` permanece no search filtrado  
**E** a operação não levanta erro de validação por lista vazia

### VS-09 — Corner: dimensão de vetor incompatível

**Dado** store com `vector_size=N`  
**Quando** `upsert` recebe `VectorRecord` com `len(vector) != N`  
**Então** levanta `VectorDimensionError` (subclasse de `VectorStoreError`)  
**E** não persiste o ponto

### VS-10 — Corner: `delete_repo` e `delete_paths`

**Dado** pontos de `repo-a` em paths `src/a.py` e `src/b.py` e pontos de `repo-b`  
**Quando** `delete_paths(scope_a, ["src/a.py"])`  
**Então** só o path `src/a.py` de `repo-a`/commit do scope some  
**E** `src/b.py` e `repo-b` permanecem  

**Quando** `delete_repo("repo-a")`  
**Então** nenhum hit de `repo-a` permanece; `repo-b` intacto

### VS-11 — Corner: search com filtro `repo_ids` e limite

**Dado** pontos em `repo-a` e `repo-b`  
**Quando** `search(vector, limit=1, repo_ids=["repo-a"])`  
**Então** retorna no máximo 1 hit  
**E** todo hit tem `repo_id == "repo-a"`

### VS-12 — Corner: `OpenAICompatibleEmbedder` — batch vazio e texto inválido

**Dado** um `OpenAICompatibleEmbedder` com cliente `openai.OpenAI` stub/fake injetado (`dimensions` conhecido)  
**Quando** `embed(())`  
**Então** retorna `()`  
**E** o stub **não** recebe chamada a `embeddings.create`  

**Quando** `embed` recebe texto vazio ou só whitespace  
**Então** levanta `EmbeddingValidationError` (subclasse de `EmbeddingError`)  
**E** o stub **não** recebe chamada a `embeddings.create` (validação antes do runtime)

### VS-13 — Upsert idempotente por point id (mesmo repo/commit/chunk_id)

**Dado** um record upsertado uma vez  
**Quando** o mesmo `VectorRecord` (mesmo scope + chunk_id) é upsertado de novo com metadata/vetor atualizados  
**Então** `search` devolve um único hit para aquele chunk_id no scope  
**E** o payload/vetor refletem a segunda escrita

### VS-14 — DEC-003 / ENG-008: T13 não redefine unidade de chunk

**Dado** as superfícies de produção `QdrantVectorStore` e `OpenAICompatibleEmbedder`  
**Quando** inspecionadas assinaturas públicas (`upsert`/`replace_repo_commit`/`embed` e construtores)  
**Então** não existem parâmetros `max_chars`, `chunk_size`, `overlap` ou split por linhas  
**E** a unidade persistida é `EnrichedChunk` / `VectorRecord` que embute `SemanticChunk` de T11 — T13 não produz chunks a partir de texto bruto

## Fora de escopo destes BDD

- UI percentual / apoio SLM na interação (BDD-010 perspectiva UI → T16/T18)
- Geração de metadados SLM (T12) e chunking (T11)
- Orquestração de indexação / BR-005 (T14 consome ports e erros tipados)
- Integration testcontainers Qdrant (opcional; não bloqueia gate)

## Execução

```bash
python -m pytest tests/bdd/test_qdrant_vector_store.py -q
```
