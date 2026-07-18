# Task T19 — container-delivery

| Campo | Valor |
|---|---|
| Task ID | `T19-container-delivery` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W8 |

## Objetivo

Empacotar o produto em imagens/compose para uso local padronizado: `CONFIG_PATH`, secrets por env, volumes de repos locais, UI e MCP disponíveis.

## Escopo

- Dockerfile(s) e `docker-compose` (app, postgres, qdrant, zoekt, runtime SLM se aplicável).
- Documentar env: `CONFIG_PATH`, token GitHub, `INDEX_WORKERS`, `QUERY_WORKERS`, horário diário default, recursos sugeridos.
- Montagem de volumes para JSON e `file:///repos/...` (ENG-005).
- Imagem primária `linux/amd64` (ENG-006).
- Healthchecks básicos para UI e MCP.

## Fora de escopo

- Novas features de domínio; registro corporativo obrigatório (dúvida não bloqueante).

## Dependências

- `T17-mcp-evidence-server`, `T18-management-ui`

## Critérios de aceite

- BDD-020; smoke de BDD-021/022 no boot do container.
- Com `CONFIG_PATH`, secrets e volumes corretos, UI e MCP sobem.
- Config inválida falha de forma observável sem aplicar parcial.

## Arquivos prováveis

- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `docs/runbook-local.md` ou seção no README
- `examples/config.json`

## Rastreabilidade

- REQ-036–038; DEC-011–012; BDD-020–022.

## Handoff

- Entrega final do MVP empacotado.
- Rollback: não publicar/usar a tag; volumes locais descartáveis.
