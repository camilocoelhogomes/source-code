# Interfaces — T23-gap-ui-browser

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T23-gap-ui-browser` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T23-gap-ui-browser` |
| Escopo desta etapa | Contratos Robot (`browser.resource`, `ui_browser.robot`) + extensão mínima Python (`GREEN_PATH_SUITES`) + contratos declarativos M-T23-* (deps, fixture, README, testids opcionais) — **sem** Protocols novos de domínio |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-19 (modo autônomo) |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Self-review: keywords browser; superfície `ui_browser.robot`; extensão `GREEN_PATH_SUITES`; M-T23-* deps/README/wildcard/testid; alinhado design 0.1.0 / BDD UB-01..18. |

## 1. Escopo e exclusões

### Em escopo

| Superfície | Artefato | Papel |
|---|---|---|
| Resource Robot | `e2e/robot/resources/browser.resource` | Keywords lifecycle browser (C-T23-02) |
| Suite Robot | `e2e/robot/ui_browser.robot` | Cases `evidencia_browser` (C-T23-03) |
| Green path Python | `src/github_rag/e2e/suite.py` (+ espelho markers) | Inclusão `ui_browser` (C-T23-04) |
| Deps e2e | `pyproject.toml` / `requirements-e2e.txt` | `robotframework-browser` (C-T23-01) |
| Fixture | `e2e/fixtures/config.e2e.json` | Wildcard inclusão (C-T23-06) |
| Docs | `e2e/README.md` | `rfbrowser init` + suite (D-T23-013) |
| UI mínima (opcional) | `web/index.html` / `web/app.js` | `data-testid` só se necessário (C-T23-05) |
| Gate CI | `tests/bdd/test_ui_browser_gap.py` (+ unitários) | Manifesto sem Playwright (C-T23-07) |

### Fora de escopo

| Item | Motivo |
|---|---|
| Novos `Protocol` de domínio em `src/github_rag/**` (exceto extensão de lista já existente) | T23 = evidência e2e; D-T23-014 |
| Remover/substituir `ui.robot` / `catalog_indexing.robot` | D-T23-012 |
| Tooling compose/zoekt | T22 |
| Assert paralelismo workers (BDD-002) | R-T23-05 / T26 |
| BDD-015; feature filha | Fora do aceite |
| Redesign UI | D-T23-004 |

## 2. Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T23-001 | Resource novo `browser.resource` separado de `common.resource` | Lifecycle Browser ≠ sessão HTTP RequestsLibrary | D-T23-002; C-T23-02 |
| I-T23-002 | Suite nova `ui_browser.robot` (não expandir `ui.robot` com browser) | Isola deps Playwright; tags `evidencia_browser` claras | D-T23-003; C-T23-03 |
| I-T23-003 | Keywords canônicas: `Open Ui Browser`, `Close Ui Browser`, `Wait Repos Table Loaded` | Contrato mínimo de lifecycle + wait de tabela | design §3.2; UB-03/18 |
| I-T23-004 | Suite Setup/Teardown obrigatórios chamando Open/Close | Browser sempre aberto/fechado na suite | UB-18; design §5 |
| I-T23-005 | `Library Browser` na suite; `Force Tags ui browser mvp` + tags `bdd00x` | Aceite inventário + filtro Robot | UB-04; design §3.3 |
| I-T23-006 | Extender `GREEN_PATH_SUITES` com `"ui_browser"` **após** `"ui"` | Ordem canônica design §3.3; prova `python -m github_rag.e2e` | UB-02; C-T23-04 |
| I-T23-007 | Espelhar markers em `tests/unit/e2e/helpers.py` (`GREEN_PATH_SUITE_MARKERS`) | Gate unitário/BDD T21 não diverge do runtime | UB-02 |
| I-T23-008 | **Não** alterar Protocols `E2eStackLauncher` / `RobotMvpSuite` / assinatura `run()` | T21 estável; só lista de suites muda | T21 I-T21-002; design §9 |
| I-T23-009 | Dep `robotframework-browser>=18` em optional `e2e` + `requirements-e2e.txt`; preservar RF/Requests/httpx | Motor browser no ambiente e2e | D-T23-001; UB-01 |
| I-T23-010 | Bootstrap `rfbrowser init` documentado em `e2e/README.md`; **fora** do pytest unitário | Binários Playwright não no gate CI manifesto | D-T23-013/014; UB-05 |
| I-T23-011 | Fixture `config.e2e.json`: inclusão wildcard (ex. `camilocoelhogomes/source-*`); token só `{ "env": "GITHUB_TOKEN" }` | BDD-001 integral + sem secrets | D-T23-005/015; UB-06/07 |
| I-T23-012 | Seletores: IDs/`data-*` existentes; `data-testid` só se mínimo | Estabilidade sem redesign | D-T23-004; UB-18 |
| I-T23-013 | Helper Python de match wildcard (glob/`fnmatch`): **opcional**; se criado, em módulo de teste ou helper fino testável — não Protocol de produto | Só se keyword Robot precisar; unitários cobrem extremos | design §3.5.1 / §3.7 |
| I-T23-014 | Contratos declarativos `M-T23-*` materializados pelo Developer; pytest Camada A asserta existência/shape | Padrão T22 | UB-01..09 |
| I-T23-015 | Headless Chromium default; variável headed opcional se implementada | Operabilidade debug sem mudar aceite | design §3.1; UB-05 |
| I-T23-016 | Keywords **não** logam token; reuso redaction `common.resource` onde aplicável | BDD-019 / REQ-048 | D-T23-015; UB-12 |

