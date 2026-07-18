# Plano de testes unitários — T13-qdrant-vector-store

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T13-qdrant-vector-store` |
| Autor | QA Engineer + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Interfaces base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Correções: UT-Q20 SDK→VectorStoreError; UT-Q21 delete_paths por commit; UT-Q17 scope em purge/replace/delete_paths. |

## Artefatos

| Artefato | Caminho |
|---|---|
| Types | `tests/unit/index/vector/test_types.py` |
| Errors | `tests/unit/index/vector/test_errors.py` |
| Ports | `tests/unit/index/vector/test_ports.py` |
| Qdrant store | `tests/unit/index/vector/test_qdrant_store.py` |
| Embedder | `tests/unit/index/vector/test_embedder.py` |
| Helpers | `tests/unit/index/vector/fixtures.py` |
| BDD | `tests/bdd/test_qdrant_vector_store.py` |

## Matriz

| ID | Foco | Entrada | Esperado | Rastreabilidade | Arquivo |
|---|---|---|---|---|---|
| UT-T01 | `ChunkMetadata` frozen | mutate attr | `FrozenInstanceError` | I-T13-002 | `test_types.py` |
| UT-T02 | `symbols` default | só summary+keywords | `symbols == ()` | I-T13-003 | `test_types.py` |
| UT-T03 | `EnrichedChunk` frozen | mutate | `FrozenInstanceError` | I-T13-002 | `test_types.py` |
| UT-T04 | `RepoCommitScope` frozen | mutate | `FrozenInstanceError` | I-T13-002 | `test_types.py` |
| UT-T05 | `VectorRecord` frozen | mutate | `FrozenInstanceError` | I-T13-002 | `test_types.py` |
| UT-T06 | `SemanticHit` frozen | mutate | `FrozenInstanceError` | I-T13-002 | `test_types.py` |
| UT-T07 | composição `EnrichedChunk` | SemanticChunk + ChunkMetadata | campos preservados | §3.2 | `test_types.py` |
| UT-E01 | hierarquia VectorStore | subclasses | `issubclass(..., VectorStoreError)` | I-T13-006 / VS-04/09 | `test_errors.py` |
| UT-E02 | hierarquia Embedding | `EmbeddingValidationError` | subclasse de `EmbeddingError` | VS-12 | `test_errors.py` |
| UT-E03 | bases distintas | Vector vs Embedding | não subclass uma da outra | I-T13-006 | `test_errors.py` |
| UT-E04 | mensagem base | `VectorStoreError("x")` | `"x" in str` | observabilidade | `test_errors.py` |
| UT-P01 | `Embedder` Protocol | `@runtime_checkable` | `isinstance(fake, Embedder)` | I-T13-001 | `test_ports.py` |
| UT-P02 | `VectorStore` Protocol | fake completo | `isinstance(fake, VectorStore)` | I-T13-001 | `test_ports.py` |
| UT-P03 | adaptadores ↔ ports | Qdrant / OpenAI embedder | `isinstance` True | §3.10–3.11 | `test_ports.py` |
| UT-P04 | sem chunking params | signatures ports/adaptadores | sem max_chars/chunk_size/overlap | VS-14 / I-T13-007 | `test_ports.py` |
| UT-Q01 | upsert + search payload | record completo | hit reidrata §4.8 | VS-01 | `test_qdrant_store.py` |
| UT-Q02 | ranking semântico | vetores A próximo / B ortogonal | A primeiro; score A > B | VS-02 | `test_qdrant_store.py` |
| UT-Q03 | `replace_repo_commit` | old → newsha | só newsha no filtro | VS-03 | `test_qdrant_store.py` |
| UT-Q04 | summary vazio/whitespace | `""` / `"  "` | `VectorValidationError`; 0 hits | VS-04 | `test_qdrant_store.py` |
| UT-Q05 | text / chunk_id vazios | text=`""` / chunk_id=`""` | `VectorValidationError` | VS-04 | `test_qdrant_store.py` |
| UT-Q06 | dimensão errada | `len(vector)!=N` | `VectorDimensionError` | VS-09 | `test_qdrant_store.py` |
| UT-Q07 | purge escopado | repo-a old/keep + repo-b | remove só old de repo-a | VS-07 | `test_qdrant_store.py` |
| UT-Q08 | replace vazio | `records==()` | limpa repo-a; sem ValidationError | VS-08 | `test_qdrant_store.py` |
| UT-Q09 | `delete_paths` | path a.py | só a.py some no scope | VS-10 | `test_qdrant_store.py` |
| UT-Q10 | `delete_repo` | repo-a | repo-a vazio; repo-b ok | VS-10 | `test_qdrant_store.py` |
| UT-Q11 | search filter+limit | multi-repo | ≤1 hit; todos repo-a | VS-11 | `test_qdrant_store.py` |
| UT-Q12 | upsert idempotente | 2x mesmo chunk_id | 1 hit; payload 2ª escrita | VS-13 / I-T13-010 | `test_qdrant_store.py` |
| UT-Q13 | upsert não purge | upsert newsha com old presente | old permanece até replace/purge | §3.9 upsert | `test_qdrant_store.py` |
| UT-Q14 | keywords/symbols vazios | `()` | upsert ok; reidrata `()` | corner payload | `test_qdrant_store.py` |
| UT-Q15 | collection vazia | search sem upsert | `()` | estado vazio | `test_qdrant_store.py` |
| UT-Q16 | upsert `records==()` | lista vazia | completa sem erro | empty input | `test_qdrant_store.py` |
| UT-Q17 | scope inválido | repo_id/commit_sha vazios/whitespace em upsert/purge/replace/delete_paths | `VectorValidationError` | §3.3 | `test_qdrant_store.py` |
| UT-Q18 | SDK Qdrant | source + `:memory:` | usa `qdrant_client`; sem httpx/requests | VS-05 / BDD-024 | `test_qdrant_store.py` |
| UT-Q19 | dois chunk_ids | upsert A+B | search encontra ambos | point id distinto | `test_qdrant_store.py` |
| UT-Q20 | falha SDK Qdrant | client stub raises | `VectorStoreError` (não Validation/Dimension) | §3.10 / §6 | `test_qdrant_store.py` |
| UT-Q21 | `delete_paths` por commit | same path em oldsha+newsha; delete newsha | só newsha some; oldsha permanece | §3.9 ENG-012 | `test_qdrant_store.py` |
| UT-EM01 | batch vazio | `embed(())` | `()`; stub sem `create` | VS-12 | `test_embedder.py` |
| UT-EM02 | whitespace / vazio | `"   "` / `""` / misto | `EmbeddingValidationError`; sem `create` | VS-12 | `test_embedder.py` |
| UT-EM03 | happy path ordem | 2 textos | len=2; ordem; dim ok | §3.8 | `test_embedder.py` |
| UT-EM04 | dim mismatch retorno | stub dim≠configured | `EmbeddingValidationError` | §3.7 | `test_embedder.py` |
| UT-EM05 | falha SDK | stub raises | `EmbeddingError` | §3.7 | `test_embedder.py` |
| UT-EM06 | sem chat | source inspect | sem `chat.completions` | VS-06 / I-T13-009 | `test_embedder.py` |
| UT-EM07 | `dimensions` property | ctor dimensions=4 | `embedder.dimensions == 4` | §3.11 | `test_embedder.py` |
| UT-EM08 | model no create | happy path | `create` recebe `model=` | VS-06 | `test_embedder.py` |

## Extremos / concorrência / idempotência

| ID | Caso | Esperado | Arquivo |
|---|---|---|---|
| UT-X01 | point id estável (mesmo repo/commit/chunk_id) | 2ª upsert sobrescreve; 1 hit | `test_qdrant_store.py` (UT-Q12) |
| UT-X02 | point id muda com commit_sha | old+new coexist até purge | UT-Q13 |
| UT-X03 | metadata keywords/symbols `()` | aceito no upsert | UT-Q14 |
| UT-X04 | embedder: texto válido após batch vazio | stub chamado só no válido | `test_embedder.py` |
| UT-X05 | delete_paths não cruza commit_sha | UT-Q21 | `test_qdrant_store.py` |
| UT-X06 | SDK Qdrant falha tipada | UT-Q20 | `test_qdrant_store.py` |

## Fixtures

- `QdrantClient(":memory:")` — SDK oficial; sem Docker.
- Vetores normalizados `_VECTOR_SIZE=4`.
- `OpenAICompatibleEmbedder` + `MagicMock` client (`embeddings.create`).
- Stub `MagicMock` de `QdrantClient` para falha SDK (UT-Q20).
- `SemanticChunk` / `ChunkMetadata` manuais (T12 ausente).

## Red esperado

Antes da implementação, imports de `github_rag.index.vector.*` falham (`ModuleNotFoundError` / `ImportError`). Deps `qdrant-client` / `openai` ficam para o Developer — testes de adaptador podem falhar no import do SDK.

```bash
.venv/bin/python -m pytest tests/unit/index/vector -q
```
