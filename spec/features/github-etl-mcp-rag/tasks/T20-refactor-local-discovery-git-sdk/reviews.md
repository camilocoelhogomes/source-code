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
