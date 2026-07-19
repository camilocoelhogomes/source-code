# Reviews — T01-coverage-inventory

| Data | Autor | Artefato | Decisão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | BDD INV-01..INV-08 + `tests/bdd/test_mvp_e2e_audit_coverage_inventory.py` | `TESTS_READY_FOR_REVIEW` | RED confirmado: artefato `audit/coverage-inventory.md` ausente. Aguarda review Architect + aprovação humana. |

---

## Review BDD — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` v0.1.0 + `tests/bdd/test_mvp_e2e_audit_coverage_inventory.py` |
| Data | 2026-07-18 |
| Branch | `feature/mvp-e2e-audit-hardening-T01-coverage-inventory` |
| Resultado | `CHANGES_REQUIRED` |

### Checks executados

| Check | Resultado |
|---|---|
| Schema §6 (colunas, 23 linhas, domínio status/superficie/browser) | OK — INV-04..06 |
| BDD-015 excluído (sem linha + nota) | OK — INV-03/04 |
| Sem execução Robot/e2e | OK |
| RED até matriz existir | OK — `_read_inventory` / INV-01 |
| BDD-001 (inventário coberto/lacuna) | PARCIAL — estrutura ok; regra anti-parcial não executável |
| BDD-008 / handoff T06 | OK estrutural — INV-08 |
| BR-001 / “parcial T21 ≠ integral” | FALHA — ver M-01/M-02 |

### Achados

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| M-01 | `MAJOR` | `bdd.md` INV-07 3º bullet; `TestINV07LacunaDocumentation` só valida linhas já `lacuna` | Bullet “fatias parciais não aparecem como `coberto-integral`” **não é testado**. BDD T21 parciais/smoke (design T21 §3.5: 003, 006, 013, 024) podem ser marcados `coberto-integral` e a suíte fica verde — viola BR-001 / critério de review. | Adicionar teste executável: denylist mínima dos BDD com fatia T21 `parcial`/`smoke` **deve** ser `lacuna` (ou regra equivalente documentada que prove integral além da fatia T21). Alinhar INV-07 no `bdd.md` ao assert. |
| M-02 | `MAJOR` | `TestINV06RowValueDomains` aceita qualquer string não vazia em evidências | Linha `status=coberto-integral` com `evidencia_robot`/`evidencia_pytest` = `ausente` (ou ambos `n/a`) passa — contradiz REQ-009 / design §3.2 (integral exige evidência que cubra o critério). | Assert: se `status=coberto-integral`, ao menos uma evidência Robot ou pytest ≠ `ausente`/`n/a` (e não vazia); opcionalmente reforçar D-T01-005 (UI + `evidencia_browser=nao` ⇒ não pode ser `coberto-integral`). |
| S-01 | `SUGGESTION` | INV-02 só exige substring `bdd-015` no arquivo | Exclusão no cabeçalho fica fraca; INV-03 cobre o corpo. | Opcional: exigir no cabeçalho palavra-chave de exclusão (`exclu` / `fora`) junto de BDD-015. |

### Bloqueios abertos

- M-01, M-02

### Decisão

`CHANGES_REQUIRED` — devolver ao QA. Não registrar `ARCHITECT_BDD` aprovado até M-01/M-02 fechados.

### Lista objetiva para o QA

1. Implementar assert INV-07 anti-parcial: BDD-003, BDD-006, BDD-013, BDD-024 (mínimo T21 parcial/smoke) não podem ser `coberto-integral` sem regra explícita de prova integral (preferência: forçar `lacuna` + `nota_parcial_t21`).
2. Implementar assert: `coberto-integral` exige evidência Robot ou pytest real (≠ `ausente` / `n/a`).
3. Atualizar `bdd.md` se a redação do cenário mudar; manter RED até a matriz existir.
4. Reenviar para review Architect (sem Robot/e2e).

---

## Resposta QA aos findings (BDD v0.1.1)

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Artefato | `bdd.md` v0.1.1 + `tests/bdd/test_mvp_e2e_audit_coverage_inventory.py` |
| Resultado | `TESTS_READY_FOR_REVIEW` |

| Finding | Ação |
|---|---|
| M-01 | `test_t21_known_partial_or_smoke_must_be_lacuna_with_nota`: denylist `BDD-003/006/013/024` ⇒ `status=lacuna` + `nota_parcial_t21` ≠ `—`. Extra: `test_ui_without_browser_cannot_be_coberto_integral` (D-T01-005). INV-07 reescrito no `bdd.md`. |
| M-02 | `test_coberto_integral_requires_real_robot_or_pytest_evidence`: `coberto-integral` exige Robot ou pytest ≠ `ausente`/`n/a`. INV-06 atualizado. |
| S-01 | INV-02 valida exclusão no **preâmbulo** (antes da tabela): `bdd-015` + `exclu`/`fora`. |

RED reconfirmado: artefato ainda ausente. Aguarda re-review Architect.

---

## Review BDD (re-review) — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` v0.1.1 + `tests/bdd/test_mvp_e2e_audit_coverage_inventory.py` |
| Data | 2026-07-18 |
| Branch | `feature/mvp-e2e-audit-hardening-T01-coverage-inventory` |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| M-01 anti-parcial T21 (003/006/013/024 ⇒ lacuna + nota) | OK — `test_t21_known_partial_or_smoke_must_be_lacuna_with_nota` |
| M-02 `coberto-integral` exige evidência real | OK — `test_coberto_integral_requires_real_robot_or_pytest_evidence` |
| S-01 exclusão 015 no cabeçalho | OK — INV-02 preâmbulo `bdd-015` + `exclu`/`fora` |
| D-T01-005 UI sem browser | OK — `test_ui_without_browser_cannot_be_coberto_integral` |
| Schema §6 / 23 linhas / sem BDD-015 | OK — INV-03..05 |
| Sem Robot/e2e; RED até matriz | OK |
| BDD-001 / BDD-008 (parcial) | OK — INV-01..08 |

### Achados

| ID | Severidade | Evidência | Achado | Correção |
|---|---|---|---|---|
| — | — | — | Nenhum BLOCKING/MAJOR aberto | — |
| M-01 | `MAJOR` | — | **Fechado** na v0.1.1 | — |
| M-02 | `MAJOR` | — | **Fechado** na v0.1.1 | — |
| S-01 | `SUGGESTION` | — | **Fechado** na v0.1.1 | — |

### Bloqueios abertos

Nenhum.

### Decisão

`APPROVED_BY_ARCHITECT` — BDD v0.1.1 apto para gate de interfaces (artefato documental) / aprovação humana do BDD. Sem implementação da matriz nesta etapa.
