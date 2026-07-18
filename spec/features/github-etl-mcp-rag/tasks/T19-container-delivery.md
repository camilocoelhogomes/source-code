# Task T19 — container-delivery

| Campo | Valor |
|---|---|
| Task ID | `T19-container-delivery` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W8 |

## Objetivo

Empacotar o produto em imagens/compose para uso local padronizado: `CONFIG_PATH`, secrets por env, volumes de repos locais, UI e MCP disponíveis, com **reconcile de indexação no startup** do container.

## Escopo

- Dockerfile(s) e `docker-compose` (app, postgres, qdrant, zoekt, runtime SLM se aplicável).
- Instalar na imagem as **deps/SDKs** das tasks (PyGithub, GitPython, pathspec, tree-sitter + grammars, qdrant-client, openai, APScheduler, mcp, FastAPI, SQLAlchemy/Alembic/psycopg3, etc.) — sem omitir T20/GitPython.
- Documentar env: `CONFIG_PATH`, token GitHub, `INDEX_WORKERS`, `QUERY_WORKERS`, **`INDEX_CRON`**, recursos sugeridos.
- Montagem de volumes para JSON e `file:///repos/...` (ENG-005).
- Imagem primária `linux/amd64` (ENG-006).
- Healthchecks básicos para UI e MCP.
- **Boot do container (ENG-011):** após config válida + sync de catálogo, a aplicação **deve** executar a validação de indexação (comparar tip `main` × PostgreSQL) e enfileirar repos que não estejam `atualizado` — via `IndexingOrchestrator` / startup reconcile (T14). Não inventar estados.

## Fora de escopo

- Novas features de domínio; registro corporativo obrigatório (dúvida não bloqueante).

## Dependências

- `T17-mcp-evidence-server`, `T18-management-ui`, `T20-refactor-local-discovery-git-sdk` (BDD-024 / DT-001 fechada na entrega; e, na prática, T14 já integrado na app empacotada)

## Critérios de aceite

- BDD-020; smoke de BDD-021/022 no boot do container.
- Com `CONFIG_PATH`, secrets e volumes corretos, UI e MCP sobem **e** o reconcile de startup é disparado (repos desatualizados vs PostgreSQL entram na fila conforme T14).
- Config inválida falha de forma observável sem aplicar parcial.

## Arquivos prováveis

- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `docs/runbook-local.md` ou seção no README
- `examples/config.json`

## Rastreabilidade

- REQ-036–038; DEC-011–012, DEC-015; BR-023–024; BDD-020–022; BDD-024; ENG-011.

## Handoff

- Entrega final do MVP empacotado.
- Rollback: não publicar/usar a tag; volumes locais descartáveis.
