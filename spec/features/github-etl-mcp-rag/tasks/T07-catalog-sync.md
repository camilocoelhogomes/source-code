# Task T07 — catalog-sync

| Campo | Valor |
|---|---|
| Task ID | `T07-catalog-sync` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W3 |

## Objetivo

Sincronizar repositórios descobertos (GitHub + local) para o catálogo PostgreSQL na inicialização, preservando estados/commits já conhecidos e expondo origem e conexão.

## Escopo

- Serviço de bootstrap: config válida → discovery → upsert no `CatalogRepository`.
- Campos: nome da conexão, origem, org ou path, estado inicial coerente com o enum REQ-020 apenas.
- Repositório presente na descoberta anterior e ausente da config/descoberta atual: **remover do catálogo ativo** (deixa de aparecer em UI/MCP). Histórico de execuções pode permanecer no PostgreSQL. **Não** inventar estado `indisponível` nem qualquer estado fora de REQ-020.
- Base para UI/MCP listarem o catálogo derivado da config (não editável).

## Fora de escopo

- Indexação; edição de config; busca; novos estados de UI.

## Dependências

- `T03-catalog-persistence`, `T05-github-discovery`, `T06-local-discovery`

## Critérios de aceite

- BDD-001, BDD-016, BDD-021, BDD-023 (catálogo refletido, sem CRUD de definições).
- Repositórios aparecem com origem `github` ou `local` e conexão de origem.
- Sync não reprocessa commits; apenas atualiza metadados de catálogo.
- Repo ausente da config atual não permanece listável no catálogo ativo e não usa estado fora de REQ-020.

## Arquivos prováveis

- `src/.../catalog/sync.py`
- `src/.../app/bootstrap.py`
- `tests/bdd/...`
- `tests/unit/catalog/sync_*.py`

## Rastreabilidade

- REQ-035; BR-001, BR-016, BR-017; BDD-001,016,021,023.

## Handoff

- Interface: `CatalogSync` (usa discoveries + repository).
- Consumidores: `T14`, `T17`, `T18`.
- Política de ausência: remoção do catálogo ativo + histórico retenível; zero estados extras.
