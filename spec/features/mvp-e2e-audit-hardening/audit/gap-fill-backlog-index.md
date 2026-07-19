# Gap-fill backlog index — T06 (ParentGapFillBacklog)

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T06-open-gap-fill-tasks-parent` |
| Contrato | `ParentGapFillBacklog` |
| Data | 2026-07-19 |
| SoT lacunas | [`coverage-inventory.md`](./coverage-inventory.md) (T01) |
| Pré-requisito falhas | [`failure-backlog-index.md`](./failure-backlog-index.md) (T05) + pai `T22-fix-tooling-e2e-compose-zoekt` |
| Ordem (BDD-007 / REQ-019 / BR-007) | Falhas (T05/T22) **antes** de lacunas (esta fase) |
| ENG-010 | Esta feature **não implementa** keywords/browser/produto; correção no pipeline do pai. Sem alteração de `src/github_rag/**`, `e2e/robot/**` nem composes nesta entrega T06. |

## Cross-ref T22 — não duplicar

T22 (`tooling-e2e`) é task de **falha** runtime (compose/zoekt). **Não** reabrir como gap-tooling. Lacunas abaixo são cobertura integral / browser do inventário T01, distintas de F-T04-*.

## Tasks de lacuna abertas no pai

| Task pai | Superfície | Classificação REQ-017 | BDD lacunas | Evidência |
|---|---|---|---|---|
| [`T23-gap-ui-browser`](../../github-etl-mcp-rag/tasks/T23-gap-ui-browser.md) | `ui` | `gap-teste` (+ `assert-fraco` API-smoke) | BDD-001, 002, 007, 009, 010, 016, 019, 023 | T01 |
| [`T24-gap-catalog-indexing-integral`](../../github-etl-mcp-rag/tasks/T24-gap-catalog-indexing-integral.md) | `catalog_indexing` | `assert-fraco` / `gap-teste` | BDD-003, 005, 006, 017 | T01 |
| [`T25-gap-negative-integral`](../../github-etl-mcp-rag/tasks/T25-gap-negative-integral.md) | `negative` | `gap-teste` / `assert-fraco` | BDD-008, 018, 022 | T01 |
| [`T26-gap-mcp-parallel-slo`](../../github-etl-mcp-rag/tasks/T26-gap-mcp-parallel-slo.md) | `mcp` | `assert-fraco` | BDD-013 | T01 |
| [`T27-gap-sdk-dec015-conformity`](../../github-etl-mcp-rag/tasks/T27-gap-sdk-dec015-conformity.md) | `sdk` | `assert-fraco` / `gap-teste` | BDD-024 | T01 |

## Cobertura das lacunas do inventário

| bdd_id | superfície | task pai |
|---|---|---|
| BDD-001 | ui | T23 |
| BDD-002 | ui | T23 |
| BDD-003 | catalog_indexing | T24 |
| BDD-005 | catalog_indexing | T24 |
| BDD-006 | catalog_indexing | T24 |
| BDD-007 | ui | T23 |
| BDD-008 | negative | T25 |
| BDD-009 | ui | T23 |
| BDD-010 | ui | T23 |
| BDD-013 | mcp | T26 |
| BDD-016 | ui | T23 |
| BDD-017 | catalog_indexing | T24 |
| BDD-018 | negative | T25 |
| BDD-019 | ui | T23 |
| BDD-022 | negative | T25 |
| BDD-023 | ui | T23 |
| BDD-024 | sdk | T27 |

**BDD-015** — excluído (REQ-010 / DEC-019); não gera task.

**Coberto-integral (sem task gap):** BDD-004, 011, 012, 014, 020, 021.

## Superfícies sem task gap nesta fase

| Superfície | Motivo |
|---|---|
| `tooling-e2e` | Já coberta por falha T22 — não duplicar |
| `health` | Sem linha `lacuna` no inventário (BDD-020 coberto-integral) |

## Contagens

| Item | Qtd |
|---|---|
| Lacunas inventário (exc. 015) | `17` |
| Tasks gap abertas no pai | `5` (T23–T27) |
| Tasks gap-tooling | `0` (não duplicar T22) |

## Handoff

- T07: consolidação de evidências + índice de tasks abertas (T22 + T23–T27).
- Implementação de T23–T27: apenas no pipeline de `github-etl-mcp-rag` (não nesta feature filha).