## 3. Contratos Robot — `browser.resource`

**Arquivo:** `e2e/robot/resources/browser.resource`  
**Componente:** C-T23-02  
**Importa:** `common.resource` (URLs, `${UI_BASE}`, `${REFERENCE_REPO}`, timeouts, redaction)

### 3.1 Responsabilidade do resource

Congelar keywords de **lifecycle e wait** do Browser Library para a management UI, reutilizando constantes de `common.resource` sem misturar sessão RequestsLibrary.

### 3.2 Motivo da separação

| Separação | Por quê |
|---|---|
| `browser.resource` × `common.resource` | HTTP session / redaction HTTP ≠ New Browser / New Page / Close Browser |
| Keywords nomeadas × uso direto da lib nos cases | Open/Close/Wait são o contrato estável; Click/Fill/Get podem ser da lib nos cases (design §3.2) |
| Resource × suite | Lifecycle reutilizável; cases BDD ficam em `ui_browser.robot` |

### 3.3 Keywords canônicas

```robot
*** Keywords ***
Open Ui Browser
    [Documentation]
    ...    Responsabilidade: criar browser Chromium (headless default) e abrir
    ...    página ``${UI_BASE}/``.
    ...    Motivo da separação: único ponto de New Browser/New Page; Suite Setup
    ...    não duplica argv Playwright; headed opcional via variável se existir.
    # New Browser    chromium    headless=${True}   (ou equivalente Browser Library)
    # New Page    ${UI_BASE}/

Close Ui Browser
    [Documentation]
    ...    Responsabilidade: encerrar o browser (Suite Teardown).
    ...    Motivo da separação: teardown idempotente sem acoplar a cases.
    # Close Browser

Wait Repos Table Loaded
    [Documentation]
    ...    Responsabilidade: aguardar ``#repos-table`` pronta para asserts
    ...    (ex.: ``tbody tr`` ou empty-state documentado).
    ...    Motivo da separação: evita race nos cases 001/016/002 sem poll
    ...    duplicado em cada case.
    # Wait For Elements State    ...
```

| Keyword | Entrada | Efeito | BDD |
|---|---|---|---|
| `Open Ui Browser` | — (usa `${UI_BASE}`) | Browser+Page na UI | UB-18 |
| `Close Ui Browser` | — | Fecha browser | UB-18 |
| `Wait Repos Table Loaded` | — | Tabela pronta | UB-03; UB-10/11/14 |

Wrappers finos adicionais (`Click`/`Fill Text`/`Get Text`) **não** são contrato obrigatório; permitidos se reduzirem ruído.

## 4. Contratos Robot — superfície `ui_browser.robot`

