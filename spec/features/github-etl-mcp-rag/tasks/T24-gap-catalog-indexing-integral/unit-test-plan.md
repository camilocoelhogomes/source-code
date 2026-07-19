# Unit Test Plan — T24-gap-catalog-indexing-integral

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T24-gap-catalog-indexing-integral` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Design / BDD / Interfaces | `0.1.0` / `0.1.0` / `0.1.0` (todos `APPROVED_BY_ARCHITECT`) |
| Cobertura alvo | Helpers `CatalogIndexingKeywords` + seed `ensure_local_git_fixture`; suite global ≥95% |
| Branch | `feature/github-etl-mcp-rag-T24-gap-catalog-indexing-integral` |
| Suíte | `tests/unit/e2e/test_catalog_indexing_keywords.py` + extensão `tests/unit/e2e/test_coverage_gaps.py` |
| Import alvo | `e2e/robot/libraries/CatalogIndexingKeywords.py` (sys.path) + `github_rag.e2e.launcher` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Plano + unitários TDD; RED por ImportError (library ausente) + AssertionError (seed BDD-006 incompleto). |
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Review: reforço E01/S01 com tokens canônicos I-T24-009 (MAJOR corrigido); S03 coberto por S01 + T21 `creates_repo`. |

## 1. Estratégia

| Camada | Arquivo | Fronteira |
|---|---|---|
| Helpers cron/MCP/git host | `test_catalog_indexing_keywords.py` UT-T24-C* / P* / H* / E* / M* / R* | `CatalogIndexingKeywords` (I-T24-003) |
| Seed launcher | `test_coverage_gaps.py` (extensão) UT-T24-S* | `ensure_local_git_fixture` (I-T24-006) |

- Sem stack Podman/Robot nesta camada (helpers isolados + tempfile git).
- Import: `sys.path` → `e2e/robot/libraries/` (interfaces §6); **não** mover helpers para `src/` fora de `launcher.py`.
- Pré-implementação: `ImportError` (módulo ausente) e/ou `AssertionError` (seed T21 sem paths BDD-006).
- Domínio ETL intocado; só superfície e2e.

## 2. Matriz unitária

### 2.1 `cron_expression_firing_soon_utc` (UT-T24-C*)

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-T24-C01 | `now` injetado meio do minuto (ex. 12:34:10 UTC) | 5 campos; minuto absoluto 34 **ou** 35; hora/dom/mon/dow coerentes UTC | §6.1; I-T24-007 |
| UT-T24-C02 | minuto 59 → wrap | minuto `0`; hora +1 (ex. 14:59 → `0 15 …`) | limite minuto |
| UT-T24-C03 | 23:59 UTC → wrap dia | minuto `0`; hora `0`; `dom` avança (mês/ano se necessário) | wrap UTC |
| UT-T24-C04 | formato | exatamente 5 tokens numéricos (ou `*` só se produto exigir — preferir absolutos) | §6.1 |
| UT-T24-C05 | `now=None` usa UTC (não local) | com relógio mockado UTC, expressão bate no UTC mock | R-T24-01 |
| UT-T24-C06 | minuto 0 | expressão válida (0 ou 1) sem negativo | limite inferior |

### 2.2 `parse_mcp_list_repos_commits` (UT-T24-P*)

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-T24-P01 | happy: `{"repos":[…]}` por `repository_id` | dict com SHAs | §6.2; MCP serialize |
| UT-T24-P02 | lookup por `repo_key` / `repo_identifier` | localiza repo correto | id vs identifier |
| UT-T24-P03 | repo ausente | `AssertionError` (ou exceção clara) | §6.2 |
| UT-T24-P04 | JSON inválido (`not-json`) | exceção clara | JSON inválido |
| UT-T24-P05 | campos `null` / ausentes | strings vazias **ou** erro explícito (não TypeError opaco) | campos null |
| UT-T24-P06 | shape aninhado content/list | ainda extrai se envelope tipico MCP | JSON aninhado |
| UT-T24-P07 | lista `repos` vazia | erro (repo ausente) | estado vazio |
| UT-T24-P08 | sem `repo_id` nem `repo_identifier` | erro claro | entrada inválida |

### 2.3 `host_commit_on_main` (UT-T24-H*)

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-T24-H01 | repo git com `main` | retorna SHA 40 hex; tip muda | §6.3 |
| UT-T24-H02 | segundo commit (conteúdo distinto) | SHA_B ≠ SHA_A | tip muda |
| UT-T24-H03 | diretório sem `.git` | exceção com stderr/mensagem (sem secrets) | falha |
| UT-T24-H04 | mensagem/content únicos opcionais | arquivo relativo criado; commit usa message | §6.3 |

### 2.4 `prepare_eligibility_tree` (UT-T24-E*)

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-T24-E01 | árvore mínima paths include/exclude | paths + tokens canônicos §4 nos arquivos + mapa markers não vazio; PNG mínimo | §6.4; I-T24-009 |
| UT-T24-E02 | 2ª chamada idempotente | sem erro; árvore permanece; markers estáveis | idempotência |
| UT-T24-E03 | `.gitignore` → `ignored_dir/` | arquivo ignore + secret marker presentes | BDD-006 |
| UT-T24-E04 | sem `.git` | falha clara | falha |

### 2.5 `prepare_main_only_branches` (UT-T24-M*)

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-T24-M01 | pós-condição | HEAD `main`; `other` existe; uncommitted no WT não staged | §6.5 |
| UT-T24-M02 | markers | `MAIN_ONLY` na main; `OTHER` só em other; `UNCOMMITTED` no WT | I-T24-009 |
| UT-T24-M03 | 2ª chamada idempotente | HEAD main; uncommitted recriado; other existe | idempotência |
| UT-T24-M04 | sem `.git` | falha clara | falha |

### 2.6 `resolve_sample_local_dir` (UT-T24-R*)

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-T24-R01 | `repos_root` informado | `…/sample-local` | §6.6 |
| UT-T24-R02 | default / env | Path sob fixture e2e ou `HOST_REPOS` | §6.6 |

### 2.7 `ensure_local_git_fixture` seed T24 (UT-T24-S*)

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-T24-S01 | 1ª chamada cria seed BDD-006 | paths include/exclude + `.gitignore` + tokens canônicos I-T24-009 no blob | §7; I-T24-006/009 |
| UT-T24-S02 | rerun com `.git` existente | **não** early-return cego; seed idempotente ainda materializa paths + `MAIN_ONLY_MARKER` | §7 contrato |
| UT-T24-S03 | compat T21 | README + `.git` + `main` permanecem | coberto por S01 + `test_ensure_local_git_fixture_creates_repo` |

## 3. Demonstração RED (TDD)

```bash
.venv/bin/python -m pytest \
  tests/unit/e2e/test_catalog_indexing_keywords.py \
  tests/unit/e2e/test_coverage_gaps.py -k 't24 or T24 or seed_bdd006 or eligibility' \
  -q --tb=line --no-cov
```

Falhas esperadas pré-implementação:

| Área | Razão |
|---|---|
| `CatalogIndexingKeywords` | `ImportError` / `ModuleNotFoundError` — arquivo ainda não existe |
| `ensure_local_git_fixture` seed | `AssertionError` — early-return T21 sem paths BDD-006 |

### Evidência RED (2026-07-19)

```text
30 failed in 0.19s
- 28× ModuleNotFoundError: No module named 'CatalogIndexingKeywords'
- 2× AssertionError: seed BDD-006 paths ausentes / early-return com .git
```

Comando:

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/unit/e2e/test_catalog_indexing_keywords.py \
  tests/unit/e2e/test_coverage_gaps.py::TestLauncherCoverage::test_ensure_local_git_fixture_seeds_bdd006_paths \
  tests/unit/e2e/test_coverage_gaps.py::TestLauncherCoverage::test_ensure_local_git_fixture_seed_idempotent_with_existing_git \
  -q --tb=line --no-cov
```

## 4. Estado

`APPROVED_BY_ARCHITECT` — unit-test-plan `0.1.1` + unitários RED (tokens canônicos I-T24-009). Sem implementação de produção.
