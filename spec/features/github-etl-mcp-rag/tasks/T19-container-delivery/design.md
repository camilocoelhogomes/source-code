# Design — T19-container-delivery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T19-container-delivery` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.2.0` |
| Branch | `feature/github-etl-mcp-rag-T19-container-delivery` |
| Base | `main` (plano 0.1.7 / reqs 0.5.0 — commit `5727340`) |
| Rastreabilidade | REQ-036–038, REQ-043–044, REQ-050; DEC-011–012, DEC-015–017; BR-023–025; BDD-020–022, BDD-024–025, BDD-028 (parte T19); ENG-002, ENG-005–006, ENG-009, ENG-011, ENG-013–017 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Design: composition root `github_rag.delivery` (`ContainerRuntime` / `run_container_boot`); Dockerfile+compose (app/postgres/qdrant/zoekt/slm); boot ENG-011; deps `pyproject.toml` na imagem; amd64; healthchecks UI+MCP; sem domínio novo. |
| 2026-07-18 | Tech Lead Architect | `PENDING_ARCHITECT_REVIEW` | `0.2.0` | Delta plano 0.1.7 / REQ-043: **três** composes (`docker-compose.yml`, `docker-compose.e2e.yml`, `docker-compose.dev.yml`); gate manifesto/doubles (REQ-044); sem Robot/`compose up` real (T21). |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.2.0` | Re-review pós-correção: D-T19-020 em §12; §13 delta completo; §6.1 `E2E_GITHUB_TOKEN`; §14 T21/Robot; §15 residual manifesto. Sem BLOCKING/MAJOR abertos. |

## 1. Contexto

A onda W8 empacota o MVP para uso local padronizado (REQ-036, DEC-011). Domínio e superfícies já existem atrás de portas estáveis:

| Dependência | Porta / artefato | Uso em T19 |
|---|---|---|
| T01 | `AppSettings` / `load_settings` | `CONFIG_PATH`, workers, `INDEX_CRON` |
| T02 | `ConfigLoader` | Smoke BDD-021/022 no boot |
| T03 | `CatalogRepository` + Alembic + `DATABASE_URL` | Persistência; migrate no boot |
| T05/T06/T20 | Discovery GitHub/local (PyGithub / GitPython) | Sync de catálogo |
| T07 | `CatalogSync` / `run_catalog_sync` | Sync-only antes do reconcile |
| T14 | `StartupIndexReconcile` + `IndexingOrchestrator` | ENG-011 no boot |
| T15 | `DailyScheduler` | Agenda pós-boot |
| T16 | `QueryService` | UI + MCP |
| T17 | `McpEvidenceServer` | Superfície MCP |
| T18 | `ManagementUiApi` | Superfície UI HTTP |
| DEC-015 / BDD-024 | SDKs em `pyproject.toml` | **Todas** instaladas na imagem (incl. GitPython/T20) |

Pacote reservado: `src/github_rag/delivery/` (T01). Dockerfile/compose vivem na **raiz** do repositório; código de boot fica em `delivery`.

## 2. Problema

O desenvolvedor precisa subir o produto com:

1. imagem/compose reproduzível (sem `.venv` do host — ENG-009);
2. `CONFIG_PATH` + JSON externo + secrets por env + volumes `file:///repos/...` (ENG-005, REQ-037–038);
3. UI e MCP disponíveis (BDD-020);
4. no boot: config válida → sync catálogo → reconcile de indexação (ENG-011 / smoke BDD-021);
5. config inválida → falha observável sem aplicação parcial (BDD-022);
6. SDKs DEC-015 presentes na imagem (BDD-024);
7. plataforma primária `linux/amd64` (ENG-006);
8. healthchecks básicos UI e MCP;
9. **três** arquivos compose com papéis distintos (REQ-043 / BDD-025 / ENG-017);
10. gate de testes só manifesto/doubles — sem Robot nem `compose up` real (REQ-044 / DEC-017; ownership e2e = T21);
11. **sem** novas features de domínio.

