# Task T05 — open-failure-tasks-parent

| Campo | Valor |
|---|---|
| Task ID | `T05-open-failure-tasks-parent` |
| Feature | `mvp-e2e-audit-hardening` |
| Estado | `PENDING_PO_REVIEW` |
| Onda | W3 |
| Plano | v0.1.0 |

## Objetivo

Converter falhas da fase run-first (pytest + Robot) em tasks de correção em `github-etl-mcp-rag`, agrupadas por superfície e classificadas (`produto` | `flakiness` | `gap-teste` | `assert-fraco`).

## Escopo

- Consumir resumos de T03 e T04.
- Agrupar achados nas superfícies: `health`, `catalog_indexing`, `ui`, `mcp`, `negative`, `tooling-e2e` (REQ-016).
- Criar arquivos `spec/features/github-etl-mcp-rag/tasks/T22-*.md` (ou IDs livres após T21) — uma task por superfície/tipo dominante afetado; não 1:1 BDD obrigatório.
- Cada task: objetivo, evidência do run, classificação ENG-007, critérios de aceite, arquivos prováveis, dependências, handoff; **sem** implementar a correção.
- Se run-first verde: registrar “zero falhas runtime”; ainda assim permitir T06 para lacunas.

## Fora de escopo

- Implementar correções de produto ou keywords.
- Abrir tasks só de lacuna documental sem falha (T06).
- Alterar suíte Robot nesta feature.
- Declarar MVP entregue.

## Dependências

- **Dura:** T03, T04.

## Critérios de aceite

- Toda falha run-first refletida em task(s) no pai por superfície (BDD-005; BR-005).
- Cada task declara classificação REQ-017.
- Nenhuma implementação de fix nesta feature (ENG-010).

## Arquivos prováveis

- `spec/features/github-etl-mcp-rag/tasks/T22-*.md` … (IDs após T21)
- Índice local: `spec/features/mvp-e2e-audit-hardening/audit/failure-backlog-index.md`

## Rastreabilidade

- REQ-005, REQ-016–017; BR-005–007; DEC-006–008; ENG-006–007, ENG-009; BDD-005, BDD-007 (parcial).

## Handoff

- Tasks do pai prontas para pipeline de implementação **após** aprovação do plano desta feature e gates do pai.
- Desbloqueia T06 (gap-fill só depois das tasks de falha).