**Arquivo:** `e2e/robot/ui_browser.robot`  
**Componente:** C-T23-03

### 4.1 Responsabilidade da suite

Provar no DOM (Browser Library) os fluxos UI dos BDD-001,002,007,009,010,016,019,023 — evidência `evidencia_browser` — sem substituir smokes API T21.

### 4.2 Motivo da separação

| Separação | Por quê |
|---|---|
| `ui_browser.robot` × `ui.robot` | API-smoke RequestsLibrary ≠ interação DOM; falha Playwright não quebra smoke API |
| `ui_browser.robot` × `catalog_indexing.robot` | Index/listagem HTTP permanece complementar; browser é adicional (D-T23-012) |
| Tags `browser` + `bdd00x` × tags API | Inventário filha / filtro Robot futuro |

### 4.3 Settings obrigatórios

```robot
*** Settings ***
Documentation    Evidência browser (Browser Library) — lacuna UI T23; não substitui ui.robot / catalog_indexing.robot
Resource         resources/browser.resource
Library          Browser
Force Tags       ui    browser    mvp
Suite Setup      Open Ui Browser
Suite Teardown   Close Ui Browser
```

### 4.4 Cases / tags (contrato de cobertura)

| Tag case | BDD | Assert mínimo (DOM) | Cenário BDD |
|---|---|---|---|
| `bdd001` | BDD-001 | `#repos-table` contém `${REFERENCE_REPO}`; linhas `github` casam inclusão wildcard | UB-10 |
| `bdd016` | BDD-016 | Origem `local` visível na tabela | UB-11 |
| `bdd019` | BDD-019 | Sem `<input type="password">` / campo token; body sem valor do env token | UB-12 |
| `bdd023` | BDD-023 | Sem CRUD connections; presentes `#repos-table`, checkbox `data-id`, `#btn-index`, forms exact/semantic | UB-13 |
| `bdd002` | BDD-002 | Checkbox + `#btn-index` + estados PT (`na fila`/`indexando`/`atualizado`) via poll `#btn-refresh` | UB-14 |
| `bdd007` | BDD-007 | `#repo-detail` com progresso e flags `zoekt=`/`tree_sitter=`/`metadata=` | UB-15 |
| `bdd009` | BDD-009 | `#exact-pattern` + `#exact-form` → `#search-results` não vazio | UB-16 |
| `bdd010` | BDD-010 | `#semantic-query` + `#semantic-form` → `#search-results` com hits | UB-17 |

Ordem sugerida dos cases na suite: alinhada ao fluxo design §5 (listagem → local → no-token → no-CRUD → index → detalhe → buscas). Não é contrato rígido de ordem de keywords, mas evita flake de pré-condição.

### 4.5 Seletores canônicos (contrato de estabilidade)

| Seletor | Uso |
|---|---|
| `#repos-table` / `#repos-table tbody` | listagem, origem, estados |
| `#repos-table input[type=checkbox][data-id=…]` | BDD-002 |
| `#btn-index`, `#btn-refresh` | index / poll |
| `[data-detail="…"]` | abrir detalhe BDD-007 |
| `#repo-detail` | progresso / flags |
| `#exact-pattern`, `#exact-form` | BDD-009 |
| `#semantic-query`, `#semantic-form` | BDD-010 |
| `#search-results` | hits 009/010 |
| Ausência de forms CRUD connections | BDD-023 |

`data-testid` opcionais: ver M-T23-020.

## 5. Contratos Python — extensão green path

### 5.1 `GREEN_PATH_SUITES` (obrigatório)

**Módulo:** `src/github_rag/e2e/suite.py` (e espelho de markers em `tests/unit/e2e/helpers.py`)

```python
# Extensão canônica T23 — ordem congelada (design §3.3)
GREEN_PATH_SUITES = (
    "health",
    "catalog_indexing",
    "ui",
    "ui_browser",  # NOVO — I-T23-006
    "mcp",
    "negative",
)
```

**Responsabilidade:** garantir que `DefaultRobotMvpSuite` / `python -m github_rag.e2e` invoque a suite browser no green path canônico.

