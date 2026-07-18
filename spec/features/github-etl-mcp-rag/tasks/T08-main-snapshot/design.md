# Design — T08-main-snapshot

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T08-main-snapshot` |
| Autor | Implementation Task Runner |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 (re-review design v0.1.1) |
| Branch | `feature/github-etl-mcp-rag-T08-main-snapshot` |
| Base | `main` |
| Rastreabilidade | REQ-013; BR-002–004, BR-015, BR-023; DEC-015; BDD-005, BDD-017, BDD-024; ENG-012 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | `0.1.0` | MAJOR: list_tree/read_file GitHub devem resolver commit_sha pedido. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | MAJOR M-01 e SUGGESTION S-01..S-04 fechados (D-T08-006..009; §4.6/§5/§7). Sem BLOCKING/MAJOR abertos. |

## 1. Contexto

T01 estabelece a fronteira `github_rag.snapshot`. T08 materializa o provedor unificado de snapshot da branch `main` para origens GitHub e locais: tip (SHA), árvore/arquivos no commit, leitura de conteúdo **completo** no tip, e diff de paths entre `last_processed_commit` e `current_main_commit` (ENG-012).

Consumidores futuros: T14 (orquestração/reindex) e T16 (read/tree sobre commit indexado). Fora de escopo: elegibilidade (T09), fila (T14), UI.

## 2. Problema

Antes de indexar ou reconciliar, o sistema precisa:

1. Obter o SHA do tip de `main` (nunca working tree suja / outras branches — BR-015).
2. Listar a árvore de arquivos daquele commit.
3. Ler o conteúdo completo de um path no tip (unidade de reindexação = arquivo inteiro).
4. Calcular o conjunto de paths adicionados/modificados/removidos entre dois SHAs.
5. Tratar corner cases tipados: `main` ausente, repo corrompido, falha de rede GitHub, primeiro index (sem commit anterior → sinal explícito para T14 tratar como “todos os elegíveis”).

## 3. Solução proposta

Módulo `github_rag.snapshot` com porta única `MainSnapshotProvider` e adaptadores por origem, todos baseados em SDKs de mercado (BR-023 / DEC-015):

| Componente | Módulo | Papel |
|---|---|---|
| Modelos + erros tipados | `models.py`, `errors.py` | DTOs imutáveis e exceções de domínio |
| Porta `MainSnapshotProvider` | `provider.py` | Contrato unificado tip/árvore/read/diff |
| Diff de arquivos | `diff.py` | `FileDiff` + classificação add/mod/del |
| Adaptador local (interno) | `local.py` | GitPython sobre path local |
| Adaptador GitHub (interno) | `github.py` | PyGithub tip + clone shallow mockável (GitPython) |
| Clone port | `clone.py` | `GitClonePort` mockável |
| Re-exports | `__init__.py` | Superfície pública |

Fluxo feliz (local):

```text
local_path
  → GitPython Repo(local_path)
  → tip = refs/heads/main (somente branch local main; BR-015)
  → tree = commit.tree → list paths
  → blob data_stream → conteúdo completo do path no tip
  → git.diff(last..current, name-status) → FileDiffSet
```

Fluxo feliz (GitHub):

```text
owner/repo + token
  → PyGithub: repo.get_branch("main").commit.sha  (tip)
  → para árvore/conteúdo/diff: porta GitClonePort (clone mockável)
       → materializa workspace com o(s) commit(s) pedidos
       → GitPython sobre clone local temporário
  → mesmos contratos de Snapshot / FileDiffSet
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T08 | Fora de T08 |
|---|---|---|
| BDD-005 | Expor tip atual ≠ last_processed; diff de paths; conteúdo no tip | Persistência `last_processed` / orquestração (T14) |
| BDD-017 | Snapshot local = tip `main` apenas; ignora uncommitted e ≠ `main` | Descoberta (T06); elegibilidade (T09) |
| BDD-024 (Git) | Operações Git via GitPython; GitHub tip via PyGithub | Demais SDKs |

## 4. Componentes

### 4.1 `MainSnapshot`

Campos imutáveis:

