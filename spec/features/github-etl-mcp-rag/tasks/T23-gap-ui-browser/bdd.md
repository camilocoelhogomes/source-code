# BDD — T23-gap-ui-browser

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T23-gap-ui-browser` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-19 (modo autônomo) |
| Execução (contratos / CI padrão) | `tests/bdd/test_ui_browser_gap.py` (manifesto deps/suite/resource/tags/README/fixture; **sem** Playwright / `rfbrowser` / browser real) |
| Execução (prova real) | Robot `e2e/robot/ui_browser.robot` + `resources/browser.resource` via `python -m github_rag.e2e` (stack T21/T22; Browser Library / Playwright) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | UB-01..UB-18; Browser Library na suíte; manifesto pytest sem Playwright; RequestsLibrary sozinha = não-aceite. Modo autônomo — aguarda review Architect. |
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Review: alinhado design 0.1.0; Camada A manifesto / Camada B Robot; UB-01..18 cobrem D-T23-001..015 e inventário evidencia_browser; sem BLOCKING/MAJOR. Modo autônomo. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **Contrato (pytest BDD)** | Dep `robotframework-browser`; `GREEN_PATH_SUITES` / markers com `ui_browser`; existência de `browser.resource` + `ui_browser.robot`; tags; README `rfbrowser init`; wildcard em `config.e2e.json`; sem secrets; aceite negativo RequestsLibrary-só | CI unitário/BDD — **proibido** subir Chromium / `rfbrowser init` neste gate |
| **Robot browser (stack real)** | Interação/assert no DOM para BDD-001,002,007,009,010,016,019,023 (`evidencia_browser`) | Operador / job e2e após `rfbrowser init` — **não** no gate pytest |

- Suite canônica: `e2e/robot/ui_browser.robot` (D-T23-003).
- Resource canônico: `e2e/robot/resources/browser.resource` (D-T23-002) — keywords `Open Ui Browser`, `Close Ui Browser`, `Wait Repos Table Loaded`; importa `common.resource`.
- Tags: `Force Tags    ui    browser    mvp` + por caso `bdd001`, `bdd002`, `bdd007`, `bdd009`, `bdd010`, `bdd016`, `bdd019`, `bdd023`.
- Suítes API T21 (`ui.robot`, `catalog_indexing.robot`) **permanecem** (D-T23-012); browser é evidência adicional.
- Sem secrets versionados (D-T23-015 / REQ-048 / BR-028).
- Paralelismo de workers (cláusula BDD-002) **fora** desta task (R-T23-05 / T26).

---

## Camada A — Contratos manifesto (executável em pytest)

### UB-01 — Dependência `robotframework-browser` no optional e2e (D-T23-001)

**Tipo:** contrato (manifesto)  
**Dado** `pyproject.toml` `[project.optional-dependencies].e2e` e `requirements-e2e.txt`  
**Quando** inspecionar as dependências e2e  
**Então** ambos declaram `robotframework-browser` (mínimo `>=18` ou pin compatível)  
**E** `robotframework` / `robotframework-requests` / `httpx` permanecem  
**E** nenhum segredo é introduzido nesses arquivos

**Camada pytest:** leitura de texto/TOML — sem `pip install` de Playwright no assert.

---

### UB-02 — `GREEN_PATH_SUITES` inclui `ui_browser` (D-T23-003 / C-T23-04)

**Tipo:** contrato (manifesto)  
**Dado** `src/github_rag/e2e/suite.py` e espelhos `tests/unit/e2e/helpers.py` / markers BDD T21  
**Quando** inspecionar a lista canônica do green path  
**Então** `GREEN_PATH_SUITES` (e `GREEN_PATH_SUITE_MARKERS`) incluem `"ui_browser"`  
**E** a ordem preserva as suites T21 existentes e insere `ui_browser` após `ui` (ou após `catalog_indexing`, conforme design §3.3)  
**E** `health`, `catalog_indexing`, `ui`, `mcp`, `negative` continuam presentes

---

### UB-03 — Artefatos Robot browser existem (C-T23-02 / C-T23-03)

**Tipo:** contrato (filesystem)  
**Dado** a árvore `e2e/robot/`  
**Quando** verificar paths canônicos  
**Então** existe `e2e/robot/resources/browser.resource`  
**E** existe `e2e/robot/ui_browser.robot`  
**E** `browser.resource` declara keywords `Open Ui Browser` e `Close Ui Browser` (e espera-se `Wait Repos Table Loaded`)  
**E** `ui_browser.robot` referencia `Resource … browser.resource` e `Library    Browser`

---

### UB-04 — Tags Robot `browser` + `bdd00x` (aceite inventário)

**Tipo:** contrato (texto Robot)  
**Dado** `e2e/robot/ui_browser.robot`  
**Quando** inspecionar Settings e cases  
**Então** há `Force Tags` contendo `ui`, `browser` e `mvp`  
**E** existem cases (ou tags) cobrindo `bdd001`, `bdd002`, `bdd007`, `bdd009`, `bdd010`, `bdd016`, `bdd019`, `bdd023`  
**E** a Documentation / Settings deixam explícito uso de Browser Library (não só RequestsLibrary)

---

### UB-05 — README documenta `rfbrowser init` e suite `ui_browser` (D-T23-013)

**Tipo:** contrato (docs)  
**Dado** `e2e/README.md`  
**Quando** o operador consultar bootstrap e2e  
**Então** o README menciona instalação das deps e2e **e** o passo `rfbrowser init`  
**E** lista/invocação de suites inclui `ui_browser.robot`  
**E** nota headless default (e variável headed opcional, se implementada)  
**E** não embute PAT/`ghp_`

---

### UB-06 — Fixture e2e com wildcard de inclusão (D-T23-005 / BDD-001)

**Tipo:** contrato (manifesto)  
**Dado** `e2e/fixtures/config.e2e.json`  
**Quando** inspecionar a conexão GitHub de referência  
**Então** o padrão de inclusão de repos usa **wildcard** (ex.: `camilocoelhogomes/source-*`) que continua a incluir `${REFERENCE_REPO}` (`camilocoelhogomes/source-code`)  
**E** `token` permanece `{ "env": "GITHUB_TOKEN" }` sem valor literal  
**E** a conexão local `file://` permanece para BDD-016

