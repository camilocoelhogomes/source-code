# Task T11 — treesitter-chunker

| Campo | Valor |
|---|---|
| Task ID | `T11-treesitter-chunker` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W4 |

## Objetivo

Produzir a **única** unidade de chunk semântico/RAG a partir de arquivos elegíveis via **Tree-sitter** (DEC-003), antes de metadados SLM e persistência no Qdrant.

## Escopo

- Porta `ContextualChunker` baseada em Tree-sitter.
- A saída desta porta é a **fonte exclusiva** dos chunks usados no RAG semântico.
- **Proibido** chunking genérico por tamanho, janela deslizante ou linhas como fonte de chunks semânticos.
- Chunking estrutural por linguagem com grammar Tree-sitter; para textuais (ex.: Markdown) usar grammar/parser Tree-sitter adequado — não substituir por split por linhas/bytes.
- Política de erro (grammar ausente/falha de parse) alinhada a BR-005 no orquestrador; detalhar no design **sem** introduzir chunking por tamanho/linhas.
- Saída: chunks com path, ranges, texto e identificação estável para T12/T13/T14.

## Fora de escopo

- SLM; Qdrant; Zoekt; orquestração; embeddings.

## Dependências

- `T01-project-foundation`

## Critérios de aceite

- Arquivos suportados geram chunks Tree-sitter não vazios em casos nominais.
- Nenhum caminho de produção de chunk semântico usa split por tamanho/linhas.
- Corner cases: arquivo vazio, binário escapado, grammar indisponível — erros/política tipados sem fallback genérico de chunking.
- Contrato estável para T12 (metadados por chunk) e T13 (payload).

## Arquivos prováveis

- `src/.../index/chunking/treesitter.py`
- `src/.../index/chunking/types.py`
- `tests/unit/index/chunking/...`

## Rastreabilidade

- DEC-003; REQ-022 (etapa Tree-sitter); BDD-007.

## Handoff

- Interface: `ContextualChunker`.
- Consumidores: `T12`, `T13`, `T14`.
- Fluxo seguinte obrigatório: cada chunk → SLM (T12) → Qdrant (T13) via T14.
