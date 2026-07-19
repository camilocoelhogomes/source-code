# Unit-test plan — T07-consolidate-evidence-close

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T07-consolidate-evidence-close` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `DRAFT` |
| Versão | `0.1.0` |
| Interfaces base | `0.1.0` |
| Natureza | Documental — **sem** unitários em `src/`; contratos via BDD CLOSE-01..12 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| — | — | pendente | `0.1.0` | Aguarda review Architect. |

## 1. Escopo de testes

| Camada | Arquivo | Papel |
|---|---|---|
| BDD contrato | `tests/bdd/test_mvp_e2e_audit_closure_pack.py` | CLOSE-01..12 — existência, links T01–T06, T22–T27, ordem, métricas, anti-MVP, sanitização, ENG-010 |
| Unitários `src/` | — | N/A (I-T07-003 / D-T07-005) |

## 2. Cenários extremos / corner cases (via BDD)

| ID | Corner | Como coberto |
|---|---|---|
| C-01 | Pacote ausente | RED pré-implementação CLOSE-01 |
| C-02 | Omite inventário T01 | CLOSE-02 |
| C-03 | Omite HITL T02 | CLOSE-03 |
| C-04 | Omite run pytest T03 | CLOSE-04 |
| C-05 | Omite run e2e T04 | CLOSE-05 |
| C-06 | Omite T22 / failure index | CLOSE-06 |
| C-07 | Omite T23–T27 / gap index | CLOSE-07 |
| C-08 | Sem ordem run-first→gap-fill | CLOSE-08 |
| C-09 | Métricas / BR-005 incompletos | CLOSE-09 |
| C-10 | Declara MVP entregue / omite CLOSURE_READY | CLOSE-10 |
| C-11 | Leak de token | CLOSE-11 |
| C-12 | Claim de fix na filha / omissão escopo | CLOSE-12 |

## 3. Entradas inválidas / estados vazios

- Pacote vazio ou só título → falha CLOSE-02..12.
- Ausência total → CLOSE-01.

## 4. Concorrência / idempotência

N/A — artefato estático versionado; reabrir T07 = editar Markdown.

## 5. Falhas e regressão

- Não enfraquecer asserts CLOSE-10 (anti-MVP) / CLOSE-12 (ENG-010) para obter verde.
- Não implementar T22–T27 para “passar” o pacote.
- Cobertura global do projeto permanece ≥95% (sem código novo em `src/`).

## 6. Demonstração RED

```bash
python -m pytest tests/bdd/test_mvp_e2e_audit_closure_pack.py -q --no-cov
# esperado pré-artefatos: 12 failed
```