**Motivo da separação:** lista de suites ≠ Protocols de launcher/credencial (I-T23-008); delta T23 é só o membro `"ui_browser"` e ordem após `"ui"`.

| Regra | Contrato |
|---|---|
| Presença | `"ui_browser"` ∈ `GREEN_PATH_SUITES` e markers espelhados |
| Ordem | imediatamente após `"ui"` |
| Preservação | `health`, `catalog_indexing`, `ui`, `mcp`, `negative` permanecem |
| Protocols | `E2eStackLauncher` / `RobotMvpSuite` / `run() -> int` **inalterados** |

### 5.2 Helper de match wildcard (opcional)

```python
# Somente se a implementação Robot precisar de helper Python (design §3.5.1).
# Local preferido: keyword Robot pura OU helper sob tests/ / e2e library fina.
# NÃO criar Protocol de produto em github_rag.catalog / github_rag.config.

def repo_matches_inclusion(repo_id: str, patterns: Sequence[str]) -> bool:
    """Responsabilidade: decidir se identificador repo casa com glob(s) de inclusão.

    Motivo da separação: regra de match testável (fnmatch) isolada de keywords
    Browser e do loader de config de produto; evita acoplar e2e ao domínio T02.
    """
    ...
```

Se **não** houver helper Python, o assert de match fica em keyword Robot — permitido; unitários extras só se o helper existir (I-T23-013).

## 6. Contratos declarativos — M-T23-*

### 6.1 Dependências e2e

| ID | Requisito | Arquivos | BDD |
|---|---|---|---|
| M-T23-001 | Declarar `robotframework-browser` (mínimo `>=18` ou pin compatível) em `[project.optional-dependencies].e2e` | `pyproject.toml` | UB-01 |
| M-T23-002 | Espelhar a mesma dep em `requirements-e2e.txt` | `requirements-e2e.txt` | UB-01 |
| M-T23-003 | Manter `robotframework`, `robotframework-requests`, `httpx` nas deps e2e | ambos | UB-01 |
| M-T23-004 | Nenhum segredo (PAT/`ghp_`) nesses arquivos | ambos | UB-07 |

**Responsabilidade (M-T23-001..004):** travar o manifesto de instalação do motor browser no optional e2e.  
**Motivo da separação deps × README init:** pip declara pacote; `rfbrowser init` baixa binários — gates distintos (I-T23-009/010).

### 6.2 Artefatos Robot e green path

| ID | Requisito | Arquivos | BDD |
|---|---|---|---|
| M-T23-010 | Existe `e2e/robot/resources/browser.resource` com keywords Open/Close (e Wait documentada) | filesystem | UB-03 |
| M-T23-011 | Existe `e2e/robot/ui_browser.robot` com `Resource … browser.resource` e `Library Browser` | filesystem | UB-03 |
| M-T23-012 | `Force Tags` contém `ui`, `browser`, `mvp`; cases/tags `bdd001`…`bdd023` do inventário T23 | `ui_browser.robot` | UB-04 |
| M-T23-013 | `GREEN_PATH_SUITES` (+ markers) inclui `ui_browser` após `ui` | `suite.py` / helpers | UB-02 |
| M-T23-014 | `ui.robot` e `catalog_indexing.robot` permanecem (browser adicional) | filesystem | UB-09 |
| M-T23-015 | Ausência de `ui_browser` na lista **ou** ausência dos artefatos Robot falha o gate pytest Camada A | testes | UB-08 |

**Responsabilidade (M-T23-010..015):** travar evidência canônica no caminho green path; formaliza aceite negativo “API HTTP sozinha não basta”.  
**Motivo da separação suite × resource:** lifecycle keywords ≠ cases BDD (I-T23-001/002).

### 6.3 Fixture e docs

