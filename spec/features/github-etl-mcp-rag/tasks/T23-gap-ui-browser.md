# Task T23 — gap-ui-browser

| Campo | Valor |
|---|---|
| Task ID | `T23-gap-ui-browser` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` (candidata; aberta por auditoria filha) |
| Superfície | `ui` |
| Origem | feature filha `mvp-e2e-audit-hardening` / T06 (`ParentGapFillBacklog`) |
| Evidência | `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md` |

## Classificação (REQ-017)

| Tipo | Motivo |
|---|---|
| `gap-teste` (primária) | Fluxos UI sem evidência browser (`evidencia_browser=nao`) |
| `assert-fraco` | T21 cobre via RequestsLibrary / API-smoke; critério integral exige UI no browser |

## BDD lacunas cobertos

BDD-001, BDD-002, BDD-007, BDD-009, BDD-010, BDD-016, BDD-019, BDD-023.

## Objetivo

Fortalecer a suíte Robot T21 com **automação browser** (Browser Library / Playwright / equivalente) para os fluxos UI do inventário — listagem com wildcards, seleção/indexação, progresso, buscas exata/semântica, origem local, ausência de token na UI, bloqueio de CRUD de connections na UI.

**API HTTP sozinha não encerra** esta lacuna UI (ENG-008 / BDD-006 da feature filha).

## Escopo

- Adicionar keywords/cenários browser em `e2e/robot/**` (tipicamente `ui.robot` / resources).
- Cobrir asserts visuais/interação para os BDD listados conforme texto integral do pai.
- Manter ownership Robot no pai (BR-002 da auditoria).

## Fora de escopo

- Implementação nesta feature filha `mvp-e2e-audit-hardening` (ENG-010).
- Correção de tooling compose/zoekt (já T22).
- BDD-015.

## Critérios de aceite

- Automação **browser** exercita os fluxos UI dos BDD-001/002/007/009/010/016/019/023.
- RequestsLibrary / `GET|POST /api/*` **sozinha** não é aceite suficiente.
- Nenhum segredo versionado.
- Implementação no **pipeline do pai**; a filha só abriu o backlog.

## Arquivos prováveis

- `e2e/robot/ui.robot`, `e2e/robot/catalog_indexing.robot`
- `e2e/robot/resources/**`, `e2e/robot/libraries/**`
- dependências Browser/Playwright no ambiente e2e (T19/T21)

## Dependências

- T21 (suíte Robot), T18 (management UI)
- T22 (stack e2e saudável antes de re-rodar)
- Evidência auditoria: inventário T01 + índice T06

## Handoff

- Ownership: `github-etl-mcp-rag` (esta task).
- Feature filha **não implementa** keywords/browser — sem alteração de `src/github_rag/**`, `e2e/robot/**` nem composes **nessa** feature.
