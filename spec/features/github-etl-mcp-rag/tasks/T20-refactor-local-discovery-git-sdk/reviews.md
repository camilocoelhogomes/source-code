# Reviews — T20-refactor-local-discovery-git-sdk

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T20-refactor-local-discovery-git-sdk` |

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
| M-01 | `MAJOR` | `design.md` §3 (fluxo: “bare”); T06 `design.md` §4.4 + `git_fs.py` `_resolve_git_dir` (só `.git` dir/file) | Declarar política explícita de bare: (a) paridade T06 — não tratar bare como candidato válido, ou (b) aceitar bare como delta intencional do SDK, com justificativa e caso de teste. Remover menção ambígua que contradiz “sem mudança de produto”. |
| M-02 | `MAJOR` | `design.md` D-T20-003 + D-T20-005 + §7; `git_fs.py` L107–L120 (`.git` dir ⇒ `is_git_repo=True`) vs GitPython `InvalidGitRepositoryError` | Incluir tabela de paridade T06→GitPython para: worktree, gitdir file, packed-refs, sem `main`, não-git, não-diretório, `.git` incompleto/corrupto, bare. Onde a classificação/`reason` mudar, documentar como exceção justificada à D-T20-003 (não afirmar “reason idênticas” de forma absoluta). |
| S-01 | `SUGGESTION` | `design.md` §3 / implementação futura de `inspect_repo` | Usar `Repo` com close/context manager para evitar vazamento de recursos do SDK. |
| S-02 | `SUGGESTION` | `design.md` §8 (“backend git do ambiente”); T06 design §4.4 (“sem exigir binário git”) | Explicitar no DoD/riscos se `git` CLI no PATH é requisito runtime/CI desta task (além da lib GitPython). |

### Resumo

Alinhamento geral a BR-023 / DEC-015 / DT-001, fronteira no adaptador `git_fs.py` e preservação de `LocalRepoDiscovery` estão corretos. Rollback e fora de escopo adequados. Não aprovar enquanto M-01 e M-02 permanecerem abertos — contradizem a promessa de paridade observável com T06.

## Review — Design v0.1.1

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `design.md` v0.1.1 |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Achados anteriores

| ID | Severidade | Estado | Evidência da correção |
|---|---|---|---|
| M-01 | `MAJOR` | `RESOLVED` | D-T20-006; fluxo §3 (`repo.bare` → `not a git repository`); §3.2 linha bare; DoD §14 |
| M-02 | `MAJOR` | `RESOLVED` | §3.2 tabela de paridade; D-T20-003 escopo a caminhos de produto; deltas de stub justificados |
| S-01 | `SUGGESTION` | `RESOLVED` | `with git.Repo(path) as repo`; DoD context manager |
| S-02 | `SUGGESTION` | `RESOLVED` | D-T20-007; §8/§11/§14 (`git` no PATH) |

### Achados novos

Nenhum `BLOCKING` ou `MAJOR`.

### Resumo

`APPROVED_BY_ARCHITECT` — design v0.1.1 fecha M-01/M-02 com política bare explícita e tabela de paridade; S-01/S-02 incorporados. Pronto para BDD/interfaces no pipeline.

## Review — BDD v0.1.0

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` v0.1.0 |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Achados

| ID | Severidade | Evidência | Correção esperada |
|---|---|---|---|
| S-BDD-01 | `SUGGESTION` | `bdd.md` T20-SDK-01 (proíbe ad-hoc `refs/heads/*` e `packed-refs`); design §2/§14 também exige zero parse ad-hoc de `.git` | Opcional: alinhar o Então de T20-SDK-01 à proibição completa (`.git` + refs + `packed-refs`), espelhando `interfaces.md` §3.1. Não bloqueia: uso obrigatório de `git.Repo` já implica o fechamento de DT-001. |

### Cobertura verificada

| Critério | Evidência |
|---|---|
| Regressão BDD-016/018 (LOC T06) | T20-LOC-01..06 mapeiam LOC-01..06; intenção preservada |
| Conformidade SDK (DT-001 / BDD-024 parcial) | T20-SDK-01 (`git.Repo`, sem ad-hoc refs/`packed-refs`) |
| Corners packed-refs / gitdir / bare | T20-SDK-02, T20-SDK-03, bare em T20-SDK-01 (D-T20-006) |

### Resumo

`APPROVED_BY_ARCHITECT` — BDD cobre regressão de produto e conformidade SDK com corners exigidos. Nenhum `BLOCKING`/`MAJOR`.

