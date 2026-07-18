# Unit test plan — T20-refactor-local-discovery-git-sdk

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T20-refactor-local-discovery-git-sdk` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Interfaces base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` (M-UT-01, M-UT-02) | `0.1.0` |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` — asserts SDK endurecidos (`from git import Repo` / `with Repo(` / spy `create=True`) | `0.1.1` |

## 1. Estratégia

- Preservar suíte T06 de `discovery` (mocks da interface) — não deve quebrar.
- Atualizar fixtures de `git_fs` / BDD para repos GitPython-válidos (D-T20-005).
- Novos testes focam em: uso de GitPython, zero parse ad-hoc, bare, packed-refs, gitdir, extremos.
- Demonstrar falha vermelha **antes** da implementação (TDD).

## 2. Casos — `git_fs.inspect_repo` (GitPython)

| ID | Cenário | Tipo | Expectativa |
|---|---|---|---|
| UT-T20-01 | Worktree real com `main` (`Repo.init` + commit) | happy | `is_valid_candidate` |
| UT-T20-02 | Diretório sem Git | negativo | `not a git repository` |
| UT-T20-03 | Não-diretório | negativo | `not a directory` |
| UT-T20-04 | Git sem branch `main` | negativo | `main branch not found` |
| UT-T20-05 | `main` só em packed-refs | corner | válido |
| UT-T20-06 | `.git` file (gitdir) | corner | válido |
| UT-T20-07 | Bare com `main` | paridade T06 | `not a git repository` (D-T20-006) |
| UT-T20-08 | `.git` incompleto (sem objects) | delta §3.2 | `not a git repository` |
| UT-T20-09 | `git.Repo` é chamado (mock/spy) | contrato SDK | abertura via SDK |
| UT-T20-10 | Context manager / close | recurso | `Repo` usado em `with` ou closed |
| UT-T20-11 | Produção sem parse ad-hoc | conformidade | fonte de `git_fs.py` sem leitura de `packed-refs` / `refs/heads` paths |

## 3. Casos — regressão discovery (inalterados em intenção)

| ID | Cenário |
|---|---|
| UT-T06-* | Suíte existente `test_discovery.py` com mocks — permanece verde |
| BDD LOC-01..06 | Fixtures SDK-válidas; intenção BDD-016/018 |

## 4. BDD SDK novos

| ID | Arquivo |
|---|---|
| T20-SDK-01..03 | `tests/bdd/test_local_discovery_git_sdk.py` |

## 5. Evidência TDD (vermelho esperado pré-impl)

Comando (worktree T20, pré-impl ad-hoc):

```bash
PYTHONPATH=src python -m pytest \
  tests/unit/sources/local/test_git_fs.py::TestGitFilesystemInspector::test_t20_inspect_uses_gitpython_repo \
  tests/unit/sources/local/test_git_fs.py::TestGitFilesystemInspector::test_t20_no_adhoc_packed_refs_or_loose_ref_parse \
  tests/unit/sources/local/test_git_fs.py::TestGitFilesystemInspector::test_t20_repo_opened_as_context_manager \
  tests/unit/sources/local/test_git_fs.py::TestGitFilesystemInspector::test_t20_incomplete_git_dir_rejected \
  tests/bdd/test_local_discovery_git_sdk.py -q --no-cov
```

Resultado observado (2026-07-18): **5 failed, 2 passed** — falhas pela razão esperada (código ainda ad-hoc):

| Teste | Razão do vermelho |
|---|---|
| `test_t20_inspect_uses_gitpython_repo` | `git_fs.Repo` inexistente / não chamado |
| `test_t20_no_adhoc_packed_refs_or_loose_ref_parse` | fonte ainda contém `packed-refs` / helpers ad-hoc |
| `test_t20_repo_opened_as_context_manager` | `inspect_repo` sem `with Repo` |
| `test_t20_incomplete_git_dir_rejected` | ad-hoc classifica stub sem `objects/` como git |
| `test_t20_sdk01_...` | idem conformidade / `packed-refs` na fonte |

`T20-SDK-02` / `T20-SDK-03` já passam na intenção (packed-refs/gitdir) mesmo no ad-hoc; permanecem como regressão pós-migração.

## 6. Execução

```bash
PYTHONPATH=src python -m pytest tests/unit/sources/local tests/bdd/test_local_discovery.py tests/bdd/test_local_discovery_git_sdk.py -q
```
