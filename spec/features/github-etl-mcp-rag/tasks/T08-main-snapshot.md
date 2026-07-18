# Task T08 — main-snapshot

| Campo | Valor |
|---|---|
| Task ID | `T08-main-snapshot` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W3 |

## Objetivo

Obter o snapshot atual do commit da branch `main` para repositórios GitHub e locais, excluindo outras branches e alterações não confirmadas.

## Escopo

- `MainSnapshotProvider` unificado por origem.
- Retornar commit SHA e acesso à árvore/arquivos daquele commit.
- Locais: usar commit de `main`, nunca working tree suja.
- GitHub: snapshot do tip de `main` via API ou clone shallow conforme design (porta mockável).

## Fora de escopo

- Filtro de elegibilidade (T09); indexação; comparação com DB (orquestrador T14).

## Dependências

- `T01-project-foundation` (contratos de origem podem reutilizar tipos de T05/T06 quando disponíveis; não bloqueia design se usar DTOs próprios).

## Critérios de aceite

- BDD-005 (obter novo snapshot), BDD-017.
- Snapshot local ignora uncommitted e branches ≠ `main`.
- Corner cases: `main` ausente, repo corrompido, rede GitHub falha — erros tipados.

## Arquivos prováveis

- `src/.../snapshot/provider.py`
- `src/.../snapshot/github.py`
- `src/.../snapshot/local.py`
- `tests/unit/snapshot/...`
- `tests/bdd/...`

## Rastreabilidade

- REQ-013; BR-002–004, BR-015; BDD-004,005,017.

## Handoff

- Interface: `MainSnapshotProvider`.
- Consumidores: `T14`, `T16` (read/tree sobre commit indexado).
