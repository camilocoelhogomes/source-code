# Task T13 — qdrant-vector-store

| Campo | Valor |
|---|---|
| Task ID | `T13-qdrant-vector-store` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W4 |

## Objetivo

Persistir e recuperar vetores/chunks no Qdrant para busca semântica baseada em embeddings.

## Escopo

- Porta `VectorStore`: upsert por repo/commit, delete/replace em reindexação completa, search semântico.
- Associação a metadados contextuais e localização (repo, path, commit, trecho).
- Geração/obtenção de embeddings atrás de porta (pode compor com T12 ou porta `Embedder` irmã — decidir no design sem acoplar ao MCP).

## Fora de escopo

- Narrativa SLM; Zoekt; UI/MCP diretos.

## Dependências

- `T01-project-foundation`

## Critérios de aceite

- Upsert + search retornam evidências semanticamente relacionadas (base BDD-010).
- Reindexação de repo substitui vetores do commit anterior de forma consistente com política de restart total.
- Testes com Qdrant fake/testcontainer conforme design.

## Arquivos prováveis

- `src/.../index/vector/qdrant_store.py`
- `src/.../index/vector/embedder.py`
- `tests/unit/index/vector/...`

## Rastreabilidade

- DEC-004; REQ-002; BR-011; BDD-010.

## Handoff

- Interfaces: `VectorStore`, opcionalmente `Embedder`.
- Consumidores: `T14`, `T16`.