| Campo | Tipo | Invariantes |
|---|---|---|
| `origin` | `RepoOrigin` | `github` ou `local` |
| `repo_key` | `str` | Identificador estável (path ou `owner/repo`) |
| `commit_sha` | `str` | SHA completo (40 hex) do tip `main` |
| `branch` | `str` | Sempre `"main"` |

### 4.2 `FileDiff` / `FileDiffSet`

| Campo | Tipo | Descrição |
|---|---|---|
| `path` | `str` | Path relativo no repo (POSIX) |
| `change` | `FileChangeKind` | `added` \| `modified` \| `deleted` |
| `added` / `modified` / `deleted` | `tuple[str, ...]` | Agregados em `FileDiffSet` |

Semântica ENG-012: paths add/mod → reindex arquivo **inteiro** no tip; deleted → limpeza de índices (T14). Conteúdo não faz parte do diff.

**Renames (D-T08-007):** diff sem detecção de rename (`-M` off). Um rename aparece como `deleted` (path antigo) + `added` (path novo). T14 reindexa o novo path por inteiro e limpa o antigo.

### 4.3 `MainSnapshotProvider` (Protocol)

```python
class MainSnapshotProvider(Protocol):
    def get_main_tip(self, source: SnapshotSource) -> MainSnapshot: ...
    def list_tree(self, source: SnapshotSource, *, commit_sha: str) -> tuple[str, ...]: ...
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
```

`SnapshotSource` é um discriminated union tipado:

- `LocalSnapshotSource(local_path: str)`
- `GitHubSnapshotSource(full_name: str, token: str)` — token só em memória; erros sem vazar valor (BR-008)

### 4.4 `FirstIndexSignal`

Quando `from_commit is None` (primeiro index), `diff_files` **não** inventa lista de todos os arquivos: retorna `FirstIndexSignal` tipado. T14 interpreta como “todos os elegíveis”. Evita acoplar snapshot a elegibilidade (T09).

### 4.5 Adaptador local — `LocalGitSnapshotAdapter` (interno)

- Usa **somente** GitPython (`git.Repo`); proibido parse ad-hoc de `.git` (BR-023 / DEC-015).
- Tip: exclusivamente `refs/heads/main` / `repo.heads.main` (não usa `origin/main` como substituto).
- Working tree suja / arquivos untracked **não** entram em tip, tree nem `read_file`.
- Branches ≠ `main` ignoradas.
- Erros: `MainBranchMissingError`, `CorruptRepositoryError`, `SnapshotError`.

### 4.6 Adaptador GitHub — `GitHubGitSnapshotAdapter` (interno)

- Tip de `main`: **PyGithub** (`get_repo` → `get_branch("main")`).
- Árvore / conteúdo / diff: via `GitClonePort` (protocolo injetável) — **sem** client HTTP inventado.
- **Obrigatório:** `list_tree` / `read_file` / `diff_files` devem resolver o `commit_sha` (e `from_commit` quando houver) pedido pelo chamador. Se o SHA não estiver no workspace, o port faz fetch/depth adequado; se impossível, falha com `CommitNotFoundError` — nunca devolver árvore/conteúdo de outro commit (ex.: tip do shallow) silenciosamente. Necessário para T16 (read/tree do commit indexado, que pode ≠ tip atual).
- Default `ShallowGitClonePort` usa GitPython `Repo.clone_from` com auth por token injetado **somente em memória** (URL com credencial efêmera ou `GIT_ASKPASS`/config transitória); token **nunca** em `str(exc)`, logs ou remote URL persistente no disk do usuário (BR-008).
- Mockável nos testes unitários (não exige rede).

### 4.7 Fachada unificada — porta pública

`DefaultMainSnapshotProvider` é a **única** implementação pública de `MainSnapshotProvider`. Despacha por `SnapshotSource` para os adaptadores internos local/GitHub. T14/T16 dependem só da porta/`DefaultMainSnapshotProvider`; adaptadores não são API estável.

## 5. Fluxo de dados

