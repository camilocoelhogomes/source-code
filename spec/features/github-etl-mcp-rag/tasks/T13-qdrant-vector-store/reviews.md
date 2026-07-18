# Reviews — T13-qdrant-vector-store

## Review — Design (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Escopo T13 (VectorStore + Embedder; sem chunking/SLM/UI/MCP) | OK | §1 fora de escopo; D-T13-011 |
| DEC-004 — Qdrant como store | OK | §3, §4.9 |
| DEC-015 / BR-023 / BDD-024 — só `qdrant-client` + `openai` | OK | §4.5–4.6, §4.9–4.10, D-T13-003 |
| DEC-003 — não redefine unidade de chunk | OK | §3.1, §4.2, D-T13-011 |
| BR-010 — metadados no payload; Embedder ≠ MetadataGenerator | OK | §4.1, §4.5, D-T13-002, D-T13-010 |
| BR-011 — search devolve evidências | OK | §4.4 `SemanticHit`, §5 |
| Contrato enriquecido estável sem T12 na branch | OK | `ChunkMetadata` + `EnrichedChunk` §4.1–4.2, D-T13-001 |
| Reindex substitui commit anterior | OK | `replace_repo_commit` §4.6, D-T13-004 |
| Payload chunk Tree-sitter + metadata SLM | OK | §4.8 |
| Estratégia de teste (fake / SDK `:memory:`) | OK | §11, D-T13-009 |
| Handoff T14/T16 + ENG-012 paths | OK | §4.6 `delete_paths`, §16 |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING`, `MAJOR` ou `SUGGESTION` | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.0. Prosseguir para BDD (QA) e interfaces sem alteração de escopo.

---

## QA — BDD red (v0.1.0)

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Artefato | `bdd.md` + `tests/bdd/test_qdrant_vector_store.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `TESTS_READY_FOR_REVIEW` |

### Cenários

VS-01..VS-13 — BDD-010 (persistência + search), BDD-024 (`qdrant-client` / `openai`), reindex `replace_repo_commit`, invariantes de upsert, purge/empty replace/dimensão/delete/filtro/idempotência/Embedder corners.

### RED

`pytest tests/bdd/test_qdrant_vector_store.py` falha na coleta com `ModuleNotFoundError: No module named 'github_rag.index.vector.types'` (API de produção ainda inexistente) — esperado nesta etapa.

---

## Review — BDD (v0.1.0 → v0.1.1)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `tests/bdd/test_qdrant_vector_store.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| BDD-010 — persistência chunk+metadata + search relacionado | OK | VS-01, VS-02 (v0.1.1 ranges em VS-01) |
| BDD-024 — `qdrant-client` + `openai`; sem HTTP caseiro | OK | VS-05, VS-06 |
| DEC-003 / ENG-008 — sem redefinir chunk | OK | VS-14 (adicionado v0.1.1) |
| Reindex substitui commit anterior | OK | VS-03, VS-07, VS-08 |
| Invariantes payload / erros tipados | OK | VS-04, VS-09 |
| Ports alinhadas ao design (`replace`, `delete_*`, filtro) | OK | VS-10, VS-11, VS-13 |
| Embedder corners no adaptador real (não fake circular) | OK | VS-12 → `OpenAICompatibleEmbedder` + stub |
| Fixtures `:memory:` / sem implementação prematura além do RED | OK | imports de produção; sem corpo de adaptador nos testes |

### Achados (v0.1.0) — corrigidos em v0.1.1

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | VS-01 não assertava `start_byte`/`end_byte`/`start_point`/`end_point` do payload §4.8 | `test_qdrant_vector_store.py` VS-01; design §4.8 | Reidratar e comparar ranges/points | Corrigido VS-01 |
| `MAJOR` | VS-12 testava só `FakeEmbedder` definido no próprio teste (auto-cumprimento) | bdd VS-12 v0.1.0; teste circular | Exercitar `OpenAICompatibleEmbedder` + stub; assert sem `embeddings.create` | Corrigido VS-12 |
| `MAJOR` | DEC-003/ENG-008 listado no design §3.1 sem cenário BDD | design §3.1; bdd v0.1.0 | Cenário: sem params de chunking; unidade = `EnrichedChunk`/`SemanticChunk` | Corrigido VS-14 |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — bdd.md v0.1.1 + testes alinhados. Prosseguir para interfaces.

---