---

### UB-07 — Sem secrets versionados (aceite T23 / D-T23-015)

**Tipo:** contrato (manifesto)  
**Dado** artefatos tocados por T23 (`e2e/robot/**`, `e2e/fixtures/**`, `e2e/README.md`, deps e2e, `web/*` se alterado)  
**Quando** inspecionar conteúdo versionado  
**Então** não há PAT/`ghp_` embutido  
**E** credenciais só como nomes de variáveis (`GITHUB_TOKEN`, `E2E_GITHUB_TOKEN`)  
**E** caches Playwright / `e2e/results/` não são commitados como evidência com secret

---

### UB-08 — RequestsLibrary sozinha NÃO basta (aceite negativo / ENG-008)

**Tipo:** contrato (aceite de evidência)  
**Dado** o inventário T01 com `evidencia_browser=nao` para BDD-001/002/007/009/010/016/019/023  
**E** as suites T21 `ui.robot` / `catalog_indexing.robot` (somente RequestsLibrary / `GET|POST /api/*`)  
**Quando** avaliar se a lacuna UI está fechada  
**Então** a presença exclusiva de cases HTTP **não** satisfaz o aceite desta task  
**E** o green path **deve** incluir suite browser (`ui_browser` em `GREEN_PATH_SUITES`)  
**E** o gate pytest desta task falha se `ui_browser` estiver ausente da lista ou se `ui_browser.robot` / `browser.resource` não existirem  
**E** asserts de UB-01..UB-04 são pré-condição documental de que a evidência browser está no caminho canônico

**Nota:** este cenário formaliza o critério de aceite “API HTTP sozinha não encerra a lacuna”; a prova DOM está na Camada B.

---

