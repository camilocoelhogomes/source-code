# Interfaces — T05-github-discovery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T05-github-discovery` |
| Autor | Implementation Task Runner + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T05-github-discovery` |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `DiscoveredGitHubRepo` | `sources/github/models.py` | Snapshot de repo descoberto |
| `GitHubRepoRaw` | `sources/github/models.py` | DTO da API (interno ao client) |
| `GitHubApiClient` | `sources/github/client.py` | Porta HTTP mockável |
| `HttpGitHubApiClient` | `sources/github/client.py` | Implementação urllib |
| `GitHubDiscoveryError` | `sources/github/discovery.py` | Erro tipado sem segredo |
| `GitHubRepoDiscovery` | `sources/github/discovery.py` | Orquestrador de descoberta |
| `matches_inclusion_pattern` | `sources/github/wildcard.py` | Filtro BR-022 |

### Fora de escopo

| Item | Dono |
|---|---|
| `ConfigLoader` / validação JSON | T02 |
| Persistência catálogo | T07 |
| Descoberta local | T06 |
| UI / MCP | T18 / T17 |

## 2. Decisões de contrato

| ID | Decisão | Motivo |
|---|---|---|
| I-T05-001 | `DiscoveredGitHubRepo` frozen dataclass sem campo token | BDD-019; handoff T07 |
| I-T05-002 | Porta `GitHubApiClient` separada de `GitHubRepoDiscovery` | Mock HTTP; DEC-014 testabilidade |
| I-T05-003 | Token passado ao client como parâmetro opaco; header Bearer | REQ-011; isolamento HTTP |
| I-T05-004 | Wildcard em módulo próprio | BR-022 testável sem rede |
| I-T05-005 | `discover(connection_name, connection)` retorna `tuple` ordenado | Determinismo catálogo |
| I-T05-006 | `repos` vazio ⇒ resultado vazio (sem match implícito) | BR-022 inclusão exclusiva |
| I-T05-007 | Erros via `GitHubDiscoveryError`; nunca valor do token na mensagem | BDD-014 / BR-008 |

## 3. Contratos detalhados

### 3.1 `DiscoveredGitHubRepo`

```python
@dataclass(frozen=True)
class DiscoveredGitHubRepo:
    connection_name: str
    full_name: str
    org: str
    name: str
    private: bool
```

- **Responsabilidade:** representar um repositório elegível descoberto para sync (T07).
- **Motivo da separação:** DTO de saída estável sem acoplar ao JSON da API GitHub nem ao catálogo PG.
- **Invariantes:** `full_name == f"{org}/{name}"`; sem segredo em str/repr.

### 3.2 `GitHubApiClient` (Protocol)

```python
@runtime_checkable
class GitHubApiClient(Protocol):
    def list_org_repos(self, org: str, *, token: str) -> Sequence[GitHubRepoRaw]: ...
```

- **Responsabilidade:** listar todos os repos de uma org (paginação interna na implementação HTTP).
- **Motivo da separação:** isola I/O de rede da lógica de wildcard e do modelo T02; testes injetam fake.
- **Erros:** implementação levanta `GitHubDiscoveryError` (sem token na mensagem).

### 3.3 `GitHubRepoDiscovery`

```python
class GitHubRepoDiscovery:
    def __init__(self, client: GitHubApiClient | None = None) -> None: ...

    def discover(
        self,
        connection_name: str,
        connection: GitHubConnection,
    ) -> tuple[DiscoveredGitHubRepo, ...]: ...
```

- **Responsabilidade:** orquestrar listagem por org + filtro de inclusão usando `connection.secret`.
- **Motivo da separação:** consumidor T07 depende de uma porta de domínio, não de urllib nem da API REST.
- **Invariantes:** assume `GitHubConnection` válida (T02); deduplica por `full_name`; ordena por `full_name`.
- **Erros:** `GitHubDiscoveryError` propagado do client ou envolvido com contexto de conexão/org.

### 3.4 `matches_inclusion_pattern(full_name: str, pattern: str) -> bool`

- **Responsabilidade:** avaliar se `full_name` casa padrão `org/repo_part` (prefixo, sufixo, `*`, exato).
- **Motivo da separação:** regra BR-022 pura, testável unitariamente sem mock de rede.
- **Invariantes:** org do padrão deve coincidir; padrões malformados (sem `/`) retornam `False`.

### 3.5 `GitHubDiscoveryError`

- **Responsabilidade:** falhas de descoberta (auth, rede, rate limit, org inacessível).
- **Motivo da separação:** distinto de `ConfigLoadError` (T02) e erros de catálogo (T07).
- **Invariantes:** `str(self)` não contém valor do token.

## 4. Reexports (`sources/github/__init__.py`)

```python
from github_rag.sources.github.discovery import GitHubDiscoveryError, GitHubRepoDiscovery
from github_rag.sources.github.models import DiscoveredGitHubRepo
from github_rag.sources.github.client import GitHubApiClient, HttpGitHubApiClient
```

## 5. Handoff T07

`CatalogSync` (T07) chamará `GitHubRepoDiscovery.discover(name, github_connection)` para cada conexão `type: github` do `AppConfig` e persistirá `DiscoveredGitHubRepo` no catálogo.
