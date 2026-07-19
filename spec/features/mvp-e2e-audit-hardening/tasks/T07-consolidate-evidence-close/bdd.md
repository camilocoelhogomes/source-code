# BDD — T07-consolidate-evidence-close

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T07-consolidate-evidence-close` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `TESTS_READY_FOR_REVIEW` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Execução | `tests/bdd/test_mvp_e2e_audit_closure_pack.py` — valida pacote canônico (sem fixes/MVP) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | CLOSE-01..CLOSE-12; contrato `AuditClosurePack`; RED até pacote. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **Artefato (pytest BDD)** | `closure-pack.md`: links T01–T06, tasks T22–T27, métricas, ordem run-first→gap-fill, anti-MVP-entregue, ENG-010, secrets, status encerrável | CI |
| **Fixes / merge / MVP** | Fora do escopo | Pipeline pai / humano |

Paths canônicos:

```text
spec/features/mvp-e2e-audit-hardening/audit/closure-pack.md
spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md
spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md
spec/features/mvp-e2e-audit-hardening/runs/pytest-all-tasks.md
spec/features/mvp-e2e-audit-hardening/runs/e2e-robot-green-path.md
spec/features/mvp-e2e-audit-hardening/audit/failure-backlog-index.md
spec/features/mvp-e2e-audit-hardening/audit/gap-fill-backlog-index.md
spec/features/github-etl-mcp-rag/tasks/T22-fix-tooling-e2e-compose-zoekt.md
spec/features/github-etl-mcp-rag/tasks/T23-gap-ui-browser.md
spec/features/github-etl-mcp-rag/tasks/T24-gap-catalog-indexing-integral.md
spec/features/github-etl-mcp-rag/tasks/T25-gap-negative-integral.md
spec/features/github-etl-mcp-rag/tasks/T26-gap-mcp-parallel-slo.md
spec/features/github-etl-mcp-rag/tasks/T27-gap-sdk-dec015-conformity.md
```

## Rastreabilidade

| Cenário | Feature BDD / REQ | Design |
|---|---|---|
| CLOSE-01 | métricas; ENG-002 | §3.3 pacote canônico |
| CLOSE-02 | BDD-001; métricas inventário | §3.4 / §3.5 T01 |
| CLOSE-03 | BDD-002 | §3.4 T02 |
| CLOSE-04 | BDD-004; métricas pytest | §3.4 / §3.5 T03 |
| CLOSE-05 | BDD-003; métricas e2e | §3.4 / §3.5 T04 |
| CLOSE-06 | BDD-005; BR-005; T22 | §3.4 T05 |
| CLOSE-07 | BDD-006/008; T23–T27 | §3.4 T06 |
| CLOSE-08 | BDD-007; REQ-019 | §3.4 ordem |
| CLOSE-09 | métricas; BR-005 | §3.5 todas falhas/lacunas → IDs |
| CLOSE-10 | D-T07-002/003 | status encerrável; anti-MVP |
| CLOSE-11 | BR-004 | sanitização |
| CLOSE-12 | ENG-010; D-T07-004/005 | sem fix nesta feature |

## Resultado RED esperado (pré-implementação)

```bash
python -m pytest tests/bdd/test_mvp_e2e_audit_closure_pack.py -q --no-cov
```

| Métrica | Valor esperado |
|---|---|
| passed | `0` |
| failed | `12` |
| Motivo | `closure-pack.md` ausente |

### Evidência RED (execução QA)

| Campo | Valor |
|---|---|
| Data | 2026-07-19 |
| Comando | `python -m pytest tests/bdd/test_mvp_e2e_audit_closure_pack.py -q --no-cov` |
| passed | `0` |
| failed | `12` |
| Status | `RED` — artefato ausente (razão esperada) |

---

## CLOSE-01 — Pacote canônico existe

**Dado** a consolidação T07  
**Quando** `AuditClosurePack` for publicado  
**Então** existe `spec/features/mvp-e2e-audit-hardening/audit/closure-pack.md`

## CLOSE-02 — Inventário T01 referenciado

**Dado** o pacote  
**Quando** o conteúdo for lido  
**Então** referencia `coverage-inventory.md` / inventário T01

## CLOSE-03 — Checklist HITL T02 referenciado

**Dado** o pacote  
**Quando** o conteúdo for lido  
**Então** referencia `hitl-env-checklist.md` / T02

## CLOSE-04 — Run pytest T03 referenciado

**Dado** o pacote  
**Quando** o conteúdo for lido  
**Então** referencia `pytest-all-tasks.md` / T03 / ParentPytestRun

## CLOSE-05 — Run e2e T04 referenciado

**Dado** o pacote  
**Quando** o conteúdo for lido  
**Então** referencia `e2e-robot-green-path.md` / T04 / RobotGreenPathRun

## CLOSE-06 — Falhas T05 / T22 referenciados

**Dado** o pacote  
**Quando** o conteúdo for lido  
**Então** referencia `failure-backlog-index.md` / T05  
**E** lista task pai `T22-fix-tooling-e2e-compose-zoekt` (ou T22 com slug fix-tooling)

## CLOSE-07 — Gap-fill T06 / T23–T27 referenciados

**Dado** o pacote  
**Quando** o conteúdo for lido  
**Então** referencia `gap-fill-backlog-index.md` / T06  
**E** lista tasks pai T23–T27 (slugs gap-*)

## CLOSE-08 — Ordem run-first → falha → gap-fill

**Dado** BDD-007 / BR-007  
**Quando** o pacote for lido  
**Então** demonstra ordem inventário/HITL/runs → falhas (T22) → lacunas (T23–T27)

## CLOSE-09 — Métricas de sucesso + BR-005

**Dado** as métricas de sucesso do requirements  
**Quando** o pacote for inspecionado  
**Então** verifica inventário completo, pytest+e2e executados, falhas/lacunas em tasks, gap-fill após run-first  
**E** lista IDs T22–T27 como backlog aberto no pai

## CLOSE-10 — Feature encerrável; MVP não entregue

**Dado** D-T07-002 / D-T07-003  
**Quando** o pacote (e status da feature) for lido  
**Então** declara feature encerrável / aguardando merge dos PRs / `CLOSURE_READY`  
**E** declara explicitamente que MVP de produto **não** está entregue  
**E** não afirma “MVP entregue” / “MVP delivered” como conclusão positiva

## CLOSE-11 — Sem secrets

**Dado** o pacote  
**Quando** o conteúdo for escaneado  
**Então** não há prefixos `ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_` nem assignment de token com valor

## CLOSE-12 — ENG-010 sem fix nesta feature

**Dado** ENG-010  
**Quando** o pacote for lido  
**Então** declara que correções/implementação ficam no pipeline do pai (T22+)  
**E** afirma que T07 não altera `src/github_rag/**` / `e2e/robot/**` / composes  
**E** não declara merge das tasks do pai como feito nesta feature
