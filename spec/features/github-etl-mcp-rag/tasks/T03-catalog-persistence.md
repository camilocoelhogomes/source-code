# Task T03 — catalog-persistence

| Campo | Valor |
|---|---|
| Task ID | `T03-catalog-persistence` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W1 |

## Objetivo

Estabelecer PostgreSQL como fonte de verdade do catálogo de repositórios, estados de indexação, commits processados, progresso, etapas por arquivo e histórico de execuções.

## Escopo

- Schema/migrations versionadas.
- Modelo de domínio: conexão, origem (`github`|`local`), repositório, estados fechados, último commit processado, progresso, erros, histórico.
- `CatalogRepository` com operações necessárias ao sync e ao orquestrador.
- Registro de etapas por arquivo: Zoekt, Tree-sitter, metadados persistidos.

## Fora de escopo

- Descoberta de repos; pipeline de indexação; UI; Qdrant/Zoekt.

## Dependências

- `T01-project-foundation`

## Critérios de aceite

- Estados apenas (REQ-020): `não indexado`, `na fila`, `indexando`, `atualizado`, `erro`.
- Persistência permite comparar commit atual vs último processado (suporte a BDD-004/005 e ao **startup reconcile** ENG-011).
- Consultas/leituras necessárias ao reconcile: listar catálogo ativo com estado + `last_processed_commit`.
- Histórico de execução com mensagem e horário de erro (suporte a BDD-008).
- Testes unitários cobrem transições e corner cases (repo inexistente, update concorrente básico).

## Arquivos prováveis

- `src/.../catalog/models.py`
- `src/.../catalog/repository.py`
- `migrations/` ou equivalente
- `tests/unit/catalog/...`

## Rastreabilidade

- BR-001, BR-004; dados operacionais do requirements; BDD-004,007,008 (camada de persistência).

## Handoff

- Interface: `CatalogRepository`.
- Consumidor principal: `T07`, depois `T14`, `T18`.
- Decisão: schema versionado desde o início para evitar migrações ad hoc.
