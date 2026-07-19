# Interfaces — T19-container-delivery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T19-container-delivery` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T19-container-delivery` |
| Escopo desta etapa | Contratos de comunicação T19 **somente** (stubs/assinaturas; sem implementação de produção) |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Porta `ContainerRuntime`; `run_container_boot`; wiring/health/`__main__`/mcp_stdio; manifesto fora do pacote Python. |

## 1. Escopo e exclusões

### Em escopo (Python — pacote `github_rag.delivery`)

| Contrato | Módulo | Papel |
|---|---|---|
| `ContainerRuntime` | `delivery/ports.py` | Protocol do lifecycle de boot |
| `DefaultContainerRuntime` | `delivery/runtime.py` | Composition root injetável + `boot()` |
| `run_container_boot` | `delivery/runtime.py` | Função de módulo / entrypoint |
| Wiring helpers | `delivery/wiring.py` | Factories de adaptadores + migrate/wait |
| Health | `delivery/health.py` | `GET /healthz` + payload |
| `__main__` | `delivery/__main__.py` | `python -m github_rag.delivery` |
| `mcp_stdio` | `delivery/mcp_stdio.py` (+ `__main__` do submódulo) | Entry alternativo stdio (D-T19-007) |
| Re-exports | `delivery/__init__.py` | Superfície pública CD-10 |

### Superfície de manifesto (não é interface Python)

| Artefato | Papel | Como congela contrato |
|---|---|---|
| `Dockerfile` | Imagem `app` | Asserts BDD CD-05/06/07/10 |
| `docker-compose.yml` | Serviços ENG-002 + volumes + healthcheck | Asserts CD-07/08/09 |
| `.env.example` | Nomes de env sem segredos | Assert CD-09 |
| `docs/runbook-local.md` / README | amd64, portas, volumes | Assert CD-07 |

**Responsabilidade da superfície de manifesto:** declarar SO, `pip install .`, serviços, mounts e CMD.  
**Motivo da separação:** entrega Docker (ENG-002/009) fica na raiz; o pacote `delivery` só orquestra processo Python — testes de manifesto leem arquivos, não Protocols.

### Dependências consumidas (não redefinidas)

| Task | Contratos |
|---|---|
| T01 | `AppSettings`, `load_settings`, `SettingsBootstrapError`, `ENV_*` |
| T02 | `ConfigLoader`, `ConfigLoadError`, `AppConfig` |
| T03 | `CatalogRepository`, `create_postgres_catalog_repository` |
| T04 | `create_index_limiter`, `create_query_limiter` |
| T05/T06/T20 | Discoveries GitHub/local |
| T07 | `CatalogSync`, `run_catalog_sync` |
| T10–T13 | Zoekt / tree-sitter / SLM / Qdrant (via factories existentes) |
| T14 | `IndexingOrchestrator`, `StartupIndexReconcile` |
| T15 | `DailyScheduler` |
| T16 | `QueryService` |
| T17 | `McpEvidenceServer` / `DefaultMcpEvidenceServer` |
| T18 | `ManagementUiApi` / `DefaultManagementUiApi` |

### Fora de escopo

| Item | Dono |
|---|---|
| Regras tip×estado / pipeline de indexação | T14 |
| CRUD de conexões/token | Proibido (T18/T19) |
| Alterar contratos T01–T18 | Fora |
| `docker build` / compose real nos unit/BDD | Fora (só leitura de manifesto) |
| Novas features de domínio | Proibido (D-T19-012) |

