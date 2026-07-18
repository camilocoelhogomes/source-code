# Task T14 — indexing-orchestrator

| Campo | Valor |
|---|---|
| Task ID | `T14-indexing-orchestrator` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W5 |

## Objetivo

Orquestrar indexação sob demanda e em lote: seleção de repos, fila, estados REQ-020, skip de commit já processado, Zoekt para busca exata e pipeline RAG **Tree-sitter → SLM (por chunk) → Qdrant**, com progresso e reinício total do repositório em falha parcial.

## Escopo

- `IndexingOrchestrator` + fila respeitando `WorkerLimiter`.
- Estados exclusivamente REQ-020: `não indexado` | `na fila` | `indexando` | `atualizado` | `erro`. Sem estados extras.
- Transições: a partir de `não indexado` ou `erro` → `na fila` → `indexando` → `atualizado` | `erro`.
- Comparar commit `main` vs último processado (BR-002–004).
- **Commit novo na `main`:** tip ≠ último processado → `não indexado` (elegível); sem `desatualizado`.
- Skip: tip `main` = último processado → permanece `atualizado`.
- Por arquivo elegível:
  1. Zoekt (índice exato)
  2. Tree-sitter → lista de chunks semânticos (**única** fonte; sem chunking por tamanho/linhas)
  3. Para **cada** chunk: SLM local → metadados contextuais (BR-010, DEC-006)
  4. Para **cada** chunk enriquecido: persistir no Qdrant (vetor + payload com chunk + metadados) (DEC-004)
- Progresso: percentual, arquivos, etapa; flags por arquivo Zoekt / Tree-sitter / metadados persistidos (REQ-022).
- Falha em qualquer etapa (incl. SLM ou Qdrant no meio dos chunks): `erro` + histórico; nova tentativa reinicia o repo inteiro.
- Mesmo pipeline GitHub e local (BR-014).
- Disparo por checkbox — API; UI em T18.

## Fora de escopo

- Scheduler diário (T15); MCP; UI visual.

## Dependências

- `T04`, `T07`, `T08`, `T09`, `T10`, `T11`, `T12`, `T13`

## Critérios de aceite

- BDD-002, BDD-004, BDD-005, BDD-007, BDD-008.
- Pipeline RAG executa Tree-sitter → SLM por chunk → Qdrant; não grava no Qdrant chunks que não sejam Tree-sitter nem sem metadados SLM.
- Workers respeitados.
- Commit igual → sem reprocessamento e permanece `atualizado`.
- Commit diferente → `não indexado` e elegível.
- Falha parcial → `erro` + restart completo.
- Enum idêntico a REQ-020.

## Arquivos prováveis

- `src/.../indexing/orchestrator.py`
- `src/.../indexing/pipeline.py`
- `src/.../indexing/progress.py`
- `tests/bdd/...`
- `tests/unit/indexing/...`

## Rastreabilidade

- REQ-005,012,016,018–022,024; BR-002–005,010,014; DEC-003,004,006; BDD-002,004,005,007,008.

## Handoff

- Interface: `IndexingOrchestrator`.
- Consumidores: `T15`, `T18`.
- Critical path; dono da sequência RAG obrigatória.