## 3. Solução proposta

### 3.1 Separação Dockerfile × código

| Camada | Onde | Responsabilidade |
|---|---|---|
| **Imagem / Compose** | `Dockerfile`, `docker-compose.yml`, `.env.example`, docs | SO base, `pip install` do projeto + deps, binários (`git`), serviços infra, volumes, ports, healthchecks, recursos sugeridos |
| **Composition root** | `github_rag.delivery` | Wire de adaptadores → boot ordenado → expor UI/MCP/scheduler; **zero** lógica de domínio nova |

```text
docker compose up
  → serviços: postgres, qdrant, zoekt, slm, app
  → app CMD: python -m github_rag.delivery
       ContainerRuntime.boot() / run_container_boot()
         1. load_settings
         2. ConfigLoader.load(CONFIG_PATH)     # BDD-021/022
         3. aguardar deps (PG); alembic upgrade
         4. wire Catalog / discoveries / orchestrator / query / UI / MCP / scheduler
         5. run_catalog_sync(config, sync)     # T07
         6. StartupIndexReconcile.run()        # ENG-011
         7. DailyScheduler.start()
         8. servir UI (uvicorn) + MCP (transporte container)
```

### 3.2 Escopo BDD nesta task

| Cenário | Cobertura T19 | Fora |
|---|---|---|
| BDD-020 | Compose sobe; UI HTTP + MCP acessíveis | Features de domínio |
| BDD-021 | Boot com JSON válido → conexões carregadas + sync deriva catálogo | Discovery interno (T05/T06) |
| BDD-022 | Config ausente/inválida → exit ≠ 0; sem sync/reconcile/UI “meio ligada” | Mensagens UI de erro genérico |
| BDD-024 | Imagem contém deps DEC-015 (pin `pyproject.toml`); GitPython (T20) presente; sem reinventar clientes | Revisão de adaptadores já entregues |
| BDD-025 | Existem `Dockerfile` + **3** composes + `.env.example` sem segredos; testes de manifesto passam | Robot / `compose up` real (T21) |
| BDD-028 (parte T19) | PR #19 só container; não inclui Robot | Declaração MVP (exige T21) |
| ENG-011 | Passo 6 do boot chama só `StartupIndexReconcile.run()` | Pipeline de indexação (T14) |
| ENG-017 | Três composes + `.env.example`; gate doubles | Prova runtime Podman (T21) |

## 4. Componentes

### 4.1 Pacote `github_rag.delivery` (fronteira)

```text
src/github_rag/delivery/
  __init__.py          # exports públicos do boot
  ports.py             # Protocol ContainerRuntime (opcional mas recomendado)
  runtime.py           # DefaultContainerRuntime + run_container_boot
  wiring.py            # factories: PG, Zoekt, Qdrant, SLM, Embedder, UI, MCP…
  health.py            # rotas /healthz (UI) e readiness MCP
  __main__.py          # python -m github_rag.delivery
```

**Responsabilidade do pacote:** composition root + lifecycle de processo do container.  
**Motivo da separação:** entrega (ENG-002/009) não mistura com domínio; T14/T07/T18/T17 permanecem testáveis sem Docker.

**Proibido em `delivery`:** regras de catálogo, indexação, query, parsing de config reinventado, cliente HTTP/SDK ad-hoc.

### 4.2 `ContainerRuntime` (porta pública)

```python
class ContainerRuntime(Protocol):
    def boot(self) -> None:
        """Executa o boot ordenado até superfícies prontas ou falha fatal."""
        ...
```

- **Responsabilidade:** orquestrar o lifecycle de processo do container (settings → config → infra → sync → reconcile → serve).
- **Motivo da separação:** isola entrypoint testável do Dockerfile (`CMD`); permite fakes de wiring nos testes sem subir compose.

### 4.3 `run_container_boot` / `DefaultContainerRuntime`

