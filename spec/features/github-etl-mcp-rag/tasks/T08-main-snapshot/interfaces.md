# Interfaces — T08-main-snapshot

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T08-main-snapshot` |
| Estado | `PENDING_ARCHITECT_REVIEW` |
| Versão | `0.1.0` |
| Design base | `0.1.1` |
| BDD base | `0.1.0` |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| — | — | — | `0.1.0` |

## 1. Escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `MainSnapshot`, `SnapshotSource`, `FirstIndexSignal`, `FileChangeKind` | `models.py` | DTOs imutáveis |
| `FileDiff`, `FileDiffSet` | `diff.py` | Diff de paths entre commits |
| Erros tipados | `errors.py` | Hierarquia de falhas |
| `MainSnapshotProvider`, `DefaultMainSnapshotProvider` | `provider.py` | Porta pública + fachada |
| `GitClonePort` | `clone.py` | Porta mockável de materialização GitHub |
| Adaptadores internos | `local.py`, `github.py` | Não API estável |
| Re-exports | `__init__.py` | Superfície pública |

## 2. Contratos

### 2.1 `LocalSnapshotSource` / `GitHubSnapshotSource`

**Responsabilidade:** identificar a origem do snapshot sem acoplar a catálogo/config.

**Motivo da separação:** T14/T16 passam uma origem tipada; local e GitHub diferem em credenciais e transporte (D-T08-001).

```python
@dataclass(frozen=True)
class LocalSnapshotSource:
    local_path: str  # path absoluto do repo

@dataclass(frozen=True)
class GitHubSnapshotSource:
    full_name: str  # owner/repo
    token: str      # só memória; nunca em logs/erros
```

`SnapshotSource = LocalSnapshotSource | GitHubSnapshotSource`

---

### 2.2 `MainSnapshot`

**Responsabilidade:** snapshot imutável do tip `main`.

**Motivo da separação:** handoff tipado para comparação com `last_processed_commit` (BR-002–004) sem expor I/O Git.

| Campo | Tipo | Invariantes |
|---|---|---|
| `origin` | `RepoOrigin` | `github` ou `local` |
| `repo_key` | `str` | path ou `owner/repo` |
| `commit_sha` | `str` | SHA do tip `main` |
| `branch` | `str` | sempre `"main"` |

---

### 2.3 `FileChangeKind` / `FileDiff` / `FileDiffSet`

**Responsabilidade:** classificar paths alterados entre dois commits (ENG-012).

**Motivo da separação:** diff de paths é independível de elegibilidade (T09) e de leitura de conteúdo; renames = deleted+added (D-T08-007).

```python
class FileChangeKind(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"

@dataclass(frozen=True)
class FileDiff:
    path: str
    change: FileChangeKind

@dataclass(frozen=True)
class FileDiffSet:
    added: tuple[str, ...]
    modified: tuple[str, ...]
    deleted: tuple[str, ...]
```

---

### 2.4 `FirstIndexSignal`

**Responsabilidade:** sinalizar ausência de commit anterior (primeiro index).

**Motivo da separação:** evita que snapshot invente “todos os elegíveis” (T14+T09); D-T08-003.

```python
@dataclass(frozen=True)
class FirstIndexSignal:
    to_commit: str
```

---

### 2.5 Erros tipados

**Responsabilidade:** falhas de snapshot sem vazar segredos (BR-008).

**Motivo da separação:** corner cases do DoD tipados; consumidores (T14) tratam por tipo.

```python
class SnapshotError(Exception): ...
class MainBranchMissingError(SnapshotError): ...
class CorruptRepositoryError(SnapshotError): ...
class GitHubSnapshotNetworkError(SnapshotError): ...
class CommitNotFoundError(SnapshotError): ...
class FileNotFoundInCommitError(SnapshotError): ...
```

---

### 2.6 `GitClonePort`

**Responsabilidade:** materializar workspace Git local para um repo GitHub com os SHAs necessários.

**Motivo da separação:** isola clone/rede dos contratos de domínio; mockável nos unitários (D-T08-005). Deve garantir presença de todo `commit_sha` / `from_commit` referenciado ou falhar com `CommitNotFoundError` (D-T08-008; S-05 do design).

```python
class GitClonePort(Protocol):
    def ensure_commits(
        self,
        *,
        full_name: str,
        token: str,
        commit_shas: Sequence[str],
    ) -> Path:
        """Retorna path de workspace contendo todos os SHAs pedidos."""
        ...
```

---

### 2.7 `MainSnapshotProvider` (Protocol) + `DefaultMainSnapshotProvider`

**Responsabilidade:** tip `main`, árvore, leitura de arquivo completo e diff de paths — porta única para T14/T16.

**Motivo da separação:** unifica origens atrás de um contrato estável; adaptadores internos não são API pública (D-T08-009).

```python
class MainSnapshotProvider(Protocol):
    def get_main_tip(self, source: SnapshotSource) -> MainSnapshot: ...

    def list_tree(
        self, source: SnapshotSource, *, commit_sha: str
    ) -> tuple[str, ...]: ...

    def read_file(
        self, source: SnapshotSource, *, commit_sha: str, path: str
    ) -> bytes: ...

    def diff_files(
        self,
        source: SnapshotSource,
        *,
        from_commit: str | None,
        to_commit: str,
    ) -> FileDiffSet | FirstIndexSignal: ...


class DefaultMainSnapshotProvider:
    def __init__(
        self,
        *,
        clone_port: GitClonePort | None = None,
        github_factory: Callable[[str], Any] | None = None,
    ) -> None: ...
    # implementa MainSnapshotProvider
```

**Invariantes:**

- Local: tip só `refs/heads/main`; ignora working tree e ≠ `main` (BR-015).
- Git: somente GitPython; tip GitHub via PyGithub (BR-023 / DEC-015).
- `from_commit is None` → `FirstIndexSignal`.
- `list_tree`/`read_file`/`diff_files` resolvem SHAs pedidos ou erro tipado.
- Conteúdo = arquivo completo no commit informado.
- Token nunca em `str`/`repr` de erros.

## 3. Superfície pública (`github_rag.snapshot`)

| Símbolo | Export |
|---|---|
| `MainSnapshotProvider` | sim |
| `DefaultMainSnapshotProvider` | sim |
| `MainSnapshot` | sim |
| `LocalSnapshotSource` | sim |
| `GitHubSnapshotSource` | sim |
| `FileDiffSet` | sim |
| `FileChangeKind` | sim |
| `FirstIndexSignal` | sim |
| Erros tipados | sim |
| `GitClonePort` | sim (para testes/injeção) |

Adaptadores `LocalGitSnapshotAdapter` / `GitHubGitSnapshotAdapter` **não** são exports públicos estáveis.

## 4. Fronteiras

| Fora de T08 | Dono |
|---|---|
| Elegibilidade de arquivos | T09 |
| Orquestração / fila / first-index → todos elegíveis | T14 |
| Persistência `last_processed_commit` | T03/T14 |
| Descoberta de repos | T05/T06 |
| UI | T18 |
