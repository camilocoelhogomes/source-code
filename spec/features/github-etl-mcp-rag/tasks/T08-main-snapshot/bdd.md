# BDD — T08-main-snapshot

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T08-main-snapshot` |
| Autor | Implementation Task Runner (QA step) |
| Data | 2026-07-18 |
| Estado | `PENDING_ARCHITECT_REVIEW` |
| Versão BDD | `0.1.0` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T08-main-snapshot` |
| Rastreabilidade | REQ-013; BR-002–004, BR-015, BR-023; DEC-015; BDD-005, BDD-017, BDD-024; ENG-012 |

## Rastreabilidade

| Cenário | Aceite / requisito |
|---|---|
| MS-01 | BDD-005 — tip `main` atual exposto como snapshot |
| MS-02 | BDD-005 / ENG-012 — diff de paths entre commits |
| MS-03 | BDD-005 / ENG-012 — conteúdo = arquivo completo no tip |
| MS-04 | BDD-017 / BR-015 — ignora uncommitted e branches ≠ `main` |
| MS-05 | Primeiro index — `from_commit is None` → `FirstIndexSignal` |
| MS-06 | Corner — `main` ausente → `MainBranchMissingError` |
| MS-07 | Corner — repo corrompido → `CorruptRepositoryError` |
| MS-08 | Corner — rede GitHub falha → `GitHubSnapshotNetworkError` |
| MS-09 | GitHub tip via PyGithub; tree/read resolvem `commit_sha` pedido |
| MS-10 | BDD-024 — Git via GitPython (sem parse ad-hoc `.git`) |
| MS-11 | Rename → deleted + added |
| MS-12 | Token ausente de erros (BR-008) |

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Steps / asserts | `tests/bdd/test_main_snapshot.py` |

## Como executar

```bash
.venv/bin/python -m pytest tests/bdd/test_main_snapshot.py -q
```

## Cenários

### MS-01 — Obter tip da main (BDD-005)

**Dado** um repositório local Git válido com branch `main` em commit `SHA_A`  
**Quando** `MainSnapshotProvider.get_main_tip` for chamado com `LocalSnapshotSource`  
**Então** o resultado deve ter `commit_sha == SHA_A`, `branch == "main"` e `origin == local`.

### MS-02 — Diff de arquivos entre commits (BDD-005 / ENG-012)

**Dado** tip `SHA_B` e último processado `SHA_A`, com paths `a.py` modificado, `b.py` adicionado e `c.py` removido  
**Quando** `diff_files(from_commit=SHA_A, to_commit=SHA_B)` for chamado  
**Então** deve retornar `FileDiffSet` com `a.py` em `modified`, `b.py` em `added` e `c.py` em `deleted`.

### MS-03 — Conteúdo completo no tip (ENG-012)

**Dado** arquivo `src/App.java` com conteúdo completo `CONTENT` no tip `SHA_B`  
**Quando** `read_file(..., commit_sha=SHA_B, path="src/App.java")` for chamado  
**Então** o retorno deve ser exatamente os bytes de `CONTENT` (arquivo inteiro, não patch).

### MS-04 — Ignorar uncommitted e outras branches (BDD-017 / BR-015)

**Dado** repositório local com `main` em `SHA_A`, branch `feature/x` com commit distinto e working tree com arquivo uncommitted `dirty.txt`  
**Quando** `get_main_tip`, `list_tree` e `read_file` forem executados sobre o tip de `main`  
**Então** o tip deve ser `SHA_A`  
**E** `dirty.txt` não deve aparecer na árvore nem ser legível via tip  
**E** conteúdo exclusivo de `feature/x` não deve aparecer no snapshot de `main`.

### MS-05 — Primeiro index (sem commit anterior)

**Dado** tip `SHA_B` e `from_commit is None`  
**Quando** `diff_files` for chamado  
**Então** deve retornar `FirstIndexSignal`  
**E** não deve inventar a lista de todos os paths elegíveis (responsabilidade de T14 + T09).

### MS-06 — Branch main ausente

**Dado** repositório Git válido sem branch `main`  
**Quando** `get_main_tip` for chamado  
**Então** deve levantar `MainBranchMissingError`.

### MS-07 — Repositório corrompido

**Dado** diretório que não é um repositório Git válido (ou GitPython reporta corrupção)  
**Quando** `get_main_tip` for chamado  
**Então** deve levantar `CorruptRepositoryError`.

### MS-08 — Falha de rede GitHub

**Dado** `GitHubSnapshotSource` e client/clone que simulam falha de rede  
**Quando** `get_main_tip` for chamado  
**Então** deve levantar `GitHubSnapshotNetworkError`  
**E** a mensagem não deve conter o token.

### MS-09 — GitHub: tip e commit_sha pedido

**Dado** tip `main` = `SHA_TIP` via PyGithub mock  
**E** workspace/clone contendo `SHA_OLD` e `SHA_TIP`  
**Quando** `list_tree`/`read_file` forem chamados com `commit_sha=SHA_OLD`  
**Então** devem refletir o conteúdo de `SHA_OLD`, não o tip  
**Quando** o SHA pedido estiver ausente e não puder ser obtido  
**Então** deve levantar `CommitNotFoundError`.

### MS-10 — Conformidade GitPython (BDD-024)

**Dado** a implementação do adaptador local  
**Quando** tip/árvore/diff/read forem executados  
**Então** as operações Git devem usar GitPython  
**E** não deve haver parse ad-hoc de arquivos `.git` no módulo `snapshot`.

### MS-11 — Rename como deleted + added

**Dado** commit que renomeia `old.py` → `new.py` sem detecção `-M`  
**Quando** `diff_files` for chamado entre os SHAs  
**Então** `old.py` deve estar em `deleted` e `new.py` em `added`.

### MS-12 — Token ausente de erros (BR-008)

**Dado** token com valor conhecido em `GitHubSnapshotSource`  
**Quando** qualquer operação falhar  
**Então** `str(exc)` e `repr(exc)` não devem conter o valor do token.
