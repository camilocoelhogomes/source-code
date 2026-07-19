# Design — T18-management-ui

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T18-management-ui` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T18-management-ui` |
| Base | `feature/github-etl-mcp-rag-T15-daily-scheduler` (+ merge `main` para T16/T17) |
| Rastreabilidade | REQ-006,012,017,020–027,035; BR-012,017,023; DEC-015; BDD-002,003,007,009–010,016,023,024; ENG-001, ENG-010 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Design: `ManagementUiApi` via FastAPI + frontend estático; catálogo/orquestrador/scheduler/QueryService; sem CRUD conexões/token; labels PT REQ-020. |

## 1. Contexto

A onda W7 entrega a superfície **UI de gestão e busca** (REQ-006). Dependências:

| Dependência | Porta / artefato | Uso em T18 |
|---|---|---|
| T07/T03 | `CatalogRepository` (`list_active_catalog`, `get_repository`, `list_executions`, `list_file_progress`) | Listagem, progresso, histórico de falhas |
| T14 | `IndexingOrchestrator.enqueue` + `run_until_idle` | Disparo sob demanda (checkbox) |
| T15 | `DailyScheduler.active_cron` / `set_cron` | Preferência cron (ENG-004/010) |
| T16 | `QueryService` (+ opcional `QueryReformulator`) | Busca exact/semantic (BDD-009/010) |
| DEC-015 / ENG-001 | **FastAPI** | Único framework HTTP da UI API |

## 2. Problema

O usuário local precisa, pela UI:

1. ver repos do catálogo com origem (`github`/`local`) e estado REQ-020 (rótulos PT);
2. selecionar por checkbox e disparar indexação (BDD-002);
3. acompanhar percentual/arquivos/etapa e flags Zoekt/Tree-sitter/metadados (BDD-007);
4. em `erro`, ver mensagem, horário e histórico (REQ-023);
5. configurar expressão cron (BDD-003 / ENG-010);
6. buscar exact e semantic (BDD-009/010; reformulate opcional REQ-027);
7. **sem** criar/editar/remover conexões ou token (BDD-023 / BR-012/017).

## 3. Solução proposta

Pacote `github_rag.ui` com porta pública `ManagementUiApi` que:

1. monta um `fastapi.FastAPI` com rotas `/api/*` tipadas;
2. serve frontend estático leve (`web/` embutido ou `StaticFiles`);
3. delega a catálogo / orquestrador / scheduler / `QueryService`;
4. **não** expõe endpoints de conexões, `CONFIG_PATH` ou token.

```text
Browser
  → Static (HTML/JS/CSS)
  → FastAPI /api/*
       ├─ GET  /api/repos              → CatalogRepository.list_active_catalog
       ├─ GET  /api/repos/{id}         → get_repository + progress + file flags
       ├─ GET  /api/repos/{id}/executions → list_executions (REQ-023)
       ├─ POST /api/repos/index        → IndexingOrchestrator.enqueue (+ drain async/thread)
       ├─ GET  /api/scheduler/cron     → DailyScheduler.active_cron
       ├─ PUT  /api/scheduler/cron     → DailyScheduler.set_cron
       ├─ POST /api/search/exact       → QueryService.search_exact
       └─ POST /api/search/semantic    → QueryService.search_semantic (reformulate opcional)
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T18 | Fora |
|---|---|---|
| BDD-002 | Checkbox → enqueue; estados na listagem | Pipeline interno T14 |
| BDD-003 | PUT cron → `set_cron`; GET active | Tick APScheduler (T15) |
| BDD-007 | Progresso % / arquivos / etapa + flags arquivo | Persistência T03/T14 |
| BDD-009 | POST exact → hits | Zoekt real |
| BDD-010 | POST semantic → hits; `reformulate` opcional | Embeddings reais |
| BDD-016 | Origem `local` visível na listagem | Discovery T06 |
| BDD-023 | Ausência de rotas CRUD conexão/repo/token | Config T02 |
| BDD-024 | Só FastAPI oficial; sem HTTP caseiro | Demais SDKs |
| REQ-023 | Executions: message + error_at + histórico | — |

## 4. Componentes

### 4.1 Dependência SDK (`fastapi` + `httpx`/`starlette` via FastAPI)

| Decisão | Valor |
|---|---|
| Pacote | **`fastapi`** (+ `uvicorn` runtime opcional para T19) |
| Pin | `fastapi>=0.115,<1` |
| Testes | `httpx` (TestClient Starlette) em `dev` |
| Proibido | Flask/Django reinventado; servidor HTTP ad-hoc; CRUD de config |

### 4.2 `ManagementUiApi` (porta pública)

```python
class ManagementUiApi(Protocol):
    def build(self) -> FastAPI: ...
