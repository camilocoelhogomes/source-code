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
