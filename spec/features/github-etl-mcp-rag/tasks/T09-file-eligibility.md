# Task T09 — file-eligibility

| Campo | Valor |
|---|---|
| Task ID | `T09-file-eligibility` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W3 |

## Objetivo

Filtrar arquivos do snapshot: incluir textuais de desenvolvimento (qualquer linguagem, incl. Markdown e Java); excluir CSV, imagens e paths cobertos por `.gitignore` (ex.: `target`, `node_modules`).

## Escopo

- `FileEligibilityFilter` puro e testável.
- Matching de `.gitignore` via **pathspec** (GitWildMatch) — DEC-015 / BR-023; alternativa aceitável: GitPython check-ignore se documentada. Proibido reimplementar GitWildMatch do zero.
- Regras de inclusão/exclusão alinhadas a REQ-014–015.
- Sem limite funcional de tamanho no MVP (REQ-019) — não introduzir caps de produto.

## Fora de escopo

- Leitura remota; indexação; UI.

## Dependências

- `T01-project-foundation`

## Critérios de aceite

- BDD-006 completo.
- Corner cases: sem `.gitignore`, gitignore aninhado, extensões mistas, arquivos sem extensão tratados de forma documentada nos testes.

## Arquivos prováveis

- `src/.../eligibility/filter.py`
- `src/.../eligibility/rules.py`
- `tests/bdd/...`
- `tests/unit/eligibility/...`

## Rastreabilidade

- REQ-014, REQ-015, REQ-019; BR-023; DEC-015; BDD-006; BDD-024.

## Handoff

- Interface: `FileEligibilityFilter`.
- Consumidor: `T14`.
