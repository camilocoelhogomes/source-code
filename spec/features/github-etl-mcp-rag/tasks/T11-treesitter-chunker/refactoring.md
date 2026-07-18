# Refatoração Blue — T11-treesitter-chunker

| Campo | Valor |
|---|---|
| Task | `T11-treesitter-chunker` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

## Baseline

| Item | Valor |
|---|---|
| Testes T11 | `56 passed, 14 subtests` (`tests/unit/index/chunk` + `tests/bdd/test_treesitter_chunker.py`) |
| Contratos | design/interfaces/BDD `0.1.1` aprovados; implementação `APPROVED_BY_ARCHITECT` |
| Escopo Blue | Simplificação / gargalos com evidência reproduzível — sem otimização especulativa |

## Avaliação

| Candidato | Evidência de gargalo? | Ação |
|---|---|---|
| Eager load de grammars em `OfficialGrammarRegistry.__init__` | Não — só observação de startup; sem benchmark before/after | Nenhuma mudança |
| DFS recursivo em `select_semantic_nodes` | Não — arquivos típicos de repo; REQ-019 aceita parse in-memory | Nenhuma mudança |
| Re-parse a cada `chunk()` | Não — contrato stateless; sem medição de hot path | Nenhuma mudança |

Módulos T11 já estão separados por responsabilidade (types / errors / ports / registry / selectors / adaptador). Não há complexidade desnecessária que justifique refactor estrutural sem alterar comportamento.

## Decisão

`BLUE_APPROVED_BY_ARCHITECT` — sem mudanças estruturais nesta etapa. Baseline = testes verdes + contratos preservados. Qualquer otimização futura exige comparação reproduzível before/after.