### UB-09 — Cases API T21 preservados (D-T23-012)

**Tipo:** contrato (filesystem / regressão)  
**Dado** `e2e/robot/ui.robot` e `e2e/robot/catalog_indexing.robot`  
**Quando** inspecionar após a entrega T23  
**Então** ambos os arquivos permanecem  
**E** cases BDD-009/010/023 (API) e BDD-001/002/007/016 (API) não foram removidos  
**E** `ui_browser.robot` é **adicional**, não substituto

---

## Camada B — Suíte Robot browser (prova real; documentada)

> Prova MVP de `evidencia_browser` em stack real. **Não** faz parte do gate pytest.  
> Pré-reqs: stack T21 saudável (T22), `pip install -e ".[e2e]"`, `rfbrowser init`.  
> Suite Setup: `Open Ui Browser` → `${UI_BASE}/`. Suite Teardown: `Close Ui Browser`.

### UB-10 — BDD-001 listagem UI + wildcards no browser

**Arquivo:** `e2e/robot/ui_browser.robot`  
**Tags:** `bdd001`, `browser`, `ui`, `mvp`  
**Resource:** `browser.resource`  
**Dado** stack e2e up com `CONFIG_PATH` = fixture com wildcard de inclusão (UB-06)  
**E** browser aberto em `${UI_BASE}/`  
**Quando** `Wait Repos Table Loaded` e a tabela `#repos-table` é inspecionada  
**Então** o texto/células da tabela contêm `${REFERENCE_REPO}` (`camilocoelhogomes/source-code`)  
**E** para cada linha com origem `github`, o identificador casa com o(s) padrão(ões) de inclusão do fixture (glob/`fnmatch`)  
**E** a evidência é DOM/Browser Library — não apenas `GET /api/repos` via RequestsLibrary

**Corner:** se o token só enxergar o repo referência, (referência presente + match do padrão) ainda passa.

---

### UB-11 — BDD-016 origem `local` visível na tabela

**Arquivo:** `e2e/robot/ui_browser.robot`  
**Tags:** `bdd016`, `browser`, `ui`, `mvp`  
**Dado** volume local e2e montado e conexão `file://` na fixture  
**E** browser na página de gestão  
**Quando** inspecionar `#repos-table` (coluna Origem / texto da linha)  
**Então** ao menos uma linha exibe origem `local`  
**E** o assert usa texto/atributo no DOM (Browser), não só JSON da API

---

### UB-12 — BDD-019 página sem input de token e body sem valor do env

**Arquivo:** `e2e/robot/ui_browser.robot`  
**Tags:** `bdd019`, `browser`, `ui`, `mvp`  
**Dado** container com token em variável de ambiente (`GITHUB_TOKEN` / `E2E_GITHUB_TOKEN`)  
**E** browser na UI  
**Quando** inspecionar o DOM da página  
**Então** **não** existe `<input type="password">` nem campo de formulário para colar/persistir token GitHub  
**E** `Get Text` do `body` **não** contém o valor atual do token do ambiente  
**E** keywords **não** logam o token (reuso `Response Must Not Contain Token` / redaction de `common.resource` sobre texto de página)

**Corner:** ausência de token input mesmo com cron/search forms presentes.

---

### UB-13 — BDD-023 sem CRUD de connections; gestão e pesquisa presentes

**Arquivo:** `e2e/robot/ui_browser.robot`  
**Tags:** `bdd023`, `browser`, `ui`, `mvp`  
**Dado** browser na UI de gestão  
**Quando** inspecionar a página  
**Então** **não** há forms/botões de add/edit/delete connections (ausência de superfície CRUD de conexões)  
**E** estão presentes `#repos-table`, checkbox(es) `input[type=checkbox][data-id]`, `#btn-index`  
**E** estão presentes `#exact-form` / `#exact-pattern` e `#semantic-form` / `#semantic-query`  
**E** a evidência de “conseguir visualizar/selecionar/indexar/pesquisar” é no browser; o 404 API de `ui.robot` permanece complementar

