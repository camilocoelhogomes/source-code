# Task T17 — mcp-evidence-server

| Campo | Valor |
|---|---|
| Task ID | `T17-mcp-evidence-server` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W7 |

## Objetivo

Disponibilizar servidor MCP com as tools aprovadas, retornando somente evidências, com consultas paralelas limitadas e sem uso do SLM para narrativa.

## Escopo

- Tools: `list_repos`, `search_code`, `semantic_search`, `read_file`, `list_tree`.
- Delegação a catálogo + `QueryService`.
- Paralelismo via `QUERY_WORKERS` / `WorkerLimiter`.
- Detalhes opcionais conforme solicitação (BDD-012).
- Proibir vazamento de token (BDD-014).
- Não expor `ask_codebase` nem geração narrativa.

## Fora de escopo

- UI; indexação; validação humana Discovery end-to-end completa (BDD-015 é critério de produto; task entrega capacidade das tools).

## Dependências

- `T04`, `T07`, `T16`

## Critérios de aceite

- BDD-011, BDD-012, BDD-013, BDD-014; suporte a BDD-015 (tools utilizáveis).
- Nenhuma chamada a `MetadataGenerator`/SLM no caminho MCP.
- Respostas contêm evidências estruturadas apenas.

## Arquivos prováveis

- `src/.../mcp/server.py`
- `src/.../mcp/tools/*.py`
- `tests/bdd/mcp/...`
- `tests/unit/mcp/...`

## Rastreabilidade

- REQ-003,028–033; DEC-008; BR-008, BR-011; BDD-011–015.

## Handoff

- Interface: `McpEvidenceServer`.
- Delivery (T19) expõe o processo MCP na imagem.
