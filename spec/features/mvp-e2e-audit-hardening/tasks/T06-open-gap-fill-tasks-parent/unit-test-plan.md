# Unit-test plan — T06-open-gap-fill-tasks-parent

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T06-open-gap-fill-tasks-parent` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Interfaces base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Natureza | Documental — **sem** unitários em `src/`; contratos via BDD GAP-01..12 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Corners via GAP-01..12; sem `src/`; cobertura global ≥95% sem código novo de produto. |

## 1. Escopo de testes

| Camada | Arquivo | Papel |
|---|---|---|
| BDD contrato | `tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py` | GAP-01..12 — existência, superfícies, classificação, browser, lacunas, denylist, BDD-015, T22, ordem, sanitização, ENG-010 |
| Unitários `src/` | — | N/A (I-T06-003 / D-T06-006) |

## 2. Cenários extremos / corner cases (via BDD)

| ID | Corner | Como coberto |
|---|---|---|
| C-01 | Artefatos ausentes | RED pré-implementação |
| C-02 | UI sem menção a browser | GAP-05 |
| C-03 | UI só API como suficiente | GAP-05 (API insuficiente) |
| C-04 | Lacuna inventário omitida | GAP-06 parse inventário |
| C-05 | Denylist 003/006/013/024 omitida | GAP-07 |
| C-06 | Task BDD-015 inventada | GAP-08 |
| C-07 | gap-tooling / duplicata T22 | GAP-09 |
| C-08 | Índice sem ref T05/falhas | GAP-10 |
| C-09 | Leak de token | GAP-11 |
| C-10 | Claim de keywords na filha / omissão escopo | GAP-12 |
| C-11 | Classificação só `produto` sem gap | GAP-04 |
| C-12 | Superfície sdk omitida | GAP-03 |

## 3. Entradas inválidas / estados vazios

- Índice vazio ou só título → falha GAP-03..10.
- T23 sem browser → GAP-05.
- Ausência total → GAP-01/02.

## 4. Concorrência / idempotência

N/A — artefatos estáticos versionados; reabrir T06 = editar Markdown, sem estado runtime.

## 5. Falhas e regressão

- Não enfraquecer asserts GAP-05/06/09/12 para obter verde.
- Não criar gap-tooling para “passar” T22.
- Cobertura global do projeto permanece ≥95% (sem código novo em `src/`; impacto = só testes BDD).

## 6. Demonstração RED

```bash
python -m pytest tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py -q --no-cov
# esperado pré-artefatos: 12 failed
```

Evidência: registrada em `bdd.md` (RED).