```text
T14/T16
  → MainSnapshotProvider.get_main_tip(source)
  → compara tip.commit_sha com last_processed_commit (catálogo)
  → se iguais: skip (BDD-004 / BR-003) — fora desta task
  → se tip novo:
       diff_files(from=last|None, to=tip)
         → FirstIndexSignal | FileDiffSet
       para path in added∪modified:
         read_file(tip, path) → bytes completos
       deleted → handoff limpeza (T14)
```

Histórico no clone GitHub: o `GitClonePort` deve garantir presença de todo SHA referenciado (`to_commit`, `from_commit` quando não-`None`, e `commit_sha` de `list_tree`/`read_file`). Estratégia (depth maior, fetch por SHA, etc.) é detalhe do adaptador; contrato: diff/árvore/conteúdo corretos para os SHAs pedidos ou `CommitNotFoundError` / `SnapshotError` tipado — nunca inventar estados nem servir tip errado.

## 6. Erros tipados

| Erro | Quando |
|---|---|
| `MainBranchMissingError` | Branch `main` ausente |
| `CorruptRepositoryError` | Repo Git inválido/corrompido (GitPython falha estrutural) |
| `GitHubSnapshotNetworkError` | Falha de rede/API PyGithub ou clone |
| `CommitNotFoundError` | SHA inexistente no repo |
| `FileNotFoundInCommitError` | Path ausente no commit |
| `SnapshotError` | Base genérica; demais herdam |

Mensagens **nunca** incluem o valor do token (BR-008).

## 7. Segurança

- Token GitHub apenas parâmetro em memória / factory; não logar, não incluir em `str(exc)`.
- Clone: credencial efêmera (env/`GIT_ASKPASS`/URL transitória); não persistir remote com token embutido após a operação.
- Sem mutação de working tree do usuário: clone GitHub em temp; local só leitura via GitPython.

## 8. Compatibilidade

- Depende de T01 (pacote). Tipos de origem: reutiliza `RepoOrigin` de `catalog.models` quando aplicável; `SnapshotSource` é DTO próprio do módulo snapshot.
- Não altera contratos T05/T06.
- Nova dependência: `GitPython` em `pyproject.toml` (DEC-015). PyGithub já presente.

## 9. Observabilidade

- Erros tipados com `repo_key` / path (sem segredos).
- Sem métricas nesta task; T14 instrumenta orquestração.

## 10. Riscos e rollback

| Risco | Mitigação |
|---|---|
| Shallow clone insuficiente para diff/read | Fetch/depth adaptativo ou `CommitNotFoundError` |
| Repos bare / gitdir file | GitPython resolve; testes de corner |
| Performance em monorepos grandes | Fora de MVP (REQ-019); sem limite funcional |

Rollback: reverter merge da branch; módulo isolado em `snapshot/`.

## 11. Decisões fechadas (D-T08)

| ID | Decisão |
|---|---|
| D-T08-001 | Porta única `MainSnapshotProvider`; adaptadores local/GitHub atrás dela |
| D-T08-002 | Git local/diff/clone = GitPython; tip GitHub = PyGithub; proibido parse ad-hoc `.git` |
| D-T08-003 | `from_commit is None` → `FirstIndexSignal` (não lista todos os paths aqui) |
| D-T08-004 | Conteúdo = arquivo completo no tip; diff só paths + kind |
| D-T08-005 | Clone GitHub via porta `GitClonePort` mockável |
| D-T08-006 | Snapshot local ignora working tree e branches ≠ `main`; tip só `refs/heads/main` |
| D-T08-007 | Renames = deleted + added (sem `-M`) |
| D-T08-008 | `list_tree`/`read_file` no GitHub resolvem o `commit_sha` pedido ou `CommitNotFoundError` |
| D-T08-009 | Única porta pública: `DefaultMainSnapshotProvider` implementa `MainSnapshotProvider` |

## 12. Arquivos previstos

```text
src/github_rag/snapshot/
  __init__.py
  models.py
  errors.py
  provider.py
  diff.py
  local.py
  github.py
  clone.py
tests/unit/snapshot/
tests/bdd/test_main_snapshot.py
spec/features/github-etl-mcp-rag/tasks/T08-main-snapshot/
```
