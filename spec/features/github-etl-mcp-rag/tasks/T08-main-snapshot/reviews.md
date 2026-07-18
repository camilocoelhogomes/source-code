# Reviews — T08-main-snapshot

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T08-main-snapshot` |

## Review — Design v0.1.0

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `design.md` v0.1.0 |
| Resultado | `CHANGES_REQUIRED` |

### Achados

| ID | Severidade | Evidência | Correção esperada |
|---|---|---|---|
| M-01 | `MAJOR` | §4.3 (`commit_sha`); §4.6 (clone shallow tip); §5 (fetch só para diff); §1 (T16 read/tree commit indexado) | `list_tree`/`read_file` no GitHub resolvem `commit_sha` pedido ou `CommitNotFoundError` |
| S-01 | `SUGGESTION` | §3 vs §4.5 (“main remota equivalente”) | Tip local só `refs/heads/main` |
| S-02 | `SUGGESTION` | §4.6 / §7 | Auth clone sem persistir token (BR-008) |
| S-03 | `SUGGESTION` | §4.2 | Renames = deleted+added (`-M` off) |
| S-04 | `SUGGESTION` | §4.7 | Única porta pública: `DefaultMainSnapshotProvider` |

## Review — Design v0.1.1

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `design.md` v0.1.1 |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Achados

| ID | Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|---|
| — | — | Nenhum BLOCKING/MAJOR | M-01 e S-01..S-04 fechados em §3, §4.2, §4.5–4.7, §5, §7, D-T08-006..009 | — | `APPROVED_BY_ARCHITECT` |
| S-05 | `SUGGESTION` | D-T08-008 omite `diff_files`/`from_commit` já cobertos em §4.6/§5 | §11 D-T08-008 vs §4.6 | Alinhar texto da decisão na etapa de interfaces (não bloqueia) | aberto (não bloqueante) |

## Review — BDD v0.1.0

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` v0.1.0 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| BDD-005 / ENG-012 | OK | MS-01 tip; MS-02 diff paths; MS-03 arquivo completo (não patch) |
| BDD-017 / BR-015 | OK | MS-04 ignora uncommitted e branches ≠ `main` |
| Corner cases da task | OK | MS-05 FirstIndexSignal; MS-06 MainBranchMissingError; MS-07 CorruptRepositoryError; MS-08 GitHubSnapshotNetworkError |
| Alinhamento design (contratos/SDKs) | OK | MS-09 commit_sha pedido + PyGithub; MS-10 GitPython; MS-11 rename deleted+added; MS-12 BR-008 |
| Sem expandir T09/T14 | OK | MS-05 não inventa elegíveis; sem orquestração/persistência last_processed |
| Cenários executáveis (Given/When/Then + API) | OK | Porta `MainSnapshotProvider`, fontes tipadas, erros tipados |

### Achados

| ID | Severidade | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| — | — | Nenhum BLOCKING/MAJOR | — | `APPROVED_BY_ARCHITECT` |
| S-BDD-01 | `SUGGESTION` | `bdd.md` § Artefatos: `tests/bdd/test_main_snapshot.py` ainda ausente no worktree | QA materializa o executável (red) na mesma etapa BDD, antes de interfaces | aberto (não bloqueante) |
| S-BDD-02 | `SUGGESTION` | MS-09 cobre tip via mock PyGithub mas não asserta explicitamente `get_main_tip` → `origin == github` / `commit_sha == SHA_TIP` | Incluir assert no executável ou subpasso Then em MS-09 | aberto (não bloqueante) |

### Decisão

`APPROVED_BY_ARCHITECT` — BDD v0.1.0. Prosseguir para interfaces (após materializar pytest BDD em red, conforme S-BDD-01).
