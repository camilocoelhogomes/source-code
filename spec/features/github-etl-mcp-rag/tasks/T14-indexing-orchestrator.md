# Task T14 — indexing-orchestrator

| Campo | Valor |
|---|---|
| Task ID | `T14-indexing-orchestrator` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W5 |

## Objetivo

Orquestrar indexação sob demanda, em lote, **no startup do container** e via cron: seleção de repos, fila, estados REQ-020, skip de commit já processado, reindexação por **arquivo inteiro modificado**, Zoekt + pipeline RAG **Tree-sitter → SLM (por chunk) → Qdrant**, com progresso e reinício total do repositório em falha parcial.

## Escopo

- `IndexingOrchestrator` + fila respeitando `WorkerLimiter`.
- Estados exclusivamente REQ-020: `não indexado` | `na fila` | `indexando` | `atualizado` | `erro`. Sem estados extras.
- Transições: a partir de `não indexado` ou `erro` → `na fila` → `indexando` → `atualizado` | `erro`.
- Comparar commit `main` vs último processado no PostgreSQL (BR-002–004).
- **Commit novo na `main`:** tip ≠ último processado → `não indexado` (elegível); sem `desatualizado`.
- Skip de repositório: tip `main` = último processado → permanece `atualizado`.

### Startup reconcile (ENG-011)

- Após bootstrap de config + sync de catálogo, **no startup**: para cada repo do catálogo ativo, comparar tip `main` com último commit processado / estado no PostgreSQL.
- Enfileirar indexação dos que **não** estão `atualizado` com tip = último processado (inclui `não indexado`, `erro`, e tip ≠ processado → tratar como `não indexado` antes da fila).
- Respeitar `INDEX_WORKERS`; mesma política de falha (restart do repo inteiro).

### Reindexação por arquivo modificado (ENG-012)

- Quando há commit anterior processado e tip novo: obter arquivos alterados (T08); para cada path **modificado ou adicionado** e elegível (T09), reindexar o **arquivo inteiro** no tip atual (Zoekt + Tree-sitter em todo o arquivo → SLM por cada chunk → Qdrant substituindo pontos daquele path).
- **Proibido** indexar só um delta/hunk de linhas como substituto do arquivo completo quando o arquivo mudou.
- Paths **removidos**: remover entradas correspondentes dos índices (Zoekt/Qdrant) para aquele path/commit anterior.
- Primeiro index (sem último processado): processar todos os arquivos elegíveis do snapshot.
- Falha parcial em qualquer arquivo: estado `erro`; nova tentativa reinicia o **repositório inteiro** (BR-005) — política de falha inalterada.

### Pipeline por arquivo (quando o arquivo entra na leva)

1. Zoekt (arquivo completo)
2. Tree-sitter → chunks semânticos do arquivo completo
3. Para **cada** chunk: SLM → metadados
4. Qdrant: vetor + payload por chunk

- Progresso: percentual, arquivos, etapa; flags REQ-022.
- Disparo também por checkbox (UI) e cron (T15).

## Fora de escopo

- Implementação visual da UI; MCP; definição do compose (T19 documenta que o boot chama este reconcile).

## Dependências

- `T04`, `T07`, `T08`, `T09`, `T10`, `T11`, `T12`, `T13`

## Critérios de aceite

- BDD-002, BDD-004, BDD-005, BDD-007, BDD-008.
- Startup: repos cujo tip `main` ≠ último processado (ou não `atualizado`) entram na fila de indexação automaticamente.
- Arquivo modificado no commit → reindexação do arquivo **inteiro**; não apenas chunks parciais do diff.
- Pipeline RAG Tree-sitter → SLM por chunk → Qdrant.
- Workers respeitados.
- Commit igual → sem reprocessamento e permanece `atualizado`.
- Falha parcial → `erro` + restart completo do repo.
- Enum idêntico a REQ-020.

## Arquivos prováveis

- `src/.../indexing/orchestrator.py`
- `src/.../indexing/pipeline.py`
- `src/.../indexing/progress.py`
- `src/.../indexing/startup_reconcile.py`
- `tests/bdd/...`
- `tests/unit/indexing/...`

## Rastreabilidade

- REQ-005,012,016,018–022,024; BR-002–005,010,014; DEC-003,004,006; BDD-002,004,005,007,008; ENG-011, ENG-012.

## Handoff

- Interface: `IndexingOrchestrator` (+ `StartupIndexReconcile`).
- Consumidores: bootstrap/T19, `T15`, `T18`.
- Critical path; dono da sequência RAG e do reconcile de boot.
