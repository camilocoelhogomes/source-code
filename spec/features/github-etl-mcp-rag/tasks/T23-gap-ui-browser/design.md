# Design — T23-gap-ui-browser

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T23-gap-ui-browser` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T23-gap-ui-browser` |
| Base | `origin/feature/github-etl-mcp-rag-T22-fix-tooling-e2e-compose-zoekt` |
| Rastreabilidade | inventário T01 (`evidencia_browser=nao`); ParentGapFillBacklog T06; BDD-001,002,007,009,010,016,019,023; ENG-008; REQ-045/047; BR-026; T18 UI; T21 Robot; T22 tooling |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Browser Library / Playwright na suíte Robot; suite nova `ui_browser.robot`; resource `browser.resource`; API RequestsLibrary preservada; manifesto unitário sem Playwright. Modo autônomo. |

## 1. Contexto

A auditoria filha `mvp-e2e-audit-hardening` (T01/T06) classificou a superfície `ui` como `lacuna` para os BDD acima: T21 cobre via **RequestsLibrary** / API-smoke (`GET|POST /api/*`), mas o critério integral exige interação/assert **no browser** (`evidencia_browser=nao`).

Estado atual relevante:

| Artefato | Papel |
|---|---|
| `web/index.html` + `web/app.js` (T18) | UI estática: `#repos-table`, `#btn-index`, `#exact-pattern`, `#semantic-query`, `#search-results`, `#repo-detail`, checkboxes `data-id` |
| `e2e/robot/ui.robot` | BDD-009/010/023 só via HTTP API |
| `e2e/robot/catalog_indexing.robot` | BDD-001/002/007/016/019 via HTTP API |
| `e2e/robot/resources/common.resource` | URLs, waits, redaction de token |
| `src/github_rag/e2e/suite.py` | `GREEN_PATH_SUITES` = health, catalog_indexing, ui, mcp, negative |
| optional-deps `e2e` / `requirements-e2e.txt` | `robotframework`, `robotframework-requests`, `httpx` — **sem** Browser Library |
| T22 | Stack compose/zoekt saudável; pré-condição operacional, fora do escopo de código desta task |

Ownership permanece no pai (`github-etl-mcp-rag`); a filha só abriu o backlog (ENG-010).

## 2. Problema

1. Fechar lacuna `gap-teste` / `assert-fraco`: fluxos UI dos BDD-001,002,007,009,010,016,019,023 devem ser exercitados com **automação browser**.
2. API HTTP sozinha **não** encerra a lacuna (ENG-008 / inventário).
3. Manter suíte T21 (RequestsLibrary) intacta como evidência complementar — não substituir nem remover.
4. Integrar Browser Library (Playwright) no ambiente e2e com bootstrap documentado (`rfbrowser init`).
5. Gate unitário/BDD pytest = contratos de manifesto (deps, suite list, resource, tags) — **sem** subir Playwright no pytest unitário.
6. Sem secrets versionados; sem tooling T22; sem BDD-015; sem implementação na feature filha.

## 3. Solução proposta

### 3.1 Dependência Browser Library

Adicionar ao optional-deps `[e2e]` em `pyproject.toml` e espelhar em `requirements-e2e.txt`:

```text
robotframework-browser>=18
```

(versão mínima flexível `>=18` alinhada a RF 7; pin exato na implementação se o lock do ambiente exigir.)

Bootstrap de browser binaries (operador/CI, **fora** do pytest unitário):

```bash
python -m pip install -e ".[e2e]"
rfbrowser init
```

Documentar em `e2e/README.md` (passo obrigatório após instalar deps e2e; falha sem init = Browser Library sem Chromium).

Não versionar caches Playwright; não embutir tokens.

### 3.2 Resource `e2e/robot/resources/browser.resource`

Novo resource com keywords Browser Library:

| Keyword (canônica) | Uso |
|---|---|
| `Open Ui Browser` | `New Browser` (chromium, headless default) + `New Page` `${UI_BASE}/` |
| `Close Ui Browser` | `Close Browser` (Suite Teardown) |
| `Wait Repos Table Loaded` | `Wait For Elements State` em `#repos-table tbody tr` (ou empty-state documentado) |
| `Click` / `Fill Text` / `Get Text` / `Wait For Elements State` | Wrappers finos só se reduzir ruído; caso contrário usar keywords da lib diretamente nos cases |

