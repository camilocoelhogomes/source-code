# Task T27 — gap-sdk-dec015-conformity

| Campo | Valor |
|---|---|
| Task ID | `T27-gap-sdk-dec015-conformity` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` (candidata; aberta por auditoria filha) |
| Superfície | `sdk` |
| Origem | feature filha `mvp-e2e-audit-hardening` / T06 (`ParentGapFillBacklog`) |
| Evidência | `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md` |

## Classificação (REQ-017)

| Tipo | Motivo |
|---|---|
| `assert-fraco` | T21 smoke (denylist BDD-024): imagem sobe / tools smoke ≠ conformidade integral DEC-015/BR-024 |
| `gap-teste` | Falta evidência e2e integral das integrações pinadas (git SDK, Tree-sitter, Qdrant, Zoekt, delivery) |

## BDD lacunas cobertos

BDD-024.

## Objetivo

Elevar a prova BDD-024 de smoke para conformidade integral DEC-015 / BR-024 nas integrações relevantes — via suíte/testes do pai, não na feature filha.

## Escopo

- Expandir evidência além de tags smoke MCP/health: asserts de conformidade/pins nas integrações cobertas por DEC-015.
- Coordenar com testes unitários/BDD já existentes (local discovery git SDK, treesitter, qdrant, zoekt, container delivery) para fechar o critério integral e2e quando aplicável.

## Fora de escopo

- Declarar MVP entregue (auditoria T07).
- Fix tooling T22 (pré-req de stack).
- Implementação na feature filha (ENG-010).

## Critérios de aceite

- Evidência e2e/integrada satisfaz texto integral BDD-024 / DEC-015 (não só smoke).
- Sem secrets versionados.
- Implementação no pipeline do pai.

## Arquivos prováveis

- `e2e/robot/mcp.robot`, `e2e/robot/health.robot`
- testes BDD/unitários das integrações DEC-015
- manifests T19 quando aplicável

## Dependências

- T19–T21; T22 para stack e2e
- Evidência: inventário T01 + índice T06

## Handoff

- Ownership: `github-etl-mcp-rag`.
- Filha **não implementa** — sem alteração de `src/github_rag/**`, `e2e/robot/**` nem composes nessa feature.
