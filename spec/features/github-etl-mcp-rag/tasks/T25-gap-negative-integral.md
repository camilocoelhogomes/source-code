# Task T25 — gap-negative-integral

| Campo | Valor |
|---|---|
| Task ID | `T25-gap-negative-integral` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` (candidata; aberta por auditoria filha) |
| Superfície | `negative` |
| Origem | feature filha `mvp-e2e-audit-hardening` / T06 (`ParentGapFillBacklog`) |
| Evidência | `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md` |

## Classificação (REQ-017)

| Tipo | BDD | Motivo |
|---|---|---|
| `assert-fraco` | BDD-008 | Payload inválido / unknown id ≠ falha parcial pós-arquivos + histórico + reindex |
| `gap-teste` | BDD-018, BDD-022 | Sem volume ausente/inacessível na UI; sem CONFIG_PATH inválido fail-fast sem leak |

## BDD lacunas cobertos

BDD-008, BDD-018, BDD-022.

## Objetivo

Fortalecer cenários negativos integrais na suíte T21 (e asserts associados) para as lacunas do inventário.

## Escopo

- Falha parcial de pipeline com histórico observável e caminho de reindex (BDD-008).
- Volume local ausente/inacessível com erro correspondente (BDD-018; UI pode exigir browser via T23 — coordenar asserts).
- `CONFIG_PATH` ausente/malformado: fail-fast, sem aplicação parcial, sem leak de segredos (BDD-022).

## Fora de escopo

- Fix tooling T22.
- Implementação na feature filha (ENG-010).

## Critérios de aceite

- Asserts e2e/negativos cobrem o texto integral dos BDD-008/018/022.
- Sem secrets em logs/artefatos de teste.
- Implementação no pipeline do pai.

## Arquivos prováveis

- `e2e/robot/negative.robot`, `e2e/robot/catalog_indexing.robot`
- `e2e/robot/resources/**`
- testes de config loader / indexing orchestrator no pai

## Dependências

- T21; T22 para re-run; coordenação com T23 se assert UI
- Evidência: inventário T01 + índice T06

## Handoff

- Ownership: `github-etl-mcp-rag`.
- Filha **não implementa** — sem alteração de `src/github_rag/**`, `e2e/robot/**` nem composes nessa feature.
