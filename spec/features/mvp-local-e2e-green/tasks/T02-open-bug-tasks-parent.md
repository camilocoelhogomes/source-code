# Task T02 — open-bug-tasks-parent

| Campo | Valor |
|---|---|
| Task ID | `T02-open-bug-tasks-parent` |
| Feature | `mvp-local-e2e-green` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W2 |
| Plano | v0.1.0 |

## Objetivo

Converter **cada falha distinta** do run T01 em task de implementação em `github-etl-mcp-rag`, agrupada por superfície, **reutilizando T22–T27** quando o achado já estiver coberto.

## Escopo

- Consumir resumo sanitizado de T01.
- Agrupar por superfície: `health` | `catalog_indexing` | `ui` | `mcp` | `negative` | `tooling-e2e` | `container-delivery` (REQ-015).
- **Dedup BR-005 / DEC-008:** antes de criar T28+, verificar cobertura por tasks existentes:

| Superfície / achado | Task existente |
|---|---|
| compose/zoekt/boot e2e | **T22** |
| UI browser / fluxos visuais | **T23** |
| catálogo/indexação integral | **T24** |
| cenários negativos integral | **T25** |
| MCP paralelismo/SLO | **T26** |
| conformidade SDK/BDD-024 | **T27** |

- Se achado = task existente: **atualizar** evidência e manter `READY_FOR_IMPLEMENTATION` (ou estado pipeline); **não** duplicar.
- Se achado novo: criar `spec/features/github-etl-mcp-rag/tasks/T28-*.md` em diante (ENG-009 pai).
- Cada task nova inclui: evidência sanitizada (comando, cenário Robot, log), classificação (`produto` | `flakiness` | `gap-teste` | `tooling-e2e`), critério de aceite ligado ao BDD do pai quando aplicável, estado `READY_FOR_IMPLEMENTATION` (REQ-016).
- Índice local: `spec/features/mvp-local-e2e-green/runs/failure-backlog-index.md`.
- **Sem** implementar correções nesta feature.

## Fora de escopo

- Disparar orquestrador (T03).
- Build imagem / compose end-user (T04).
- Declarar MVP entregue.
- Alterar código em `src/github_rag/**`.

## Dependências

- **Dura:** T01.

## Critérios de aceite

- Toda falha T01 refletida em task pai ou update de T22–T27 (BDD-002, REQ-003).
- Nenhuma duplicação de achado já rastreado (BR-005).
- Tasks novas iniciam `READY_FOR_IMPLEMENTATION` (REQ-016).
- Handoff lista completa para T03 (IDs + dependências).

## Arquivos prováveis

- `spec/features/github-etl-mcp-rag/tasks/T28-*.md` (novas)
- Updates: `T22` … `T27` (evidência)
- `spec/features/mvp-local-e2e-green/runs/failure-backlog-index.md`

## Rastreabilidade

- REQ-003, REQ-015–017; BR-002, BR-005; DEC-003, DEC-008; BDD-002.

## Handoff

- Lista de task IDs + DAG → T03 (`orchestrate-bugfix-loop`).
- Incluir obrigatoriamente T22–T27 pendentes além de T28+.
