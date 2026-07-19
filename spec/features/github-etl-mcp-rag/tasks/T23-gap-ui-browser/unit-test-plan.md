# Unit Test Plan — T23-gap-ui-browser

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T23-gap-ui-browser` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `TESTS_READY_FOR_REVIEW` |
| Versão | `0.1.0` |
| Design / BDD / Interfaces | `0.1.0` / `0.1.0` / `0.1.0` (todos `APPROVED_BY_ARCHITECT`) |
| Cobertura alvo | Gate manifesto (deps/suite/resource/tags/README/fixture); suite global ≥95% permanece |
| Branch | `feature/github-etl-mcp-rag-T23-gap-ui-browser` |
| Suíte | `tests/bdd/test_ui_browser_gap.py` + `tests/unit/e2e/test_ui_browser_manifest.py` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Plano + testes manifesto TDD; RED por dep/suite/resource/README/wildcard ausentes. Modo autônomo — aguarda review Architect. |

## 1. Estratégia

| Camada | Arquivo | Fronteira |
|---|---|---|
| BDD Camada A (UB-01..09, UB-18 leve) | `tests/bdd/test_ui_browser_gap.py` | texto/TOML/filesystem reais |
| Unit extremos / corners | `tests/unit/e2e/test_ui_browser_manifest.py` | asserts de shape + sintéticos |
| Helper wildcard (se Developer criar) | unit dedicado só se existir módulo | I-T23-013 — opcional |

- **Sem** Playwright / `rfbrowser init` / browser real (D-T23-014 / I-T23-010).
- BDD = superfície de aceite Camada A; unitários focam extremos (ordem green path, tags incompletas, fixture sem wildcard, README fraco, secrets).
- Sem alteração de produção nesta etapa QA.
- Pré-implementação: falhas nos asserts de artefatos reais — **RED esperado**.

## 2. Matriz unitária / manifesto

### 2.1 Dependências e2e (M-T23-001..004 / UB-01)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-UB-01 | `pyproject.toml` `[e2e]` declara `robotframework-browser` (≥18 ou pin) | presente | M-T23-001; UB-01 |
| UT-UB-02 | `requirements-e2e.txt` espelha a dep | presente | M-T23-002; UB-01 |
| UT-UB-03 | RF / Requests / httpx permanecem em ambos | presentes | M-T23-003 |
| UT-UB-04 | deps e2e sem PAT/`ghp_` real | sem secret | M-T23-004; UB-07 |

### 2.2 Green path (M-T23-013 / UB-02 / UB-08)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-UB-10 | `GREEN_PATH_SUITES` contém `"ui_browser"` | presente | I-T23-006; UB-02 |
| UT-UB-11 | `"ui_browser"` imediatamente após `"ui"` | ordem canônica | design §3.3 |
| UT-UB-12 | suites T21 (`health`…`negative`) permanecem | presentes | UB-02 |
| UT-UB-13 | `GREEN_PATH_SUITE_MARKERS` (helpers) espelha `ui_browser` | presente + ordem | I-T23-007 |
| UT-UB-14 | Aceite negativo: sem `ui_browser` na lista = falha gate | assert falha se ausente | UB-08; M-T23-015 |

### 2.3 Artefatos Robot (M-T23-010..012 / UB-03/04/18)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-UB-20 | Existe `e2e/robot/resources/browser.resource` | arquivo | M-T23-010; UB-03 |
| UT-UB-21 | Resource declara `Open Ui Browser`, `Close Ui Browser`, `Wait Repos Table Loaded` | keywords | I-T23-003 |
| UT-UB-22 | Existe `e2e/robot/ui_browser.robot` | arquivo | M-T23-011 |
| UT-UB-23 | Suite: `Library Browser` + `Resource … browser.resource` | texto | UB-03 |
| UT-UB-24 | `Force Tags` contém `ui`, `browser`, `mvp` | tags | UB-04 |
| UT-UB-25 | Tags case `bdd001,002,007,009,010,016,019,023` | todas presentes | UB-04; inventário |
| UT-UB-26 | Suite Setup/Teardown Open/Close Ui Browser | presentes | UB-18 |
| UT-UB-27 | Seletores canônicos referidos na suite (`#repos-table`, `#btn-index`, …) | texto | UB-18 |

### 2.4 API T21 preservada (M-T23-014 / UB-09)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-UB-30 | `ui.robot` e `catalog_indexing.robot` existem | arquivos | D-T23-012 |
| UT-UB-31 | Tags/cases API BDD-009/010/023 e 001/002/007/016 ainda no texto | não removidos | UB-09 |

### 2.5 Fixture + README + secrets (M-T23-016..019 / UB-05/06/07)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-UB-40 | `config.e2e.json` inclusão GitHub com wildcard (`*` / `?` / `[`) que cobre `source-code` | wildcard | D-T23-005; UB-06 |
| UT-UB-41 | `token` = `{ "env": "GITHUB_TOKEN" }`; conexão `file://` local permanece | shape | UB-06/07 |
| UT-UB-42 | README: `rfbrowser init` + deps e2e + `ui_browser.robot` + headless | strings | UB-05; M-T23-018 |
| UT-UB-43 | Artefatos T23 sem PAT/`ghp_` real | sem secret | UB-07 |

