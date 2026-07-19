# BDD — T24-gap-catalog-indexing-integral

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T24-gap-catalog-indexing-integral` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Pipeline | autonomous (Architect aprova gates; sem HITL intermediário) |
| Execução (prova real) | Robot Framework em `e2e/robot/catalog_indexing.robot` (+ resource/keywords previstos) via stack e2e Podman |
| Execução (esta etapa) | **Somente especificação** — arquivos `.robot`/keywords **não** implementados nesta entrega QA |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Cenários integrais BDD-003/005/006/017 (CI-T24-003..006); documenta falha esperada vs asserts fracos T21. |
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Review vs design D-T24-003..006; sem BLOCKING/MAJOR; modo autônomo. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **Robot (stack real)** | Texto integral BDD-003, BDD-005, BDD-006, BDD-017 na superfície `catalog_indexing` | Operador / job e2e — **não** gate pytest unitário |
| **Fora desta task** | Browser UI (T23); tooling compose/zoekt (T22); domínio ETL | — |

- Mutações Git do fixture **somente no host** (`e2e/fixtures/repos/sample-local`); volume no container é `:ro` (D-T24-009).
- Observar commits via MCP `list_repos` → `last_processed_commit` / `current_main_commit` (D-T24-002); **não** exigir campos novos na UI.
- Plano primário: **sem** `POST /api/scheduler/tick` e **sem** endpoints novos (D-T24-007); contingência D-T24-008 só com flakiness evidenciada.
- Soft-pass / skip por `manual_or_partial` **proibido** como único gate destes BDD.
- Tokens: `Response Must Not Contain Token` / MCP sem vazamento permanece.

---

## Lacuna T21 atual (por que estes cenários falham hoje)

Estado parcial em `e2e/robot/catalog_indexing.robot` (DEC-019 / inventário `assert-fraco` / `gap-teste`):

| BDD | Caso Robot T21 atual | Por que **não** cobre o texto integral | Falha esperada dos cenários T24 |
|---|---|---|---|
| BDD-003 | `BDD-003 Scheduler Cron Get And Put` — só GET/PUT `/api/scheduler/cron` e restore | Não cria repo desatualizado; não aguarda janela/tick; não prova indexação sem `POST /api/repos/index` | Asserts de poll `up_to_date` + MCP SHA pós-tick **ausentes** → red até keywords/cron-tick |
| BDD-005 | Tag `bdd005` colada em `BDD-002` (index referência até `up_to_date`) | Sem mutação de tip; sem captura de SHA; sem assert `last_processed_commit` | Caso próprio CI-T24-005 **não existe** / asserts MCP **ausentes** → red |
| BDD-006 | `BDD-006 Exact Search Finds Python Or Markdown` — hits com `pattern=def` no repo GitHub | Sem seed CSV/imagem/gitignore; sem asserts de exclusão nem `files[]` elegíveis | Asserts de ausência + paths em `files[]` **ausentes** → red |
| BDD-017 | `BDD-017 Local Repo Can Be Indexed` — indexa local até `up_to_date` | Sem branch `other` / uncommitted; sem markers de ausência | Asserts `OTHER_BRANCH` / `UNCOMMITTED` zero hits **ausentes** → red |

**Confirmação QA:** com a suíte Robot atual, os cenários CI-T24-003..006 abaixo são especificações que **falham** (ou nem compilam keywords) pela ausência dos asserts integrais — não por flakiness de stack. Implementação Robot/fixture fica para Developer após aprovação Architect deste artefato.

---

## Pré-condições globais (suite)

| ID | Pré-condição |
|---|---|
| PRE-01 | Stack e2e up e saudável (`GET /healthz` → UI+MCP ready) |
| PRE-02 | Credencial e2e presente (`E2E_GITHUB_TOKEN` ou `GITHUB_TOKEN` HITL); sem logar token |
| PRE-03 | Fixture local `sample-local` montada via `HOST_REPOS`; `ensure_local_git_fixture` (ou seed T24) garante `.git` + branch `main` |
| PRE-04 | Sessão UI (`Create UI Session`) e base MCP SSE `http://127.0.0.1:8001` |
| PRE-05 | Repo local identificável em `GET /api/repos` com `origin=local` |

### Teardown global / por cenário