## 2. Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T19-001 | Fronteira Python = pacote `github_rag.delivery`; Dockerfile/compose na raiz | D-T19-001; ENG-002/009 | design §4.1; CD-10 |
| I-T19-002 | Porta `@runtime_checkable` `ContainerRuntime` com `boot() -> None` | Isola entrypoint testável do CMD | D-T19-002; CD-01/10 |
| I-T19-003 | `run_container_boot(environ: Mapping[str, str] \| None = None) -> None` | Entrypoint de módulo; `environ=None` ⇒ `os.environ` | D-T19-002; CD-03 |
| I-T19-004 | `DefaultContainerRuntime` keyword-only; deps injetáveis (`sync`, `reconcile`, `scheduler`, `bind_ui`, `bind_mcp`, `skip_infra`, …) | Doubles BDD; production factory lê env | design §4.3; CD-01..04 |
| I-T19-005 | Ordem congelada em `boot()`: settings → config → (infra/migrate se não `skip_infra`) → wire → `run_catalog_sync` → `StartupIndexReconcile.run()` → `DailyScheduler.start()` → bind UI/MCP | D-T19-003; ENG-011 | CD-04 |
| I-T19-006 | Qualquer falha pré-bind → log seguro + `SystemExit(1)`; proibido bind/sync/reconcile parcial | BDD-022; D-T19-004 | CD-03 |
| I-T19-007 | `GET /healthz` → HTTP 200 `{ "status": "ok", "ui": "ready", "mcp": "ready" }` sem segredos | D-T19-007/008 | CD-01/08 |
| I-T19-008 | Wiring helpers em `wiring.py` (wait PG, alembic, factories UI/MCP/adapters); runtime só orquestra | Composition testável; sem domínio | design §4.1 |
| I-T19-009 | Envs de fronteira (`DATABASE_URL`, `ZOEKT_*`, `QDRANT_URL`, `OPENAI_*`, `UI_*`, `MCP_*`) lidas por factories/wiring — **sem** expandir `AppSettings` T01 | Padrão T03/T10; DEC-015 | design §6.1 |
| I-T19-010 | Entries: `__main__` → `run_container_boot()`; `python -m github_rag.delivery.mcp_stdio` para stdio | D-T19-007 | design §4.7 |
| I-T19-011 | `skip_infra: bool = False` — quando `True`, omite wait PG / alembic / I/O de infra (BDD unitário) | CD-01..04 sem Docker | bdd.md convenções |
| I-T19-012 | `bind_ui` / `bind_mcp` callables injetáveis; default production faz uvicorn + transporte MCP | BDD registra ordem sem portas reais | CD-04 |
| I-T19-013 | Após boot ok, runtime expõe `ui_app` **ou** `asgi_app` (FastAPI) com `/healthz` | CD-01 TestClient | CD-01 |
| I-T19-014 | Reconcile **somente** via `StartupIndexReconcile.run()`; delivery não tip×estado | D-T19-011 | CD-04 |
| I-T19-015 | MCP compose default: transport SSE/streamable HTTP (`MCP_TRANSPORT=sse`, `MCP_PORT`); stdio só no entry `mcp_stdio` | D-T19-007 | design §4.7 |
| I-T19-016 | Exports públicos: `ContainerRuntime`, `DefaultContainerRuntime`, `run_container_boot` | CD-10 | CD-10 |
| I-T19-017 | Manifesto (Dockerfile/compose/env/runbook) validado por asserts de arquivo; **não** Protocols Python | Separação imagem × processo | CD-05..09 |
| I-T19-018 | Proibido em `delivery`: regras de catálogo/index/query; parse de config reinventado; clientes HTTP/SDK ad-hoc | D-T19-012; ENG-013 | design §4.1 |
| I-T19-019 | Logs/erros de boot sem valor de token / URL completa / PAT (`ghp_`) | BR-008; design §7–8 | CD-03 |
| I-T19-020 | Stubs desta etapa: contratos em markdown; implementação pelo Developer após unit plan | Gate interfaces ≠ código produção | pipeline |

## 3. Layout do pacote

```text
src/github_rag/delivery/
  __init__.py          # exports I-T19-016
  ports.py             # ContainerRuntime
  runtime.py           # DefaultContainerRuntime + run_container_boot
  wiring.py            # helpers de composition
  health.py            # /healthz
  __main__.py          # python -m github_rag.delivery
  mcp_stdio.py         # entry stdio opcional (D-T19-007)
```

**Responsabilidade do pacote:** composition root + lifecycle de processo do container.  
**Motivo da separação:** entrega (ENG-002/009) não mistura com domínio; T07/T14/T17/T18 permanecem testáveis sem Docker.

## 4. Porta `ContainerRuntime`

