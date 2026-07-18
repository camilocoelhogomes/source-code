# Task T16 — query-services

| Campo | Valor |
|---|---|
| Task ID | `T16-query-services` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W6 |

## Objetivo

Expor serviços de consulta compartilhados: busca exata, busca semântica, `read_file` e `list_tree`, com detalhes opcionais sob demanda.

## Escopo

- `QueryService` (ou portas compostas) sobre Zoekt, Qdrant e snapshot/catálogo.
- Campos opcionais: repositório, caminho, commit, trecho — só quando solicitados.
- Busca semântica via embeddings/Qdrant; SLM pode apoiar reformulação na UI (porta opcional), nunca gerar evidência falsa.
- Sem narrativa MCP.

## Fora de escopo

- Servidor MCP; telas UI; indexação.

## Dependências

- `T07`, `T08`, `T10`, `T13`

## Critérios de aceite

- BDD-009, BDD-010, BDD-012 (camada de serviço).
- Resultados sem detalhes não solicitados.
- Falhas de backends tipadas.

## Arquivos prováveis

- `src/.../query/service.py`
- `src/.../query/exact.py`
- `src/.../query/semantic.py`
- `src/.../query/browse.py`
- `tests/bdd/...`
- `tests/unit/query/...`

## Rastreabilidade

- REQ-002,026–027,030; BR-011; BDD-009–012.

## Handoff

- Interface: `QueryService`.
- Consumidores: `T17`, `T18` — única fachada de consulta.
