# Refatoração Blue — T11-treesitter-chunker

| Campo | Valor |
|---|---|
| Task | `T11-treesitter-chunker` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

## Baseline (v0.1 — pré-config)

| Item | Valor |
|---|---|
| Testes T11 | `56 passed, 14 subtests` (`tests/unit/index/chunk` + `tests/bdd/test_treesitter_chunker.py`) |
| Contratos | design/interfaces/BDD `0.1.1` aprovados; implementação `APPROVED_BY_ARCHITECT` |
| Escopo Blue | Simplificação / gargalos com evidência reproduzível — sem otimização especulativa |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` — sem mudanças estruturais |

## Baseline (v0.2 — pós-config / commit `1d0a37b`)

| Item | Valor |
|---|---|
| Suite global | `594 passed, 1 skipped` |
| Cobertura global | `98.51%` (≥95%) |
| Módulos chunk | ≥98% (`node_selectors` 98%; demais 100%) |
| Contratos | design/interfaces/BDD v0.2.x aprovados; implementação config `APPROVED_BY_ARCHITECT` |
| Escopo Blue | Simplificação / gargalos com evidência reproduzível — sem otimização especulativa |

## Avaliação (v0.2)

| Candidato | Evidência de gargalo? | Ação |
|---|---|---|
| Eager load de grammars em `OfficialGrammarRegistry.__init__` (agora + yaml/json/xml/toml) | Não — só observação de startup; sem benchmark before/after | Nenhuma mudança |
| DFS recursivo em `select_semantic_nodes` | Não — arquivos típicos de repo; REQ-019 aceita parse in-memory | Nenhuma mudança |
| Re-parse a cada `chunk()` | Não — contrato stateless; sem medição de hot path | Nenhuma mudança |
| Duplicação de prioridades `_KIND_PRIORITY` vs alvos config | Não — tabela explícita e legível; extrair helper não muda comportamento | Nenhuma mudança |

Módulos T11 permanecem separados por responsabilidade (types / errors / ports / registry / selectors / adaptador). Ampliação v0.2 adicionou ramos mínimos no enum, mapa de extensões, `_language_ptr` e `_TARGETS` — sem complexidade desnecessária que justifique refactor estrutural.

## Decisão

`BLUE_APPROVED_BY_ARCHITECT` — sem mudanças de código nesta etapa. Baseline reproduzível = `594 passed, 1 skipped` + cobertura `98.51%` + contratos v0.2 preservados. Qualquer otimização futura (ex.: lazy grammar cache) exige comparação before/after reproduzível.