| Item | Decisão |
|---|---|
| Função de módulo | `run_container_boot(environ: Mapping[str, str] | None = None) -> None` |
| Implementação | `DefaultContainerRuntime` |
| Entrypoint | `__main__.py` → `run_container_boot()` |
| Falha | qualquer erro de settings/config/migrate/sync → log seguro + `SystemExit(1)` **antes** de bind de UI/MCP |
| Sucesso parcial | **proibido** (BDD-022): não aplicar subset de conexões; não iniciar UI/MCP se boot falhou |

Construtor / wiring keyword-only (deps injetáveis nos testes; production factory lê env):

| Dep | Origem |
|---|---|
| `settings` | `load_settings` |
| `config` | `ConfigLoader().load(settings.config_path)` |
| `catalog` | factory PG (`DATABASE_URL`) |
| `sync` | `CatalogSync` + discoveries |
| `reconcile` | `DefaultStartupIndexReconcile` |
| `orchestrator` | `IndexingOrchestrator` |
| `scheduler` | `DailyScheduler` |
| `ui` | `ManagementUiApi.build()` → FastAPI |
| `mcp` | `McpEvidenceServer.build()` → FastMCP |

Pós-reconcile: `scheduler.start()`; drain da fila de indexação em thread/background via política já existente (`run_until_idle` / workers T04) — **não** bloquear bind HTTP indefinidamente no request path da UI (alinhar T18 `drain_on_index`).

### 4.4 Artefatos na raiz do repositório

| Arquivo | Papel |
|---|---|
| `Dockerfile` | Imagem `app` multi-stage opcional; Python 3.12; `pip install .` (runtime); `git` CLI; usuário non-root; `PLATFORM=linux/amd64` documentado |
| `docker-compose.yml` | Compose **usuário final / imagem pública** (REQ-043) — serviços ENG-002 + volumes ENG-005 + healthchecks |
| `docker-compose.e2e.yml` | Compose **stack e2e** (REQ-043) — consumido por T21 (Podman) e pela esteira; volumes/projeto isolados; credencial via env (`GITHUB_TOKEN` / `E2E_GITHUB_TOKEN`) sem secret no git |
| `docker-compose.dev.yml` | Compose **desenvolvimento** (REQ-043) — build local + montagens de código/config convenientes; postgres exposto; sem `.venv` do host |
| `.env.example` | Nomes de env sem segredos reais |
| `docs/runbook-local.md` (ou seção README) | Portas, recursos, volumes, Cursor MCP, amd64, qual compose usar |
| `examples/config.json` | Já alinhado a `file:///repos/*` — referenciado no runbook |

### 4.4.1 Três composes — contratos distintos (D-T19-020)

Os três arquivos compartilham o **mesmo conjunto de serviços ENG-002** (`app`, `postgres`, `qdrant`, `zoekt`, `slm`), o mesmo entrypoint `python -m github_rag.delivery`, volumes `CONFIG_PATH` + `/repos`, healthcheck `/healthz` e plataforma `linux/amd64`. Diferem no **papel operacional**:

| Arquivo | Consumidor | Diferenças obrigatórias |
|---|---|---|
| `docker-compose.yml` | Operador / usuário final | Nome de projeto default; imagem/`build` estável; mounts host via `HOST_CONFIG`/`HOST_REPOS`; sem bind de `./src` |
| `docker-compose.e2e.yml` | T21 + CI (`docs-cicd`) | `name:` isolado (`github-rag-e2e`); volumes nomeados com prefixo `e2e_`; `GITHUB_TOKEN: ${E2E_GITHUB_TOKEN:-${GITHUB_TOKEN:-}}`; comentário de ownership T21/Podman; **sem** montar código-fonte do host |
| `docker-compose.dev.yml` | Desenvolvedor local | `name:` `github-rag-dev`; monta `./src` (e opcionalmente `./web`) read-write para iteração; expõe `postgres:5432`; comentário ENG-009 (nunca `.venv`) |

**Gate de testes (REQ-044):** asserts de manifesto leem os três arquivos (existência + serviços + volumes + health + ausência de `.venv` + ausência de segredos). **Não** é gate executar `compose up` nem Robot.