### 2.6 Extremos / corners / entradas inválidas

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-UB-50 | Fixture com match exato (sem `*`) | rejeita (estado atual = RED) | D-T23-005 |
| UT-UB-51 | Fixture wildcard que **não** casa `source-code` (ex. `other-*`) | rejeita | corner BDD-001 |
| UT-UB-52 | Fixture `repos: []` | rejeita (estado vazio) | entradas inválidas |
| UT-UB-53 | Green path com `ui_browser` antes de `ui` | rejeita ordem | I-T23-006 |
| UT-UB-54 | Green path sem `ui` mas com `ui_browser` | rejeita | regressão T21 |
| UT-UB-55 | Suite Robot só com `Library RequestsLibrary` (sem Browser) | rejeita | UB-03/08 |
| UT-UB-56 | Tags `Force Tags` sem `browser` | rejeita | UB-04 |
| UT-UB-57 | Subconjunto de tags bdd (falta `bdd019`) | rejeita | inventário |
| UT-UB-58 | README menciona Browser Library mas sem `rfbrowser init` | rejeita | M-T23-018 |
| UT-UB-59 | README vazio | rejeita | estado vazio |
| UT-UB-60 | Resource sem `Close Ui Browser` | rejeita | lifecycle |
| UT-UB-61 | Texto com `ghp_` + ≥20 chars alfanuméricos | rejeita | secrets |
| UT-UB-62 | Placeholder documental `ghp_...` | aceita | corner docs |
| UT-UB-63 | Happy path sintético: lista suites canônica T23 | aceita | I-T23-006 |

## 3. Mapeamento UB-* → testes

| Cenário BDD | Pytest (manifesto) | Unit extremos |
|---|---|---|
| UB-01 | `TestUB01BrowserDep` | UT-UB-01..04 |
| UB-02 | `TestUB02GreenPathSuites` | UT-UB-10..14, 53..54, 63 |
| UB-03 | `TestUB03RobotArtifacts` | UT-UB-20..23, 55, 60 |
| UB-04 | `TestUB04Tags` | UT-UB-24..25, 56..57 |
| UB-05 | `TestUB05Readme` | UT-UB-42, 58..59 |
| UB-06 | `TestUB06FixtureWildcard` | UT-UB-40..41, 50..52 |
| UB-07 | `TestUB07NoSecrets` | UT-UB-43, 61..62 |
| UB-08 | `TestUB08RequestsAloneNotEnough` | UT-UB-14 (+ artefatos) |
| UB-09 | `TestUB09ApiSuitesPreserved` | UT-UB-30..31 |
| UB-10..17 | Camada B Robot (fora do gate pytest) | — |
| UB-18 | `TestUB18LifecycleSelectors` (texto) | UT-UB-26..27 |

## 4. Demonstração RED (TDD)

```bash
python -m pytest tests/bdd/test_ui_browser_gap.py tests/unit/e2e/test_ui_browser_manifest.py -q --tb=line --no-cov
```

Falhas esperadas pré-implementação (artefatos reais):

| Área | Razão |
|---|---|
| UB-01 / UT-UB-01..02 | `robotframework-browser` ausente em pyproject / requirements-e2e |
| UB-02 / UT-UB-10..13 | `GREEN_PATH_SUITES` / markers sem `ui_browser` |
| UB-03 / UT-UB-20..23 | `browser.resource` / `ui_browser.robot` ausentes |
| UB-04 / UB-18 | suite inexistente → tags/lifecycle falham |
| UB-05 | README sem `rfbrowser init` / `ui_browser.robot` |
| UB-06 / UT-UB-40/50 | fixture com match exato (sem wildcard) |
| UB-08 | green path / artefatos browser ausentes |
| UB-07 / UB-09 / UT-UB-03 / corners sintéticos | devem **passar** (API suites + secrets ok no status quo; sintéticos exercitam helpers) |

Evidência pré-implementação (2026-07-19): `15 failed, 20 passed`
(`pytest tests/bdd/test_ui_browser_gap.py tests/unit/e2e/test_ui_browser_manifest.py --no-cov`).

Após implementação Developer: Camada A verde; Camada B = Robot + `rfbrowser init` na stack.

## 5. Fora de escopo unitário

- Playwright / Chromium / `rfbrowser init` no pytest
- Prova DOM real (UB-10..17)
- Tooling compose/zoekt (T22)
- Alterar deps/suite/robot/README/fixture nesta etapa QA
- Assert paralelismo workers (T26)

## 6. Estado

`TESTS_READY_FOR_REVIEW` — plano `0.1.0` + suíte manifesto/unitários prontos para review Architect. **Não** marcado `APPROVED` nesta entrega.