**Corner:** CRUD connections ausente no DOM (não basta só HTTP 404).

---

### UB-14 — BDD-002 checkbox + Indexar + estados na UI

**Arquivo:** `e2e/robot/ui_browser.robot`  
**Tags:** `bdd002`, `browser`, `ui`, `mvp`  
**Dado** `${REFERENCE_REPO}` listado na `#repos-table` (estado inicial tipicamente não indexado / elegível)  
**Quando** marcar o checkbox `#repos-table input[type=checkbox][data-id=…]` do repo de referência  
**E** clicar `#btn-index`  
**E** poll via `#btn-refresh` (ou reload) até timeout `${INDEXING_TIMEOUT_SECONDS}`  
**Então** a UI mostra progressão de estados em português na coluna Estado: ao menos transição observável por `na fila` e/ou `indexando` até `atualizado`  
**E** a seleção e o disparo ocorreram por interação browser (não `POST /api/repos/index` via RequestsLibrary neste case)

**Corner:** checkbox + botão Indexar no DOM; paralelismo de workers **não** assertado aqui (R-T23-05).

---

### UB-15 — BDD-007 detalhe com progresso e flags zoekt/tree_sitter/metadata

**Arquivo:** `e2e/robot/ui_browser.robot`  
**Tags:** `bdd007`, `browser`, `ui`, `mvp`  
**Dado** repo de referência indexado ou em indexação (pode reutilizar resultado de UB-14 / `catalog_indexing` na mesma run)  
**Quando** clicar o controle de detalhe (`[data-detail="…"]` / botão linkish do repo)  
**Então** `#repo-detail` fica visível/não vazio  
**E** o texto contém indicação de progresso (percentual e/ou etapa / `files_processed` conforme `progressLabel` de `app.js`)  
**E** após indexação com arquivos, o detalhe contém flags `zoekt=` / `tree_sitter=` / `metadata=` (texto emitido por `app.js`)

**Corner:** progresso/detalhe no DOM `#repo-detail`, não só payload JSON.

---

### UB-16 — BDD-009 busca exata: form + `#search-results` no DOM

**Arquivo:** `e2e/robot/ui_browser.robot`  
**Tags:** `bdd009`, `browser`, `ui`, `mvp`  
**Dado** repositórios atualizados / índice disponível (pré-condição green path)  
**E** browser na seção de busca  
**Quando** preencher `#exact-pattern` com padrão conhecido (ex.: `github_rag` ou `def`)  
**E** submeter `#exact-form`  
**Então** `#search-results` não fica vazio  
**E** o conteúdo do elemento reflete hits da busca (texto/JSON renderizado no DOM)  
**E** o assert **não** se limita a `POST /api/search/exact` via RequestsLibrary

**Corner:** resultados de busca no DOM (`#search-results`).

---

### UB-17 — BDD-010 busca semântica: form + `#search-results` no DOM

**Arquivo:** `e2e/robot/ui_browser.robot`  
**Tags:** `bdd010`, `browser`, `ui`, `mvp`  
**Dado** chunks/metadados indexados no Qdrant (stack e2e)  
**E** browser na seção de busca  
**Quando** preencher `#semantic-query` com consulta conhecida  
**E** submeter `#semantic-form`  
**Então** `#search-results` apresenta hits semanticamente relacionados (não vazio / estrutura de hits)  
**E** a evidência é interação + DOM via Browser Library

**Corner:** resultados no DOM; checkbox `#semantic-reformulate` opcional (não obrigatório para o aceite mínimo).

---

### UB-18 — Suite Setup/Teardown browser e seletores estáveis (D-T23-002 / D-T23-004)

**Arquivo:** `e2e/robot/ui_browser.robot` + `browser.resource`  
**Tags:** `browser`, `ui`, `mvp` (meta / documentação executável via existência de keywords)  
**Dado** a suite `ui_browser.robot`  
**Quando** a suite inicia e termina  
**Então** Suite Setup chama `Open Ui Browser` (Chromium headless default → `${UI_BASE}/`)  
**E** Suite Teardown chama `Close Ui Browser`  
**E** cases usam seletores estáveis já existentes (`#repos-table`, `#btn-index`, `#btn-refresh`, `#exact-pattern`, `#semantic-query`, `#search-results`, `#repo-detail`, `data-id`, `data-detail`)  
**E** `data-testid` só aparece se mínimo necessário para estabilidade (sem redesign UI)