### 4.5 Serviços Compose (ENG-002)

| Serviço | Imagem / build | Porta host sugerida | Volume / notas |
|---|---|---|---|
| `app` | build `Dockerfile` | UI `8080`, MCP `8001` | monta config + `/repos`; depende de PG/Qdrant/Zoekt/SLM healthy |
| `postgres` | `postgres:16` (pin documentado) | `5432` (opcional expor) | volume dados; `DATABASE_URL` interno |
| `qdrant` | oficial `qdrant/qdrant` (pin) | `6333` | volume storage |
| `zoekt` | oficial Sourcegraph Zoekt (pin; alinhar T10) | `6070` | `ZOEKT_INDEX_DIR=/data/index` |
| `slm` | runtime OpenAI-compatible (**Ollama** default documentado; vLLM aceitável) | `11434` | modelo default `qwen2.5-coder:3b` (T12); pull documentado no runbook |

SLM é **aplicável** (ENG-002 + pipeline T12/T13): serviço `slm` no compose; app aponta `OPENAI_BASE_URL` (ou nome canônico documentado em `.env.example`) para `http://slm:11434/v1`. Sem SLM, indexação RAG falha tipada — não é feature nova; é pré-requisito operacional do MVP.

### 4.6 Dependências que DEVEM estar na imagem `app`

Alinhamento obrigatório a `[project].dependencies` de `pyproject.toml` (BDD-024 / DEC-015). A imagem instala o pacote (`pip install .` ou `pip install -e .` **dentro** do build — nunca monta `.venv` do host):

| Integração | Pacote na imagem |
|---|---|
| PostgreSQL ORM | `sqlalchemy>=2`, `alembic`, `psycopg[binary]` |
| Cron | `apscheduler>=3.10,<4` |
| GitHub | `PyGithub>=2` |
| Git (T08/T20) | `GitPython>=3.1` |
| `.gitignore` | `pathspec>=0.12` |
| Tree-sitter + grammars | `tree-sitter==0.26.0` + grammars pinadas no `pyproject.toml` |
| Qdrant | `qdrant-client>=1.12` |
| SLM / embeddings | `openai>=1.40` |
| MCP | `mcp>=1.27,<2` |
| UI HTTP | `fastapi>=0.115,<1` |
| ASGI server (T19) | **`uvicorn[standard]`** — adicionar a `pyproject.toml` runtime (T18 deixou explícito como runtime T19) |

Sistema (apt/apk no Dockerfile, não pip):

| Binário | Motivo |
|---|---|
| `git` | GitPython / discovery local / snapshot |
| ca-certificates | HTTPS GitHub / clients |

**Não** instalar extras `dev`/`integration` na imagem de entrega. Zoekt CLI/webserver vive no serviço `zoekt`, não na imagem `app` (app só cliente HTTP + paths de index dir via env T10).

### 4.7 Healthchecks

| Superfície | Mecanismo | Critério |
|---|---|---|
| UI | `GET /healthz` no FastAPI (registrado pelo composition root em `delivery.health`) | HTTP 200 após boot completo |
| MCP | Processo MCP escutando transporte container + `GET /healthz` reporta `"mcp": "ready"` **após** `McpEvidenceServer.build()` ok | Compose `healthcheck` no serviço `app` (e/ou probe na porta MCP) |

Transporte MCP no container (D-T19-007):

| Modo | Uso |
|---|---|
| **SSE / streamable HTTP** (porta `MCP_PORT`, default `8001`) | Default no compose — viabiliza healthcheck e uso local sem stdio |
| **stdio** | Entry alternativo `python -m github_rag.delivery.mcp_stdio` para Cursor via `docker compose run -i` |

Tools e `McpEvidenceServer` **não mudam** (T17); só o transport de processo na delivery.

## 5. Fluxo de boot (detalhado)