| Escopo | Ação |
|---|---|
| Cron (CI-T24-003) | Restaurar expressão capturada em `GET /api/scheduler/cron` via `PUT` (mesmo payload original) |
| Fixture host | Preparação idempotente; markers estáveis; não deixar cron de teste (`*/1` / minuto absoluto) persistido |
| Segredos | Nenhuma resposta/log com substring de token |

---

## Camada Robot — cenários integrais

> Arquivo alvo: `e2e/robot/catalog_indexing.robot`  
> Resource preferível: `e2e/robot/resources/catalog_indexing.resource`  
> Libraries: `McpKeywords.py` (+ helper leve se parsing/cron UTC exigir)  
> Seed: `ensure_local_git_fixture` e/ou keywords host (D-T24-010)  
> **Esta etapa QA não cria/altera `.robot` nem `src/` de domínio.**

### CI-T24-003 — Agendamento diário: cron na janela + efeito do tick (BDD-003 / D-T24-003)

**Arquivo previsto:** `e2e/robot/catalog_indexing.robot`  
**Tags:** `bdd003` `catalog_indexing` `mvp`  
**Decisão:** D-T24-003  

**Dado** o repo local fixture elegível no catálogo  
**E** o fixture foi indexado pelo menos uma vez até `state=up_to_date` (pode usar enqueue prévio só na preparação)  
**E** no **host** foi criado um novo commit na `main` do fixture (tip ≠ último processado) **sem** chamar `POST /api/repos/index` após a mutação  
**E** `GET /api/scheduler/cron` capturou a expressão atual (`cron_original`)  
**Quando** `PUT /api/scheduler/cron` configura expressão de 5 campos que dispara na janela do teste (UTC explícito: minuto corrente ou próximo minuto, **ou** `*/1 * * * *` se aceito pelo produto)  
**E** o teste **não** invoca `POST /api/repos/index` para esse repo após a mutação  
**Então** dentro do timeout de poll (≥ 120s, intervalo estável) `GET /api/repos/{id}` atinge `state=up_to_date` e `state_label=atualizado`  
**E** MCP `list_repos` para o mesmo repo: `last_processed_commit` == `current_main_commit` == tip SHA do commit criado no host  
**E** no teardown `PUT /api/scheduler/cron` restaura `cron_original`  
**E** respostas não contêm token

**Asserts concretos**

| Superfície | Assert |
|---|---|
| UI `PUT /api/scheduler/cron` | HTTP 200; body `cron` == expressão de teste |
| UI `GET /api/repos/{id}` | `state == up_to_date` após tick (poll) |
| UI | **Proibido** no caminho de prova: `POST /api/repos/index` após tip mudar |
| MCP `list_repos` | `last_processed_commit` == tip pós-mutação; igual a `current_main_commit` |
| Teardown | cron restaurado ao valor pré-teste |

**Keywords previstas (contrato comportamental):** `Capture Scheduler Cron`, `Put Cron Firing Soon Utc`, `Wait Repo Indexed By Scheduler Tick`, `Mcp Repo Commits`, `Restore Scheduler Cron`

---

### CI-T24-005 — Tip da main muda → último processado atualiza (BDD-005 / D-T24-004)

**Arquivo previsto:** `e2e/robot/catalog_indexing.robot`  
**Tags:** `bdd005` `catalog_indexing` `mvp`  
**Decisão:** D-T24-004  
**Nota:** tag `bdd005` **não** deve permanecer apenas colada em BDD-002; este caso é o gate integral.

**Dado** o repo local fixture indexado até `up_to_date`  
**E** MCP `list_repos` capturou `SHA_A = last_processed_commit` (não vazio)  
**Quando** no **host** um novo commit é criado na `main` do fixture (arquivo/mensagem únicos → tip `SHA_B` ≠ `SHA_A`)  
**E** `POST /api/repos/index` com `repository_ids=[local_id]` retorna 202  
**E** o teste faz poll até `state=up_to_date`  
**Então** MCP `list_repos`: `last_processed_commit == SHA_B`  
**E** `last_processed_commit != SHA_A`  
**E** `last_processed_commit == current_main_commit`  
**E** (opcional) `GET /api/repos/{id}/executions` último `commit_target` == `SHA_B`  
**E** (opcional) `POST /api/search/exact` com token do novo arquivo retorna hit com `commit == SHA_B`  
**E** respostas não contêm token

**Asserts concretos**