Módulo: `github_rag.delivery.ports`

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ContainerRuntime(Protocol):
    """Lifecycle de processo do container (composition root).

    Responsabilidade
        Orquestrar o boot ordenado até superfícies UI/MCP prontas ou falha fatal
        com SystemExit(1), sem aplicar configuração parcial.

    Motivo da separação
        Isola o entrypoint testável do Dockerfile (CMD ``python -m github_rag.delivery``)
        dos adaptadores de domínio (T07/T14/T17/T18). Permite doubles de wiring
        nos testes sem subir compose (I-T19-002 / D-T19-002).
    """

    def boot(self) -> None:
        """Executa o boot ordenado até superfícies prontas ou falha fatal.

        Responsabilidade
            Percorrer a ordem I-T19-005; em sucesso bind UI/MCP; em falha
            pré-bind levantar ``SystemExit(1)`` (I-T19-006).

        Motivo da separação
            Único método da porta — callers (``__main__``, testes) não conhecem
            stages internos nem factories.

        Erros
            ``SystemExit(1)`` para falhas de settings/config/infra/sync (e
            equivalentes tipados encapsulados). Não faz bind em falha.
        """
        ...
```

## 5. `DefaultContainerRuntime` + `run_container_boot`

Módulo: `github_rag.delivery.runtime`

```python
from collections.abc import Callable, Mapping
from typing import Any

class DefaultContainerRuntime:
    """Implementação default do composition root de entrega.

    Responsabilidade
        Materializar I-T19-005/006 com deps keyword-only injetáveis; em
        produção compor adaptadores via ``wiring``; em testes aceitar doubles.

    Motivo da separação
        Mantém ``ContainerRuntime`` como Protocol estável e concentra a
        orquestração (não domínio) numa classe testável (CD-01..04).
    """

    def __init__(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        settings: Any | None = None,
        config: Any | None = None,
        config_loader: Any | None = None,
        catalog: Any | None = None,
        sync: Any | None = None,
        reconcile: Any | None = None,
        orchestrator: Any | None = None,
        scheduler: Any | None = None,
        ui: Any | None = None,
        mcp: Any | None = None,
        bind_ui: Callable[..., None] | None = None,
        bind_mcp: Callable[..., None] | None = None,
        skip_infra: bool = False,
    ) -> None: ...

    def boot(self) -> None: ...

    # Após boot bem-sucedido (I-T19-013):
    # ui_app: FastAPI | None
    # e/ou asgi_app: FastAPI | None  — ao menos um deve existir p/ CD-01
```

### 5.1 Semântica do construtor

| Parâmetro | Default / produção | Papel |
|---|---|---|
| `environ` | `os.environ` | Mapping injetável (padrão T01/T03) |
| `settings` | `load_settings(environ)` no boot | Bootstrap T01 |
| `config` / `config_loader` | `ConfigLoader().load(settings.config_path)` | T02; fail-fast se path ausente/blank/inválido |
| `catalog` | factory PG (`DATABASE_URL`) | T03 |
| `sync` | `CatalogSync` + discoveries | T07; BDD injeta `RecordingSync` |
| `reconcile` | `DefaultStartupIndexReconcile` | T14; só `.run()` |
| `orchestrator` | `IndexingOrchestrator` | T14; background pós-bind |
| `scheduler` | `DailyScheduler` | T15; `.start()` após reconcile |
| `ui` | `DefaultManagementUiApi(...).build()` | T18 FastAPI |
| `mcp` | `DefaultMcpEvidenceServer(...).build()` | T17 FastMCP |
| `bind_ui` / `bind_mcp` | uvicorn + MCP SSE/HTTP | Injetáveis nos testes |
| `skip_infra` | `False` | `True` omite wait PG / alembic (BDD) |

### 5.2 `run_container_boot`

```python
def run_container_boot(environ: Mapping[str, str] | None = None) -> None:
    """Entrypoint de módulo do container.

    Responsabilidade
        Instanciar ``DefaultContainerRuntime(environ=environ)`` (wiring de
        produção) e chamar ``boot()``.

    Motivo da separação
        ``__main__`` e operadores chamam uma função estável sem conhecer a
        classe; testes CD-03 exercitam fail-fast do entrypoint (I-T19-003).

    Erros
        Propaga ``SystemExit(1)`` de ``boot()`` (I-T19-006).
    """
    ...
