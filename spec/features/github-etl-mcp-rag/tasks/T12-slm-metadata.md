# Task T12 — slm-metadata

| Campo | Valor |
|---|---|
| Task ID | `T12-slm-metadata` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W4 |

## Objetivo

Gerar metadados contextuais com a **SLM local** (abstrata; default Qwen Coder 3B) **para cada chunk** produzido pelo Tree-sitter, a serem salvos no payload do Qdrant (BR-010, DEC-006).

## Escopo

- Porta `MetadataGenerator` (provedor/modelo substituível).
- Adaptador default: cliente **OpenAI-compatible** (`openai`) apontando a runtime local (DEC-015 / BR-023); proibido client HTTP inventado.
- **Entrada:** um chunk Tree-sitter (unidade de T11) — geração **por chunk**, não por arquivo agregado como substituto do per-chunk.
- **Saída:** metadados contextuais serializáveis associados àquele chunk.
- Implementação default apontando para runtime SLM local configurável — detalhe no design.
- Não inventa chunks; não substitui Tree-sitter; não é usada para respostas MCP (BR-010).

## Fora de escopo

- Tools MCP; prosa de Discovery; upsert Qdrant (T13); UI chat completo (apoio opcional à busca na UI permanece possível via mesma abstração em T16/T18).

## Dependências

- `T11-treesitter-chunker` (contrato do chunk)

## Critérios de aceite

- Dado N chunks Tree-sitter, a porta é invocável N vezes (uma por chunk) produzindo N conjuntos de metadados.
- Troca de provedor/modelo sem alterar orquestrador (BR-009).
- Default documentado como Qwen Coder 3B (DEC-006).
- Falhas do modelo são erros tipados (alimentam restart total do repo em T14).
- Testes com fake generator cobrindo per-chunk e falha no meio da lista.

## Arquivos prováveis

- `src/.../index/metadata/generator.py`
- `src/.../index/metadata/qwen.py`
- `tests/unit/index/metadata/...`

## Rastreabilidade

- BR-009, BR-010, BR-023; DEC-006, DEC-015; REQ-022; BDD-007, BDD-010; BDD-024.

## Handoff

- Interface: `MetadataGenerator`.
- Consumidor principal: `T14` (loop por chunk antes do Qdrant).
- Par com T13: payload Qdrant inclui estes metadados.