```

- **Responsabilidade:** expor a app HTTP+static da UI de gestão.
- **Motivo da separação:** T19 sobe o processo; domínio permanece em catalog/indexing/schedule/query.

### 4.3 `DefaultManagementUiApi`

Construtor keyword-only:

| Dep | Tipo | Obrigatório |
|---|---|---|
| `catalog` | `CatalogRepository` | sim |
| `orchestrator` | `IndexingOrchestrator` | sim |
| `scheduler` | `DailyScheduler` | sim |
| `query` | `QueryService` | sim |
| `drain_on_index` | `bool` | default `True` — após enqueue chama `run_until_idle` em thread (testável) |

### 4.4 Apresentação de estados (REQ-020)

Slug interno permanece `RepoState.value`. A API devolve também `state_label` PT:

| value | state_label |
|---|---|
| `not_indexed` | `não indexado` |
| `queued` | `na fila` |
| `indexing` | `indexando` |
| `up_to_date` | `atualizado` |
| `error` | `erro` |

### 4.5 Frontend

Diretório `web/` (empacotado via `StaticFiles` em `/`):

- Uma página: lista repos (checkbox, origem, estado), progresso, histórico erro, form cron, busca exact/semantic.
- Sem formulários de conexão/token.
- Consome só `/api/*`.

## 5. Fluxo de dados

### 5.1 Indexação sob demanda

1. UI POST `{ "repository_ids": [1,2] }`
2. API valida ids ativos; `orchestrator.enqueue(ids)`
3. Se `drain_on_index`: `run_until_idle()` (thread) para progressão observável em testes/local
4. 202 + snapshot dos repos afetados

### 5.2 Cron

- GET → `{ "cron": "<active>", "source": "preference"|"env" }` — source derivado: preference se store ≠ None via comparação `active_cron` vs settings não disponível na porta; simplificação: devolver só `cron` de `active_cron()` (suficiente BDD-003). Opcional: injetar `CronPreferenceStore.get()` só para `source` — **não** expor store como escrita (escrita só via `set_cron`).
- PUT `{ "cron": "0 3 * * *" }` → `scheduler.set_cron`; 400 se `InvalidCronExpressionError`.

### 5.3 Buscas

- Exact/semantic montam `ExactSearchRequest` / `SemanticSearchRequest` com `DetailFields` all-true na UI (usuário vê repo/path/commit/snippet).
- Semantic aceita `reformulate: bool` (default false); se true e reformulator injetado no QueryService (composition root), T16 aplica.

## 6. Erros

| Situação | HTTP | Corpo |
|---|---|---|
| Repo inexistente | 404 | `{ "detail": "..." }` |
| Cron inválido | 400 | `{ "detail": "..." }` |
| QueryError | 400/404 conforme tipo | `{ "detail": "..." }` sem token |
| Body inválido | 422 | FastAPI validation |

Token nunca em respostas (BR-008 / BDD-014 superfície UI).

## 7. Segurança

- Sem endpoints que aceitem/persistam token.
- Sem mutação de `CONFIG_PATH` / conexões.
- Erros sanitizam segredos se presentes em mensagens (reutilizar padrão simples: não ecoar headers Authorization).

## 8. Compatibilidade

- Windows/macOS/Linux first-class: paths via pathlib no static mount; cron UTC (T15).
- FastAPI ASGI — T19 empacota uvicorn.

## 9. Observabilidade

- Logs estruturados: `ui_index_enqueue`, `ui_cron_set`, `ui_search_*` sem payloads de segredo.

## 10. Riscos e rollback

| Risco | Mitigação |
|---|---|
| Drain síncrono bloqueia request | `drain_on_index` + thread; T19 pode desligar drain e usar workers |
| Stack T15 não na main | PR empilhado em T15; merge order T15→T18 |
| Frontend mínimo | Escopo MVP; sem framework SPA |

Rollback: reverter PR; sem migration própria (cron store é T15).

## 11. Decisões congeladas

| ID | Decisão |
|---|---|
| D-T18-001 | Porta `ManagementUiApi.build() -> FastAPI` |
| D-T18-002 | FastAPI único SDK HTTP (BDD-024) |
| D-T18-003 | Labels PT só em apresentação; slugs ASCII no domínio |
| D-T18-004 | Escrita cron só via `DailyScheduler.set_cron` |
| D-T18-005 | Zero rotas de conexão/token/CONFIG |
| D-T18-006 | DetailFields all-true nas buscas UI |
| D-T18-007 | Frontend estático em `web/` servido pelo FastAPI |

## 12. Fora de escopo

- MCP; CRUD config; compose/imagem (T19); stream de logs genéricos; reformulador concreto (só flag + injeção T16).