```

### 5.3 Invariantes de `boot()` (comportamento completo — Developer)

1. **Pré-bind:** nenhum `bind_ui` / `bind_mcp` até sync + reconcile + scheduler ok.  
2. **Ordem observável (CD-04):** `sync` → `reconcile.run()` → `scheduler.start()` → `bind_ui` / `bind_mcp`.  
3. **Sync:** exatamente uma invocação de sync/`run_catalog_sync` com `AppConfig` completo (CD-02).  
4. **CONFIG_PATH:** ausente, blank, arquivo inexistente ou JSON inválido → `SystemExit(1)` sem sync/reconcile/bind (CD-03).  
5. **Segredos:** logs/stdout/stderr/health sem valor de token / `ghp_` (I-T19-019).  
6. **`skip_infra=True`:** não exige PG real; ainda executa load settings/config + sync/reconcile/scheduler/bind injetados.  
7. **Pós-bind:** fila de indexação em background; não bloqueia health no request path (alinhar T18 `drain_on_index`).

## 6. Wiring helpers

Módulo: `github_rag.delivery.wiring`

```python
from collections.abc import Mapping
from typing import Any

def wait_for_postgres(
    environ: Mapping[str, str],
    *,
    timeout_seconds: float = 60.0,
    interval_seconds: float = 1.0,
) -> None:
    """Aguarda PostgreSQL aceitar conexões (retry/backoff).

    Responsabilidade
        Bloquear o boot até PG ready ou timeout → falha tipada/segura.

    Motivo da separação
        Isola I/O de readiness do orquestrador ``boot()``; omitido quando
        ``skip_infra=True`` (I-T19-011). Não vaza ``DATABASE_URL`` completa.
    """
    ...


def run_alembic_upgrade(environ: Mapping[str, str]) -> None:
    """Executa ``alembic upgrade head`` com URL do ambiente.

    Responsabilidade
        Migrar schema do catálogo antes do wire de repositório.

    Motivo da separação
        Migração é preocupação de entrega/processo, não de domínio T03 runtime.
        Mensagens sem credenciais (design §7).
    """
    ...


def wire_catalog(environ: Mapping[str, str]) -> Any:
    """Constrói ``CatalogRepository`` (factory PG existente).

    Responsabilidade: delegar a ``create_postgres_catalog_repository``.
    Motivo da separação: ponto único de wire no delivery sem reabrir T01.
    """
    ...


def wire_catalog_sync(environ: Mapping[str, str], *, catalog: Any) -> Any:
    """Constrói ``CatalogSync`` + discoveries (GitHub/local).

    Responsabilidade: composition de sync T07 para o boot.
    Motivo da separação: discoveries ficam atrás da porta; delivery só injeta.
    """
    ...


def wire_indexing_stack(
    environ: Mapping[str, str],
    *,
    catalog: Any,
    settings: Any,
) -> tuple[Any, Any]:
    """Constrói ``(IndexingOrchestrator, StartupIndexReconcile)``.

    Responsabilidade: factories Zoekt/Qdrant/SLM/embedder/eligibility/snapshot.
    Motivo da separação: runtime chama só ``reconcile.run()`` / enqueue background
    (I-T19-014); não tip×estado.
    """
    ...


def wire_scheduler(
    environ: Mapping[str, str],
    *,
    catalog: Any,
    orchestrator: Any,
    settings: Any,
) -> Any:
    """Constrói ``DailyScheduler`` com preferência PG (ENG-004).

    Responsabilidade: agenda pós-boot.
    Motivo da separação: T15 permanece dono da política de cron.
    """
    ...


def wire_query_service(
    environ: Mapping[str, str],
    *,
    catalog: Any,
    settings: Any,
) -> Any:
    """Constrói ``QueryService`` + dependências de busca.

    Responsabilidade: handoff T16 para UI/MCP.
    Motivo da separação: superfícies não montam índices sozinhas.
    """
    ...


def wire_ui_app(
    *,
    catalog: Any,
    orchestrator: Any,
    scheduler: Any,
    query: Any,
) -> Any:
    """``DefaultManagementUiApi(...).build()`` → FastAPI.

    Responsabilidade: materializar superfície UI (T18).
    Motivo da separação: delivery só sobe ASGI; rotas ficam em ``ui``.
    """
    ...


def wire_mcp_server(
    *,
    catalog: Any,
    query: Any,
    query_limiter: Any,
) -> Any:
    """``DefaultMcpEvidenceServer(...).build()`` → FastMCP.

    Responsabilidade: materializar superfície MCP (T17).
    Motivo da separação: tools não mudam; só o transport de processo (I-T19-015).
    """
    ...


def default_bind_ui(app: Any, environ: Mapping[str, str]) -> None:
    """Serve UI via uvicorn (``UI_HOST``/``UI_PORT``).

    Responsabilidade: bind HTTP da UI após boot completo.
    Motivo da separação: injetável nos testes (``RecordingSurfaces.bind_ui``).
    """
    ...


