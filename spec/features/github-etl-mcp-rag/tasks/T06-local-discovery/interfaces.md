# Interfaces — T06-local-discovery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T06-local-discovery` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` |
| BDD base | `0.1.0` |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` |

## 1. Escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `DiscoveredLocalRepo`, `LocalDiscoveryIssue`, `LocalDiscoveryResult` | `discovery.py` | Modelos imutáveis de saída |
| `LocalRepoDiscovery` | `discovery.py` | Porta de descoberta local |
| `GitFilesystemInspector`, `RepoInspection`, `ParsedFileUrl` | `git_fs.py` | I/O filesystem + heurística Git |
| Re-exports | `__init__.py` | Superfície pública |

## 2. Contratos

### 2.1 `DiscoveredLocalRepo`

**Responsabilidade:** representar um repositório local elegível à catalogação (Git válido + `main`).

**Motivo da separação:** handoff tipado para T07 sem acoplar ao `CatalogRepository`; origem e path montado explícitos (REQ-034/035).

| Campo | Tipo | Invariantes |
|---|---|---|
| `connection_name` | `str` | Nome da conexão declarativa |
| `origin` | `RepoOrigin` | Sempre `RepoOrigin.LOCAL` |
| `local_path` | `str` | Path absoluto normalizado |
| `repo_identifier` | `str` | Identificador estável (basename) |

---

### 2.2 `LocalDiscoveryIssue`

**Responsabilidade:** registrar falha não fatal por conexão ou path expandido.

**Motivo da separação:** distinguir candidatos válidos de erros operacionais (BDD-018) sem exceção que aborte outras conexões.

| Campo | Tipo |
|---|---|
| `connection_name` | `str` |
| `path` | `str` |
| `message` | `str` |

---

### 2.3 `LocalDiscoveryResult`

**Responsabilidade:** agregar repos descobertos e issues da execução.

**Motivo da separação:** resultado único consumível por T07/bootstrap; separa sucesso parcial de falha total de config (T02).

| Campo | Tipo |
|---|---|
| `repos` | `tuple[DiscoveredLocalRepo, ...]` |
| `issues` | `tuple[LocalDiscoveryIssue, ...]` |

---

### 2.4 `GitFilesystemInspector`

**Responsabilidade:** parse de URL `file://`, expansão de glob, acessibilidade e inspeção Git mínima.

**Motivo da separação:** isola I/O e heurística Git da orquestração de descoberta; permite mocks nos unitários sem stubar `LocalRepoDiscovery` inteiro.

```python
class GitFilesystemInspector:
    def parse_file_url(self, url: str) -> ParsedFileUrl: ...
    def is_accessible(self, path: Path) -> bool: ...
    def expand_candidates(self, base: Path, pattern: str | None) -> Sequence[Path]: ...
    def inspect_repo(self, path: Path) -> RepoInspection: ...
```

---

### 2.5 `LocalRepoDiscovery`

**Responsabilidade:** orquestrar descoberta de todas as conexões `git` de um `AppConfig`.

**Motivo da separação:** porta única consumida por T07; não conhece PostgreSQL nem UI.

```python
class LocalRepoDiscovery:
    def __init__(self, inspector: GitFilesystemInspector | None = None) -> None: ...

    def discover(self, config: AppConfig) -> LocalDiscoveryResult: ...

    def discover_connection(
        self, connection_name: str, connection: GitConnection
    ) -> LocalDiscoveryResult: ...
```

**Invariantes:**

- Ignora conexões `github`.
- Falha por conexão/path → `issues`; nunca retorna subset silencioso sem registrar issue.
- Não muta filesystem; não lê working tree além de metadados `.git`.

## 3. Superfície pública (`github_rag.sources.local`)

| Símbolo | Export |
|---|---|
| `DiscoveredLocalRepo` | sim |
| `LocalDiscoveryIssue` | sim |
| `LocalDiscoveryResult` | sim |
| `LocalRepoDiscovery` | sim |

`GitFilesystemInspector` exportável para testes unitários; não é API de bootstrap.

## 4. Fronteiras

| Fora de T06 | Dono |
|---|---|
| `ConfigLoader` / validação JSON | T02 |
| Persistência catálogo | T07 |
| Snapshot/indexação `main` | T08/T14 |
| GitHub discovery | T05 |