**Camada pytest:** pode assertar presença das keywords/seletores referidos no `.robot`/`.resource`; runtime Playwright só na prova real.

---

## Rastreabilidade

| Cenário | Critério / decisão | Camada | Evidência alvo |
|---|---|---|---|
| UB-01 | D-T23-001; aceite deps | pytest | `pyproject.toml` / `requirements-e2e.txt` |
| UB-02 | D-T23-003; C-T23-04 | pytest | `GREEN_PATH_SUITES` + markers |
| UB-03 | D-T23-002/003 | pytest | `browser.resource`, `ui_browser.robot` |
| UB-04 | tags inventário | pytest | tags `browser` + `bdd00x` |
| UB-05 | D-T23-013 | pytest | `e2e/README.md` |
| UB-06 | D-T23-005; BDD-001 wildcard | pytest | `config.e2e.json` |
| UB-07 | D-T23-015; sem secrets | pytest | artefatos versionados |
| UB-08 | Aceite negativo ENG-008 | pytest | green path browser obrigatório |
| UB-09 | D-T23-012 | pytest | API suites preservadas |
| UB-10 | BDD-001 | Robot browser | `#repos-table` + wildcard |
| UB-11 | BDD-016 | Robot browser | origem `local` |
| UB-12 | BDD-019 | Robot browser | sem token input / redaction |
| UB-13 | BDD-023 | Robot browser | sem CRUD; gestão/pesquisa |
| UB-14 | BDD-002 | Robot browser | checkbox + index + estados |
| UB-15 | BDD-007 | Robot browser | `#repo-detail` progresso/flags |
| UB-16 | BDD-009 | Robot browser | form exata + `#search-results` |
| UB-17 | BDD-010 | Robot browser | form semântica + `#search-results` |
| UB-18 | D-T23-002/004 | Robot + pytest leve | lifecycle + seletores |

### Mapeamento inventário (`evidencia_browser`)

| bdd_id | Antes | Cenário browser | Tag |
|---|---|---|---|
| BDD-001 | nao | UB-10 (+ UB-06) | `bdd001` |
| BDD-002 | nao | UB-14 | `bdd002` |
| BDD-007 | nao | UB-15 | `bdd007` |
| BDD-009 | nao | UB-16 | `bdd009` |
| BDD-010 | nao | UB-17 | `bdd010` |
| BDD-016 | nao | UB-11 | `bdd016` |
| BDD-019 | nao | UB-12 | `bdd019` |
| BDD-023 | nao | UB-13 | `bdd023` |

---

## Execução

```bash
# Gate CI / manifesto (sem Playwright)
python -m pytest tests/bdd/test_ui_browser_gap.py -q

# Prova real (após rfbrowser init + stack up)
python -m github_rag.e2e
# ou:
robot --exclude bdd015 e2e/robot/ui_browser.robot
```

Estado esperado **antes** da implementação Developer: **FAIL** no manifesto (dep/suite/resource/README/wildcard ausentes; `GREEN_PATH_SUITES` sem `ui_browser`).  
Estado esperado **depois** da implementação: **PASS** na Camada A; Camada B verde com Browser Library na stack e2e.

## Fora de escopo (não cobrir nestes cenários)

- Tooling compose/zoekt (T22).
- BDD-015.
- Assert de paralelismo de workers no browser (BDD-002 cláusula workers → T26).
- Redesign da management UI.
- Implementação na feature filha `mvp-e2e-audit-hardening`.

---

## Estado

`APPROVED_BY_ARCHITECT` — bdd.md `0.1.0` completo, sem BLOCKING/MAJOR abertos. Prosseguir para interfaces.
