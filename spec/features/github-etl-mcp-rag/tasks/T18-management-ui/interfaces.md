# Interfaces — T18-management-ui

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T18-management-ui` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` |
| BDD base | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T18-management-ui` |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Porta `ManagementUiApi`; DTOs HTTP; labels PT; proibição CRUD; FastAPI. |

## 1. Escopo

| Contrato | Módulo | Papel |
|---|---|---|
| Labels PT | `ui/labels.py` | `STATE_LABELS` / `state_label()` |
| Erros HTTP map | `ui/errors.py` | mapeamento domínio → HTTP |
| Porta | `ui/ports.py` | `ManagementUiApi` |
| App FastAPI | `ui/app.py` | rotas + static |
| Implementação | `ui/api.py` | `DefaultManagementUiApi` |
| Serialização | `ui/serialize.py` | CatalogEntry → JSON UI |
| Frontend | `web/` | HTML/JS/CSS estático |
| Fake | `ui/fake.py` | `FakeManagementUiApi` (opcional testes) |

## 2. Dependências consumidas (não redefinidas)

| Task | Contratos |
|---|---|
| T03/T07 | `CatalogRepository`, `CatalogEntry`, `Progress`, `IndexingExecution`, `FileProgress`, `RepoState`, `RepoOrigin` |
| T14 | `IndexingOrchestrator` |
| T15 | `DailyScheduler`, `InvalidCronExpressionError` |
| T16 | `QueryService`, requests/DTOs, `QueryError` |

## 3. Decisões de interface

| ID | Decisão | Motivo |
|---|---|---|
| I-T18-001 | Porta `ManagementUiApi` com `build() -> FastAPI` | D-T18-001; T19 sobe ASGI |
| I-T18-002 | Construtor keyword-only de `DefaultManagementUiApi` | Paridade T16/T17 |
| I-T18-003 | Escrita cron só `scheduler.set_cron` | I-T15-002 |
| I-T18-004 | Index: `enqueue` + opcional `run_until_idle` | BDD-002 observável |
| I-T18-005 | `state` slug + `state_label` PT | REQ-020 apresentação |
| I-T18-006 | Zero rotas connections/token/CONFIG | BDD-023 |
| I-T18-007 | Buscas UI com `DetailFields` all-true | UX; BDD-009/010 |
| I-T18-008 | `@runtime_checkable` na porta | Convenção Protocols |
| I-T18-009 | FastAPI único SDK HTTP no pacote `ui` | BDD-024 / DEC-015 |
| I-T18-010 | StaticFiles monta `web/` em `/` após rotas `/api` | Frontend leve |

## 4. Labels

```python
STATE_LABELS: Mapping[RepoState, str] = {
    RepoState.NOT_INDEXED: "não indexado",
    RepoState.QUEUED: "na fila",
    RepoState.INDEXING: "indexando",
    RepoState.UP_TO_DATE: "atualizado",
    RepoState.ERROR: "erro",
}

def state_label(state: RepoState) -> str:
    """Traduz slug REQ-020 para rótulo PT de UI.

    Responsabilidade: apresentação; não altera o domínio.
    Motivo da separação: enums ASCII estáveis (T03) vs copy PT (REQ-020).
    """
    ...
```

## 5. Porta `ManagementUiApi`

```python
@runtime_checkable
class ManagementUiApi(Protocol):
    """Superfície HTTP+static de gestão e busca.

    Responsabilidade
        Expor FastAPI com listagem, indexação sob demanda, progresso,
        histórico de falhas, cron e buscas — sem CRUD de config/token.

    Motivo da separação
        Isola ENG-001/BR-017 da orquestração e dos índices (ENG-007).
    """

    def build(self) -> FastAPI:
        """Monta a aplicação ASGI pronta para servir.

        Responsabilidade: registrar rotas /api e static.
        Motivo da separação: composition root vs handlers.
        """
        ...
```

## 6. `DefaultManagementUiApi`

```python
class DefaultManagementUiApi:
    def __init__(
        self,
        *,
        catalog: CatalogRepository,
        orchestrator: IndexingOrchestrator,
        scheduler: DailyScheduler,
        query: QueryService,
        drain_on_index: bool = True,
        web_root: Path | None = None,
    ) -> None: ...
```

- **Responsabilidade:** composition default da UI.
- **Motivo da separação:** testável com fakes; T19 injeta concretos.
- **`web_root`:** default = pacote `web/` resolvido relativo ao repo/package.

## 7. Rotas canônicas

| Método | Path | Corpo / query | Resposta |
|---|---|---|---|
| GET | `/api/repos` | — | `{ "repos": [ RepoView, ... ] }` |
| GET | `/api/repos/{repository_id}` | — | `RepoDetailView` |
| GET | `/api/repos/{repository_id}/executions` | — | `{ "executions": [ ExecutionView, ... ] }` |
| POST | `/api/repos/index` | `{ "repository_ids": int[] }` | 202 `{ "repos": [...] }` |
| GET | `/api/scheduler/cron` | — | `{ "cron": str }` |
| PUT | `/api/scheduler/cron` | `{ "cron": str }` | `{ "cron": str }` |
| POST | `/api/search/exact` | `{ "pattern": str, "repo_key"?: str, ... }` | `{ "hits": [...] }` |
| POST | `/api/search/semantic` | `{ "query": str, "reformulate"?: bool, ... }` | `{ "hits": [...] }` |

### 7.1 Views (JSON)

```python
# RepoView
{
  "id": int,
  "connection_name": str,
  "origin": "github" | "local",
  "repo_identifier": str,
  "state": str,           # slug
  "state_label": str,     # PT
  "progress": null | {
    "percent": int | null,
    "files_processed": int | null,
    "files_total": int | null,
    "current_stage": str | null,
  }
}

# RepoDetailView = RepoView +
{
  "files": [
    {
      "path": str,
      "zoekt": bool,
      "tree_sitter": bool,
      "metadata_persisted": bool,
    }
  ],
  "current_execution_id": int | null,
}

# ExecutionView
{
  "id": int,
  "status": str,
  "started_at": str (ISO),
  "finished_at": str | null,
  "error_message": str | null,
  "error_at": str | null (ISO),
  "commit_target": str | null,
}
```

## 8. Proibições (I-T18-006)

Não declarar nem registrar:

- `/api/connections*`
- `/api/config*`
- `/api/token*`
- qualquer mutação de definição de repo fora do catálogo SoT (enqueue não é CRUD de config)

## 9. ENG-013 / BDD-024 por módulo

| Módulo | Permitido | Proibido |
|---|---|---|
| `ports.py`, `labels.py`, `serialize.py`, `errors.py` | typing/stdlib/domínio | fastapi, httpx |
| `app.py`, `api.py` | fastapi, starlette | servidor HTTP caseiro |
| `web/*` | HTML/JS fetch | frameworks backend |

## 10. Handoff

| Consumidor | Uso |
|---|---|
| T19 | `DefaultManagementUiApi(...).build()` + uvicorn |
| Testes | TestClient + fakes |

Mudança de assinatura da porta ou adição de CRUD de config ⇒ `SCOPE_CHANGE_REQUIRED`.
