# Interfaces — T35-fix-e2e-indexing-zoekt-wrapper-and-boot-race

| Estado | `APPROVED_BY_ARCHITECT` |

## `exec_zoekt_index_cli` (zoekt_bin.py)

Sem mudança de assinatura. Comportamento: mkdir container, cp com timeout,
exec com timeout, cleanup best-effort.

## `DefaultStartupIndexReconcile.__init__`

```python
def __init__(
    self,
    *,
    catalog: CatalogRepository,
    snapshot: MainSnapshotProvider,
    orchestrator: IndexingOrchestrator,
    github_token: str | None = None,
    defer_enqueue: bool = False,
) -> None:
```

Responsabilidade: `defer_enqueue=True` pula chamadas a `orchestrator.enqueue`
após tip/reconcile — evita corrida com Robot e2e.

Motivo: política e2e isolada do domínio; wiring lê `E2E_DEFER_STARTUP_INDEX`.

## `DefaultIndexingOrchestrator.enqueue`

Contrato ampliado (docstring): aceita repos em `indexing` — adiciona à fila
interna sem transição de estado (re-enqueue de job preso).

## `build_host_delivery_env` / launcher

Launcher passa `extra={"E2E_DEFER_STARTUP_INDEX": "1"}` quando compose e2e.