| ID | Requisito | Arquivos | BDD |
|---|---|---|---|
| M-T23-016 | Inclusão GitHub usa wildcard que inclui `${REFERENCE_REPO}` (ex. `camilocoelhogomes/source-*`) | `e2e/fixtures/config.e2e.json` | UB-06 |
| M-T23-017 | `token` permanece `{ "env": "GITHUB_TOKEN" }` sem valor literal; conexão `file://` local permanece | fixture | UB-06/07 |
| M-T23-018 | README documenta `pip install -e ".[e2e]"`, passo `rfbrowser init`, suite `ui_browser.robot`, headless default | `e2e/README.md` | UB-05 |
| M-T23-019 | README/docs/fixtures/robot tocados **não** embutem PAT/`ghp_` | artefatos T23 | UB-07 |

**Responsabilidade (M-T23-016..019):** dados de fixture + operabilidade operador/CI sem secrets.  
**Motivo da separação fixture × README:** critério BDD-001 (dados) ≠ bootstrap Playwright (host).

### 6.4 `data-testid` (opcional mínimo)

| ID | Requisito | Arquivos | BDD |
|---|---|---|---|
| M-T23-020 | Se seletor existente for frágil, permitir `data-testid` mínimo (ex. `repo-origin`, `repo-state`) em `web/*` | `web/index.html` / `web/app.js` | UB-18; D-T23-004 |
| M-T23-021 | Proibido redesign, features UI novas ou mudança de comportamento além de estabilidade e2e | `web/*` | design §3.4 |

**Responsabilidade (M-T23-020..021):** estabilidade de seletor sem alterar produto.  
**Motivo da separação testid × cases Robot:** atributo DOM é contrato de UI mínima; asserts permanecem na suite.

## 7. Reuso T21 / T22 (congelado)

| Contrato | Mudança em T23? |
|---|---|
| `E2eStackLauncher` / `PodmanE2eStackLauncher` | Não |
| `RobotMvpSuite` / `DefaultRobotMvpSuite.run()` | Não (só lista de suites) |
| `E2eCredentialResolver` / erros / timeouts | Não |
| Compose zoekt / provider docs (T22) | Não — pré-req operacional |
| `common.resource` (URLs, redaction) | Reuso; sem misturar Browser keywords |

**Responsabilidade desta seção:** deixar explícito o boundary estável.  
**Motivo da separação:** T23 adiciona evidência browser; não reabre launcher/credencial/tooling.

## 8. Gate pytest (Camada A) vs prova real (Camada B)

| Camada | O que o contrato exige | Proibido |
|---|---|---|
| A — `tests/bdd/test_ui_browser_gap.py` (+ unit) | Asserts M-T23-* / I-T23-006 (texto/TOML/filesystem) | `rfbrowser init`, Chromium, browser real |
| B — Robot stack | Cases UB-10..17 verdes com Browser Library | Contar RequestsLibrary-só como aceite |

**Responsabilidade:** D-T23-014 / padrão T22.  
**Motivo da separação:** CI unitário leve × prova e2e pesada.

## 9. Rastreabilidade

| Contrato | Design | BDD |
|---|---|---|
| I-T23-001..003 / §3 keywords | D-T23-002; §3.2 | UB-03/18 |
| I-T23-002/004/005 / §4 suite | D-T23-003; §3.3–3.5 | UB-04; UB-10..17 |
| I-T23-006/007 / §5 GREEN_PATH | D-T23-003; C-T23-04 | UB-02/08 |
| M-T23-001..004 deps | D-T23-001 | UB-01 |
| M-T23-016..017 fixture | D-T23-005/015 | UB-06/07 |
| M-T23-018 README | D-T23-013 | UB-05 |
| M-T23-020..021 testid | D-T23-004 | UB-18 |
| M-T23-014/015 API preservada + negativo | D-T23-012; ENG-008 | UB-08/09 |

## 10. Handoff

| Próximo | Entrega |
|---|---|
| QA (unit plan) | Testes unitários dos contratos Python/manifesto + extremos do helper se existir |
| Developer | Materializar `browser.resource`, `ui_browser.robot`, deps, suite list, fixture, README, testids mínimos |
| CI e2e | Garantir `rfbrowser init` no job que roda Camada B (R-T23-01 residual) |

## 11. Estado

`APPROVED_BY_ARCHITECT` — interfaces.md `0.1.0` completo, sem BLOCKING/MAJOR abertos. Alinhado ao design e BDD aprovados. Prosseguir para unitários QA.
