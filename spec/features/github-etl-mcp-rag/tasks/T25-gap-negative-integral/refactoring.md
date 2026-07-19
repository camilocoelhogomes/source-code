# Refatoração Blue — T25-gap-negative-integral

| Campo | Valor |
|---|---|
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Data | 2026-07-19 |
| Versão | `0.1.0` |

## Baseline

| Métrica | Valor |
|---|---|
| Suíte | `1232 passed, 2 skipped` |
| Cobertura global | `96.64%` |
| Código novo crítico | `ui/issues.py` 100%; `ui/serialize.issue_to_view` 100%; probes fora do pacote e2e |

## Mudanças Blue (sem alteração de comportamento)

1. Probes relocados para `e2e/probes/` (já na implementação) para satisfazer UT-X04 — simplifica fronteira do pacote launcher.
2. Keyword Robot usa `${CURDIR}` (diretório do suite) em vez de `${EXECDIR}` — path estável independente do cwd do processo.
3. Sem otimizações de hot-path: nenhum gargalo mensurável; nada a micro-otimizar.

## Resultado pós-Blue

| Métrica | Valor |
|---|---|
| Suíte | inalterada em intenção (re-run confirma verde) |
| Cobertura | ≥ 95% mantida |
| Contratos | NEG-01..03 / I-T25-* intactos |

## Decisão Architect

`BLUE_APPROVED_BY_ARCHITECT` — sem gargalo comprovado; estrutura já mínima.