## Review — Interfaces (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Ports `VectorStore` / `Embedder` com responsabilidade e motivo | OK | §3.8, §3.9 |
| Types frozen alinhados ao design §4.1–4.4 | OK | §3.1–3.5; I-T13-002/003 |
| Erros tipados VS-04/VS-09/VS-12 | OK | §3.6, §3.7; I-T13-006 |
| Assinaturas = design + BDD (`replace`, `delete_*`, stub ctor embedder) | OK | §3.9–3.11 |
| DEC-003 / sem chunking params | OK | I-T13-007; §3.8–3.9 |
| BDD-024 / BR-023 SDKs oficiais | OK | I-T13-008/009; §3.10–3.11 |
| Payload §4.8 / VS-01 | OK | §4; I-T13-011 |
| Comentários RESPONSABILIDADE / MOTIVO em cada contrato | OK | §3.1–3.11 |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING`, `MAJOR` ou `SUGGESTION` | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces.md v0.1.0. Prosseguir para testes unitários (QA).

---

## Review — Unit tests (v0.1.0 → v0.1.1)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` + `tests/unit/index/vector/` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Contratos frozen / composição / hierarquia erros | OK | UT-T01–T07, UT-E01–E04 |
| Ports runtime_checkable + sem chunking | OK | UT-P01–P04 |
| Store: payload, ranking, replace, purge, delete, filter, idempotência | OK | UT-Q01–Q19 |
| Embedder: vazio, blank, ordem, dim, SDK, sem chat | OK | UT-EM01–EM08, UT-X04 |
| Falhas tipadas SDK Qdrant | OK | UT-Q20 (v0.1.1) |
| `delete_paths` escopado por commit | OK | UT-Q21 (v0.1.1) |
| Scope inválido além de upsert | OK | UT-Q17 expandido (v0.1.1) |
| API alinhada a interfaces (sem divergência) | OK | assinaturas / keyword ctor |
| Não enfraquece BDD VS-01..VS-14 | OK | unitários aprofundam; BDD permanece |

### Achados (v0.1.0) — corrigidos em v0.1.1

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | Sem UT de falha SDK Qdrant → `VectorStoreError` (assimétrico a UT-EM05) | interfaces §3.10; plan v0.1.0 | Stub client raises → `VectorStoreError` | Corrigido UT-Q20 |
| `MAJOR` | `delete_paths` “escopo por commit” sem corner (mesmo path em 2 commits) | interfaces §3.9 | delete newsha não remove oldsha | Corrigido UT-Q21 |
| `SUGGESTION` | UT-Q17 só validava scope em `upsert` | §3.3 | Validar purge/replace/delete_paths | Corrigido UT-Q17 |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — unit-test-plan.md v0.1.1 + testes alinhados. Prosseguir para implementação (Developer).

---

## QA — unit-test-plan RED (v0.1.0)

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Artefato | `unit-test-plan.md` + `tests/unit/index/vector/` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `TESTS_READY_FOR_REVIEW` |

### Cobertura do plano

| Grupo | IDs | Arquivo |
|---|---|---|
| Types frozen / composição | UT-T01..UT-T07 | `test_types.py` |
| Erros tipados | UT-E01..UT-E04 | `test_errors.py` |
| Ports Protocol | UT-P01..UT-P04 | `test_ports.py` |
| QdrantVectorStore | UT-Q01..UT-Q19 + no-chunking | `test_qdrant_store.py` |
| OpenAICompatibleEmbedder | UT-EM01..UT-EM08 + UT-X04 | `test_embedder.py` |

Extremos: validation, dimensions, empty texts/batch/replace, purge escopado, idempotência point id, payload schema, search filters, SDK conformity (`qdrant_client` / `openai`, embedder sem chat).

### RED

```bash
.venv/bin/python -m pytest tests/unit/index/vector -q
```

Falha na coleta com `ModuleNotFoundError: No module named 'github_rag.index.vector.types'` (API de produção ainda inexistente além do placeholder `__init__.py`) — esperado nesta etapa. Deps `qdrant-client`/`openai` deixadas para o Developer.

---

## Review — Implementação

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `src/github_rag/index/vector/*` + `pyproject.toml` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Contratos types/errors/ports = interfaces | OK | `types.py`, `errors.py`, `ports.py` |
| `QdrantVectorStore` assinaturas + Cosine + payload §4.8 | OK | `qdrant_store.py` `_to_point` / `_hit_from_payload` |
| Point id UUID v5 (`repo\0commit\0chunk`) | OK | `_POINT_ID_NAMESPACE` + `_point_id` |
| `replace_repo_commit` = upsert + purge | OK | `qdrant_store.py` L110–114 |
| `delete_paths` escopado repo+commit+path | OK | Filter must com três FieldCondition |
| SDK só `qdrant-client` / `openai` (deps no pyproject) | OK | imports; `pyproject.toml` L23–24 |
| Embedder sem chat/completions; só `embeddings.create` | OK | `embedder.py` |
| Sem chunking / geração de metadata | OK | módulo só consome `EnrichedChunk` |
| Erros tipados + mapeamento SDK | OK | `VectorStoreError` / `EmbeddingError` wraps |
| Validação scope/record/dimensão | OK | `_validate_scope` / `_validate_record` |
| BDD + unitários verdes | OK | 62 passed (pytest) |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — implementação conforme design/interfaces. Prosseguir para Blue (refactor).
