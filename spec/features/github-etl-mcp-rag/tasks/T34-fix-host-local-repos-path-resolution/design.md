# Design — T34-fix-host-local-repos-path-resolution

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T34-fix-host-local-repos-path-resolution` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T34-fix-host-local-repos-path-resolution` |
| Base | `main` |
| Rastreabilidade | F-W1-008; BDD-016; ENG-005; T06; T19; T21 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Remap `/repos` → `HOST_REPOS` no host; wiring explícito |

## 1. Contexto

Modelo e2e T21: app `github_rag.delivery` no **host** + infra em compose. Config declara `file:///repos/*` (convenção container ENG-005). No container, volume `${HOST_REPOS}:/repos:ro` resolve. No host, `/repos` não existe — discovery registra issue `local volume path is inaccessible: /repos`.

## 2. Problema

`HOST_REPOS` é setado pelo launcher e2e (`e2e/fixtures/repos`) mas `LocalRepoDiscovery` resolve literalmente `/repos`, ignorando o env.

## 3. Solução

### 3.1 `remap_repos_mount_path(path, host_repos)`

Em `git_fs.py`, função pura:

- Se `host_repos` vazio/ausente → retorna `path` inalterado (container/produção).
- Se `path.as_posix()` é `/repos` → `Path(host_repos).resolve()`.
- Se prefixo `/repos/` → `Path(host_repos).resolve() / suffix`.
- Demais paths → inalterados (paths absolutos custom, Windows).

### 3.2 `LocalRepoDiscovery`

Construtor aceita `host_repos: str | None = None`. Em `discover_connection`, após `parse_file_url`, aplica remap antes de `is_accessible`.

### 3.3 `wire_catalog_sync`

Passa `environ.get("HOST_REPOS")` para `LocalRepoDiscovery(host_repos=...)`.

## 4. Compatibilidade

- Container: sem `HOST_REPOS` ou mount em `/repos` → comportamento T06 inalterado.
- Config com paths absolutos (`file:///mnt/...`) → inalterado.
- Sem alteração em `e2e/robot/**` nem `e2e/fixtures/**`.

## 5. Erros

Issue message continua referenciando path **resolvido** (pós-remap) para diagnóstico operacional.

## 6. Rollback

Remover remap; operador usa paths absolutos no config ou roda app no container.

## 7. Riscos

| Risco | Mitigação |
|---|---|
| Remap acidental fora de e2e | Só ativa com `HOST_REPOS` não vazio |
| Path relativo em HOST_REPOS | `.resolve()` no remap |