Importa `common.resource` para `${UI_BASE}`, `${REFERENCE_REPO}`, timeouts e `Response Must Not Contain Token` (reuso para texto de página).

Suite Setup browser: após health implícito da stack T21 (já up), abrir página; **não** duplicar `Create UI Session` obrigatoriamente — browser é independente da sessão RequestsLibrary.

### 3.3 Suite nova: `e2e/robot/ui_browser.robot` (D-T23-003)

**Escolha:** criar `ui_browser.robot` (não expandir cases browser dentro de `ui.robot`).

**Justificativa:**

1. Lifecycle distinto: Browser Library exige New Browser/Page/Close; misturar com Suite Setup só RequestsLibrary acopla falhas de deps Playwright aos smokes API.
2. Evidência inventário: superfície `evidencia_browser` fica em suite/tags dedicadas (`browser`, `bdd00x`).
3. `ui.robot` permanece API-smoke (aceite complementar); zero remoção de cases existentes.
4. Atualizar `GREEN_PATH_SUITES` em `suite.py` e espelho em `tests/unit/e2e/helpers.py` (`GREEN_PATH_SUITE_MARKERS`) + README lista manual de `robot …`.

Ordem sugerida no green path (após `ui` API ou após `catalog_indexing`):

```python
GREEN_PATH_SUITES = (
    "health",
    "catalog_indexing",
    "ui",
    "ui_browser",  # novo
    "mcp",
    "negative",
)
```

Tags: `Force Tags    ui    browser    mvp` + tags por caso `bdd001`, `bdd002`, …

### 3.4 Seletores estáveis

Prioridade: IDs/atributos **já existentes** em `web/`:

| Seletor | Uso BDD |
|---|---|
| `#repos-table` / `#repos-table tbody` | listagem, origem, estados |
| `#repos-table input[type=checkbox][data-id=…]` | seleção BDD-002 |
| `#btn-index` | Indexar selecionados |
| `#btn-refresh` | refresh pós-index |
| `[data-detail="…"]` / botão linkish | abrir detalhe BDD-007 |
| `#repo-detail` | progresso / flags zoekt·tree_sitter·metadata |
| `#exact-pattern`, `#exact-form` | BDD-009 |
| `#semantic-query`, `#semantic-form` | BDD-010 |
| `#search-results` | hits BDD-009/010 |
| `#cron-section` / ausência de forms connections | BDD-023 |

`data-testid` **mínimos** só se seletor atual for frágil (ex.: célula origem sem atributo). Permitido alterar `web/index.html` / `web/app.js` **apenas** para estabilidade e2e (ex.: `data-testid="repo-origin"` na célula origem, `data-testid="repo-state"`). Proibido redesign ou features UI novas.

### 3.5 Mapeamento BDD → asserts browser

| BDD | Assert browser (obrigatório) | Notas |
|---|---|---|
| **001** | Tabela `#repos-table` lista `${REFERENCE_REPO}`; wildcards — ver §3.5.1 | Complementa API em `catalog_indexing.robot` |
| **002** | Marcar checkbox do repo → Click `#btn-index` → UI mostra estados `na fila` / `indexando` / `atualizado` (poll `#btn-refresh` ou reload) | Paralelismo workers **não** exigido no browser desta task (lacuna workers permanece T26 se aplicável); foco = seleção UI + transição de estados visíveis |
| **007** | Abrir detalhe; `#repo-detail` contém percentual e/ou etapa; após indexação, flags `zoekt=` / `tree_sitter=` / `metadata=` (texto já emitido por `app.js`) | Pode rodar após/durante index do 002; poll com timeout indexação T21 |
| **009** | Fill `#exact-pattern` → submit `#exact-form` → `#search-results` não vazio / contém hit esperado | Manter case API em `ui.robot` |
| **010** | Fill `#semantic-query` → submit `#semantic-form` → `#search-results` com hits | Idem |
| **016** | Alguma linha da tabela mostra origem `local` | Visível na coluna Origem |
| **019** | DOM/página: ausência de `<input type="password">` / campos token; `Get Text` do `body` **não** contém valor de `E2E_GITHUB_TOKEN`/`GITHUB_TOKEN` | Reusa keyword de redaction |
| **023** | UI **sem** forms/botões add/edit/delete connections; presença de estados/seleção (`#repos-table`+checkbox+`#btn-index`) e pesquisa (`#exact-form`/`#semantic-form`) | API 404 em `ui.robot` permanece |

