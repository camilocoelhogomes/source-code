# Task T06 — open-gap-fill-tasks-parent

| Campo | Valor |
|---|---|
| Task ID | `T06-open-gap-fill-tasks-parent` |
| Feature | `mvp-e2e-audit-hardening` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W4 |
| Plano | v0.1.0 |

## Objetivo

Após o run-first e as tasks de falha, abrir no pai as tasks de lacuna (`gap-teste` / `assert-fraco`) para cobertura integral BDD-001–024 (exc. 015), incluindo **browser** nos fluxos UI.

## Escopo

- Consumir inventário T01 + índice T05 (evitar duplicar falha já coberta como “só gap” sem referência cruzada).
- Abrir tasks em `github-etl-mcp-rag/tasks/` (IDs após os de T05) agrupadas por superfície.
- Obrigatório: task(s) `ui` exigindo automação browser (Browser Library / Playwright / equivalente); API HTTP sozinha não encerra lacuna UI (BDD-006).
- Cobrir lacunas de asserts integrais (ex.: BDD marcados parciais no design T21: 003, 006, 013, 024 smoke, etc.) via classificação `gap-teste` / `assert-fraco`.
- Tasks descrevem o que fortalecer na suíte T21; **não** implementam keywords nesta feature.

## Fora de escopo

- Executar novamente o green path só para “passar” após expandir suíte (fica nas tasks do pai).
- Implementar browser/keywords aqui.
- BDD-015.
- Tasks de falha runtime (já em T05).

## Dependências

- **Dura:** T01, T05 (BR-007 / DEC-008).

## Critérios de aceite

- Toda lacuna do inventário vira task no pai mesmo com green path verde (BDD-008).
- Gap-fill UI inclui browser (BDD-006; REQ-007).
- Ordem respeitada: falhas antes de lacunas (BDD-007).
- Ownership Robot permanece no pai/T21 (BR-002).

## Arquivos prováveis

- `spec/features/github-etl-mcp-rag/tasks/T2N-gap-*.md` (IDs após backlog T05)
- `spec/features/mvp-e2e-audit-hardening/audit/gap-fill-backlog-index.md`

## Rastreabilidade

- REQ-005–007, REQ-018–019; BR-007–008; DEC-003, DEC-008; ENG-008–009; BDD-006, BDD-007, BDD-008.

## Handoff

- Alimenta T07.
- Implementação das tasks de gap = pipeline do pai (não desta feature).
