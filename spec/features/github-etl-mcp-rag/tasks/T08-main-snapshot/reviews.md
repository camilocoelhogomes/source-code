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

## Review — Interfaces v0.1.0

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` v0.1.0 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Porta `MainSnapshotProvider` + diff + `FirstIndexSignal` | OK | §2.3–2.4, §2.7 (`diff_files` → `FileDiffSet \| FirstIndexSignal`) |
| Comentários responsabilidade / motivo da separação | OK | §2.1–2.7 |
| D-T08-001..009 | OK | porta única; GitPython/PyGithub; FirstIndexSignal; arquivo completo; `GitClonePort`; tip só `main`; rename deleted+added; SHAs resolvidos; `DefaultMainSnapshotProvider` pública |
| D-T08-008 / S-05 (`diff_files`/`from_commit`) | OK | §2.6 (`commit_sha`/`from_commit` → `CommitNotFoundError`); §2.7 invariante `list_tree`/`read_file`/`diff_files` |
| Sem expandir escopo | OK | §4 fronteiras T09/T14/T03/T05/T06/T18 |

### Achados

| ID | Severidade | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| — | — | Nenhum BLOCKING/MAJOR | — | `APPROVED_BY_ARCHITECT` |
| S-05 | `SUGGESTION` | design §11 vs §4.6/§5 | Alinhado em interfaces §2.6/§2.7 | fechado |
| S-IF-01 | `SUGGESTION` | §2.3 “independível” | Corrigir tipografia para “independente” na próxima edição cosméticas | aberto (não bloqueante) |
| S-IF-02 | `SUGGESTION` | §3 exporta `FileDiffSet` mas não `FileDiff` | Opcional: re-exportar `FileDiff` se unitários/consumidores precisarem do DTO unitário | aberto (não bloqueante) |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces v0.1.0. Prosseguir para testes unitários (QA).

## Review — Unit test plan + fase vermelha v0.1.0

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` v0.1.0 + `tests/unit/snapshot/*.py` + `tests/bdd/test_main_snapshot.py` |
| Pipeline | autonomous (sem gate humano intermediário) |
| Interfaces base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Resultado | `CHANGES_REQUIRED` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Contratos / IDs do plano materializados | OK | U-M01..04, U-D01..02, U-L01..12, U-G01..07, U-P01..02, U-X01..05; MS-01..12 |
| Extremos / corners (main ausente, corrupt, rede, first index) | OK | U-L07/U-G07/MS-06; U-L08/MS-07; U-G04..05/MS-08; U-L11/MS-05 |
| Evidência red `ModuleNotFoundError` | OK | Coleção falha nos 6 módulos; confirmado em 2026-07-18 (`github_rag.snapshot.{diff,errors,models}` ausentes) |
| Alinhamento às interfaces | parcial | Porta/`DefaultMainSnapshotProvider`, fontes tipadas, `GitClonePort` mock, erros tipados OK; U-P03 desalinhado |
| Não enfraquecer critérios | falha | U-P03 aceita `AttributeError` e omite `SnapshotError` previsto no plano |

### Achados

| ID | Severidade | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| M-UT-01 | `MAJOR` | `unit-test-plan.md` U-P03: `TypeError ou SnapshotError`; `tests/unit/snapshot/test_provider.py:72` usa `(TypeError, AttributeError)` | Ajustar assert para `(TypeError, SnapshotError)` (remover `AttributeError`); implementação correta com `SnapshotError` deve passar | aberto |
| S-UT-01 | `SUGGESTION` | `test_diff.py:9` importa `FileChangeKind` de `snapshot.diff`; interfaces §1 colocam `FileChangeKind` em `models.py` | Importar de `github_rag.snapshot.models` (ou re-export documentado) para não forçar layout contraditório | aberto (não bloqueante) |
| S-UT-02 | `SUGGESTION` | `test_models.py` U-M04: constrói erro sem token no cenário | Preferir assert BR-008 em caminho com token (já coberto por U-G04/U-G06/MS-12) | aberto (não bloqueante) |
| S-UT-03 | `SUGGESTION` | `test_ms04` não asserta `read_file` de `dirty.txt` (bdd.md MS-04 “nem ser legível”) | Espelhar U-L05 no BDD ou manter só no unitário | aberto (não bloqueante) |

### Decisão

`CHANGES_REQUIRED` — fechar M-UT-01 (U-P03) e reapresentar para review Architect. Não avançar para implementação.

## Review — Unit test plan + fase vermelha v0.1.1

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` v0.1.1 + `tests/unit/snapshot/*.py` + `tests/bdd/test_main_snapshot.py` |
| Pipeline | autonomous (sem gate humano intermediário) |
| Interfaces base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Contratos / IDs do plano materializados | OK | U-M01..04, U-D01..02, U-L01..12, U-G01..07, U-P01..03, U-X01..05; MS-01..12 |
| Extremos / corners | OK | U-L07/U-G07/MS-06; U-L08/MS-07; U-G04..05/MS-08; U-L11/MS-05; U-X01..05 |
| Evidência red | OK | `ModuleNotFoundError` nos 6 módulos (registrada no plan §4) |
| Alinhamento às interfaces | OK | U-P03 → `(TypeError, SnapshotError)`; `FileChangeKind` de `models` |
| Não enfraquecer critérios | OK | M-UT-01 fechado; MS-04 asserta `read_file` dirty |

### Achados

| ID | Severidade | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| M-UT-01 | `MAJOR` | `test_provider.py:73` `(TypeError, SnapshotError)` | — | fechado |
| S-UT-01 | `SUGGESTION` | `test_diff.py:10` importa `FileChangeKind` de `models` | — | fechado |
| S-UT-03 | `SUGGESTION` | `test_main_snapshot.py:120-123` `read_file` dirty → `FileNotFoundInCommitError` | — | fechado |
| S-UT-02 | `SUGGESTION` | U-M04 sem token no construtor | Preferir caminho com token (já coberto U-G04/U-G06/MS-12) | aberto (não bloqueante) |

### Decisão

`APPROVED_BY_ARCHITECT` — unit-test-plan v0.1.1 + fase vermelha. Prosseguir para implementação (Developer).
