# BDD — T06-open-gap-fill-tasks-parent

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T06-open-gap-fill-tasks-parent` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Execução | `tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py` — valida índice + tasks T23–T27 no pai (sem keywords/browser) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | GAP-01..GAP-12; contrato `ParentGapFillBacklog`; RED até índice + T23–T27. |
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Alinhado design 0.1.0; browser obrigatório em T23; cobertura de todas as lacunas T01. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **Artefato (pytest BDD)** | Índice + tasks pai T23–T27; superfícies; classificação; browser UI; todas as lacunas; sem BDD-015; sem duplicar T22; sem secrets; sem keywords nesta feature | CI |
| **Implementação de keywords/browser** | Fora do escopo (ENG-010) | Pipeline do pai |
| **Falhas runtime** | T05 / T22 | Não misturar |

Paths canônicos:

```text
spec/features/mvp-e2e-audit-hardening/audit/gap-fill-backlog-index.md
spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md
spec/features/github-etl-mcp-rag/tasks/T23-gap-ui-browser.md
spec/features/github-etl-mcp-rag/tasks/T24-gap-catalog-indexing-integral.md
spec/features/github-etl-mcp-rag/tasks/T25-gap-negative-integral.md
spec/features/github-etl-mcp-rag/tasks/T26-gap-mcp-parallel-slo.md
spec/features/github-etl-mcp-rag/tasks/T27-gap-sdk-dec015-conformity.md
```

## Rastreabilidade

| Cenário | Feature BDD / REQ | Design |
|---|---|---|
| GAP-01 | BDD-008; REQ-018–019 | §3.4 índice |
| GAP-02 | BDD-008; ENG-009 | §3.3 T23–T27 |
| GAP-03 | ENG-006; D-T06-002 | superfícies |
| GAP-04 | REQ-017; ENG-007 | classificação gap-teste/assert-fraco |
| GAP-05 | BDD-006; ENG-008; REQ-007 | browser em T23 |
| GAP-06 | BDD-008; D-T06-001 | todas as lacunas inventário |
| GAP-07 | denylist T21 / INV-07 | 003, 006, 013, 024 cobertos |
| GAP-08 | D-T06-008 | sem BDD-015 |
| GAP-09 | D-T06-005; T05 | sem duplicar T22 |
| GAP-10 | BDD-007; REQ-019 | ordem após falhas / ref T05 |
| GAP-11 | BR-004 | sanitização |
| GAP-12 | ENG-010; D-T06-006 | sem keywords nesta feature |

## Resultado RED esperado (pré-implementação)

```bash
python -m pytest tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py -q --no-cov
```

| Métrica | Valor esperado |
|---|---|
| passed | `0` |
| failed | `12` |
| Motivo | índice e/ou tasks T23–T27 ausentes |

### Evidência RED (execução QA)

| Campo | Valor |
|---|---|
| Data | 2026-07-19 |
| Comando | `python -m pytest tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py -q --no-cov` |
| passed | `0` |
| failed | `12` |
| Status | `RED` — artefatos ausentes (razão esperada) |

---

## GAP-01 — Índice canônico existe

**Dado** o backlog de lacunas T06  
**Quando** `ParentGapFillBacklog` for publicado  
**Então** existe `spec/features/mvp-e2e-audit-hardening/audit/gap-fill-backlog-index.md`

## GAP-02 — Tasks T23–T27 no pai existem

**Dado** lacunas do inventário T01 após falhas T05  
**Quando** as tasks de gap-fill forem abertas no pai  
**Então** existem os arquivos T23–T27 listados nos paths canônicos

## GAP-03 — Superfícies declaradas

**Dado** índice e tasks pai  
**Quando** o conteúdo for inspecionado  
**Então** declara superfícies `ui`, `catalog_indexing`, `negative`, `mcp`, `sdk` mapeadas a T23–T27 respectivamente

## GAP-04 — Classificação gap-teste / assert-fraco

**Dado** cada task T23–T27  
**Quando** a classificação for lida  
**Então** declara `gap-teste` e/ou `assert-fraco` (REQ-017)

## GAP-05 — UI exige browser

**Dado** T23 (superfície `ui`)  
**Quando** o aceite for lido  
**Então** exige automação browser (Browser Library / Playwright / equivalente)  
**E** declara que API HTTP sozinha não encerra a lacuna UI

## GAP-06 — Todas as lacunas do inventário cobertas

**Dado** `coverage-inventory.md` com linhas `status=lacuna`  
**Quando** o índice / tasks forem inspecionados  
**Então** cada `bdd_id` lacuna (exceto BDD-015) aparece no backlog gap-fill

## GAP-07 — Denylist parcial T21 coberta

**Dado** BDD-003, BDD-006, BDD-013, BDD-024 como lacunas parciais/smoke  
**Quando** o backlog for lido  
**Então** esses quatro IDs estão cobertos por tasks gap (T24/T26/T27 conforme design)

## GAP-08 — Sem task BDD-015

**Dado** REQ-010 / DEC-019  
**Quando** o backlog for inspecionado  
**Então** não há task nem linha de aceite para BDD-015

## GAP-09 — Não duplica T22

**Dado** T22 já aberta como falha tooling  
**Quando** o índice gap-fill for lido  
**Então** declara referência a T22 / não duplicar falha tooling como gap  
**E** não existe arquivo `T2*-gap-tooling*`

## GAP-10 — Ordem após falhas (T05)

**Dado** BR-007 / REQ-019  
**Quando** o índice for lido  
**Então** referencia T05 / falhas antes de lacunas / ParentFailureBacklog / T22

## GAP-11 — Sem secrets

**Dado** índice e tasks T23–T27  
**Quando** o conteúdo for escaneado  
**Então** não há prefixos `ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_` nem assignment de token com valor

## GAP-12 — Sem implementação de keywords nesta feature

**Dado** ENG-010 / BR-002  
**Quando** T06 for inspecionado  
**Então** declara que keywords/browser são implementados no pipeline do pai  
**E** T06 não altera `src/github_rag/**` nem `e2e/robot/**` nem composes como entrega desta task
