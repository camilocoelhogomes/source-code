# Task T08 — main-snapshot

| Campo | Valor |
|---|---|
| Task ID | `T08-main-snapshot` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W3 |

## Objetivo

Obter o snapshot atual do commit da branch `main` para repositórios GitHub e locais, e expor quais **arquivos foram modificados** entre o último commit processado e o tip atual — base para reindexar o **arquivo inteiro** quando há mudança.

## Escopo

- `MainSnapshotProvider` unificado por origem.
- Operações Git locais (tip, árvore, diff) via **GitPython** (DEC-015 / BR-023); proibido parse ad-hoc de `.git`.
- Retornar commit SHA e acesso à árvore/arquivos daquele commit.
- Locais: usar commit de `main`, nunca working tree suja.
- GitHub: tip de `main` via PyGithub / clone shallow conforme design (porta mockável; sem client HTTP inventado).
- Porta/capacidade de **diff de arquivos** entre `last_processed_commit` e `current_main_commit`: lista de paths adicionados/modificados/removidos (sem inventar estados de repo).
- Conteúdo lido para reindexação é sempre o arquivo **completo** no tip da `main` (não patch/hunk isolado como unidade de indexação).

## Fora de escopo

- Filtro de elegibilidade (T09); orquestração de fila (T14); UI.

## Dependências

- `T01-project-foundation` (contratos de origem podem reutilizar tipos de T05/T06 quando disponíveis; não bloqueia design se usar DTOs próprios).

## Critérios de aceite

- BDD-005 (obter novo snapshot), BDD-017.
- Snapshot local ignora uncommitted e branches ≠ `main`.
- Dado dois SHAs, retorna o conjunto de arquivos alterados entre eles.
- Corner cases: `main` ausente, repo corrompido, rede GitHub falha, primeiro index (sem commit anterior) — erros tipados / conjunto = todos os elegíveis tratado em T14.

## Arquivos prováveis

- `src/.../snapshot/provider.py`
- `src/.../snapshot/github.py`
- `src/.../snapshot/local.py`
- `src/.../snapshot/diff.py`
- `tests/unit/snapshot/...`
- `tests/bdd/...`

## Rastreabilidade

- REQ-013; BR-002–004, BR-015, BR-023; DEC-015; BDD-004,005,017; BDD-024; ENG-012 (diff para reindexação por arquivo).

## Handoff

- Interface: `MainSnapshotProvider` (+ diff de arquivos entre commits).
- Consumidores: `T14`, `T16` (read/tree sobre commit indexado).
