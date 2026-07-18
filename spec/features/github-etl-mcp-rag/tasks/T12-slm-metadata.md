# Task T12 — slm-metadata

| Campo | Valor |
|---|---|
| Task ID | `T12-slm-metadata` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W4 |

## Objetivo

Abstrair geração de metadados contextuais por SLM, com default Qwen Coder 3B, sem uso para respostas MCP.

## Escopo

- Porta `MetadataGenerator` (provedor/modelo substituível).
- Implementação default apontando para runtime local configurável (ex.: Ollama/HTTP) — detalhe no design.
- Entrada: chunks; saída: metadados contextuais serializáveis.
- Garantir que a porta não seja usada pelo MCP (convenção + sem dependência cruzada).

## Fora de escopo

- Tools MCP; prosa de Discovery; UI chat completo (apoio à UI de busca semântica fica em T16/T18 usando a mesma abstração se necessário).

## Dependências

- `T01-project-foundation` (idealmente tipos de chunk de T11; pode depender de T11 se o Architect preferir — dependência fraca: DTOs).

## Critérios de aceite

- Troca de provedor/modelo sem alterar orquestrador (BR-009).
- Default documentado como Qwen Coder 3B.
- Falhas do modelo são erros tipados.
- Testes com fake generator.

## Arquivos prováveis

- `src/.../index/metadata/generator.py`
- `src/.../index/metadata/qwen.py`
- `tests/unit/index/metadata/...`

## Rastreabilidade

- BR-009, BR-010; DEC-006; BDD-007, BDD-010 (metadados/apoio).

## Handoff

- Interface: `MetadataGenerator`.
- Consumidores: `T14`; opcionalmente apoio UI em `T18` via query.
