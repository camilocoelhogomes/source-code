# Unit Test Plan — T19-container-delivery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T19-container-delivery` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.2.0` |
| Design / BDD / Interfaces | `0.2.0` / `0.2.0` (`APPROVED_BY_ARCHITECT`) / `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| Cobertura alvo | ≥95% em `github_rag.delivery` e gate global |
| Branch | `feature/github-etl-mcp-rag-T19-container-delivery` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Plano + suíte RED `tests/unit/delivery/`; BDD CD-01..10 já cobre superfície; unit foca corners/contratos. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Review: MAJOR fail-fast wait/secret/skip_infra, patches dual-site, scheduler em falhas, I-T19-019 URL, mcp_stdio, health pré-boot. |
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.2.0` | Delta BDD-025: UT-M03/04 nos 3 composes; UT-M07/08/09 papéis; CD-11; RED até e2e/dev existirem. |
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | `0.2.0` | Review: MAJOR — UT-M07 não asserta mapeamento `E2E_GITHUB_TOKEN`→`GITHUB_TOKEN` (D-T19-020). Ver `reviews.md`. |
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.2.0` | Correção: UT-M07 asserta fórmula canônica do alias. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.2.0` | Re-review: UT-M07 fórmula alias; MAJOR fechado. |

## 1. Estratégia

| Camada | Arquivo | Doubles |
|---|---|---|
| Runtime boot | `tests/unit/delivery/test_runtime_boot.py` | RecordingSync/Reconcile/Scheduler/Surfaces; migrate/wait patched (wiring+runtime) |
| Health | `tests/unit/delivery/test_health.py` | FastAPI mínimo + `get_state` |
| Wiring | `tests/unit/delivery/test_wiring.py` | environ incompleto; sem I/O real (exceto timeout curto em wait) |
| Manifesto | `tests/unit/delivery/test_manifest.py` | leitura de arquivos na raiz |
| Conformidade | `tests/unit/delivery/test_imports.py` | AST + exports + mcp_stdio |
| Helpers | `tests/unit/delivery/helpers.py` | doubles + env mínimo + `patch_infra` |

- Sem `docker build` / compose real / Robot (REQ-044); manifesto = asserts de arquivo nos **três** composes.
- Sem domínio novo: sync/reconcile só via portas injetadas (I-T19-014/018).
- BDD (`tests/bdd/test_container_delivery.py` CD-01..11) permanece suíte de superfície; unitários cobrem extremos e contratos isolados.
- Pré-implementação do delta 0.2.0: `AssertionError` (e2e/dev ausentes) — **RED**.

