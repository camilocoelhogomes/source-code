# Design — T05-github-discovery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T05-github-discovery` |
| Autor | Implementation Task Runner |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T05-github-discovery` |
| Base | `main` (T01–T04 mesclados) |
| Rastreabilidade | REQ-010, REQ-011, REQ-041; BR-007, BR-008, BR-019, BR-022; DEC-001, DEC-009, DEC-014; BDD-001, BDD-014, BDD-019 |

## 1. Contexto

T02 entrega `GitHubConnection` validada com `orgs`, `repos` (wildcards de inclusão), `token.env` e `secret` (`ResolvedSecret` opaco). T05 consome conexões já validadas — não revalida JSON nem resolve env — e lista repositórios GitHub acessíveis pelo token, filtrando exclusivamente por wildcards de inclusão (BR-022).

Fora de escopo: persistência (T07), clone/indexação, UI, conexões `type: git` (T06).

## 2. Problema

O bootstrap/catálogo precisa saber quais repositórios GitHub existem e são elegíveis **antes** de sincronizar o PostgreSQL (T07). A descoberta deve:

1. Autenticar com o token já resolvido em `GitHubConnection.secret` (BDD-019 / BR-019).
2. Listar repos por org configurada (públicos e privados conforme acesso do token — REQ-011).
3. Incluir **somente** repos que casam algum padrão em `connection.repos` (BR-022).
4. Nunca serializar o token no resultado nem em erlogs/mensagens (BDD-014 / BR-008).

## 3. Solução proposta

Módulo `github_rag.sources.github` com quatro responsabilidades:

| Componente | Papel |
|---|---|
| `models` | `DiscoveredGitHubRepo` — snapshot imutável sem segredo |
| `wildcard` | `matches_inclusion_pattern` — filtro prefixo/sufixo/exato/`org/*` |
| `client` | Porta `GitHubApiClient` — listagem paginada mockável |
| `discovery` | `GitHubRepoDiscovery` — orquestra client + filtro |

Fluxo feliz:

```text
GitHubConnection (T02) + connection_name
  → para cada org em connection.orgs:
      GitHubApiClient.list_org_repos(org, token=secret.get_value())
        → pagina até esgotar
  → união de repos brutos
  → filtrar: full_name casa algum padrão em connection.repos (BR-022)
  → se connection.repos vazio: resultado vazio (nenhum padrão de inclusão)
  → Sequence[DiscoveredGitHubRepo] (sem token)
```

Fluxo de erro:

```text
falha API/auth/rede → GitHubDiscoveryError (mensagem sem valor do token)
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T05 | Fora de T05 |
|---|---|---|
| BDD-001 | Somente repos acessíveis que casam wildcards | Listagem na UI (T18) |
| BDD-019 | Token via `secret` resolvido; ausente do resultado | Persistência UI |
| BDD-014 | Token ausente de `str(exc)` / repr de erros desta camada | Logs MCP/UI (T17/T18) |

## 4. Componentes

### 4.1 `DiscoveredGitHubRepo`

- Campos: `connection_name`, `full_name` (`org/repo`), `org`, `name`, `private: bool`.
- Imutável (`frozen=True`).
- `__str__`/`__repr__` sem segredo (não há campo de token).

### 4.2 `GitHubApiClient` (Protocol)

- `iter_org_repos(org: str, *, token: str) -> Iterator[GitHubRepoRaw]`.
- `list_org_repos(org: str, *, token: str) -> Sequence[GitHubRepoRaw]` (materializa a iteração).
- `GitHubRepoRaw`: `full_name`, `name`, `private`.
- Implementação default `PyGithubApiClient` usa `github.Github` / `Organization.get_repos`.
- Paginação: nativa do `PaginatedList` do PyGithub.
- Erros HTTP 401/403 → `GitHubDiscoveryError` genérico de autenticação/acesso.
- `RateLimitExceededException` → mensagem de rate limit (sem token).

### 4.3 Wildcard de inclusão

Padrão `org/repo_part` (validado em T02 na forma):

| Forma `repo_part` | Semântica |
|---|---|
| `*` | todos os repos da org |
| `prefix*` | nome começa com `prefix` |
| `*suffix` | nome termina com `suffix` |
| exato | igualdade |

Org do padrão deve coincidir com org do repo. Múltiplos padrões = união.

### 4.4 `GitHubRepoDiscovery`

- Entrada: `connection_name: str`, `connection: GitHubConnection`.
- Usa `connection.secret.get_value()` internamente; nunca expõe.
- Saída: tupla ordenada por `full_name` (determinismo para testes/catálogo).
- Erros: `GitHubDiscoveryError`.

## 5. Dados

| Campo descoberto | Origem |
|---|---|
| `connection_name` | argumento caller (T07) |
| `full_name`, `org`, `name`, `private` | API GitHub |
| Token | **nunca** no modelo de saída |

## 6. Erros e segurança

- `GitHubDiscoveryError`: mensagens citam org/conexão/status HTTP; **nunca** o token (BDD-014).
- Token só via `ResolvedSecret.get_value()` no client HTTP (header `Authorization: Bearer …`).
- Conexões inválidas já rejeitadas em T02 — T05 assume `GitHubConnection` válida.

## 7. Compatibilidade

- Consome tipos T02 sem alterar contratos.
- Handoff T07: `GitHubRepoDiscovery.discover(connection_name, connection)`.

## 8. Observabilidade

- Erros tipados com contexto (org, connection_name); sem logging de token nesta task.

## 9. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Paginação/rate limit | Paginação completa; erro explícito em rate limit; testes de contrato com client mock |
| Wildcards amplos | Filtro inclusão apenas; catálogo listável antes de indexar (plano §7) |

## 10. Rollback

Remover módulo `sources.github` além de `__init__.py`; sem migração de dados.