#### 3.5.1 BDD-001 — wildcards (decisão)

**Decisão (D-T23-005):** atualizar `e2e/fixtures/config.e2e.json` para usar padrão com **wildcard de inclusão** que continue a incluir o repo de referência, por exemplo:

```json
"repos": [
  "camilocoelhogomes/source-*"
]
```

(em vez do match exato atual `camilocoelhogomes/source-code`).

No browser:

1. Assert: `${REFERENCE_REPO}` aparece em `#repos-table`.
2. Assert: para cada linha com origem `github`, o identificador **casa** com o(s) padrão(ões) de inclusão do fixture (keyword Robot ou helper Python de glob/`fnmatch` — se helper Python novo, unitário dedicado).
3. Não é necessário enumerar todos os repos da org; basta provar que a listagem UI reflete o filtro de inclusão (repo referência presente + nenhum github listado fora do padrão).

Se na implementação o wildcard ampliado puxar repos extras acessíveis pelo token, o assert (2) ainda vale; se o token só enxergar o repo referência, (1)+(2) degeneram corretamente.

### 3.6 Preservar RequestsLibrary

| Suite | Ação |
|---|---|
| `ui.robot` | **Manter** BDD-009/010/023 API |
| `catalog_indexing.robot` | **Manter** cases API existentes (001/002/007/016/…) |
| `ui_browser.robot` | **Adicionar** evidência browser — não substitui |

### 3.7 Testes unitários / BDD pytest (padrão T22)

Contratos de **arquivo/manifesto** (sem Playwright, sem `rfbrowser`, sem browser real):

| Asserto | Alvo |
|---|---|
| Dep `robotframework-browser` | `pyproject.toml` `[e2e]` + `requirements-e2e.txt` |
| Suite no green path | `GREEN_PATH_SUITES` / markers incluem `ui_browser` |
| Resource existe | `e2e/robot/resources/browser.resource` |
| Suite existe | `e2e/robot/ui_browser.robot` |
| Tags / documentação | suite referencia Library Browser; tags `bdd001`…; README menciona `rfbrowser init` |
| Sem secrets | fixtures/docs sem PAT real |
| Helper Python novo (se houver, ex. match wildcard) | unitários de comportamento + extremos |

Cobertura projeto ≥ 95% permanece gate global.

### 3.8 Documentação operador

Atualizar `e2e/README.md`:

- deps incluem Browser Library;
- passo `rfbrowser init`;
- lista de suites inclui `ui_browser.robot`;
- nota: headless default; variável opcional para headed debug (se implementada).

## 4. Componentes

| ID | Componente | Responsabilidade | Motivo da separação |
|---|---|---|---|
| C-T23-01 | `robotframework-browser` (+ Playwright via `rfbrowser init`) | Motor de automação browser no Robot | Isola runtime browser das deps de produto |
| C-T23-02 | `e2e/robot/resources/browser.resource` | Keywords Open/Close/Wait + reuso URLs | Separar lifecycle browser de HTTP (`common.resource`) |
| C-T23-03 | `e2e/robot/ui_browser.robot` | Cases BDD UI no browser | Evidência `evidencia_browser` sem acoplar a `ui.robot` API |
| C-T23-04 | `GREEN_PATH_SUITES` / markers / README | Inclusão da suite no green path T21 | Prova canônica `python -m github_rag.e2e` exercita browser |
| C-T23-05 | `web/*` (opcional mínimo) | `data-testid` só se necessário | Estabilidade e2e sem mudar produto |
| C-T23-06 | `config.e2e.json` (wildcard) | Inclusão com wildcard para BDD-001 integral | Alinha fixture ao critério de wildcards |
| C-T23-07 | Testes manifesto `tests/` | Gate CI sem Playwright | Padrão T22 / REQ-044 |

**Fora:** tooling compose/zoekt (T22); BDD-015; domínio ETL além de fixture/UI mínima; implementação na filha.

## 5. Fluxo

```text
Operador / CI (stack T21 já saudável — T22)
  │
  ├─ pip install -e ".[e2e]"
  ├─ rfbrowser init                          # Chromium Playwright
  │
  └─ python -m github_rag.e2e
       ├─ … health, catalog_indexing, ui (API) …
       ├─ ui_browser.robot
       │     Suite Setup: Open Ui Browser → ${UI_BASE}/
       │     cases: 001 listagem+wildcard → 016 local → 019 no-token
       │            → 023 no-CRUD + superfície gestão
       │            → 002 checkbox+index+estados
       │            → 007 detalhe progresso/flags
       │            → 009/010 forms + #search-results
       │     Suite Teardown: Close Ui Browser
       └─ mcp, negative …
```