```text
[0] Processo inicia (sem bind UI/MCP)
[1] load_settings(environ)
      - CONFIG_PATH obrigatório no container (ausente/blank → exit 1, BDD-022)
      - INDEX_WORKERS / QUERY_WORKERS / INDEX_CRON com defaults T01
[2] ConfigLoader.load(path)
      - inválido / I/O / segredo ausente → ConfigLoadError → exit 1 (BDD-022)
      - sucesso → AppConfig completo (nunca parcial)
[3] Esperar PostgreSQL aceitar conexões (retry com backoff curto; timeout documentado)
[4] alembic upgrade head (DATABASE_URL)
[5] Wire adaptadores (Zoekt URL, Qdrant, OpenAI base_url, token GitHub só em memória)
[6] run_catalog_sync(config, sync)          # T07 — BDD-021
[7] StartupIndexReconcile.run()             # ENG-011 — enfileira não atualizado
[8] DailyScheduler.start()                  # APScheduler; preferência PG prevalece (ENG-004)
[9] Registrar /healthz; bind uvicorn UI; start MCP transport container
[10] Background: processar fila (orchestrator) sem bloquear health
```

Ordem **congelada**: sync **antes** de reconcile (D-T07 / D-T14-003). Reconcile **somente** via `StartupIndexReconcile` — proibido duplicar tip×estado no `delivery`.

## 6. Dados / env / volumes

### 6.1 Variáveis (documentar em `.env.example` + runbook)

| Env | Obrigatória no compose | Default / notas |
|---|---|---|
| `CONFIG_PATH` | sim | ex. `/config/config.json` |
| `GITHUB_TOKEN` | se houver conexão github | referenciada pelo JSON `{ "env": "GITHUB_TOKEN" }` |
| `E2E_GITHUB_TOKEN` | não (só e2e/CI) | Alias opcional no `docker-compose.e2e.yml`: mapeia para `GITHUB_TOKEN` no container (`${E2E_GITHUB_TOKEN:-${GITHUB_TOKEN:-}}`); nunca versionar valor |
| `INDEX_WORKERS` | não | `2` (ENG-003) |
| `QUERY_WORKERS` | não | `4` |
| `INDEX_CRON` | não | `0 2 * * *` (ENG-004/010) |
| `DATABASE_URL` | sim (compose injeta) | `postgresql+psycopg://...@postgres:5432/...` |
| `ZOEKT_URL` | sim | `http://zoekt:6070` |
| `ZOEKT_INDEX_DIR` | sim se indexar | `/data/index` (volume compartilhado app↔zoekt **ou** indexação via serviço — documentar layout T10) |
| `QDRANT_URL` | sim | `http://qdrant:6333` (nome canônico no wiring T19; factory lê env) |
| `OPENAI_BASE_URL` | sim p/ RAG | `http://slm:11434/v1` |
| `OPENAI_API_KEY` | não | placeholder `local` |
| `SLM_MODEL` / model embed | não | default T12 `qwen2.5-coder:3b`; embed model documentado no wiring |
| `UI_HOST` / `UI_PORT` | não | `0.0.0.0:8080` |
| `MCP_PORT` | não | `8001` |
| `MCP_TRANSPORT` | não | `sse` no container; `stdio` no entry alternativo |

Secrets **nunca** no JSON em claro (T02); nunca em logs/health.

### 6.2 Volumes (ENG-005, REQ-038)

| Mount no `app` | Conteúdo |
|---|---|
| `${HOST_CONFIG}:/config/config.json:ro` | JSON Sourcebot-like; `CONFIG_PATH=/config/config.json` |
| `${HOST_REPOS}:/repos:ro` | Repos locais; URLs `file:///repos/...` (exemplo oficial) |

Montagens adicionais permitidas se o JSON declarar outros `file://` paths.

### 6.3 Recursos sugeridos (runbook; dúvida não bloqueante)

| Recurso | Sugestão MVP (amd64) |
|---|---|
| CPU | 4 vCPU |
| RAM | 8 GiB (SLM 3B + índices); 16 GiB confortável |
| Disco | 20 GiB+ para volumes PG/Qdrant/Zoekt/repos |
| Workers | defaults ENG-003; não exceder vCPU disponível |

