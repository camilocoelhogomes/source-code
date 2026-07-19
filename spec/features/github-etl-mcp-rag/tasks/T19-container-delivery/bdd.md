# BDD — T19-container-delivery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T19-container-delivery` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Execução | `tests/bdd/test_container_delivery.py` (runtime com fakes + asserts de manifesto Dockerfile/compose/pyproject) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Cenários CD-01..CD-10; red até `github_rag.delivery` + artefatos de raiz existirem. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Review: ordem D-T19-003 completa; BDD-022 com doubles + blank/missing file; grammars DEC-015. |

## Convenções

- Boot testável via `DefaultContainerRuntime` (deps keyword-only injetáveis) e `run_container_boot(environ)`.
- Sem `docker build` / compose real no gate unitário: superfícies e ordem de boot com doubles; imagem/compose via leitura de manifesto (`Dockerfile`, `docker-compose.yml`, `.env.example`, runbook).
- Falha de boot → `SystemExit(1)` **antes** de bind UI/MCP; sem sync/reconcile parcial (BDD-022 / D-T19-004). Asserts de “sem parcial” usam doubles injetados no `DefaultContainerRuntime`.
- Ordem congelada: sync → `StartupIndexReconcile.run()` → scheduler → bind UI/MCP (D-T19-003 / ENG-011).
- Segredos nunca em `/healthz` nem em mensagens de falha observáveis nos asserts.

---

## CD-01 — UI e MCP disponíveis após boot com CONFIG_PATH/secrets/volumes (BDD-020)

**Dado** ambiente de container com `CONFIG_PATH`, segredo GitHub resolvível e paths alinhados a volumes (`/config/...`, `/repos/...`)  
**E** wiring injetado (sync, reconcile, scheduler, UI, MCP) sem I/O real de infra  
**Quando** `DefaultContainerRuntime(...).boot()` conclui com sucesso  
**Então** a superfície UI fica pronta para servir HTTP  
**E** a superfície MCP fica marcada como pronta  
**E** `GET /healthz` responde 200 com `status=ok`, `ui=ready` e `mcp=ready`

## CD-02 — Config válida carrega conexões e dispara sync (BDD-021 smoke)

**Dado** JSON válido com conexões GitHub e local (`file:///repos/...`) apontado por `CONFIG_PATH`  
**Quando** o boot executa a etapa de carga + sync  
**Então** o `AppConfig` carregado contém todas as conexões nomeadas do arquivo  
**E** `run_catalog_sync` / sync é invocado exatamente uma vez com esse config  
**E** nenhuma conexão é omitida (sucesso completo, nunca parcial)

## CD-03 — Config inválida ou ausente falha observável sem parcial (BDD-022 smoke)

**Dado** `CONFIG_PATH` ausente, blank, arquivo inexistente ou JSON inválido  
**Quando** `DefaultContainerRuntime(...).boot()` (ou `run_container_boot(environ)`) inicia  
**Então** o processo termina com `SystemExit` code `1`  
**E** sync de catálogo **não** é chamado (doubles injetados)  
**E** `StartupIndexReconcile.run()` **não** é chamado  
**E** UI/MCP **não** fazem bind  
**E** a mensagem/log de falha não contém valor de token (`ghp_`, PAT)

## CD-04 — StartupIndexReconcile após sync no boot (ENG-011 / D-T19-003)

**Dado** boot com config válida e doubles de sync + reconcile + scheduler + bind  
**Quando** `boot()` completa as etapas de catálogo até superfícies  
**Então** `StartupIndexReconcile.run()` é chamado exatamente uma vez  
**E** a ordem é **sync → reconcile → scheduler → bind UI/MCP**  
**E** o delivery não reimplementa tip×estado (só delega à porta T14)

## CD-05 — SDKs DEC-015 / pyproject na superfície de delivery (BDD-024)

**Dado** o manifesto de runtime (`pyproject.toml` `[project].dependencies`) e o `Dockerfile` da imagem `app`  
**Quando** a superfície de entrega for inspecionada  
**Então** o Dockerfile instala o projeto via `pip install` a partir do build context (`.` / pacote), não extras `dev`/`integration`  
**E** o conjunto DEC-015 está declarado no `pyproject.toml` (incl. `GitPython`, `PyGithub`, `pathspec`, `tree-sitter` + grammars pinadas, `qdrant-client`, `openai`, `apscheduler`, `mcp`, `fastapi`, `sqlalchemy`, `alembic`, `psycopg`)  
**E** `uvicorn` está nas dependências runtime do projeto (servir UI)  
**E** o Dockerfile inclui o binário de sistema `git`

## CD-06 — Imagem não usa `.venv` do host (ENG-009)

**Dado** `Dockerfile` e `docker-compose.yml`  
**Quando** inspecionar COPY/VOLUME/volumes/bind mounts  
**Então** não há montagem nem cópia de `.venv` do host para o container  
**E** a instalação de deps ocorre no build (`pip install`), não por reutilizar venv externo

## CD-07 — Plataforma primária linux/amd64 documentada (ENG-006)

**Dado** artefatos de entrega (`Dockerfile` e/ou `docker-compose.yml` e/ou runbook/`README`)  
**Quando** buscar a plataforma primária  
**Então** `linux/amd64` (ou `amd64`) está documentada como arquitetura primária

## CD-08 — Healthchecks UI e MCP no compose (ENG-002 / D-T19-007/008)

**Dado** `docker-compose.yml`  
**Quando** inspecionar o serviço `app` (e health da app)  
**Então** existe `healthcheck` observável para a app  
**E** o mecanismo cobre UI (`/healthz`) e readiness MCP (`mcp` ready / porta MCP)  
**E** os serviços `postgres`, `qdrant`, `zoekt` e `slm` estão declarados no compose

## CD-09 — Volumes CONFIG_PATH e `/repos` (ENG-005 / BDD-020)

**Dado** `docker-compose.yml` e `.env.example`  
**Quando** inspecionar montagens e variáveis  
**Então** `CONFIG_PATH` está documentado/injetado (ex. `/config/config.json`)  
**E** há volume/mount para repositórios locais em `/repos`  
**E** `.env.example` lista `CONFIG_PATH`, `GITHUB_TOKEN`, `INDEX_WORKERS`, `QUERY_WORKERS`, `INDEX_CRON` sem segredos reais

## CD-10 — Entrypoint do container é o composition root delivery

**Dado** `Dockerfile`  
**Quando** inspecionar `CMD`/`ENTRYPOINT`  
**Então** o processo da app invoca `python -m github_rag.delivery` (ou equivalente explícito ao módulo delivery)  
**E** o pacote exporta `run_container_boot` / `DefaultContainerRuntime` / `ContainerRuntime`

---

## Mapeamento

| BDD / ENG produto | Cenários T19 |
|---|---|
| BDD-020 | CD-01, CD-09 |
| BDD-021 | CD-02 |
| BDD-022 | CD-03 |
| BDD-024 / DEC-015 | CD-05 |
| ENG-011 | CD-04 |
| ENG-009 | CD-06 |
| ENG-006 | CD-07 |
| ENG-002 / healthchecks | CD-08 |
| D-T19-001/002 | CD-10 |
| D-T19-003 | CD-04 |
