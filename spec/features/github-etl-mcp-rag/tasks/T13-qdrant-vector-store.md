# Task T13 — qdrant-vector-store

| Campo | Valor |
|---|---|
| Task ID | `T13-qdrant-vector-store` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W4 |

## Objetivo

Persistir e recuperar no Qdrant **cada** unidade RAG como vetor + payload contendo o chunk Tree-sitter e os metadados contextuais gerados pela SLM para aquele chunk.

## Escopo

- Porta `VectorStore`: upsert por repo/commit, delete/replace em reindexação completa, search semântico.
- Integração Qdrant via **`qdrant-client`** (DEC-015 / BR-023); proibido client HTTP inventado.
- **Upsert por chunk enriquecido:** texto/localização do chunk Tree-sitter + metadados SLM no payload + vetor (embedding).
- Não redefine a unidade de chunk (não chunka por tamanho/linhas); consome apenas chunks Tree-sitter já enriquecidos.
- Porta `Embedder` (ou equivalente) para vetores — distinta da SLM de metadados; embeddings via SDK OpenAI-compatible (`openai`) apontando a runtime local (DEC-015).
- Busca semântica devolve evidências a partir desses pontos (BDD-010).

## Fora de escopo

- Narrativa SLM; Zoekt; geração de chunks; UI/MCP diretos.

## Dependências

- `T11-treesitter-chunker` (contrato do chunk; metadados tipados alinhados a T12)

## Critérios de aceite

- Persistência de um chunk exige payload com dados do chunk Tree-sitter **e** metadados SLM associados.
- Upsert + search retornam evidências semanticamente relacionadas (base BDD-010).
- Reindexação de repo substitui vetores do commit anterior (política de restart total).
- Testes com Qdrant fake/testcontainer conforme design.

## Arquivos prováveis

- `src/.../index/vector/qdrant_store.py`
- `src/.../index/vector/embedder.py`
- `tests/unit/index/vector/...`

## Rastreabilidade

- DEC-004, DEC-015; DEC-003 (unidade de chunk); BR-010, BR-023 (metadados no payload / SDK); REQ-002; BR-011; BDD-010; BDD-024.

## Handoff

- Interfaces: `VectorStore`, `Embedder`.
- Consumidores: `T14`, `T16`.
- Fluxo esperado do orquestrador: chunk Tree-sitter → metadados SLM → upsert Qdrant.
