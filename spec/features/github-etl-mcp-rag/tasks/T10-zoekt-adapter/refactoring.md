# Refactoring Blue — T10-zoekt-adapter

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T10-zoekt-adapter` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Baseline | Suite T10: **67 passed**; cobertura global projeto: **97%** (meta fail_under=95) |

## 1. Baseline (pré-Blue)

| Métrica | Valor |
|---|---|
| Testes T10 (unit `tests/unit/index/zoekt` + BDD `test_zoekt_adapter.py`) | 67 passed |
| Suite completa do projeto | 372 passed, 1 skipped, 161 subtests |
| Cobertura global (`fail_under=95`) | 97.52% |
| Pacote sob revisão | `src/github_rag/index/zoekt/` |

## 2. Análise (complexidade / performance)

| Candidato | Evidência | Decisão Blue |
|---|---|---|
| Extrair mais helpers de `ZoektExactCodeIndex` | Módulo já separa escape/query/map/snippet; ~125 stmts | Sem ganho claro de clareza |
| Remover `_git_index_bin` / `_git_workdir` | Campos reservados D-T10-001 (otimização opcional) | **Não remover** — quebraria superfície do construtor |
| Cache / pool HTTP | Sem evidência de gargalo; transporte stdlib fino | Otimização especulativa — proibida |
| Unificar Fake × Zoekt paths | Contratos distintos (DEC-016 / D-T10-005) | Fora de escopo Blue |

## 3. Mudanças aplicadas

**Sem mudança necessária.**

Justificativa: a implementação já é um adaptador fino (DEC-016) sobre HTTP/CLI oficiais, com separação porta/transporte alinhada a `interfaces.md`. Não há complexidade desnecessária mensurável nem gargalo de performance com evidência reproduzível. Alterações cosméticas não justificam risco de regressão de contrato.

A única correção pós-review de implementação (envelopar `OSError` de `unlink` em `ExactCodeIndexError`) é correção de contrato, não refatoração Blue.

## 4. Pós-Blue (validação)

| Check | Resultado |
|---|---|
| Suite T10 | 67 passed |
| Suite completa + cobertura | 372 passed, 1 skipped; **97.52%** (≥95%) |
| Contratos / comportamento | Inalterados (sem diff Blue de código) |

## 5. Decisão

`BLUE_APPROVED_BY_ARCHITECT` — baseline aceita; sem refatoração estrutural.
