# Interfaces — T31 fix-healthz-static-mount-order

| Campo | Valor |
|---|---|
| Task | `T31-fix-healthz-static-mount-order` |
| Estado | `APPROVED_BY_ARCHITECT` |

## I-T31-001 — `create_app` com health opcional antes do static

```python
def create_app(
    *,
    catalog: CatalogRepository,
    orchestrator: IndexingOrchestrator,
    scheduler: DailyScheduler,
    query: QueryService,
    drain_on_index: bool,
    web_root: Path,
    issue_store: CatalogIssueStore | None = None,
    get_state: Callable[[], Any] | None = None,
) -> FastAPI:
    """Monta FastAPI com rotas da Management UI.

    Responsabilidade: único lugar de registro de rotas /api e ordem de mount.
    Motivo da separação: quando ``get_state`` é fornecido (T31), registra
    ``/healthz`` antes do ``StaticFiles`` em ``/`` para não ser interceptado
    (I-T19-007 / F-W1-001).
    """
```

## I-T31-002 — `DefaultManagementUiApi.build` propaga `get_state`

```python
def build(
    self,
    *,
    get_state: Callable[[], Any] | None = None,
) -> FastAPI:
    """Monta a aplicação ASGI (I-T18-001).

    Responsabilidade: delegar a ``create_app``; ``get_state`` opcional para
    probe de entrega T19/T31 antes do mount estático.
    Motivo da separação: composition root (runtime) injeta readiness sem
    alterar contratos /api da T18.
    """
```

## I-T31-003 — `wire_ui_app` retorna builder

```python
def wire_ui_app(...) -> DefaultManagementUiApi:
    """``DefaultManagementUiApi(...)`` — builder, não FastAPI built.

    Responsabilidade: compor deps UI; ``build()`` ocorre em
    ``_materialize_surfaces`` com ``get_state`` do runtime.
    Motivo da separação: permite registrar ``/healthz`` na ordem correta
    (I-T19-013 / T31).
    """
```