| Superfície | Assert |
|---|---|
| MCP `list_repos` (antes) | `SHA_A = last_processed_commit` preenchido |
| Host git | tip `main` == `SHA_B` ≠ `SHA_A` |
| UI `POST /api/repos/index` | 202 |
| UI `GET /api/repos/{id}` | `state == up_to_date` |
| MCP `list_repos` (depois) | `last_processed_commit == SHA_B == current_main_commit` |

**Keywords previstas:** `Mcp Capture Last Processed Commit`, `Host Commit On Main`, `Index Repo And Wait Up To Date`, `Mcp Assert Last Processed Equals`

---

### CI-T24-006 — Elegibilidade include code/MD/Java + exclude CSV/imagem/gitignore (BDD-006 / D-T24-005)

**Arquivo previsto:** `e2e/robot/catalog_indexing.robot`  
**Tags:** `bdd006` `catalog_indexing` `mvp`  
**Decisão:** D-T24-005  

**Dado** o fixture `sample-local` preparado de forma idempotente com árvore mínima commitada na `main`:

| Path | Papel | Marker único (exemplo) |
|---|---|---|
| `src/Hello.java` e/ou `src/app.py` | include código | `T24_INCLUDE_JAVA_…` / `T24_INCLUDE_PY_…` |
| `docs/notes.md` | include Markdown | `T24_INCLUDE_MD_…` |
| `data/report.csv` | exclude denylist CSV | `T24_EXCLUDE_CSV_…` |
| `img/photo.png` | exclude imagem | (binário mínimo; marker só no CSV ou sidecar não indexável) |
| `.gitignore` com `ignored_dir/` | exclude pathspec | — |
| `ignored_dir/secret_marker.txt` | exclude gitignore | `T24_EXCLUDE_GITIGNORE_…` |

**Quando** `POST /api/repos/index` → poll `up_to_date`  
**Então** `POST /api/search/exact` com cada marker de **include** → `hits` não vazio; paths coerentes (`src/…`, `docs/notes.md`)  
**E** `POST /api/search/exact` com cada marker de **exclude** (`T24_EXCLUDE_CSV_…`, `T24_EXCLUDE_GITIGNORE_…`) → `hits` vazio (zero hits)  
**E** `GET /api/repos/{id}` → `files[].path` contém os includes e **não** contém `data/report.csv`, `img/photo.png`, `ignored_dir/secret_marker.txt`  
**E** (complemento permitido) smoke MD/Python do T21 permanece, mas **não** substitui estes asserts  
**E** respostas não contêm token

**Asserts concretos**

| Superfície | Assert |
|---|---|
| UI search exact | includes → `len(hits) >= 1`; path bate com arquivo seed |
| UI search exact | excludes → `hits == []` (ou equivalente vazio) |
| UI `GET /api/repos/{id}` | `files[].path` ⊇ includes; `files[].path` ∩ excludes = ∅ |

**Keywords previstas:** `Prepare Eligibility Fixture Tree`, `Assert Exact Search Hits`, `Assert Exact Search Empty`, `Assert Repo Files Paths Eligible`

---

### CI-T24-017 — Somente main; other branch + uncommitted ausentes (BDD-017 / D-T24-006)

**Arquivo previsto:** `e2e/robot/catalog_indexing.robot`  
**Tags:** `bdd017` `catalog_indexing` `mvp`  
**Decisão:** D-T24-006  

**Dado** o fixture local preparado de forma idempotente:

| Elemento | Marker |
|---|---|
| Commit na `main` | `MAIN_ONLY_MARKER` (token único estável) |
| Branch `other` (ou `feature/x`) com commit **somente** nela | `OTHER_BRANCH_MARKER` |
| Working tree: arquivo **não** staged / **não** commitado | `UNCOMMITTED_MARKER` |

**Quando** `POST /api/repos/index` para o repo local → poll `up_to_date`  
**Então** `POST /api/search/exact` com `MAIN_ONLY_MARKER` → hits não vazios  
**E** hit de `MAIN_ONLY_MARKER` tem `commit` == tip `main` observado via MCP (`current_main_commit` / `last_processed_commit`)  
**E** busca `OTHER_BRANCH_MARKER` → zero hits  
**E** busca `UNCOMMITTED_MARKER` → zero hits  
**E** (opcional) MCP `list_tree` / `read_file` no tip processado não lista o path uncommitted nem paths exclusivos da outra branch  
**E** respostas não contêm token

