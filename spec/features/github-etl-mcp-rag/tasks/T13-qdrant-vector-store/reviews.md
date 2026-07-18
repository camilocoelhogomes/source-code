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
