# Task T14 — indexing-orchestrator

| Campo | Valor |
|---|---|
| Task ID | `T14-indexing-orchestrator` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W5 |

## Objetivo

Orquestrar indexação sob demanda e em lote: seleção de repos, fila, estados REQ-020, skip de commit já processado, pipeline Zoekt→Tree-sitter→metadados→persistência, progresso e reinício total do repositório em falha parcial.

## Escopo

- `IndexingOrchestrator` + fila respeitando `WorkerLimiter`.
- Estados exclusivamente REQ-020: `não indexado` | `na fila` | `indexando` | `atualizado` | `erro`. **Proibido** `desatualizado` ou qualquer outro.
- Transições: a partir de `não indexado` ou `erro` → `na fila` → `indexando` → `atualizado` | `erro`.
- Comparar commit `main` vs último processado (BR-002–004).
- **Commit novo na `main`:** se o tip de `main` ≠ último commit processado, o repositório **não** pode permanecer `atualizado` (BR-004). Transicionar para `não indexado` e torná-lo elegível a indexação. Sem estado intermediário inventado.
- Skip: somente quando commit atual da `main` = último processado → permanece `atualizado` e não reprocessa.
- Progresso: percentual, arquivos processados, etapa atual; flags por arquivo (Zoekt, Tree-sitter, metadata).
- Falha em qualquer etapa: estado `erro`, mensagem, horário e histórico; nova tentativa reinicia repo inteiro (limpa artefatos parciais via portas).
- Mesmo pipeline para GitHub e local (BR-014).
- Disparo por seleção (checkbox) — API de aplicação; UI em T18.

## Fora de escopo

- Scheduler diário (T15); MCP; implementação visual da UI.

## Dependências

- `T04`, `T07`, `T08`, `T09`, `T10`, `T11`, `T12`, `T13`

## Critérios de aceite

- BDD-002, BDD-004, BDD-005, BDD-007, BDD-008.
- Workers respeitados.
- Commit igual → sem reprocessamento e permanece `atualizado`.
- Commit da `main` diferente do processado → estado `não indexado` (não `desatualizado`) e elegível a reindexação.
- Falha parcial → `erro` + restart completo na próxima execução.
- Enum de estados idêntico a REQ-020.

## Arquivos prováveis

- `src/.../indexing/orchestrator.py`
- `src/.../indexing/pipeline.py`
- `src/.../indexing/progress.py`
- `tests/bdd/...`
- `tests/unit/indexing/...`

## Rastreabilidade

- REQ-005,012,016,018–022,024; BR-002–005,014; BDD-002,004,005,007,008.

## Handoff

- Interface: `IndexingOrchestrator`.
- Consumidores: `T15`, `T18`.
- Critical path task.
