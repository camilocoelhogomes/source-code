# AuditClosurePack — pacote de evidências (T07)

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T07-consolidate-evidence-close` |
| Contrato | `AuditClosurePack` |
| Data | 2026-07-19 |
| Estado da feature | `CLOSURE_READY` — encerrável / aguardando merge dos PRs |
| MVP de produto | **não** entregue (correções e green path integral pendentes no pai) |
| ENG-010 | Esta feature **não implementa** fixes; trabalho restante no pipeline do pai (T22+). Sem alteração de `src/github_rag/**`, `e2e/robot/**` nem composes nesta entrega T07. |

## 1. Índice de evidências (T01–T06)

| Task | Contrato | Artefato |
|---|---|---|
| T01 | `CoverageInventory` | [`audit/coverage-inventory.md`](./coverage-inventory.md) |
| T02 | `HitlEnvPrep` | [`audit/hitl-env-checklist.md`](./hitl-env-checklist.md) |
| T03 | `ParentPytestRun` | [`runs/pytest-all-tasks.md`](../runs/pytest-all-tasks.md) |
| T04 | `RobotGreenPathRun` | [`runs/e2e-robot-green-path.md`](../runs/e2e-robot-green-path.md) |
| T05 | `ParentFailureBacklog` | [`audit/failure-backlog-index.md`](./failure-backlog-index.md) |
| T06 | `ParentGapFillBacklog` | [`audit/gap-fill-backlog-index.md`](./gap-fill-backlog-index.md) |

## 2. Ordem demonstrada (BDD-007 / BR-007 / REQ-019)

Ordem **run-first → falha → gap-fill**:

```text
inventário (T01) + HITL (T02)
        → pytest (T03) + e2e Robot (T04)          [run-first]
        → falhas no pai (T05 / T22)               [antes]
        → lacunas / gap-fill (T06 / T23–T27)      [depois]
        → consolidação (T07 / este pacote)
```

Falhas (T22) foram abertas **antes** das lacunas (T23–T27). Gap-fill documentado somente após o run-first.

## 3. Verificação das métricas de sucesso

| Métrica (requirements) | Status | Evidência |
|---|---|---|
| Inventário BDD-001–024 (exc. 015) completo com status coberto / lacuna | OK (auditoria) | T01 `coverage-inventory.md` |
| Pytest (todas as tasks) e `python -m github_rag.e2e` executados e resultados registrados | OK (execução registrada) | T03 exit `0`; T04 exit `3` (stack failure — evidência válida) |
| Toda falha e toda lacuna refletida em task(s) no pai, agrupadas por superfície | OK (backlog) — **BR-005** | T05 → T22; T06 → T23–T27 |
| Plano de gap-fill (browser + asserts integrais) documentado em tasks após o run-first | OK (após falhas) | T06 índice + tasks gap; ordem §2 |

**Não** se interpreta “métricas OK” como MVP verde: o green path e2e falhou no stack (T04) e lacunas integrais permanecem abertas no pai.

## 4. Tasks abertas no pai (T22–T27) — BR-005

| Task pai | Tipo | Superfície | Path |
|---|---|---|---|
| [`T22-fix-tooling-e2e-compose-zoekt`](../../github-etl-mcp-rag/tasks/T22-fix-tooling-e2e-compose-zoekt.md) | falha | `tooling-e2e` | `spec/features/github-etl-mcp-rag/tasks/T22-fix-tooling-e2e-compose-zoekt.md` |
| [`T23-gap-ui-browser`](../../github-etl-mcp-rag/tasks/T23-gap-ui-browser.md) | lacuna | `ui` (browser obrigatório) | `spec/features/github-etl-mcp-rag/tasks/T23-gap-ui-browser.md` |
| [`T24-gap-catalog-indexing-integral`](../../github-etl-mcp-rag/tasks/T24-gap-catalog-indexing-integral.md) | lacuna | `catalog_indexing` | `spec/features/github-etl-mcp-rag/tasks/T24-gap-catalog-indexing-integral.md` |
| [`T25-gap-negative-integral`](../../github-etl-mcp-rag/tasks/T25-gap-negative-integral.md) | lacuna | `negative` | `spec/features/github-etl-mcp-rag/tasks/T25-gap-negative-integral.md` |
| [`T26-gap-mcp-parallel-slo`](../../github-etl-mcp-rag/tasks/T26-gap-mcp-parallel-slo.md) | lacuna | `mcp` | `spec/features/github-etl-mcp-rag/tasks/T26-gap-mcp-parallel-slo.md` |
| [`T27-gap-sdk-dec015-conformity`](../../github-etl-mcp-rag/tasks/T27-gap-sdk-dec015-conformity.md) | lacuna | `sdk` | `spec/features/github-etl-mcp-rag/tasks/T27-gap-sdk-dec015-conformity.md` |

| Contagem | Valor |
|---|---|
| Tasks de falha | `1` (T22) |
| Tasks de lacuna / gap-fill | `5` (T23–T27) |
| Total backlog aberto no pai | `6` |

Toda falha e toda lacuna do inventário (exc. BDD-015) aponta para task ID no pai (BR-005).

## 5. Status da feature filha

| Campo | Valor |
|---|---|
| Estado | `CLOSURE_READY` |
| Significado | Auditoria + execuções + backlog registrados; feature **encerrável** |
| Gate humano | Revisão e merge dos PRs desta feature; aprovação deste pacote |
| MVP de produto | **Não** entregue — não declarar MVP entregue neste pacote |
| Trabalho restante | Implementar T22–T27 no pipeline de `github-etl-mcp-rag` |

### PRs operacionais (referência)

| Task | PR (quando aberto) | Nota |
|---|---|---|
| T01 / T02 | mergeados | inventário + HITL |
| T03 | #24 | pytest run |
| T04 | #25 | e2e robot run |
| T05 | #26 | failure backlog / T22 |
| T06 | #27 | gap-fill / T23–T27 |
| T07 | este PR | closure pack |

Ordem de merge: … → T05 → T06 → **T07**.

## 6. Sanitização

- Pacote e artefatos referenciados: sem PAT, sem prefixos `ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_`, sem assignment de `GITHUB_TOKEN`/`E2E_GITHUB_TOKEN` com valor.
- Runs versionam resumo sanitizado; logs brutos Robot permanecem fora do git (`e2e/results/`).

## 7. Handoff

1. Humano: mergear PRs empilhados e aprovar este `AuditClosurePack`.
2. Engenharia: implementar tasks T22+ no pai (não nesta feature filha).
3. Não mesclar correções do pai como parte do encerramento desta feature.
4. MVP permanece **não** entregue até critério integral do pai (T19+T21 verdes no sentido do produto).