## 7. Erros

| Situação | Comportamento | Observabilidade |
|---|---|---|
| `SettingsBootstrapError` | exit 1; sem bind | log: nome da env + razão; sem shell jargon |
| `ConfigLoadError` / secret ausente | exit 1; **nenhuma** conexão aplicada | mensagem tipada; sem valor de token (BDD-022 / BR-008) |
| PG indisponível após timeout | exit 1 | log genérico; sem `DATABASE_URL` completa |
| Falha Alembic | exit 1 | sem credenciais |
| `CatalogSyncError` | exit 1; sem reconcile/UI | alinhado T07 |
| Falha pontual de tip no reconcile | comportamento T14 (continua outros repos) | log por repo; sem token |
| Falha de indexação em background | estados REQ-020 `erro`; UI/MCP seguem up | não derruba processo pós-bind |

## 8. Segurança

- Imagem não copia `.env` com segredos; só `.env.example`.
- Token só via env; nunca endpoint de config (T18).
- Volumes de repos: preferir `:ro` no compose de exemplo.
- Usuário non-root no Dockerfile.
- `/healthz` sem dados de catálogo/código/token.
- Logs de boot: redaction de `GITHUB_TOKEN`, `DATABASE_URL`, `OPENAI_API_KEY`.

## 9. Compatibilidade

| Tema | Decisão |
|---|---|
| Arquitetura | Primária **`linux/amd64`** (ENG-006); `arm64` best-effort (documentar limitação SLM/Zoekt) |
| Host Windows/macOS/Linux | Docker Desktop / Engine; paths do **host** no compose; paths **dentro** do container sempre POSIX |
| Dev vs delivery | Dev continua com `.venv` (ENG-009); delivery **não** monta nem usa `.venv` do host |
| Python | 3.12+ na imagem |

## 10. Observabilidade

Logs estruturados (ou prefixados estáveis) no boot:

| Evento | Campos (sem segredo) |
|---|---|
| `delivery_boot_start` | — |
| `delivery_config_loaded` | `connection_count` |
| `delivery_migrations_ok` | — |
| `delivery_catalog_sync_ok` | ativos/desativados (contagens) |
| `delivery_startup_reconcile_ok` | — |
| `delivery_surfaces_up` | `ui_port`, `mcp_transport` |
| `delivery_boot_failed` | `stage`, `error_type` |

`/healthz` exemplo:

```json
{ "status": "ok", "ui": "ready", "mcp": "ready" }
```

Antes do bind: healthcheck do compose falha (processo ainda não escuta ou app responde 503 se probe precoce — preferir só escutar após passo 9).

## 11. Riscos e rollback

| Risco | Mitigação |
|---|---|
| SLM pesada na máquina do dev | Recursos sugeridos; compose profiles `slm` opcional documentado; falha tipada se ausente |
| Zoekt index dir compartilhado app↔zoekt | Documentar volume único `/data/index`; pin de imagem Zoekt |
| MCP stdio vs healthcheck | D-T19-007: SSE/HTTP no compose; stdio como entry extra |
| Boot longo (sync+reconcile+enqueue) | Health só após superfícies up; reconcile não precisa drenar fila toda antes do bind |
| amd64 vs Apple Silicon | ENG-006; runbook avisa emulação |
| Drift de deps | Imagem instala a partir do `pyproject.toml` do build context |

**Rollback:** não publicar/usar a tag da imagem; `docker compose down -v` (volumes locais descartáveis — handoff da task).

## 12. Decisões congeladas

