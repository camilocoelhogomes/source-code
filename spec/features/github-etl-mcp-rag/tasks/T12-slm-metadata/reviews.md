# Reviews — T12-slm-metadata

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
| Escopo T12 (metadados SLM; sem MCP/Qdrant/orquestração) | OK | §1 fora de escopo; §15 handoff |
| DEC-015 / BR-023 / BDD-024 — SDK `openai` | OK | §4.4; D-T12-002; §8 |
| DEC-006 / BR-009 — default Qwen Coder 3B + abstração | OK | §4.4 modelo; D-T12-001; D-T12-004 |
| Entrada = um `SemanticChunk` (T11); per-chunk | OK | §4.1; §4.3; D-T12-003 |
| Saída serializável para T13 | OK | §4.2 `ChunkMetadata` + `to_payload()`; D-T12-005 |
| BR-010 — não inventar chunks; não prosa MCP | OK | §2; §13; D-T12-007; handoff T17 |
| Erros tipados para T14 / BR-005 | OK | §6; D-T12-006 |
| Aceite: fake per-chunk + falha no meio da lista | OK | §9; D-T12-008 |
| Seções obrigatórias (contexto→rollback + D-T12-*) | OK | §1–§12 |

### Achados na redação (corrigidos antes da aprovação)

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | Campo `raw: dict` em dataclass frozen quebra imutabilidade do contrato T13 | rascunho §4.2 | Substituir por `extra` imutável (pares escalares) | Corrigido §4.2 |
| `SUGGESTION` | Task brief cita `qwen.py`; adaptador é OpenAI-compatible genérico | T12-slm-metadata.md arquivos | Nome `openai_slm.py` alinhado a DEC-015 | Aceito §14 |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.0. Prosseguir para BDD/interfaces (QA) sem alteração de escopo.

---

## Review — BDD / Interfaces / Unit-test-plan (v0.1.0) — prontos para Architect

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `READY_FOR_ARCHITECT_REVIEW` |

### Artefatos entregues

| Artefato | Caminho | Estado |
|---|---|---|
| BDD cenários | `bdd.md` | `READY_FOR_ARCHITECT_REVIEW` |
| Interfaces | `interfaces.md` | `READY_FOR_ARCHITECT_REVIEW` |
| Plano unitário | `unit-test-plan.md` | `READY_FOR_ARCHITECT_REVIEW` |
| BDD executável | `tests/bdd/test_slm_metadata.py` | RED (impl ausente) |
| Unitários | `tests/unit/index/metadata/` | RED (impl ausente) |

### Cobertura de aceite (QA)

| Critério | Cenários / casos |
|---|---|
| BDD-007 (N→N metadados) | MD-01; UT-F01 |
| Aceite fake per-chunk | MD-02; UT-F01 |
| Aceite falha tipada no meio da lista | MD-03; UT-F02 |
| BDD-010 (payload serializável) | MD-04; UT-T02 |
| BDD-024 (SDK `openai`) | MD-05; UT-O09 |
| Default Qwen Coder 3B | MD-06; UT-C01; UT-O06 |
| BR-009 troca de provedor | MD-07; UT-P01 |
| BR-010 sem inventar chunks / sem MCP | MD-08; UT-F04; UT-O08 |
| Erros tipados / config | MD-09; MD-10; UT-E*; UT-O02..07 |

### Nota ao Architect

Artefatos BDD, interfaces e unit-test-plan estão prontos para review. **Não marcados como APPROVED** — decisão cabe ao Architect. Testes RED devem falhar por `ImportError`/`ModuleNotFoundError` (módulos de produção ainda não existem além do stub T01).

---

## Review — BDD / Interfaces / Unit-test-plan (v0.1.0 → v0.1.1)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `interfaces.md` + `unit-test-plan.md` + `tests/bdd/test_slm_metadata.py` + `tests/unit/index/metadata/*` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Alinhamento design APPROVED + BR-009/010/023, DEC-006/015, BDD-007/010/024 | OK | MD-01..10; I-T12-001..008; matriz UT |
| Interfaces com responsabilidade + motivo da separação | OK | §3.1–§3.7 em cada contrato |
| Assinatura `generate(chunk)` per-chunk | OK | MD-08; UT-P02; porta Protocol |
| SDK `openai` / proibido HTTP caseiro | OK | MD-05; UT-O09 |
| Erros tipados + FakeMetadataGenerator | OK | §3.3/§3.7; MD-03/09/10; UT-E*/F*/O* |
| Extremos / corners cobertos | OK | UT-X01..X06; UT-O02..07; summary vazio/whitespace |
| RED sem implementação | OK | 7× `ModuleNotFoundError` em `github_rag.index.metadata.*` (collection) |

### Achados corrigidos nesta review (v0.1.1)

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | Validação do construtor ambígua com `settings=None` + client injetado (UT-P01 vs MD-10) | `interfaces.md` §3.6 v0.1.0; `test_ports.py` | Regras explícitas: settings presente → validar; client-only → defaults sem `base_url`; ambos None → `MetadataConfigError` | Corrigido §3.6 |
| `MAJOR` | UT-E02 exige `chunk_id`/`path` em `str(erro)` sem contrato | `test_errors.py`; `interfaces.md` §3.3 | Documentar representação textual com ids | Corrigido §3.3 |
| `SUGGESTION` | MD-04/UT-T02 não assertavam `intent` no payload | BDD-010 / design §4.2 | Incluir `intent` no payload esperado | Corrigido MD-04 + testes |
| `SUGGESTION` | UT-E03 fraco (secret nunca no message) | `test_errors.py` | Hint do campo `api_key` + `hasattr` False | Corrigido |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — bdd/interfaces/unit-test-plan v0.1.1 e testes RED. Prosseguir para implementação (Developer) sem alteração de escopo. Produção **não** implementada nesta etapa.