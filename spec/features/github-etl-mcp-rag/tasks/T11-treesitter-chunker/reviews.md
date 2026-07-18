# Reviews — T11-treesitter-chunker

## Review — Design (v0.1.0 → v0.1.1)

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
| Escopo T11 (só chunker; sem SLM/Qdrant/Zoekt/T14) | OK | §1 fora de escopo; §5 handoff |
| DEC-003 / ENG-008 — sem chunk por tamanho/linhas | OK | §3 fluxo erro; D-T11-001; §4.4 root estrutural |
| DEC-015 / BR-023 / BDD-024 — SDK oficial + grammars | OK | §3, §4.7, §8; D-T11-002 |
| Erros tipados alinhados a BR-005 | OK | §3, §6; subclasses de `ChunkingError` |
| Contrato estável T12/T13/T14 | OK | `SemanticChunk` §4.3; `chunk_id` §4.3.1; `len>=1` |
| Corner cases DoD (vazio, binário, grammar) | OK | §3 fluxo erro; §4.6; §6 |

### Achados (v0.1.0) — corrigidos em v0.1.1

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | Política de nós aninhados/overlap/dedupe ausente — ambígua para N chunks SLM/Qdrant | design v0.1.0 §4.4 | Definir: ranges distintos → ambos; range idêntico → dedupe; ordem determinística | Corrigido §4.4.1 / D-T11-008 |
| `MAJOR` | `chunk_id` “hash determinístico” sem algoritmo/canônico | design v0.1.0 §4.3 | SHA-256 hex de payload canônico | Corrigido §4.3.1 / D-T11-004 |
| `MAJOR` | `ParseFailureError` vs nós `ERROR` do Tree-sitter indefinido | design v0.1.0 §6 | ERROR não falha sozinho; falha só se não materializar chunk | Corrigido §4.8 / D-T11-009 |
| `MAJOR` | `.tsx` mapeado a typescript sem variante Language | design v0.1.0 §4.2 | Registry resolve `language_tsx` vs `language_typescript` | Corrigido §4.2 / §4.7 / D-T11-010 |
| `SUGGESTION` | Diagrama §3 citava `bytes\|str` inconsistente com `content: bytes` | design v0.1.0 §3 | Unificar em `bytes` | Corrigido §3 |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.1. Prosseguir para BDD/interfaces (QA) sem alteração de escopo.
