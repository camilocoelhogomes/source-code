# Unit Test Plan — T01-coverage-inventory

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T01-coverage-inventory` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design / BDD / Interfaces | `0.1.0` / `0.1.1` / `0.1.0` (Architect-approved) |
| Natureza | Documental — sem `src/`; valida contrato `CoverageInventory` |
| Suíte | `tests/unit/audit/` |
| Branch | `feature/mvp-e2e-audit-hardening-T01-coverage-inventory` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Plano + unitários de schema/corners; RED no path canônico até existir a matriz. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Gate `ARCHITECT_UNIT_TESTS`; ver `reviews.md` / `approvals.md`. |

## 1. Estratégia

| Camada | Arquivo | Fronteira |
|---|---|---|
| Parser/schema helper (só testes) | `tests/unit/audit/inventory_schema.py` | Markdown sintético em memória |
| Corners do contrato | `tests/unit/audit/test_coverage_inventory_schema.py` | fixtures string |
| Artefato canônico | mesmo arquivo | path real `audit/coverage-inventory.md` |

- Sem Robot/e2e, sem código de produção (I-T01-003).
- BDD INV-01..08 permanece superfície de aceite; unitários isolam extremos/corners do schema §6.
- Pré-implementação: testes do artefato real falham por arquivo ausente — **RED esperado**.

## 2. Matriz unitária

### 2.1 Parser / schema (fixtures)

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-P01 | Markdown sem tabela `bdd_id`+`status` | erro explícito | schema §6 |
| UT-P02 | Tabela com coluna obrigatória ausente | erro | INV-05 / I-T01 |
| UT-P03 | Linha com `superficie` fora do domínio | erro | INV-06 |
| UT-P04 | Linha com `status` inválido | erro | INV-06 |
| UT-P05 | `evidencia_browser` ∉ {sim,nao,n/a} | erro | INV-06 |
| UT-P06 | `coberto-integral` com robot+pytest ausente/n/a | erro | REQ-009 / M-02 |
| UT-P07 | `lacuna` com `motivo_lacuna` = `—` ou vazio | erro | INV-07 |
| UT-P08 | Linha `BDD-015` presente | erro | D-T01-004 |
| UT-P09 | `bdd_id` duplicado | erro | INV-04 |
| UT-P10 | Conjunto ≠ 23 ids esperados (faltando um) | erro | INV-04 |
| UT-P11 | Denylist T21 (003/006/013/024) como `coberto-integral` | erro | BR-001 / M-01 |
| UT-P12 | Denylist sem `nota_parcial_t21` | erro | INV-07 |
| UT-P13 | `superficie=ui` + `evidencia_browser=nao` + `coberto-integral` | erro | D-T01-005 |
| UT-P14 | Fixture válida mínima (23 linhas schema-ok) | parse ok | feliz |

### 2.2 Artefato canônico (path real)

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-A01 | Path canônico existe | True | INV-01 |
| UT-A02 | Artefato passa `validate_coverage_inventory` | sem raise | schema §6 completo |
| UT-A03 | Denylist T21 no artefato = `lacuna` + nota | ok | BR-001 |
| UT-A04 | Texto não declara encerramento por green path | ok | INV-08 |

**RED pré-matriz:** UT-A01..A04 falham com artefato ausente.

## 3. Comando

```bash
python -m pytest tests/unit/audit/test_coverage_inventory_schema.py -q
```

## 4. Fora de escopo

- Executar Robot/e2e.
- Cobertura de `src/github_rag` (sem código de produção nesta task).
- Abrir tasks no pai.
