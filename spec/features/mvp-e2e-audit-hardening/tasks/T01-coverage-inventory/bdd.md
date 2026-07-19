# BDD — T01-coverage-inventory

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T01-coverage-inventory` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `TESTS_READY_FOR_REVIEW` |
| Versão | `0.1.1` |
| Design base | `0.1.0` (`HUMAN_DESIGN_APPROVED`) |
| Execução | `tests/bdd/test_mvp_e2e_audit_coverage_inventory.py` — valida artefato Markdown `CoverageInventory` (sem Robot/e2e) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | INV-01..INV-08; contrato documental do schema §6; RED até existir `audit/coverage-inventory.md`. |
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | — | M-01 (anti-parcial não executável), M-02 (`coberto-integral` + evidência ausente). Ver `reviews.md`. |
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.1` | Fecha M-01/M-02/S-01: denylist T21 003/006/013/024; evidência real para integral; cabeçalho exclusão 015. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **Artefato (pytest BDD)** | Existência, cabeçalho, nota BDD-015 e tabela schema §6 em `audit/coverage-inventory.md` | CI unitário/BDD padrão |
| **Robot / e2e** | Fora do escopo desta task (T03/T04) | Não executar |

- Critério de cobertura = texto integral BDD-001–024 do pai (BR-001 / DEC-002).
- Status binário: `coberto-integral` \| `lacuna` (parcial T21 = `lacuna` + nota).
- Denylist mínima T21 §3.5 parcial/smoke: **BDD-003, BDD-006, BDD-013, BDD-024** → obrigatoriamente `lacuna` + `nota_parcial_t21`.
- BDD-015: nota de exclusão; **sem** linha de status.
- Path canônico: `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md`.

## Rastreabilidade

| Cenário | Feature BDD / REQ | Design |
|---|---|---|
| INV-01..INV-05 | BDD-001; REQ-001, REQ-008–010 | §3.3, §6, D-T01-002–004 |
| INV-06 | BDD-001; REQ-009 | §3.2, §6 |
| INV-07 | BDD-001; REQ-009; BR-001; D-T01-005 | T21 §3.5; T01 §6 heurísticas; D-T01-003 |
| INV-08 | BDD-008 (parcial — SoT de lacunas para T06) | §1, handoff T06 |

---

## INV-01 — Artefato canônico existe

**Tipo:** artefato Markdown  
**Dado** a auditoria documental T01 concluída  
**Quando** o inventário for publicado  
**Então** existe o arquivo `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md`

## INV-02 — Cabeçalho declara metadados obrigatórios

**Tipo:** artefato Markdown  
**Dado** o artefato `coverage-inventory.md`  
**Quando** o cabeçalho (texto antes da tabela da matriz) for lido  
**Então** declara feature `mvp-e2e-audit-hardening`  
**E** declara data do inventário  
**E** declara critério = texto integral do pai (BDD-001–024)  
**E** declara exclusão/fora de BDD-015 (id + palavra `exclu`/`fora` no cabeçalho)  
**E** declara método = inspeção estática (sem run)

## INV-03 — Nota fixa BDD-015 fora do inventário automatizado

**Tipo:** artefato Markdown  
**Dado** o artefato `coverage-inventory.md`  
**Quando** o corpo for inspecionado  
**Então** há nota explícita de que BDD-015 está fora do inventário automatizado (REQ-010 / DEC-019)  
**E** a nota indica validação humana

## INV-04 — Tabela cobre BDD-001–014 e 016–024 (sem 015)

**Tipo:** artefato Markdown  
**Dado** a tabela da matriz  
**Quando** as linhas `bdd_id` forem enumeradas  
**Então** existem exatamente as 23 linhas BDD-001..014 e BDD-016..024  
**E** não existe linha com `bdd_id` = `BDD-015`

## INV-05 — Colunas do schema §6 presentes

**Tipo:** artefato Markdown  
**Dado** a tabela da matriz  
**Quando** o cabeçalho da tabela for lido  
**Então** contém as colunas: `bdd_id`, `superficie`, `status`, `evidencia_robot`, `evidencia_pytest`, `evidencia_browser`, `nota_parcial_t21`, `motivo_lacuna`

## INV-06 — Valores por linha respeitam o domínio do schema

**Tipo:** artefato Markdown  
**Dado** cada linha da matriz  
**Quando** os campos forem validados  
**Então** `superficie` ∈ {`health`, `catalog_indexing`, `ui`, `mcp`, `negative`, `tooling-e2e`, `sdk`}  
**E** `status` ∈ {`coberto-integral`, `lacuna`}  
**E** `evidencia_robot`, `evidencia_pytest` e `evidencia_browser` estão preenchidos (não vazios)  
**E** `evidencia_browser` ∈ {`sim`, `nao`, `n/a`}  
**E** se `status` = `coberto-integral`, então `evidencia_robot` **ou** `evidencia_pytest` é evidência real (≠ `ausente` / `n/a`) — REQ-009

## INV-07 — Parciais T21 e lacunas documentadas

**Tipo:** artefato Markdown  
**Dado** a matriz classificada  
**Quando** a classificação for inspecionada  
**Então** toda linha com `status` = `lacuna` tem `motivo_lacuna` ≠ `—` nem vazio  
**E** BDD-003, BDD-006, BDD-013 e BDD-024 (parcial/smoke no mapeamento T21 §3.5) têm `status` = `lacuna` **e** `nota_parcial_t21` ≠ `—`  
**E** nenhuma linha com `superficie` = `ui` e `evidencia_browser` = `nao` tem `status` = `coberto-integral` (D-T01-005)

## INV-08 — Inventário é SoT utilizável por T06 mesmo com green path

**Tipo:** artefato Markdown (contrato documental BDD-008 parcial)  
**Dado** a matriz completa com ao menos a estrutura de lacunas  
**Quando** T06 consumir o inventário  
**Então** toda linha `lacuna` permanece rastreável por `bdd_id` + `superficie` + `motivo_lacuna`  
**E** o artefato não declara auditoria encerrada só por green path T21

---

## Comando

```bash
python -m pytest tests/bdd/test_mvp_e2e_audit_coverage_inventory.py -q
```

## Estado esperado (pré-implementação)

RED: artefato `audit/coverage-inventory.md` ausente → INV-01 (e demais) falham.