Dependência de dados: indexação/busca (002/007/009/010) podem reutilizar repo já indexado por `catalog_indexing.robot` na mesma run (ordem green path). Se flaky, case browser pode indexar via UI (002) antes de buscas.

## 6. Dados

| Artefato | Persistência | Notas |
|---|---|---|
| `config.e2e.json` | versionado | Wildcard inclusão; `token.env` sem valor |
| Token | env / `.env` local | Nunca no git; assert ausência na UI |
| Artefatos Robot | `e2e/results/` | gitignored; sem dump de token |
| Cache Playwright | host local pós-`rfbrowser init` | Não versionar |
| Tabela UI | runtime | Texto `origin` / `state_label` / `progressLabel` conforme `app.js` |

## 7. Erros

| Situação | Comportamento esperado |
|---|---|
| `rfbrowser init` não executado | Suite browser falha explícita (browser/binary missing); README aponta o passo |
| Stack UI down | Timeout Wait page/table; exit Robot ≠ 0 |
| Repo referência ausente (sync/token) | Fail Find-in-table; mesmo pré-req credencial T21 |
| Indexação lenta | Poll até `${INDEXING_TIMEOUT_SECONDS}` (espelho common.resource) |
| Busca sem hits | Fail assert `#search-results` (pré-condição: repo indexado) |
| Seletor quebrado após mudança UI | Fail Robot; manifesto/testid mitiga |

## 8. Segurança

- Nenhum segredo versionado (REQ-048 / BR-028).
- Keywords **não** logam `GITHUB_TOKEN` / `E2E_GITHUB_TOKEN`.
- BDD-019: assert negativo de substring do token no texto da página + ausência de input de credencial.
- Screenshots/traces Playwright (se habilitados) devem ir para `e2e/results/` gitignored; default headless sem anexar secrets.

## 9. Compatibilidade

| Aspecto | Decisão |
|---|---|
| T21 `DefaultRobotMvpSuite` | Estende lista de suites; contratos launcher/credencial inalterados |
| `ui.robot` / `catalog_indexing.robot` | Permanecem; browser é adicional |
| T18 UI | Comportamento preservado; só `data-testid` mínimos opcionais |
| T22 tooling | Pré-req operacional; sem reabrir F-T04-* |
| CI `docs-cicd-e2e-release` | Precisa `rfbrowser init` no job e2e (documentar; implementação no consumer ou README T23) |
| Feature filha | Sem implementação (ENG-010) |
| Cobertura ≥ 95% | Mantida via manifesto + helpers |

## 10. Observabilidade

| Sinal | Onde |
|---|---|
| Tags Robot `browser` + `bdd00x` | Filtragem / inventário futuro |
| Log Robot | Pass/fail por case browser |
| `e2e/results/` | report.html / log.html |
| Manifesto CI | Falha se dep/suite/resource/README regressarem |

## 11. Riscos

| ID | Risco | Severidade | Mitigação |
|---|---|---|---|
| R-T23-01 | CI sem `rfbrowser init` → suite vermelha | Média | README + checklist; documentar no consumer CI |
| R-T23-02 | Flake timing indexação/UI poll | Média | Reusar timeouts T21; Wait Until Keyword Succeeds |
| R-T23-03 | Wildcard amplia catálogo (mais repos) | Baixa | Assert por padrão inclusão; não fixar contagem absoluta |
| R-T23-04 | Playwright pesado no ambiente unitário | Baixa | Pytest só manifesto; sem init no unit |
| R-T23-05 | Paralelismo workers (BDD-002 integral) não coberto no browser | Residual | Fora do fechamento desta lacuna UI; tracking T26 se aplicável |
| R-T23-06 | Headless vs headed divergência visual | Baixa | Default headless; seletores por ID/testid |

## 12. Rollback

1. Remover `ui_browser.robot`, `browser.resource`, entrada em `GREEN_PATH_SUITES`/markers.
2. Remover dep `robotframework-browser` de `pyproject.toml` / `requirements-e2e.txt`.
3. Reverter wildcard em `config.e2e.json` e quaisquer `data-testid` em `web/`.
4. Reverter docs README e testes manifesto.
5. Suítes API T21 continuam a provar o caminho parcial anterior.