## Review — Interfaces v0.1.0

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` v0.1.0 |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Achados

Nenhum `BLOCKING`, `MAJOR` ou `SUGGESTION`.

### Contratos verificados

| Critério | Evidência |
|---|---|
| `LocalRepoDiscovery` inalterado | §1 / §2.1 assinaturas e invariantes T06 |
| GitPython confinado | §3.1–3.2 import só em `git_fs.py`; stdlib para I/O genérico |
| Comentários responsabilidade/motivo | §2.1–2.3, §3.1 |
| Proibição parse ad-hoc | §3.1 (refs / `packed-refs` / conteúdo `.git`) |
| Bare + context manager | §3.1 (D-T20-006; `git.Repo` context manager) |

### Resumo

`APPROVED_BY_ARCHITECT` — fronteira de contrato correta; refactor interno documentado sem churn de superfície pública.

## Review — Unit test plan + testes unitários/BDD T20 v0.1.0

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` v0.1.0 + `tests/unit/sources/local/test_git_fs.py` + `tests/bdd/test_local_discovery_git_sdk.py` + fixtures `tests/bdd/test_local_discovery.py` |
| Resultado | `CHANGES_REQUIRED` |

### Achados

| ID | Severidade | Evidência | Correção esperada |
|---|---|---|---|
| M-UT-01 | `MAJOR` | `test_local_discovery_git_sdk.py` L60 `assertIn("Repo", source)`; módulo atual já contém `Repo` via `RepoInspection` (6 ocorrências) sem import GitPython | Exigir evidência inequívoca de GitPython, p.ex. `from git import Repo` / `git.Repo` / regex `with\s+Repo\s*\(`, não o substring `Repo` (colide com `RepoInspection`). |
| M-UT-02 | `MAJOR` | `test_git_fs.py` L218–L222 (`test_t20_repo_opened_as_context_manager`): só exige `"with"` e `"Repo"` no source de `inspect_repo`; `"Repo"` já casa com `return RepoInspection(...)` | Exigir padrão de context manager do SDK (`with Repo(` ou equivalente) para não passar com `with` genérico + `RepoInspection`. |

### Cobertura verificada (suficiente quando M-UT-* corrigidos)

| Critério | Evidência |
|---|---|
| Extremos/corners (bare, packed-refs, gitdir, incomplete, sem main) | UT-T20-04..08; T20-SDK-02/03; bare em UT-T20-07 + T20-SDK-01 |
| Contrato SDK (spy Repo chamado; sem parse ad-hoc) | UT-T20-09 spy; UT-T20-11 + T20-SDK-01 proíbem helpers/packed-refs |
| BDD-016/018 não enfraquecidos | LOC-01..06 em `test_local_discovery.py` com fixtures `Repo.init`; intenção preservada |
| TDD vermelho pré-impl | Confirmado: **5 failed, 2 passed** (conformidade T20); razão = código ad-hoc (§5 do plan) |

### Achados não bloqueantes

| ID | Severidade | Evidência | Nota |
|---|---|---|---|
| S-UT-01 | `SUGGESTION` | UT-T20-09 `patch.object(git_fs, "Repo", ...)` sem `create=True` → `AttributeError` pré-impl | Opcional: `create=True` para falhar em `repo_cls.called` com mensagem de asserção mais clara. |

### Resumo

`CHANGES_REQUIRED` — plano e corners/TDD estão alinhados ao design; BDD-016/018 preservados. Não aprovar enquanto M-UT-01/M-UT-02 permanecerem: asserts de conformidade SDK por substring `Repo`/`with` são falsos positivos face a `RepoInspection`.

## Review — Unit test plan + testes unitários/BDD T20 v0.1.1

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` v0.1.1 + `tests/unit/sources/local/test_git_fs.py` + `tests/bdd/test_local_discovery_git_sdk.py` + fixtures `tests/bdd/test_local_discovery.py` |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Achados anteriores

| ID | Severidade | Estado | Evidência da correção |
|---|---|---|---|
| M-UT-01 | `MAJOR` | `RESOLVED` | `test_local_discovery_git_sdk.py` L60–L65: regex `from git import Repo` (+ variante `git.repo`) e `with\s+Repo\s*\(` |
| M-UT-02 | `MAJOR` | `RESOLVED` | `test_git_fs.py` L220–L227: `assertRegex(..., r"with\s+Repo\s*\(")` |
| S-UT-01 | `SUGGESTION` | `RESOLVED` | `test_git_fs.py` L179–L181: `patch.object(..., create=True)` |

### Achados novos

Nenhum `BLOCKING` ou `MAJOR`.

### Cobertura verificada

| Critério | Evidência |
|---|---|
| Extremos/corners | UT-T20-04..08; T20-SDK-02/03; bare UT-T20-07 + T20-SDK-01 |
| Contratos SDK inequívocos | spy `Repo` chamado; import GitPython; `with Repo(`; zero parse ad-hoc |
| BDD-016/018 | LOC-01..06 fixtures `Repo.init`; intenção preservada |
| TDD vermelho pré-impl | **5 failed, 2 passed** (conformidade); falhas por código ad-hoc / SDK ainda ausente |

### Resumo

`APPROVED_BY_ARCHITECT` — M-UT-01/M-UT-02/S-UT-01 fechados; asserts SDK não colidem mais com `RepoInspection`. Pronto para implementação de produção (Developer).
