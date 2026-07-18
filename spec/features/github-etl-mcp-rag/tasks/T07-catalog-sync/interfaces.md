# Interfaces — T07-catalog-sync

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T07-catalog-sync` |
| Autor | Implementation Task Runner + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T07-catalog-sync` |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `CatalogSync` | `catalog/sync.py` | Orquestra discovery → upsert → soft-delete |
| `CatalogSyncResult` | `catalog/sync.py` | Snapshot imutável do resultado do sync |
| `CatalogSyncError` | `catalog/sync.py` | Falha fatal de sync (sem token na mensagem) |
| `run_catalog_sync` | `app/bootstrap.py` | Helper de boot; **não** reconcile/indexa |

### Fora de escopo

| Item | Dono |
|---|---|
| `CatalogRepository` / upsert / deactivate | T03 |
| `GitHubRepoDiscovery` / `DiscoveredGitHubRepo` | T05 |
| `LocalRepoDiscovery` / `LocalDiscoveryResult` / `LocalDiscoveryIssue` | T06 |
| `AppConfig` / loader | T02 |
| Startup reconcile / indexação | T14 |
| UI / MCP | T18 / T17 |

## 2. Decisões de contrato

| ID | Decisão | Motivo |
|---|---|---|
| I-T07-001 | `CatalogSync` recebe discoveries + `CatalogRepository` por injeção | Testabilidade; hexagonal; handoff brief |
| I-T07-002 | `sync(config: AppConfig) -> CatalogSyncResult` é a única operação de mutação pública | BDD-023 — sem CRUD de definições |
| I-T07-003 | Chave de identidade `(connection_name, repo_identifier)` | Paridade upsert T03 (D-T07-004) |
| I-T07-004 | Mapeamento GitHub: `origin=RepoOrigin.GITHUB`, `repo_identifier=full_name`, `github_org=org` | S-02; REQ-035 |
| I-T07-005 | Mapeamento local: `origin=RepoOrigin.LOCAL` (ou valor do DTO), `repo_identifier`, `local_path` a partir de `LocalDiscoveryResult.repos` | S-02; BDD-016 |
| I-T07-006 | `local_issues` = `LocalDiscoveryResult.issues` (passthrough) | S-02; CS-09 |
| I-T07-007 | Em `GitHubDiscoveryError`: **zero** `upsert`/`deactivate` nesta execução; envolve em `CatalogSyncError` | S-01 / CS-08 / D-T07-001 |
| I-T07-008 | Desativação só após discovery completo OK (github+local) | D-T07-001 |
| I-T07-009 | `run_catalog_sync` não chama reconcile/mark_*/start_execution | D-T07-003; CS-10; ENG-011 → T14 |
| I-T07-010 | Estados apenas via T03; T07 nunca atribui estado fora de REQ-020 | CS-12 |

## 3. Contratos detalhados

### 3.1 `CatalogSyncError`

```python
class CatalogSyncError(Exception):
    """Falha fatal na sincronização do catálogo."""
```

- **Responsabilidade:** sinalizar aborto do sync (tipicamente discovery GitHub) sem aplicar a fase de desativação; mensagem segura (sem valor de token).
- **Motivo da separação:** distinguir falha de orquestração T07 de `GitHubDiscoveryError` (T05) e de erros de persistência T03, mantendo redaction (BDD-014).
- **Invariantes:** `str(exc)` / `repr(exc)` nunca contêm o valor do token; causa opcional via `from err`.

### 3.2 `CatalogSyncResult`

```python
@dataclass(frozen=True)
class CatalogSyncResult:
    active: tuple[CatalogEntry, ...]
    upserted: tuple[CatalogEntry, ...]
    deactivated: tuple[CatalogEntry, ...]
    local_issues: tuple[LocalDiscoveryIssue, ...]
```

- **Responsabilidade:** expor o efeito observável de uma execução de sync para bootstrap/UI futura (contagens, issues).
- **Motivo da separação:** desacopla consumidores do I/O interno (ordem upsert/deactivate) e congela a forma do handoff para T14/T18.
- **Invariantes:**
  - `active` ≡ snapshot de `list_active_catalog()` pós-sync bem-sucedido.
  - `upserted` = entradas retornadas pelos `upsert_repository` desta execução (ordem estável: github por `full_name`, depois local por `repo_identifier`).
  - `deactivated` = entradas retornadas pelos `deactivate_repository` desta execução.
  - `local_issues` = issues T06 sem filtragem.

### 3.3 `CatalogSync`

```python
class CatalogSync:
    def __init__(
        self,
        *,
        catalog: CatalogRepository,
        github_discovery: GitHubRepoDiscovery,
        local_discovery: LocalRepoDiscovery,
    ) -> None: ...

    def sync(self, config: AppConfig) -> CatalogSyncResult: ...
```

