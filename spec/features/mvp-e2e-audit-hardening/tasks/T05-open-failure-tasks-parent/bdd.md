# BDD — T05-open-failure-tasks-parent

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T05-open-failure-tasks-parent` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Execução | `tests/bdd/test_mvp_e2e_audit_failure_backlog.py` — valida índice + task T22 no pai (sem fix de produto) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | FAIL-01..FAIL-10; contrato `ParentFailureBacklog`; RED até índice + T22. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` (após correção) | `0.1.1` | M-01 vínculo ID→classificação; M-02 escopo src/e2e/compose em FAIL-10. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **Artefato (pytest BDD)** | Índice + task pai T22; superfícies; classificação; zero pytest; sem T23/fix inventado; sem secrets; sem patch produto nesta feature | CI |
| **Implementação de fix** | Fora do escopo (ENG-010) | Pipeline do pai |
| **Gap-fill** | T06 | Não misturar |

Paths canônicos:

```text
spec/features/mvp-e2e-audit-hardening/audit/failure-backlog-index.md
spec/features/github-etl-mcp-rag/tasks/T22-fix-tooling-e2e-compose-zoekt.md
```

## Rastreabilidade

| Cenário | Feature BDD / REQ | Design |
|---|---|---|
| FAIL-01 | BDD-005; REQ-015–016 | §3.4 índice |
| FAIL-02 | BDD-005; ENG-009 | §3.3 T22 |
| FAIL-03 | REQ-016; ENG-006 | §3.3 superfície tooling-e2e |
| FAIL-04 | REQ-017; ENG-007; D-T05-003 | classificação combinada |
| FAIL-05 | BDD-005; BR-005 | F-T04-001..003 cobertos |
| FAIL-06 | D-T05-001; T03 | zero falhas pytest |
| FAIL-07 | D-T05-001/002 | sem T23 / health inventado |
| FAIL-08 | D-T05-001 | sem catalog/ui/mcp/negative de falha |
| FAIL-09 | BR-004 | sanitização |
| FAIL-10 | ENG-010; D-T05-005 | sem fix nesta feature |

## Resultado RED esperado (pré-implementação)

```bash
python -m pytest tests/bdd/test_mvp_e2e_audit_failure_backlog.py -q --no-cov
```

| Métrica | Valor esperado |
|---|---|
| passed | `0` |
| failed | `10` |
| Motivo | índice e/ou T22 ausentes |

### Evidência RED (execução QA)

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Comando | `python -m pytest tests/bdd/test_mvp_e2e_audit_failure_backlog.py -q --no-cov` |
| passed | `0` |
| failed | `10` |
| Status | `RED` — artefatos ausentes (razão esperada) |

---

## FAIL-01 — Índice canônico existe

**Dado** o backlog de falhas run-first T05  
**Quando** `ParentFailureBacklog` for publicado  
**Então** existe `spec/features/mvp-e2e-audit-hardening/audit/failure-backlog-index.md`

## FAIL-02 — Task T22 no pai existe

**Dado** falhas F-T04-001..003 na superfície tooling-e2e  
**Quando** as tasks de correção forem abertas no pai  
**Então** existe `spec/features/github-etl-mcp-rag/tasks/T22-fix-tooling-e2e-compose-zoekt.md`

## FAIL-03 — Superfície tooling-e2e declarada

**Dado** T22 e o índice  
**Quando** o conteúdo for inspecionado  
**Então** ambos declaram superfície `tooling-e2e`

## FAIL-04 — Classificação combinada REQ-017

**Dado** T22  
**Quando** a classificação for lida  
**Então** documenta combinação REQ-017 com vínculo explícito: F-T04-001 → `flakiness`, F-T04-002 → `produto`, F-T04-003 → consequência de F-T04-002

## FAIL-05 — Evidências F-T04-001..003

**Dado** T22 e/ou índice  
**Quando** a evidência for lida  
**Então** referencia F-T04-001, F-T04-002 e F-T04-003 (ou runs T04 equivalentes)

## FAIL-06 — Zero falhas pytest

**Dado** T03 com failed=`0`  
**Quando** o índice for lido  
**Então** declara zero falhas runtime pytest (sem task de correção pytest inventada)

## FAIL-07 — Sem task health fantasma

**Dado** fase healthy=skip e F-T04-003 como tooling-e2e  
**Quando** o backlog for inspecionado  
**Então** não existe task pai `T23-fix-health*` nem arquivo de falha health inventado; índice declara `health` sem falha observável independente

## FAIL-08 — Sem falhas inventadas catalog/ui/mcp/negative

**Dado** suítes Robot unknown  
**Quando** o índice for lido  
**Então** declara `catalog_indexing`, `ui`, `mcp`, `negative` sem falha runtime observável (lacunas → T06)

## FAIL-09 — Sem secrets

**Dado** índice e T22  
**Quando** o conteúdo for escaneado  
**Então** não há prefixos `ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_` nem assignment de token com valor

## FAIL-10 — Sem implementação de fix nesta feature

**Dado** ENG-010  
**Quando** T05 for inspecionado no índice/T22  
**Então** declara que correção ocorre no pipeline do pai / esta feature não implementa fix  
**E** T05 não altera `src/github_rag/**` nem `e2e/robot/**` nem composes como entrega desta task
