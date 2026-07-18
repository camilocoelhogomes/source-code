# Task T11 — treesitter-chunker

| Campo | Valor |
|---|---|
| Task ID | `T11-treesitter-chunker` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W4 |

## Objetivo

Produzir chunks contextuais a partir de arquivos elegíveis usando Tree-sitter, antes da persistência RAG.

## Escopo

- Porta `ContextualChunker`.
- Chunking por linguagem quando grammar disponível; fallback documentado para textuais sem grammar (ex.: Markdown) sem falhar o pipeline inteiro por arquivo — política de erro alinhada a BR-005 no orquestrador (falha de etapa = falha do repo); definir no design se fallback é sucesso.
- Saída: chunks com path, ranges e texto.

## Fora de escopo

- SLM; Qdrant; Zoekt; orquestração.

## Dependências

- `T01-project-foundation`

## Critérios de aceite

- Arquivos suportados geram chunks não vazios em casos nominais.
- Corner cases: arquivo vazio, binário escapado, linguagem sem grammar.
- Contrato estável para T12/T13.

## Arquivos prováveis

- `src/.../index/chunking/treesitter.py`
- `src/.../index/chunking/types.py`
- `tests/unit/index/chunking/...`

## Rastreabilidade

- DEC-003; BDD-007 (etapa tree-sitter).

## Handoff

- Interface: `ContextualChunker`.
- Consumidores: `T12`/`T14`.
- Nota de design: política de fallback vs falha deve ser explícita e aprovada no pipeline da task (não contradizer BR-005).
