# Reviews — T25-gap-negative-integral

## Review DESIGN v0.1.0 — Tech Lead Architect

| Data | Autor | Decisão |
|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` |

| Severidade | Achado | Evidência | Correção | Resultado |
|---|---|---|---|---|
| — | Escopo alinhado a inventário BDD-008/018/022 | design §1–3; T25.md | — | OK |
| — | Store mutável resolve wire-antes-sync | D-T25-001; §3.1 | — | OK |
| — | Browser residual explícito (T23) | D-T25-004 | — | OK |
| SUGGESTION | Documentar que payload-index permanece regressão | §3.4 | Já em design | OK |

**Gate:** avançar para `bdd.md`.

## Review BDD v0.1.0 — Tech Lead Architect

| Data | Autor | Decisão |
|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` |

| Severidade | Achado | Evidência | Correção | Resultado |
|---|---|---|---|---|
| — | NEG-01 cobre texto integral BDD-008 | bdd.md §2 | — | OK |
| — | NEG-02/03 alinhados a D-T25-* | bdd §3 | — | OK |
| — | NEG-04 não substitui CONFIG_PATH | bdd NEG-04 | — | OK |

**Gate:** avançar para `interfaces.md`.

## Review INTERFACES v0.1.0 — Tech Lead Architect

| Data | Autor | Decisão |
|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` |

| Severidade | Achado | Evidência | Correção | Resultado |
|---|---|---|---|---|
| — | Comentários de responsabilidade/separação presentes | I-T25-001..007 | — | OK |
| — | Store mutável + rota + probes cobrem NEG-* | interfaces §2–5 | — | OK |
| SUGGESTION | Default `issue_store=None` preserva T18 | I-T25-004 | Já documentado | OK |

**Gate:** avançar para unit-test-plan + testes.

## Review UNIT-TEST-PLAN + testes v0.1.0 — Tech Lead Architect

| Data | Autor | Decisão |
|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` |

| Severidade | Achado | Evidência | Correção | Resultado |
|---|---|---|---|---|
| — | Matriz UT-I/D/P cobre I-T25-* e extremos | unit-test-plan.md | — | OK |
| — | Falha pré-impl por `ModuleNotFoundError: github_rag.ui.issues` | pytest collection | — | OK (esperado) |
| — | NEG-01..03 BDD executáveis presentes | test_negative_integral.py | — | OK |

**Gate:** avançar para implementação TDD.

## Review IMPLEMENTAÇÃO — Tech Lead Architect

| Data | Autor | Decisão |
|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` |

| Severidade | Achado | Evidência | Correção | Resultado |
|---|---|---|---|---|
| BLOCKING | Probes em `github_rag.e2e` violavam UT-X04 | test_exports | Movidos para `e2e/probes/` | Corrigido |
| — | Store mutável pós-sync | runtime.py | — | OK |
| — | Sem secrets em probes/API | UT-P04 / NEG-* | — | OK |
| — | Suíte 1232 passed; cov 96.64% | pytest | — | OK |

**Gate:** Blue + docs.

## Review BLUE — Tech Lead Architect

| Data | Autor | Decisão |
|---|---|---|
| 2026-07-19 | Tech Lead Architect | `BLUE_APPROVED_BY_ARCHITECT` |

| Severidade | Achado | Resultado |
|---|---|---|
| — | Sem gargalo mensurável; `${CURDIR}` estável | OK |

**Gate:** changelog + PR.
