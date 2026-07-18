# Unit test plan — T08-main-snapshot

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T08-main-snapshot` |
| Estado | `PENDING_ARCHITECT_REVIEW` |
| Versão | `0.1.0` |
| Interfaces base | `0.1.0` |
| BDD base | `0.1.0` |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| — | — | — | `0.1.0` |

## 1. Escopo

| Área | Arquivo de teste |
|---|---|
| Models / erros | `tests/unit/snapshot/test_models.py` |
| Diff set / rename | `tests/unit/snapshot/test_diff.py` |
| Adaptador local (GitPython) | `tests/unit/snapshot/test_local.py` |
| Adaptador GitHub (mocks) | `tests/unit/snapshot/test_github.py` |
| Fachada `DefaultMainSnapshotProvider` | `tests/unit/snapshot/test_provider.py` |
| BDD MS-01..12 | `tests/bdd/test_main_snapshot.py` |

## 2. Contratos e casos

### 2.1 Models / erros

| ID | Caso | Esperado |
|---|---|---|
| U-M01 | `MainSnapshot` frozen | imutável |
| U-M02 | `FirstIndexSignal` carrega `to_commit` | campo presente |
| U-M03 | hierarquia erros ⊂ `SnapshotError` | isinstance |
| U-M04 | erro GitHub sem token em str/repr | BR-008 |

### 2.2 Diff

| ID | Caso | Esperado |
|---|---|---|
| U-D01 | FileDiffSet agrega added/modified/deleted | tuples |
| U-D02 | rename → deleted + added | MS-11 |

### 2.3 Local (GitPython, repo real temporário)

| ID | Caso | Esperado |
|---|---|---|
| U-L01 | tip `main` | SHA correto |
| U-L02 | list_tree no tip | paths do commit |
| U-L03 | read_file conteúdo completo | bytes exatos |
| U-L04 | diff entre dois commits | add/mod/del |
| U-L05 | uncommitted ignorado | não na tree/tip |
| U-L06 | branch ≠ main ignorada | tip = main |
| U-L07 | main ausente | `MainBranchMissingError` |
| U-L08 | path não-git | `CorruptRepositoryError` |
| U-L09 | commit inexistente | `CommitNotFoundError` |
| U-L10 | path ausente no commit | `FileNotFoundInCommitError` |
| U-L11 | `from_commit is None` | `FirstIndexSignal` |
| U-L12 | sem parse ad-hoc `.git` | só GitPython (import/git.Repo) |

### 2.4 GitHub (PyGithub + GitClonePort mock)

| ID | Caso | Esperado |
|---|---|---|
| U-G01 | tip via PyGithub mock | SHA tip |
| U-G02 | list_tree/read no `commit_sha` pedido ≠ tip | conteúdo do SHA pedido |
| U-G03 | SHA ausente no clone port | `CommitNotFoundError` |
| U-G04 | falha rede PyGithub | `GitHubSnapshotNetworkError` |
| U-G05 | falha clone | `GitHubSnapshotNetworkError` |
| U-G06 | token ausente de erros | BR-008 |
| U-G07 | main ausente na API | `MainBranchMissingError` |

### 2.5 Provider fachada

| ID | Caso | Esperado |
|---|---|---|
| U-P01 | despacha local | tip local |
| U-P02 | despacha github | tip github |
| U-P03 | source inválido / tipo errado | TypeError ou SnapshotError |

## 3. Extremos / concorrência / idempotência

| ID | Caso | Esperado |
|---|---|---|
| U-X01 | tree vazia (commit vazio) | `list_tree` → `()` |
| U-X02 | arquivo vazio | `read_file` → `b""` |
| U-X03 | path com subdirs | POSIX relativo |
| U-X04 | diff idêntico (mesmo SHA) | sets vazios |
| U-X05 | duas leituras do mesmo path | idempotente, mesmos bytes |

## 4. Evidência de falha (red)

Antes da implementação, a suíte deve falhar por `ImportError` / atributo ausente / `NotImplementedError` nos símbolos de `github_rag.snapshot`. Comando:

```bash
.venv/bin/python -m pytest tests/unit/snapshot tests/bdd/test_main_snapshot.py -q
```

Registrar saída no commit de testes / reviews.

### Evidência red (2026-07-18)

```text
ERROR tests/unit/snapshot/test_diff.py — ModuleNotFoundError: github_rag.snapshot.diff
ERROR tests/unit/snapshot/test_github.py — ModuleNotFoundError: github_rag.snapshot.errors
ERROR tests/unit/snapshot/test_local.py — ModuleNotFoundError: github_rag.snapshot.diff
ERROR tests/unit/snapshot/test_models.py — ModuleNotFoundError: github_rag.snapshot.errors
ERROR tests/unit/snapshot/test_provider.py — ModuleNotFoundError: github_rag.snapshot.models
ERROR tests/bdd/test_main_snapshot.py — ModuleNotFoundError: github_rag.snapshot.diff
Interrupted: 6 errors during collection
```

Razão esperada: módulos da interface ainda não implementados (fase vermelha TDD).
