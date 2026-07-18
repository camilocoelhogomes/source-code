# BDD — T20-refactor-local-discovery-git-sdk

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T20-refactor-local-discovery-git-sdk` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Rastreabilidade | BDD-016, BDD-018, BDD-024; BR-023; DEC-015; DT-001 |

## Escopo

Regressão dos cenários de produto de T06 (BDD-016 / BDD-018) **sem alteração de intenção**, mais cenários de conformidade SDK (contribuição a BDD-024 / DT-001).

## Cenários executáveis

### T20-LOC-01 — Regressão BDD-016: descobrir repos locais com `main` (GitPython)

**Dado** um `AppConfig` com conexão `git` e URL `file://<mount>/*`  
**E** volume com repositórios Git reais (worktree) contendo branch `main`  
**Quando** `LocalRepoDiscovery().discover(config)`  
**Então** cada repo válido aparece em `result.repos` com `origin == RepoOrigin.LOCAL`  
**E** `connection_name`, `local_path` e `repo_identifier` preservam o contrato T06  

*Mapeia:* LOC-01 de T06 / BDD-016.

### T20-LOC-02 — Regressão BDD-016: ignorar não-Git e sem `main`

**Dado** mount com repo válido + pasta comum + repo sem `main`  
**Quando** a descoberta é executada  
**Então** somente o repo com Git válido e `main` entra em `result.repos`  
**E** inválidos geram `result.issues`  

*Mapeia:* LOC-02 / BDD-016.

### T20-LOC-03 — Regressão BDD-018: volume inacessível

**Dado** conexão `git` para path base inexistente/ilegível  
**Quando** a descoberta é executada  
**Então** zero candidatos dessa conexão  
**E** `issues` registra erro citando conexão/path  

*Mapeia:* LOC-03 / BDD-018.

### T20-LOC-04 — Regressão: falha isolada por conexão

**Dado** duas conexões `git` (uma inacessível, uma válida)  
**Quando** a descoberta é executada  
**Então** repos da válida aparecem; a inacessível só contribui `issues`  

*Mapeia:* LOC-04.

### T20-LOC-05 — Regressão: URL sem glob

**Dado** `file://<mount>/single-repo` com Git + `main`  
**Quando** a descoberta é executada  
**Então** um único `DiscoveredLocalRepo`  

*Mapeia:* LOC-05.

### T20-LOC-06 — Regressão: conexões GitHub ignoradas

**Dado** `AppConfig` misto (`github` + `git`)  
**Quando** `discover`  
**Então** somente `git` é processada  

*Mapeia:* LOC-06.

### T20-SDK-01 — Conformidade: inspeção via GitPython (BDD-024 / DT-001)

**Dado** o módulo de produção `github_rag.sources.local.git_fs`  
**Quando** a inspeção de repositório é exercida  
**Então** a validação Git usa GitPython (`git.Repo`)  
**E** o código de produção não lê ad-hoc `refs/heads/*` nem `packed-refs`  
**E** bare é rejeitado com `reason` equivalente a “not a git repository” (D-T20-006)

### T20-SDK-02 — Corner: `main` apenas em packed-refs (via SDK)

**Dado** worktree GitPython-válido com `main` somente em `packed-refs`  
**Quando** `inspect_repo` / descoberta  
**Então** o path é candidato válido (paridade §3.2)

### T20-SDK-03 — Corner: `.git` file (gitdir)

**Dado** worktree cujo `.git` é arquivo `gitdir:` apontando para git dir com `main`  
**Quando** `inspect_repo`  
**Então** candidato válido

## Fora de escopo

- BDD-024 completo das demais integrações (T08/T09/T19 etc.)
- Snapshot/diff (T08); catálogo (T07); UI

## Execução

```bash
python -m pytest tests/bdd/test_local_discovery.py tests/bdd/test_local_discovery_git_sdk.py -q
```

Regressão T06 permanece em `tests/bdd/test_local_discovery.py` (fixtures atualizadas para repos SDK-válidos).  
Cenários T20-SDK-* em `tests/bdd/test_local_discovery_git_sdk.py`.
