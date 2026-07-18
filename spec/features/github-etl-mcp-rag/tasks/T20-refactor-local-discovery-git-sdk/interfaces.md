# Interfaces — T20-refactor-local-discovery-git-sdk

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T20-refactor-local-discovery-git-sdk` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` |

## 1. Escopo da mudança de contrato

**Nenhuma alteração de superfície pública.** Contratos T06 permanecem. Esta task documenta a fronteira de implementação interna do adaptador Git e a dependência GitPython.

| Contrato | Módulo | Mudança T20 |
|---|---|---|
| `DiscoveredLocalRepo`, `LocalDiscoveryIssue`, `LocalDiscoveryResult` | `discovery.py` | Nenhuma |
| `LocalRepoDiscovery` | `discovery.py` | Nenhuma (continua injetando `GitFilesystemInspector`) |
| `GitFilesystemInspector`, `RepoInspection`, `ParsedFileUrl` | `git_fs.py` | Assinaturas estáveis; `inspect_repo` passa a usar GitPython |
| Dependência | `pyproject.toml` | `GitPython>=3.1` |

## 2. Contratos preservados (T06)

### 2.1 `LocalRepoDiscovery`

**Responsabilidade:** orquestrar descoberta de conexões `git` em `AppConfig`, expandir `file://`+glob, validar Git+`main` e produzir candidatos com origem `local`.

**Motivo da separação:** porta única para T07; não conhece PostgreSQL, UI nem SDK Git diretamente — depende do inspector injetável.

```python
class LocalRepoDiscovery:
    def __init__(self, inspector: GitFilesystemInspector | None = None) -> None: ...
    def discover(self, config: AppConfig) -> LocalDiscoveryResult: ...
    def discover_connection(
        self, connection_name: str, connection: GitConnection
    ) -> LocalDiscoveryResult: ...
```

**Invariantes (inalterados):** ignora `github`; falhas → `issues`; não muta filesystem.

### 2.2 Modelos de saída

`DiscoveredLocalRepo`, `LocalDiscoveryIssue`, `LocalDiscoveryResult` — campos e invariantes T06 intactos.

**Motivo da separação:** handoff tipado e distinção sucesso parcial vs falha por path (BDD-018).

### 2.3 `GitFilesystemInspector` (assinatura estável)

**Responsabilidade:** parse `file://`, glob, acessibilidade e inspeção Git mínima retornando `RepoInspection`.

**Motivo da separação:** isola I/O + integração Git da orquestração; permite mocks sem stubar `LocalRepoDiscovery`; confina GitPython ao adaptador (ENG-013).

```python
class GitFilesystemInspector:
    def parse_file_url(self, url: str) -> ParsedFileUrl: ...
    def is_accessible(self, path: Path) -> bool: ...
    def expand_candidates(self, base: Path, pattern: str | None) -> Sequence[Path]: ...
    def inspect_repo(self, path: Path) -> RepoInspection: ...
```

### 2.4 `RepoInspection` / `ParsedFileUrl`

Inalterados.

```python
@dataclass(frozen=True)
class RepoInspection:
    is_git_repo: bool
    has_main_branch: bool
    reason: str | None = None
    @property
    def is_valid_candidate(self) -> bool: ...
```

## 3. Contrato de implementação interna (T20)

### 3.1 `inspect_repo` via GitPython

**Responsabilidade:** abrir o path com `git.Repo` (context manager), rejeitar bare (D-T20-006), detectar `"main" in repo.heads`, mapear falhas do SDK para `RepoInspection` com `reason` documentadas no design §3.2 / §7.

**Motivo da separação (vs parse ad-hoc):** cumprir BR-023 / DEC-015 / DT-001; edge cases de refs/packed-refs/gitdir delegados ao SDK.

**Proibido no caminho de produção:** ler manualmente `refs/heads/*`, `packed-refs`, ou parsear conteúdo de `.git` para decidir validade/`main`.

**Permitido (stdlib, BR-023):** `pathlib`, `os.access`, parse URL `file://`, `Path.glob`.

### 3.2 Dependência runtime

| Item | Contrato |
|---|---|
| Pacote | `GitPython>=3.1` em dependencies do projeto |
| Binário | `git` no PATH (D-T20-007) |
| Import | `git` / `git.Repo` / `git.exc.InvalidGitRepositoryError` (e afins) somente em `git_fs.py` |

## 4. Superfície pública (`github_rag.sources.local`)

| Símbolo | Export | Nota |
|---|---|---|
| `DiscoveredLocalRepo` | sim | inalterado |
| `LocalDiscoveryIssue` | sim | inalterado |
| `LocalDiscoveryResult` | sim | inalterado |
| `LocalRepoDiscovery` | sim | inalterado |
| `GitFilesystemInspector` | testes | inalterado na API |

## 5. Fronteiras

| Fora de T20 | Dono |
|---|---|
| Snapshot/diff GitPython | T08 |
| Catálogo | T07 |
| Imagem com `git`+deps | T19 |
| Mudança de wildcards de produto | — |
