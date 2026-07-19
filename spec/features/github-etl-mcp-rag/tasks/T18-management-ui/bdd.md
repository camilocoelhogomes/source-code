# BDD — T18-management-ui

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T18-management-ui` |
| Autor | Tech Lead Architect / QA |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` |
| Execução | `tests/bdd/test_management_ui.py` (TestClient FastAPI + fakes) |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Cenários UI cobrindo BDD-002/003/007/009/010/016/023/024 + REQ-023. |

## Convenções

- App via `DefaultManagementUiApi(...).build()` + `fastapi.testclient.TestClient`.
- Fakes: `InMemoryCatalogRepository`, spy/`FakeQueryService`, fake orchestrator, `DefaultDailyScheduler` + `InMemoryCronPreferenceStore` (ou doubles mínimos).
- Estados de domínio: slugs `RepoState`; asserções UI também checam `state_label` PT.

---

## UI-01 — Listar repositórios com origem e estado (BDD-016 / REQ-020 / REQ-035)

**Dado** catálogo ativo com um repo `origin=github` e um `origin=local`  
**Quando** `GET /api/repos`  
**Então** a resposta 200 lista ambos  
**E** cada item inclui `origin`, `state` (slug REQ-020) e `state_label` PT correspondente  
**E** o local aparece com `origin == "local"`

## UI-02 — Indexar selecionados por checkbox (BDD-002)

**Dado** repos em `not_indexed`  
**Quando** `POST /api/repos/index` com `{ "repository_ids": [<ids>] }`  
**Então** status 202  
**E** o orquestrador recebe `enqueue` com esses ids  
**E** após drain (quando habilitado) os estados evoluem até `up_to_date` (ou passam por `queued`/`indexing` observáveis no fake)

## UI-03 — Acompanhar progresso detalhado (BDD-007 / REQ-021–022)

**Dado** um repo em `indexing` com `Progress` e `FileProgress` (flags zoekt/tree_sitter/metadata)  
**Quando** `GET /api/repos/{id}`  
**Então** 200 com `progress.percent`, `files_processed`, `files_total`, `current_stage`  
**E** `files[]` com flags booleanas por etapa (Zoekt / Tree-sitter / metadata_persisted)

## UI-04 — Falha: mensagem, horário e histórico (REQ-023 / BDD-008 UI)

**Dado** repo em `error` com execução `failed` (`error_message`, `error_at`) e histórico N≥1  
**Quando** `GET /api/repos/{id}/executions`  
**Então** 200 lista execuções  
**E** a falha expõe `error_message` e `error_at`  
**E** há mais de um registro quando seed incluir tentativa anterior

## UI-05 — Configurar cron pela UI (BDD-003 / ENG-010)

**Dado** scheduler com default env `0 2 * * *`  
**Quando** `PUT /api/scheduler/cron` com `{ "cron": "30 4 * * *" }`  
**Então** 200 e `active_cron()` == `30 4 * * *`  
**Quando** `GET /api/scheduler/cron`  
**Então** devolve a expressão ativa  
**Quando** PUT com cron inválido  
**Então** 400 e preferência anterior intacta

## UI-06 — Busca exata (BDD-009)

**Dado** `FakeQueryService` com hits exact  
**Quando** `POST /api/search/exact` com `{ "pattern": "authenticate" }`  
**Então** 200 com hits contendo path/snippet conforme fake  
**E** chama `search_exact` (não semantic)

## UI-07 — Busca semântica (BDD-010)

**Dado** `FakeQueryService` com hits semantic  
**Quando** `POST /api/search/semantic` com `{ "query": "login flow", "reformulate": false }`  
**Então** 200 com hits  
**E** request ao serviço tem `reformulate=False` por default se omitido

## UI-08 — Sem CRUD de conexões/token (BDD-023 / BR-012/017)

**Dado** a app montada  
**Quando** inspecionar rotas OpenAPI / tabela de rotas  
**Então** não existem paths para create/update/delete de connections, repos de config ou token  
**E** POST em paths inventados `/api/connections` → 404  
**E** frontend estático não contém inputs `type=password` nem labels de token GitHub

## UI-09 — Conformidade FastAPI (BDD-024)

**Dado** o pacote `github_rag.ui`  
**Quando** inspecionar imports de transporte HTTP  
**Então** usa `fastapi`  
**E** não implementa servidor HTTP/JSON-RPC caseiro

## UI-10 — Token ausente da superfície (BR-008 / BDD-014 UI)

**Dado** mensagens de erro sem token  
**Quando** qualquer endpoint de erro tipado  
**Então** corpo não contém substrings típicas de PAT (`ghp_`, `github_pat_`)

---

## Mapeamento

| BDD produto | Cenários T18 |
|---|---|
| BDD-002 | UI-02 |
| BDD-003 | UI-05 |
| BDD-007 | UI-03 |
| BDD-009 | UI-06 |
| BDD-010 | UI-07 |
| BDD-016 | UI-01 |
| BDD-023 | UI-08 |
| BDD-024 | UI-09 |
| REQ-023 | UI-04 |
