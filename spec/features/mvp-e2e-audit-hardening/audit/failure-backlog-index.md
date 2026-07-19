# Failure backlog index — T05 (ParentFailureBacklog)

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T05-open-failure-tasks-parent` |
| Contrato | `ParentFailureBacklog` |
| Data | 2026-07-18 |
| Evidências | `runs/pytest-all-tasks.md` (T03) + `runs/e2e-robot-green-path.md` (T04) |
| ENG-010 | Esta feature **não implementa** o fix; correção no pipeline do pai. Sem alteração de `src/github_rag/**`, `e2e/robot/**` nem composes nesta entrega T05. |

## Resumo run-first

### Pytest (T03)

| Métrica | Valor |
|---|---|
| exit code | `0` |
| failed | `0` |
| Interpretação | **Zero falhas runtime pytest** — nenhuma task de correção pytest aberta (D-T05-001). |

### Robot / e2e (T04)

| Métrica | Valor |
|---|---|
| exit code | `3` (stack failure) |
| robot executado? | **não** |
| Falhas acionáveis | F-T04-001, F-T04-002, F-T04-003 |

## Tasks de falha abertas no pai

| Task pai | Superfície | Classificação REQ-017 | Evidência |
|---|---|---|---|
| [`T22-fix-tooling-e2e-compose-zoekt`](../../github-etl-mcp-rag/tasks/T22-fix-tooling-e2e-compose-zoekt.md) | `tooling-e2e` | combinação: F-T04-001 → `flakiness`; F-T04-002 → `produto`; F-T04-003 → consequência de F-T04-002 | T04 |

## Superfícies ENG-006

| Superfície | Status neste run-first | Nota |
|---|---|---|
| `tooling-e2e` | **afetada** — T22 | compose provider; zoekt entrypoint/`tini`; hang; robot skip |
| `health` | sem falha observável independente | fase `healthy` = skip; `/healthz` não exercitado; **não** abrir T23-fix-health |
| `catalog_indexing` | sem falha runtime observável | suíte Robot `unknown` (não executada) |
| `ui` | sem falha runtime observável | suíte Robot `unknown` (não executada) |
| `mcp` | sem falha runtime observável | suíte Robot `unknown` (não executada) |
| `negative` | sem falha runtime observável | suíte Robot `unknown` (não executada) |

Lacunas de cobertura integral / browser (inventário T01) → **T06** (`ParentGapFillBacklog`), não misturar com este índice de falhas.

## Contagens

| Item | Qtd |
|---|---|
| Falhas pytest pai | `0` |
| Falhas e2e acionáveis | `3` (F-T04-001..003) |
| Tasks de falha abertas no pai | `1` (T22) |
| Tasks health/catalog/ui/mcp/negative de falha | `0` |

## Handoff

- T06: gap-fill após este backlog de falha.
- T07: consolidação.
- Implementação de T22: apenas no pipeline de `github-etl-mcp-rag` (não nesta feature filha).
