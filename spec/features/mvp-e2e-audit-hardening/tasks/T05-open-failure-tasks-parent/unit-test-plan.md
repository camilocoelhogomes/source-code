# Unit-test plan — T05-open-failure-tasks-parent

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T05-open-failure-tasks-parent` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Interfaces base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Natureza | Documental — **sem** unitários em `src/`; contratos via BDD FAIL-01..10 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Review formal: corners via FAIL-01..10; sem `src/`; S-01 FAIL-05 opcional. Estado confirmado. |

## 1. Escopo de testes

| Camada | Arquivo | Papel |
|---|---|---|
| BDD contrato | `tests/bdd/test_mvp_e2e_audit_failure_backlog.py` | FAIL-01..10 — existência, superfície, classificação, evidência, zero pytest, sem phantoms, sanitização, ENG-010 |
| Unitários `src/` | — | N/A (I-T05-003 / D-T05-005) |

## 2. Cenários extremos / corner cases (via BDD)

| ID | Corner | Como coberto |
|---|---|---|
| C-01 | Artefatos ausentes | RED pré-implementação (AssertionError path) |
| C-02 | Classificação sem vínculo F-T04-* | FAIL-04 regex ID→classe |
| C-03 | Task health inventada | FAIL-07 glob T23/T2*-fix-health* |
| C-04 | Task pytest inventada | FAIL-06 glob T2*-fix-pytest* |
| C-05 | Superfícies robot unknown como “falha” | FAIL-08 + ponteiro T06 |
| C-06 | Leak de token | FAIL-09 |
| C-07 | Claim de fix na filha / omissão de escopo src/robot/compose | FAIL-10 |
| C-08 | Lista vazia pytest omitida | FAIL-06 exige menção zero/nenhuma |
| C-09 | F-T04-003 sem “consequência” | FAIL-04 |
| C-10 | Índice sem tooling-e2e | FAIL-03 |

## 3. Entradas inválidas / estados vazios

- Índice vazio ou só título → falha FAIL-03..08.
- T22 sem classificação combinada → FAIL-04.
- Ausência total → FAIL-01/02.

## 4. Concorrência / idempotência

N/A — artefatos estáticos versionados; reabrir T05 = editar Markdown, sem estado runtime.

## 5. Falhas e regressão

- Não enfraquecer asserts FAIL-04/07/10 para obter verde.
- Não criar T23 para “passar” health.
- Cobertura global do projeto permanece ≥95% (sem código novo em `src/`; impacto = só testes BDD).

## 6. Demonstração RED

```bash
python -m pytest tests/bdd/test_mvp_e2e_audit_failure_backlog.py -q --no-cov
# esperado pré-artefatos: 10 failed
```

Evidência: registrada em `bdd.md` (RED 10 failed).
