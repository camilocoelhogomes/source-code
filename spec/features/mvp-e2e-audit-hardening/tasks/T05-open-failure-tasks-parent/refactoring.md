# Refatoração Blue — T05-open-failure-tasks-parent

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T05-open-failure-tasks-parent` |
| Autor | Developer / Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |

## 0. Histórico

| Data | Autor | Decisão | Observações |
|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `BLUE_APPROVED_BY_ARCHITECT` | Superfície 100% documental; baseline código N/A; sem simplificação obrigatória. |

## 1. Baseline

| Métrica | Valor | Evidência |
|---|---|---|
| Natureza | Documental (D-T05-005 / ENG-010) | Índice + T22; sem módulo novo em `src/` |
| Diff produto/tooling | N/A | Sem alteração `src/github_rag/**`, `e2e/robot/**`, `docker-compose*.yml` |
| BDD contrato | 10 passed | `pytest tests/bdd/test_mvp_e2e_audit_failure_backlog.py -q --no-cov` |
| Runtime hot path | N/A | Nenhum código de produção alterado |
| Performance | N/A | Sem hot path mensurável nesta task |

## 2. Análise Blue

| Candidato | Avaliação | Ação |
|---|---|---|
| Implementar fix zoekt/compose nesta feature | Viola ENG-010 / ownership T22 no pai | Não fazer |
| Extrair schema YAML/JSON do índice | Over-engineering para backlog Markdown único | Não fazer |
| Duplicar tabela F-T04-* entre índice e T22 | Intencional (índice SoT local + task acionável no pai) | Manter |
| Enxugar markdown do índice/T22 | Já mínimo para FAIL-01..10 + handoff T06/T07 | Nenhuma mudança |

**Conclusão:** Blue N/A — sem complexidade de runtime; simplificação documental adicional não melhora legibilidade sem risco de enfraquecer asserts BDD.

## 3. Resultado pós-Blue

Sem diff adicional. Contratos e BDD mantidos (`10 passed`).

## 4. Rollback

Reverter `audit/failure-backlog-index.md` + `T22-fix-tooling-e2e-compose-zoekt.md` + `tests/bdd/test_mvp_e2e_audit_failure_backlog.py` (e specs T05 associadas).
