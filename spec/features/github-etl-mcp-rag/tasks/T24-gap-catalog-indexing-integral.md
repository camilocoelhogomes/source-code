# Task T24 — gap-catalog-indexing-integral

| Campo | Valor |
|---|---|
| Task ID | `T24-gap-catalog-indexing-integral` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` (candidata; aberta por auditoria filha) |
| Superfície | `catalog_indexing` |
| Origem | feature filha `mvp-e2e-audit-hardening` / T06 (`ParentGapFillBacklog`) |
| Evidência | `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md` |

## Classificação (REQ-017)

| Tipo | BDD | Motivo |
|---|---|---|
| `assert-fraco` | BDD-003, BDD-006 | T21 parcial/smoke (denylist): cron GET/PUT ≠ ciclo 24h; hits MD/Python ≠ exclusões CSV/binários/gitignore |
| `gap-teste` | BDD-005, BDD-017 | Sem assert e2e de commit novo → último processado; sem prova “somente main” / uncommitted excluído |

## BDD lacunas cobertos

BDD-003, BDD-005, BDD-006, BDD-017.

## Objetivo

Fortalecer asserts integrais da suíte T21 em `catalog_indexing` para fechar as lacunas do inventário — sem implementar nesta feature filha.

## Escopo

- Estender cenários/keywords Robot (e pytest de suporte se necessário no pai) para:
  - disparo/observação alinhada ao critério diário do scheduler (BDD-003);
  - mudança de commit / snapshot distinto refletida no estado (BDD-005);
  - exclusão CSV, imagens e caminhos `.gitignore` (BDD-006);
  - indexação local restrita à main / sem uncommitted (BDD-017).

## Fora de escopo

- Keywords/browser UI (T23).
- Fix tooling T22.
- Implementação na feature filha (ENG-010).

## Critérios de aceite

- Asserts e2e cobrem o texto integral dos BDD-003/005/006/017 (não só fatia DEC-019/T21 parcial).
- Nenhum segredo versionado.
- Implementação no pipeline do pai.

## Arquivos prováveis

- `e2e/robot/catalog_indexing.robot`
- `e2e/robot/resources/**`
- testes BDD/unitários de scheduler/indexing/eligibility no pai quando aplicável

## Dependências

- T21; T14/T15 (orchestrator/scheduler); T22 para re-run stack
- Evidência: inventário T01 + índice T06

## Handoff

- Ownership: `github-etl-mcp-rag`.
- Filha **não implementa** — sem alteração de `src/github_rag/**`, `e2e/robot/**` nem composes nessa feature.
