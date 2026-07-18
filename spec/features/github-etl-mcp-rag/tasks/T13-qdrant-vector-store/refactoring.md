# Refatoração Blue — T13-qdrant-vector-store

| Campo | Valor |
|---|---|
| Task | `T13-qdrant-vector-store` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

## Baseline (antes do Blue)

| Item | Valor |
|---|---|
| Testes T13 | `62 passed, 23 subtests` (`tests/unit/index/vector` + `tests/bdd/test_qdrant_vector_store.py`) |
| Suíte projeto | cobertura ≥95% (gate `fail_under`) |
| Contratos | design `0.1.0` / interfaces `0.1.0` / BDD `0.1.1` / unit-plan `0.1.1`; implementação `APPROVED_BY_ARCHITECT` |
| Escopo Blue | Simplificação / gargalos com evidência reproduzível — sem otimização especulativa |

## Avaliação de gargalos

| Candidato | Evidência de gargalo? | Ação |
|---|---|---|
| k-NN / upsert em `:memory:` ou Qdrant remoto | Não — sem requisito de latência no MVP; sem benchmark before/after | Nenhuma otimização de performance |
| Batch embeddings / tamanho de payload | Não — volume depende de T14/orquestração; sem medição | Nenhuma mudança |
| Índices de payload Qdrant (`repo_id`/`commit_sha`/`path`) | Design recomenda; ganho só em escala — sem comparação reproduzível | Adiar (T19/ops) — **depois promovido por pedido humano (PR #13); ver delta abaixo** |

Não há gargalo mensurável no MVP que justifique mudança de algoritmo ou I/O.

## Simplificações aplicadas (sem mudança de contrato)

| Mudança | Motivo | Arquivo |
|---|---|---|
| Extrair `_invoke` para mapear exceções SDK → `VectorStoreError` | Remove try/except duplicado em upsert/purge/delete/search | `qdrant_store.py` |
| `search` via generator expression para hits | Menos boilerplate; mesma reidratação | `qdrant_store.py` |
| Remover `except EmbeddingError: raise` morto antes do wrap genérico | Client OpenAI não levanta `EmbeddingError` nosso | `embedder.py` |

## Resultados (depois)

| Item | Valor |
|---|---|
| Testes T13 (`--no-cov`) | `62 passed, 23 subtests` |
| Suíte completa + cov | `442 passed, 1 skipped, 198 subtests`; cobertura total `98.49%` (≥95%) |
| Contratos / comportamento | Preservados (mesmos asserts BDD/unit) |

## Decisão (Blue inicial)

`BLUE_APPROVED_BY_ARCHITECT` — simplificação estrutural mínima; sem otimização de performance especulativa. Qualquer ganho futuro de latência/throughput exige comparação reproduzível before/after.

---

## Delta Blue — payload indexes (PR #13, 2026-07-18)

| Campo | Valor |
|---|---|
| Motivo | Pedido humano no PR #13 (não otimização especulativa Blue) |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

### Promoção do adiamento

| Item | Antes | Depois |
|---|---|---|
| Índices `repo_id`/`commit_sha`/`path` | Adiado (T19/ops) | **Implementados** no setup via `create_payload_index` KEYWORD |

### Simplificação Blue do delta

| Mudança | Motivo | Arquivo |
|---|---|---|
| Agrupar imports do pacote e constantes após imports | Achado SUGGESTION Architect (ordem de imports) | `qdrant_store.py` |

### Baseline / resultados (delta)

| Item | Valor |
|---|---|
| Testes Qdrant store | `35 passed` (+ UT-Q22..Q25) |
| BDD T13 | `16 passed` |
| Contratos | design `0.1.1` / interfaces `0.1.1` / unit-plan `0.1.2` |

### Decisão

`BLUE_APPROVED_BY_ARCHITECT` — índices promovidos por requisito humano; Blue limitado a ordem de imports; sem mudança de contrato da porta.