def default_bind_mcp(mcp_app: Any, environ: Mapping[str, str]) -> None:
    """Inicia transporte MCP container (SSE/streamable HTTP).

    Responsabilidade: escutar ``MCP_PORT`` conforme ``MCP_TRANSPORT``.
    Motivo da separação: compose healthcheck ≠ stdio Cursor (I-T19-015).
    """
    ...
```

Nomes exatos dos helpers podem ser agrupados num `wire_production_dependencies(environ) -> WiredStack` **desde que** preservem a separação acima e a injeção keyword-only do runtime. Agrupar não autoriza lógica de domínio nova.

## 7. Health

Módulo: `github_rag.delivery.health`

```python
from typing import Any, Mapping, TypedDict

class HealthzBody(TypedDict):
    status: str  # "ok"
    ui: str      # "ready"
    mcp: str     # "ready"


def healthz_payload(*, ui_ready: bool, mcp_ready: bool) -> HealthzBody:
    """Monta o JSON de ``GET /healthz``.

    Responsabilidade
        Expor readiness mínimo UI+MCP sem catálogo/código/token.

    Motivo da separação
        Contrato de observabilidade (compose healthcheck) isolado do domain
        e das rotas ``/api`` da T18 (I-T19-007).
    """
    ...


def register_health_routes(app: Any, *, get_state: Any) -> None:
    """Registra ``GET /healthz`` no FastAPI da UI.

    Responsabilidade
        Responder 200 só quando UI e MCP estiverem ready pós-boot; payload
        via ``healthz_payload``.

    Motivo da separação
        Composition root adiciona probe de entrega sem alterar contratos T18
        de gestão/busca.

    Invariantes
        Corpo sem segredos; chaves exatamente ``status``, ``ui``, ``mcp``
        nos asserts CD-01.
    """
    ...
```

Exemplo canônico (sucesso):

```json
{ "status": "ok", "ui": "ready", "mcp": "ready" }
```

Preferência de processo: **não** escutar HTTP até o passo de bind (design §10); healthcheck do compose falha enquanto o processo não serve.

## 8. Entry points

### 8.1 `__main__`

Módulo: `github_rag.delivery.__main__`

```python
"""Entry ``python -m github_rag.delivery``.

Responsabilidade
    Chamar ``run_container_boot()`` e encerrar com o código de ``SystemExit``.

Motivo da separação
    Alinha CMD do Dockerfile ao composition root (I-T19-010 / CD-10) sem
    lógica adicional.
"""

from github_rag.delivery import run_container_boot

def main() -> None:
    run_container_boot()

if __name__ == "__main__":
    main()
```

### 8.2 `mcp_stdio`

Módulo: `github_rag.delivery.mcp_stdio` (invocável como `python -m github_rag.delivery.mcp_stdio`)

```python
"""Entry alternativo MCP stdio (Cursor via ``docker compose run -i``).

Responsabilidade
    Subir (ou reutilizar wiring mínimo) e chamar ``McpEvidenceServer.run(transport=\"stdio\")``.

Motivo da separação
    Compose default usa SSE/HTTP + healthcheck (I-T19-015); stdio é caminho
    operacional distinto sem alterar tools T17 (D-T19-007).
"""

def main() -> None:
    ...
```

Boot completo ENG-011 no path stdio: se o processo stdio for **apenas** host MCP acoplado a um app já up, documentar no runbook; se for processo único, deve respeitar a mesma ordem I-T19-005 ou falhar de forma explícita — **não** bind UI no path stdio.

## 9. Exports públicos (`delivery/__init__.py`)

```python
"""Composition root de entrega (T19).

Responsabilidade
    Reexportar a superfície estável consumida por CMD, BDD e unitários.

Motivo da separação
    CD-10 exige ``ContainerRuntime``, ``DefaultContainerRuntime``,
    ``run_container_boot`` importáveis de ``github_rag.delivery``.
"""

from github_rag.delivery.ports import ContainerRuntime
from github_rag.delivery.runtime import DefaultContainerRuntime, run_container_boot

