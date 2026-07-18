# Task T05 — github-discovery

| Campo | Valor |
|---|---|
| Task ID | `T05-github-discovery` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W2 |

## Objetivo

Descobrir repositórios GitHub a partir de conexões `type: github` (orgs + wildcards de inclusão), autenticando com token resolvido do ambiente.

## Escopo

- `GitHubRepoDiscovery` usando token de `token.env`.
- Filtro exclusivo de inclusão por wildcards de prefixo/sufixo.
- Público e privado conforme acesso do token.
- Erros de token ausente/inválido/sem acesso sem expor o segredo.
- Não aplicar conexões inválidas (já rejeitadas em T02).

## Fora de escopo

- Persistência no PostgreSQL (T07); clone/indexação; UI.

## Dependências

- `T02-config-loader`

## Critérios de aceite

- BDD-001, BDD-019; proteção BDD-014 nos logs/erros desta camada.
- Somente repos que casam wildcards entram no resultado.
- Token lido só via env referenciada; nunca serializado no resultado.

## Arquivos prováveis

- `src/.../sources/github/discovery.py`
- `src/.../sources/github/client.py` (porta HTTP mockável)
- `tests/bdd/...`
- `tests/unit/sources/github/...`

## Rastreabilidade

- REQ-010, REQ-011, REQ-041; BR-007, BR-008, BR-019, BR-022; DEC-001, DEC-009, DEC-014.

## Handoff

- Interface: `GitHubRepoDiscovery`.
- Consumidor: `T07-catalog-sync`.
- Risco: paginação/rate limit da API GitHub — tratar com testes de contrato e backoff mínimo se necessário sem expandir escopo de produto.