## 13. Decisões

| ID | Decisão | Motivo |
|---|---|---|
| D-T23-001 | Dep `robotframework-browser` no optional `e2e` + `requirements-e2e.txt`; bootstrap `rfbrowser init` | Browser Library oficial sobre Playwright; alinhado ao pedido da task |
| D-T23-002 | Resource novo `e2e/robot/resources/browser.resource` | Isola keywords Browser do HTTP `common.resource` |
| D-T23-003 | Suite nova `e2e/robot/ui_browser.robot` + update `GREEN_PATH_SUITES` | Lifecycle browser distinto; preserva `ui.robot` API; evidência inventário clara |
| D-T23-004 | Seletores: IDs/`data-*` existentes; `data-testid` só se mínimo necessário | Estabilidade sem redesign UI |
| D-T23-005 | BDD-001: wildcard no `config.e2e.json` (`source-*` ou equivalente) + assert tabela UI (referência presente e github rows matching inclusão) | Critério integral de wildcards sem depender só de API |
| D-T23-006 | BDD-002: checkbox + `#btn-index` + estados PT na tabela | Fecha seleção/indexação UI |
| D-T23-007 | BDD-007: `#repo-detail` com progresso e flags zoekt/tree_sitter/metadata | Texto já produzido por `app.js` |
| D-T23-008 | BDD-009/010: forms + `#search-results` no browser | Critério apresentação UI |
| D-T23-009 | BDD-016: origem `local` visível na tabela | Critério UI local |
| D-T23-010 | BDD-019: sem input token/password; body sem valor do env token | Critério UI não solicita/persiste token |
| D-T23-011 | BDD-023: sem CRUD connections na UI; gestão/pesquisa presentes | Critério config fora da UI |
| D-T23-012 | Manter todos os cases RequestsLibrary existentes | Browser = evidência adicional |
| D-T23-013 | Documentar `rfbrowser init` em `e2e/README.md` | Operabilidade local/CI |
| D-T23-014 | Pytest unit/BDD = manifesto (deps, suite, resource, tags, README); sem Playwright no unit | Padrão T22; CI leve |
| D-T23-015 | Sem secrets versionados | REQ-048 / BR-028 |

## 14. Rastreabilidade inventário

| bdd_id | Antes (`evidencia_browser`) | Depois (esta task) |
|---|---|---|
| BDD-001 | nao | `ui_browser.robot` listagem + wildcard |
| BDD-002 | nao | checkbox + index + estados UI |
| BDD-007 | nao | detalhe progresso/flags UI |
| BDD-009 | nao | form exata + `#search-results` |
| BDD-010 | nao | form semântica + `#search-results` |
| BDD-016 | nao | origem `local` na tabela |
| BDD-019 | nao | ausência token na UI + redaction texto |
| BDD-023 | nao | sem CRUD connections; gestão/pesquisa UI |

## 15. Fora de escopo

- Tooling compose/zoekt (T22).
- BDD-015.
- Implementação na feature filha `mvp-e2e-audit-hardening`.
- Assert rígido de paralelismo de workers no browser (BDD-002 cláusula workers).
- Redesign da management UI.

## 16. Critérios de aceite (design → implementação)

1. Automação browser cobre BDD-001/002/007/009/010/016/019/023.
2. RequestsLibrary sozinha **não** basta; suite browser no green path.
3. Cases API existentes preservados.
4. `rfbrowser init` documentado; deps e2e atualizadas.
5. Manifesto unitário verde; cobertura ≥ 95%.
6. Nenhum segredo versionado.
7. Ownership no pipeline do pai.

## 17. Próximos artefatos do pipeline

1. BDD (cenários + pytest manifesto) — QA.
2. Interfaces (resource/keywords/contratos manifesto) — Architect.
3. Unitários — QA.
4. Implementação Developer (`ui_browser.robot`, resource, deps, README, suite list, fixture wildcard, testids mínimos).
5. Review Architect + Blue se aplicável.

## 18. Estado

`APPROVED_BY_ARCHITECT` — design `0.1.0` completo, sem BLOCKING/MAJOR abertos. Riscos R-T23-01/02/05 residuais documentados; não bloqueiam BDD/interfaces.