- **Responsabilidade:** sincronizar o catálogo SoT com os repositórios descobertos a partir de `AppConfig` válido: discovery GitHub (por conexão) + discovery local → upsert → soft-delete dos ausentes.
- **Motivo da separação:** concentra a política de bootstrap do catálogo (BR-001/016) fora do loader (T02), das discoveries (T05/T06) e da persistência (T03), evitando que T14/T19 reimplementem a orquestração.
- **Algoritmo contratual de `sync`:**
  1. **Discovery GitHub (antes de qualquer mutação):** para cada `(name, conn)` em `config.connections` com `type == github` (isinstance `GitHubConnection`), chamar `github_discovery.discover(name, conn)`. Se levantar `GitHubDiscoveryError` → levantar `CatalogSyncError` **sem** chamar `upsert_repository` nem `deactivate_repository` (I-T07-007 / CS-08).
  2. **Discovery local:** `local_result = local_discovery.discover(config)` (issues não abortam).
  3. Construir conjunto `discovered_keys: set[tuple[str, str]]` e lista ordenada de candidatos a upsert:
     - GitHub: chave `(connection_name, full_name)`; mapear `RepoOrigin.GITHUB`, `github_org=org`, `local_path=None`.
     - Local: para cada item em `local_result.repos`; chave `(connection_name, repo_identifier)`; mapear `RepoOrigin.LOCAL` (ou `item.origin`), `local_path`, `github_org=None`.
  4. **Upserts:** para cada candidato, `catalog.upsert_repository(...)`.
  5. **Desativações:** para cada entrada em `catalog.list_active_catalog()` cuja chave ∉ `discovered_keys`, `catalog.deactivate_repository(entry.id)`.
  6. Retornar `CatalogSyncResult` com `active=tuple(catalog.list_active_catalog())`, `upserted`, `deactivated`, `local_issues=local_result.issues`.
- **Invariantes:**
  - Não chama `mark_*`, `start_execution`, `reconcile_repository`, `update_main_commit`, `update_progress`, `record_file_stage`.
  - Não inventa estado; novos repos herdam `not_indexed` do upsert T03.
  - Idempotente sob mesma discovery (metadados de origem/path podem atualizar; estado/commits preservados pelo T03).
- **Erros:** `CatalogSyncError` em falha GitHub; demais erros de repositório propagam conforme T03.

### 3.4 `run_catalog_sync`

```python
def run_catalog_sync(config: AppConfig, sync: CatalogSync) -> CatalogSyncResult:
    ...
```

- **Responsabilidade:** ponto de wire de bootstrap que executa apenas o sync de catálogo.
- **Motivo da separação:** estabiliza o handoff para T14/T19 (`sync` → depois reconcile) sem acoplar ENG-011 a T07; evita espalhar a chamada nos entrypoints.
- **Invariantes:** equivale a `return sync.sync(config)`; **não** executa reconcile nem indexação (CS-10).

## 4. Mapeamento discovery → upsert (S-02)

| Origem | Campo discovery | Argumento `upsert_repository` |
|---|---|---|
| GitHub | `connection_name` | `connection_name` |
| GitHub | — | `origin=RepoOrigin.GITHUB` |
| GitHub | `full_name` | `repo_identifier` |
| GitHub | `org` | `github_org` |
| GitHub | — | `local_path=None` (omitido) |
| Local | `connection_name` | `connection_name` |
| Local | `origin` (default LOCAL) | `origin=RepoOrigin.LOCAL` |
| Local | `repo_identifier` | `repo_identifier` |
| Local | `local_path` | `local_path` |
| Local | — | `github_org=None` (omitido) |

`LocalDiscoveryResult.issues` → `CatalogSyncResult.local_issues` (sem transformação).

## 5. Superfície pública e BDD-023

Pacote `github_rag.catalog` deve reexportar `CatalogSync`, `CatalogSyncResult`, `CatalogSyncError`.  
Pacote `github_rag.app` exporta `run_catalog_sync`.

**Proibido** nesta task: APIs `create_connection`, `update_repo_definition`, `delete_connection` ou equivalentes de CRUD de definições.

## 6. Compatibilidade

- Consome `AppConfig`, `GitHubConnection`, `GitConnection` (T02) sem alteração.
- Consome `GitHubRepoDiscovery` / `GitHubDiscoveryError` (T05) sem alteração.
- Consome `LocalRepoDiscovery` / `LocalDiscoveryResult` / `LocalDiscoveryIssue` (T06) sem alteração.
- Consome `CatalogRepository` / `CatalogEntry` / `RepoOrigin` (T03) sem alteração.
- Sem migration nova.

## 7. Checklist de aceite das interfaces

- [x] Comentários de responsabilidade e motivo da separação em cada contrato
- [x] S-01 (abort sem mutação) e S-02 (mapeamento origin/local) explicitados
- [x] Sem reconcile/indexação na superfície
- [x] Stubs/corpo `...` apenas até o gate de implementação (TDD)
