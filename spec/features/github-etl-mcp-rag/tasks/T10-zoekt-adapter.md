# Task T10 — zoekt-adapter

| Campo | Valor |
|---|---|
| Task ID | `T10-zoekt-adapter` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W4 |

## Objetivo

Adaptar indexação e busca exata via Zoekt, incluindo metadados necessários ao índice.

## Escopo

- Porta `ExactCodeIndex`: indexar conjunto de arquivos de um repo/commit; buscar correspondências exatas.
- **Adaptador fino** sobre API HTTP e/ou CLI **oficial** do Zoekt (DEC-016); sem reinventar formato de índice nem protocolo proprietário; sem client inventado paralelo.
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

- DEC-002, DEC-016; REQ-002; BR-023; BDD-009; BDD-024.

## Handoff

- Interface: `ExactCodeIndex`.
- Consumidores: `T14`, `T16`.
