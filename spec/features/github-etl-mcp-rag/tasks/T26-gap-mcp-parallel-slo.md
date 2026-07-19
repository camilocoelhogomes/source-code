# Task T26 — gap-mcp-parallel-slo

| Campo | Valor |
|---|---|
| Task ID | `T26-gap-mcp-parallel-slo` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` (candidata; aberta por auditoria filha) |
| Superfície | `mcp` |
| Origem | feature filha `mvp-e2e-audit-hardening` / T06 (`ParentGapFillBacklog`) |
| Evidência | `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md` |

## Classificação (REQ-017)

| Tipo | Motivo |
|---|---|
| `assert-fraco` | T21 parcial (denylist BDD-013): duas calls com sucesso ≠ paralelismo sob limite + fila de excedentes / SLO |

## BDD lacunas cobertos

BDD-013.

## Objetivo

Fortalecer asserts MCP da suíte T21 para paralelismo real sob limite configurado e comportamento de fila/excedentes conforme critério integral BDD-013.

## Escopo

- Estender `e2e/robot/mcp.robot` (e suporte worker limiter) para observar concorrência + fila até o limite.
- Não confundir com smoke sequencial atual.

## Fora de escopo

- Tools MCP já cobertos integrais (BDD-011/012/014).
- Implementação na feature filha (ENG-010).

## Critérios de aceite

- Assert e2e prova paralelismo + fila/SLO alinhado ao texto integral BDD-013.
- Sem secrets (tokens) ecoados (manter BDD-014).
- Implementação no pipeline do pai.

## Arquivos prováveis

- `e2e/robot/mcp.robot`
- `e2e/robot/resources/**`
- testes `test_mcp_evidence_server` / `test_worker_limiter` no pai

## Dependências

- T17, T21; T22 para re-run stack
- Evidência: inventário T01 + índice T06

## Handoff

- Ownership: `github-etl-mcp-rag`.
- Filha **não implementa** — sem alteração de `src/github_rag/**`, `e2e/robot/**` nem composes nessa feature.
