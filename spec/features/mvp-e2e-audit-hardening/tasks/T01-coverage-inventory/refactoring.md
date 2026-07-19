# Refatoração Blue — T01-coverage-inventory

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T01-coverage-inventory` |
| Autor | Tech Lead Architect (+ Developer N/A) |
| Data | 2026-07-18 |
| Branch | `feature/mvp-e2e-audit-hardening-T01-coverage-inventory` |
| Tip baseline | `97e6ea8` (pós `ARCHITECT_IMPLEMENTATION`) |
| Natureza | Task **100% documental** (D-T01-001) |

## 1. Escopo Blue

Avaliar simplificação do artefato `CoverageInventory` e do helper de teste `tests/unit/audit/inventory_schema.py` **sem** alterar contratos, comportamento, schema §6 ou cobertura de asserts.

## 2. Baseline (antes)

| Métrica | Valor | Como reproduzir |
|---|---|---|
| Testes T01 (BDD + unit schema) | **30 passed** | `/Users/camilocoelhogomes/projects/github_rag/.venv/bin/python -m pytest tests/bdd/test_mvp_e2e_audit_coverage_inventory.py tests/unit/audit/ -q --cov-fail-under=0` |
| Artefato | `audit/coverage-inventory.md` — 23 linhas, denylist/UI ok | inspeção estática |
| Helper | `inventory_schema.py` — parser + `validate_coverage_inventory` | somente `tests/unit/audit/` |
| Produto / e2e | intocado | — |

Nota: `fail-under=95` do projeto reporta 0% cov porque T01 não importa `github_rag` — esperado; não é regressão desta task.

## 3. Análise de complexidade / performance

| Candidato | Evidência | Decisão |
|---|---|---|
| Matriz Markdown | Tabela única, schema congelado, handoff T06 claro | **Sem mudança** — já mínimo para SoT |
| `inventory_schema.py` | ~190 LOC; parse linear; sem I/O além de leitura do canônico | **Sem mudança** — sem gargalo; extrair mais módulos aumentaria indirection |
| Fixtures UT-P* | strings markdown longas | **Sem mudança** — refactor cosmético não reduz complexidade real nem melhora reprodução |
| S-UT-01 (parametrizar denylist 013/024) | suggestion anterior | **Fora de Blue** — expansão de testes, não simplificação |

Não há alegação de performance a provar (artefato documental; validação é parse de texto em ms).

## 4. Resultado Blue

| Item | Resultado |
|---|---|
| Diff de código/artefato | **N/A** — nenhuma alteração |
| Contratos / comportamento | inalterados |
| Testes após Blue | baseline permanece **30 passed** (sem reexecução obrigatória além da confirmação A; re-run opcional idêntico) |
| Meta de simplificação | atingida por **não** introduzir abstração especulativa |

## 5. Decisão

`BLUE_APPROVED_BY_ARCHITECT` — task documental; otimização/refatoração N/A com baseline registrado.
