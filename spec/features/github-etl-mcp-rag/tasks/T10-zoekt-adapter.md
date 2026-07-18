# Task T10 — zoekt-adapter

| Campo | Valor |
|---|---|
| Task ID | `T10-zoekt-adapter` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W4 |

## Objetivo

Adaptar indexação e busca exata via Zoekt, incluindo metadados necessários ao índice.

## Escopo

- Porta `ExactCodeIndex`: indexar conjunto de arquivos de um repo/commit; buscar correspondências exatas.
- Integração com serviço Zoekt (cliente HTTP/CLI conforme design).
- Metadados mínimos: repositório, caminho, commit, trechos.

## Fora de escopo

- Chunks Tree-sitter; Qdrant; MCP/UI (consomem via T16).

## Dependências

- `T01-project-foundation`

## Critérios de aceite

- Indexação bem-sucedida torna conteúdo pesquisável por correspondência exata (base BDD-009).
- Falhas do Zoekt propagam erro tipado (para T14 reiniciar repo).
- Testes com double/fake do backend Zoekt.

## Arquivos prováveis

- `src/.../index/zoekt/client.py`
- `src/.../index/zoekt/index.py`
- `tests/unit/index/zoekt/...`

## Rastreabilidade

- DEC-002; REQ-002; BDD-009.

## Handoff

- Interface: `ExactCodeIndex`.
- Consumidores: `T14`, `T16`.