## 2. Matriz unitária

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-B01 | Boot happy path registra ordem settings→config→migrate→sync→reconcile→scheduler→bind | ordem estrita; sync 1×; reconcile 1× | I-T19-005; D-T19-003; CD-04+ |
| UT-B02 | `CONFIG_PATH` ausente → `SystemExit(1)` | sem sync/reconcile/scheduler/bind | I-T19-006; CD-03 |
| UT-B03 | `CONFIG_PATH` blank/whitespace → `SystemExit(1)` | sem parcial | I-T19-006; CD-03 |
| UT-B04 | `CONFIG_PATH` arquivo inexistente → `SystemExit(1)` | sem parcial | I-T19-006; CD-03 |
| UT-B05 | JSON inválido → `SystemExit(1)` | sem parcial | I-T19-006; CD-03 |
| UT-B06 | Falha `run_alembic_upgrade` (skip_infra=False) → exit 1 | sem sync/reconcile/scheduler/bind | design §7; I-T19-006 |
| UT-B07 | Sync levanta `CatalogSyncError` → exit 1 | reconcile/scheduler/bind não chamados | design §7; CD-03+ |
| UT-B08 | Reconcile chamado exatamente 1× no happy path | idempotência observacional | I-T19-014; CD-04 |
| UT-B09 | `boot()` duas vezes após sucesso não duplica reconcile (ou falha tipada estável) | 2ª chamada não chama `run()` de novo **ou** exit tipado sem segundo reconcile | corner idempotência |
| UT-B10 | Orchestrator lento/`run_until_idle` bloqueante não impede bind | bind ocorre; idle não bloqueia caminho de bind | I-T19-005 §5.3.7; T18 drain |
| UT-B11 | `run_container_boot` sem CONFIG_PATH → `SystemExit(1)` | entrypoint | I-T19-003; CD-03 |
| UT-B12 | Protocol `ContainerRuntime` runtime_checkable com `DefaultContainerRuntime` | `isinstance` | I-T19-002 |
| UT-B13 | Logs/stdout de falha não vazam `ghp_` / token / `DATABASE_URL` completa | redaction | I-T19-019 |
| UT-B14 | Entrada `INDEX_WORKERS` inválida → exit 1 sem bind | settings tipado | T01 + I-T19-006 |
| UT-B15 | Falha `wait_for_postgres` no boot (skip_infra=False) → exit 1 | sem sync/reconcile/scheduler/bind | design §7; I-T19-006 |
| UT-B16 | `skip_infra=True` omite wait PG / alembic | happy path com doubles; wait/alembic `assert_not_called` | I-T19-011 |
| UT-B17 | `GITHUB_TOKEN` ausente com JSON que referencia secret → exit 1 | sem sync/reconcile/scheduler/bind | design §7; ConfigLoadError; I-T19-006 |
| UT-H01 | `healthz_payload(ui_ready=True, mcp_ready=True)` | `{status,ui,mcp}` canônico | I-T19-007 |
| UT-H02 | `healthz_payload` com ready=False | não reporta ui/mcp `ready` | I-T19-007 |
| UT-H03 | Sem app ASGI pré-boot; `GET /healthz` 200 só após boot completo | TestClient pós-boot | CD-01; I-T19-013 |
| UT-H04 | Payload health sem segredos / `ghp_` | blob limpo | I-T19-019 |
| UT-H05 | Chaves do body exatamente `status`,`ui`,`mcp` | sem extras de catálogo | I-T19-007 |
| UT-W01 | `wire_catalog` sem `DATABASE_URL` → erro tipado | não retorna repo | I-T19-009 |
| UT-W02 | `wait_for_postgres` timeout com URL inválida/host down → falha tipada | sem vazar URL completa | wiring §6 |
| UT-W03 | `default_bind_ui` / `default_bind_mcp` existem e aceitam `environ` | callables + signature | I-T19-012/015 |
| UT-W04 | Env incompleto (`ZOEKT_URL`/`QDRANT_URL`/`OPENAI_BASE_URL` ausentes) em wiring de stack | erro tipado / não silencia | I-T19-009 |
| UT-M01 | Dockerfile: `pip install` do `.`; sem `[dev]`; sem `.venv` | manifesto | M-T19-001/005; CD-05/06 |
| UT-M02 | Dockerfile: `git` + CMD `python -m github_rag.delivery` | manifesto | M-T19-001; CD-10 |
| UT-M03 | Nos **3** composes: serviços app/postgres/qdrant/zoekt/slm + ports UI/MCP | manifesto | M-T19-002; CD-08 |
| UT-M04 | Nos **3** composes: volumes `/repos` + `CONFIG_PATH`; healthcheck `/healthz`; sem `.venv` | manifesto | M-T19-003; CD-08/09 |
| UT-M05 | `pyproject.toml` declara DEC-015 + `uvicorn` + grammars | deps | M-T19-006; CD-05 |
| UT-M06 | `.env.example` nomes canônicos (incl. UI/MCP + `E2E_GITHUB_TOKEN`) sem segredos | manifesto | M-T19-003; CD-09/11 |
| UT-M07 | `docker-compose.e2e.yml`: `name: github-rag-e2e`, volumes `e2e_*`, alias `GITHUB_TOKEN: ${E2E_GITHUB_TOKEN:-${GITHUB_TOKEN:-}}`, sem `./src` | D-T19-020; M-T19-007 | CD-11 |
| UT-M08 | `docker-compose.dev.yml`: `name: github-rag-dev`, `./src`, `5432:5432`, sem `.venv` | D-T19-020 | CD-11 |
| UT-M09 | `docker-compose.yml` não monta `./src` | D-T19-020 | CD-11 |
| UT-X01 | `ports.py` / Protocol sem fastapi/uvicorn/SDKs | ENG-013 | I-T19-018 |
| UT-X02 | Exports públicos `ContainerRuntime`, `DefaultContainerRuntime`, `run_container_boot` | CD-10 | I-T19-016 |
| UT-X03 | Pacote `delivery` sem tip×estado / parse JSON próprio reinventado | AST: sem `json.loads` em runtime além de ConfigLoader | I-T19-018 |
| UT-X04 | `__main__` chama `run_container_boot` | entry | I-T19-010 |
| UT-X05 | `mcp_stdio.py` existe com `main` + stdio; sem uvicorn/bind UI | entry alt. | I-T19-010/015 |

## 3. Sobreposição com BDD

| Área | BDD | Unit |
|---|---|---|
| Happy UI/MCP/healthz | CD-01 | UT-H03/H04 (contrato payload isolado + pré-boot) |
| Sync 1× + conexões | CD-02 | UT-B01 (ordem inclui migrate/settings) |
| Fail-fast CONFIG_PATH | CD-03 | UT-B02..B05 + UT-B06/B07/B15/B17 (migrate/wait/sync/secret) |
| Ordem sync→reconcile→scheduler→bind | CD-04 | UT-B01 (estende com migrate); UT-B16 skip_infra |
| Manifesto DEC-015/compose | CD-05..10 | UT-M* (endurece ports/volumes/CMD/env) |

Unitários **não** duplicam asserts BDD sem valor; focam corners (migrate/wait/sync fail, secret ausente, idle não bloqueia bind, health parcial, wiring env incompleto, idempotência, mcp_stdio).

## 4. Demonstração RED (TDD)

```bash
cd /private/tmp/github_rag_T19
PYTHONPATH=src /Users/camilocoelhogomes/projects/github_rag/.venv/bin/python -m pytest tests/unit/delivery/ -q --no-cov
```

Nota: o `.venv` do repo principal pode apontar `editable` para outro worktree — use `PYTHONPATH=src` (ou `pip install -e .` neste worktree).

Falhas esperadas pré-implementação:

| Área | Razão |
|---|---|
| Runtime / health / wiring / exports | `ImportError` — `github_rag.delivery` ainda sem superfície (só stub `__init__`) |
| Manifesto UT-M* | `AssertionError` — `Dockerfile` / `docker-compose.yml` / `.env.example` ausentes |
| Conformidade UT-X* | módulos `ports.py`/`runtime.py`/`__main__.py`/`mcp_stdio.py` ausentes |

Após implementação Developer: verde + cobertura ≥95% em `github_rag.delivery`.

## 5. Fora de escopo unitário

- `docker build` / `compose up` reais
- Implementação de produção (Developer)
- Tip×estado / pipeline T14, tools MCP T17, CRUD UI
- Expandir `AppSettings` com envs de fronteira

## 6. Architect Review

| Decisão | Status | Autor | Data |
|---|---|---|---|
| Unit plan + suíte `0.1.1` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 |
| Unit plan + suíte `0.2.0` (delta 3 composes) | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 |
