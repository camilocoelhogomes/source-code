# Reviews — T05-open-failure-tasks-parent

## Review Design — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Versão revisada | `0.1.0` → `0.1.1` |
| Data | 2026-07-18 |
| Resultado | `APPROVED_BY_ARCHITECT` (após correção) |

### Checks executados

| Check | Resultado |
|---|---|
| Escopo só backlog (ENG-010) | OK |
| Consome T03+T04 reais | OK — pytest 0; F-T04-001..003 |
| Agrupamento ENG-006 / BR-006 | OK após M-01 |
| Classificação REQ-017 | OK após M-02 |
| Sem catalog/ui/mcp/negative inventados | OK |
| IDs após T21 | OK — T22 livre |
| Índice + BDD contrato | OK |

### Achados

| ID | Severidade | Evidência | Achado | Correção esperada | Status |
|---|---|---|---|---|---|
| M-01 | `MAJOR` | `design.md` v0.1.0 §3.3 T23; `runs/e2e-robot-green-path.md` L98–100, L113 | T23 `health` sem falha independente; F-T04-003 já `tooling-e2e` e consequência de F-T04-002; fase `healthy` = skip | Remover T23; só T22; índice declara health sem falha observável | Corrigido em `0.1.1` |
| M-02 | `MAJOR` | `design.md` v0.1.0 D-T05-003; T04 attempt A / S-01 | Classificação `produto` uniforme inclui F-T04-001 (compose provider no host) | Combinação REQ-017: F-T04-001=`flakiness`; F-T04-002=`produto`; F-T04-003=consequência | Corrigido em `0.1.1` |
| S-01 | `SUGGESTION` | `design.md` v0.1.0 §3.1 vs §3.6 | ID `D-T05-001` reutilizado para “opção A” e “não inventar falhas” | Renomear seção 3.1 para “abordagem”; manter D-T05-001 só na tabela de decisões | Corrigido em `0.1.1` |

### Bloqueios abertos

Nenhum `BLOCKING` / `MAJOR` aberto após `0.1.1`.

### Decisão

`APPROVED_BY_ARCHITECT` — design `0.1.1` apto para BDD/interfaces. Gate humano intermediário substituído pela aprovação Architect (modo autonomous). **Não** manter `APPROVED_BY_ARCHITECT` v0.1.0.
