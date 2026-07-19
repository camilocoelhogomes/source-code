# Interfaces — T34-fix-host-local-repos-path-resolution

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T34-fix-host-local-repos-path-resolution` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` |

## 1. Delta de contratos

### 1.1 `remap_repos_mount_path` (`git_fs.py`)

**Responsabilidade:** traduzir paths da convenção container `/repos` para root host quando `HOST_REPOS` informado.

**Motivo da separação:** função pura testável; discovery não conhece parsing de URL.

```python
def remap_repos_mount_path(path: Path, host_repos: str | None) -> Path: ...
```

### 1.2 `LocalRepoDiscovery.__init__`

**Responsabilidade:** receber override opcional de root host para remap.

**Motivo da separação:** injeção explícita via wiring evita leitura global de `os.environ` em testes.

```python
class LocalRepoDiscovery:
    def __init__(
        self,
        inspector: GitFilesystemInspector | None = None,
        *,
        host_repos: str | None = None,
    ) -> None: ...
```

### 1.3 `wire_catalog_sync`

**Responsabilidade:** extrair `HOST_REPOS` de `environ` e passar a `LocalRepoDiscovery`.

**Motivo da separação:** ponto único de composition root (T19); discovery permanece agnóstico de delivery.