**Asserts concretos**

| Superfície | Assert |
|---|---|
| UI search exact | `MAIN_ONLY_MARKER` → hits; `commit` == tip main (MCP) |
| UI search exact | `OTHER_BRANCH_MARKER` → empty |
| UI search exact | `UNCOMMITTED_MARKER` → empty |
| MCP `list_repos` | `last_processed_commit == current_main_commit` (tip main) |

**Keywords previstas:** `Prepare MainOnly Fixture Branches`, `Assert Main Marker Indexed`, `Assert Marker Absent From Exact Search`

---

## Tabela de rastreabilidade

| BDD produto | Decisão design | Cenário QA | Tags Robot | Superfícies de assert | Aceite task |
|---|---|---|---|---|---|
| BDD-003 | D-T24-003 | CI-T24-003 | `bdd003` | cron GET/PUT; poll UI state **sem** POST index; MCP commits | texto integral “quando o horário chegar” |
| BDD-005 | D-T24-004 | CI-T24-005 | `bdd005` | host tip; POST index; MCP `last_processed_commit` | tip muda → último processado |
| BDD-006 | D-T24-005 | CI-T24-006 | `bdd006` | seed include/exclude; search exact; `files[]` | include code/MD/Java; exclude CSV/img/gitignore |
| BDD-017 | D-T24-006 | CI-T24-017 | `bdd017` | seed branches/WT; search presença/ausência; MCP tip | só main; other + uncommitted ausentes |

| REQ / BR (pai) | Cenários |
|---|---|
| REQ-013–017, REQ-015 | CI-T24-003, CI-T24-005, CI-T24-006, CI-T24-017 |
| BR-002–004 | CI-T24-005, CI-T24-006, CI-T24-017 |

| Componente design | Cenários |
|---|---|
| C-T24-01 `catalog_indexing.robot` | todos |
| C-T24-02 `catalog_indexing.resource` | keywords partilhadas |
| C-T24-03 fixture + `ensure_local_git_fixture` | CI-T24-006, CI-T24-017 (+ prep 003/005) |
| C-T24-04 MCP `list_repos` | CI-T24-003, CI-T24-005, CI-T24-017 |
| C-T24-05 UI cron/repos/search | todos |
| C-T24-06 T15 `run_tick_once` via job | CI-T24-003 |

---

## Critérios de aceite da task × cenários

| Aceite | Cenários |
|---|---|
| Robot cobre texto integral BDD-003 (tick, não só CRUD cron) | CI-T24-003 |
| Robot cobre tip → `last_processed_commit` (MCP) | CI-T24-005 |
| Robot cobre include + exclude CSV/imagem/gitignore | CI-T24-006 |
| Robot cobre somente main / sem uncommitted | CI-T24-017 |
| Sem endpoints novos no plano primário | todos (só APIs/MCP existentes) |
| Nenhum segredo versionado / sem vazamento em asserts | teardown + `Response Must Not Contain Token` |
| Substitui fatias T21 fracas como único gate das tags `bdd003`/`bdd005`/`bdd006`/`bdd017` | CI-T24-* |

---

## Comando (prova real — pós-implementação Developer)

```bash
# Suíte catalog_indexing com tags integrais (stack e2e já up)
robot --include bdd003 --include bdd005 --include bdd006 --include bdd017 \
  e2e/robot/catalog_indexing.robot

# Ou via orquestrador T21 (green path completo)
python -c "from github_rag.e2e import DefaultRobotMvpSuite, PodmanE2eStackLauncher; raise SystemExit(DefaultRobotMvpSuite(launcher=PodmanE2eStackLauncher()).run())"
```

## Notas TDD / red esperado

- **Esta entrega:** apenas `bdd.md` (+ registro em `reviews.md`). Nenhum `.robot` novo/alterado; nenhum `src/github_rag/**` de domínio.
- Antes da implementação Developer: keywords/asserts de CI-T24-003..017 **não** existem na suíte atual → execução dos cenários integrais falha pela razão documentada na tabela “Lacuna T21”.
- Após implementação: green nos quatro cenários + regressão das demais tags `catalog_indexing`; cobertura projeto ≥ 95% se QA adicionar pytest de suporte a helpers e2e.
- Contingência `POST /api/scheduler/tick` (D-T24-008): **fora** dos cenários primários; só documentar se flakiness de cron for evidenciada no pipeline.