| ID | Decisão |
|---|---|
| D-T19-001 | Fronteira de código = pacote `github_rag.delivery`; Dockerfile/compose na raiz |
| D-T19-002 | Porta `ContainerRuntime.boot()` + `run_container_boot()` como entrypoint Python do container |
| D-T19-003 | Boot ordenado: settings → config → migrate → wire → `run_catalog_sync` → `StartupIndexReconcile.run()` → scheduler → UI/MCP |
| D-T19-004 | Config inválida/ausente → exit 1 sem bind e sem sync parcial (BDD-022) |
| D-T19-005 | Compose: `app`, `postgres`, `qdrant`, `zoekt`, `slm` (Ollama default OpenAI-compatible) |
| D-T19-006 | Imagem primária `linux/amd64`; não usa `.venv` do host (ENG-006/009) |
| D-T19-007 | MCP no compose: transporte SSE/streamable HTTP + `/healthz.mcp`; stdio via módulo alternativo |
| D-T19-008 | UI: uvicorn serve `ManagementUiApi.build()`; health `GET /healthz` |
| D-T19-009 | Volumes padrão: `CONFIG_PATH` file + `/repos` ↔ `file:///repos/...` (ENG-005) |
| D-T19-010 | Todas as deps runtime do `pyproject.toml` (DEC-015 incl. GitPython) + `uvicorn` + `git` CLI na imagem `app` |
| D-T19-011 | Reconcile **somente** via `StartupIndexReconcile` (D-T14-003); delivery não reimplementa tip×estado |
| D-T19-012 | Sem novas features de domínio; sem CRUD de conexões/token |
| D-T19-020 | **Três** composes na raiz (`docker-compose.yml`, `docker-compose.e2e.yml`, `docker-compose.dev.yml`) com papéis e diferenças de §4.4.1; gate de testes = manifesto/doubles apenas (REQ-043–044, BDD-025, ENG-017, DEC-017); Robot/`compose up` real = T21 |

## 13. Rastreabilidade

| Requisito / decisão | Cobertura no design |
|---|---|
| REQ-036 / DEC-011 | Compose + imagem |
| REQ-037 | Env `CONFIG_PATH`, token, workers, `INDEX_CRON` |
| REQ-038 / ENG-005 | Volume `/repos` + exemplo JSON |
| REQ-043 / BR-025 / ENG-017 | Três composes + Dockerfile + `.env.example` (§4.4 / §4.4.1 / D-T19-020) |
| REQ-044 / DEC-017 | Gate manifesto/doubles; sem Robot/`compose up` real |
| REQ-050 / BDD-028 (parte T19) | PR #19 só container; Robot fora |
| ENG-011 / BR-002–004 | Passo reconcile no boot |
| BDD-020 | UI+MCP up |
| BDD-021 / BDD-022 | ConfigLoader no boot + fail-fast |
| BDD-024 / DEC-015 / T20 | Deps na imagem; GitPython presente |
| BDD-025 | Existência dos 3 composes + manifesto (§4.4.1) |
| ENG-002 | Serviços listados |
| ENG-009 | Sem `.venv` do host na imagem |
| ENG-006 | amd64 primário |

## 14. Fora de escopo

- Novas regras de domínio, novos estados REQ-020, CRUD de config na UI.
- Registro corporativo obrigatório (dúvida não bloqueante).
- Multi-arch CI obrigatório para `arm64`.
- Otimização de tamanho de imagem além do razoável multi-stage.
- Substituir Ollama por provedor cloud.
- Alterar contratos T14/T17/T18.
- Suíte Robot Framework, `compose up` / Podman real e prova e2e do MVP (ownership = **T21**; REQ-044–047, DEC-017–018).
- Declaração de “MVP entregue” (exige T19 **e** T21 verdes).
- Esteira GitHub Actions, docs EN, release GHCR (`docs-cicd-e2e-release`) — só consome os artefatos.

## 15. Interfaces / residual do delta 0.2.0

Contratos Python de `github_rag.delivery` já formalizados em `interfaces.md` v0.1.0. O residual deste delta é só a **superfície de manifesto**:

1. Existência e papéis dos três composes (D-T19-020 / §4.4.1) — asserts BDD/unit, sem Protocols novos.
2. `.env.example` inclui nomes canônicos + menção a `E2E_GITHUB_TOKEN` (sem valor secreto).
3. Runbook documenta qual compose usar (usuário / e2e / dev).