__all__ = [
    "ContainerRuntime",
    "DefaultContainerRuntime",
    "run_container_boot",
]
```

## 10. Env canônicas lidas pelo wiring (I-T19-009)

| Env | Origem / leitor | Notas |
|---|---|---|
| `CONFIG_PATH` | T01 `load_settings` | Obrigatória no container; blank/ausente → exit 1 |
| `INDEX_WORKERS` / `QUERY_WORKERS` / `INDEX_CRON` | T01 | Defaults ENG-003/004 |
| `GITHUB_TOKEN` | T02 secret ref / discoveries | Nunca no JSON em claro; nunca em health/logs |
| `DATABASE_URL` | T03 factory / wait / alembic | Sem vazar URL completa |
| `ZOEKT_URL` / `ZOEKT_INDEX_DIR` | T10 `from_environ` / wiring | Serviço `zoekt` no compose |
| `QDRANT_URL` | wiring T13 | Default compose `http://qdrant:6333` |
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` | wiring T12/embed | SLM `http://slm:11434/v1` |
| `SLM_MODEL` (e embed model se aplicável) | wiring | Defaults T12 documentados |
| `UI_HOST` / `UI_PORT` | `default_bind_ui` | Default `0.0.0.0:8080` |
| `MCP_PORT` / `MCP_TRANSPORT` | `default_bind_mcp` | Default `8001` / `sse` |

**Não** adicionar esses nomes a `AppSettings` nesta task.

## 11. Superfície de manifesto (I-T19-017)

Contratos **declarativos** (assertados em `tests/bdd/test_container_delivery.py`):

| ID manifesto | Requisito |
|---|---|
| M-T19-001 | `Dockerfile`: `pip install` do projeto (`.`); sem extras `[dev]`; binário `git`; CMD `python -m github_rag.delivery` |
| M-T19-002 | `docker-compose.yml`: serviços `app`, `postgres`, `qdrant`, `zoekt`, `slm`; `healthcheck` com `/healthz`; MCP (`8001`/`MCP_PORT`/`mcp`) |
| M-T19-003 | Volumes/`CONFIG_PATH` + mount `/repos`; `.env.example` com nomes sem segredos reais |
| M-T19-004 | `linux/amd64` (ou `amd64`) documentado |
| M-T19-005 | Sem COPY/mount de `.venv` do host |
| M-T19-006 | `pyproject.toml` declara DEC-015 + grammars + `uvicorn` (imagem instala via pip do contexto) |

Esses itens **não** geram Protocols em `delivery/`; o Developer materializa os arquivos na implementação.

## 12. ENG-013 / BDD-024 por módulo Python

| Módulo | Permitido | Proibido |
|---|---|---|
| `ports.py` | typing/stdlib | fastapi, uvicorn, SDKs de índice |
| `health.py` | FastAPI/Starlette só para registrar rota | lógica de catálogo/query |
| `runtime.py` | orquestração + imports das portas T07/T14/T15/T17/T18 | tip×estado; parse JSON próprio |
| `wiring.py` | factories existentes + alembic/PG wait | reinventar clientes HTTP/SDK |
| `__main__.py` / `mcp_stdio.py` | chamar entrypoints | domínio |

Imagem `app` instala **todas** as deps runtime do `pyproject.toml` (incl. GitPython) + `uvicorn` + `git` CLI — validação via manifesto (CD-05), não via import em `ports.py`.

## 13. Mapeamento BDD → contratos

| Cenário | Contratos |
|---|---|
| CD-01 | I-T19-002/007/012/013 — `boot` + healthz + binds |
| CD-02 | I-T19-005 — sync 1× com `AppConfig` completo |
| CD-03 | I-T19-003/006/019 — `SystemExit(1)` sem parcial |
| CD-04 | I-T19-005/014 — ordem sync→reconcile→scheduler→bind |
| CD-05..09 | I-T19-017 / M-T19-* — manifesto |
| CD-10 | I-T19-001/010/016 — exports + CMD |

## 14. Handoff

| Consumidor | Uso |
|---|---|
| Dockerfile CMD | `python -m github_rag.delivery` → `run_container_boot()` |
| BDD / unit | `DefaultContainerRuntime(..., skip_infra=True, sync=..., ...).boot()` |
| Cursor (stdio) | `python -m github_rag.delivery.mcp_stdio` |
| QA (próximo gate) | Unitários contra estas assinaturas + extremos |

Mudança de ordem de boot, adição de CRUD de config, ou expansão de `AppSettings` com envs de fronteira ⇒ `SCOPE_CHANGE_REQUIRED`.
