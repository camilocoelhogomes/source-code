# Interfaces — T25-gap-negative-integral

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T25-gap-negative-integral` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Rastreabilidade | design D-T25-001..005; BDD NEG-01..03 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` |

## 1. Contratos (I-T25-*)

| ID | Contrato | Motivo | Cenário |
|---|---|---|---|
| I-T25-001 | `CatalogIssueStore` porta `replace` / `list_issues` | Separar handoff sync→UI da rota HTTP | NEG-02 |
| I-T25-002 | `InMemoryCatalogIssueStore` default | Implementação testável sem I/O | NEG-02 |
| I-T25-003 | `GET /api/catalog/issues` JSON estável | Superfície UI API observável BDD-018 | NEG-02 |
| I-T25-004 | `create_app` / `DefaultManagementUiApi` aceitam `issue_store` opcional | Extensão backward-compatible T18 | NEG-02 |
| I-T25-005 | `wire_ui_app(..., issue_store=)` | Composition delivery passa store | NEG-02 |
| I-T25-006 | Runtime popula store após `run_catalog_sync` | Ordem wire-antes-sync | NEG-02 |
| I-T25-007 | `NegativeIntegralProbes` (módulo e2e) `run_bdd008` / `run_bdd022` | Indução Robot sem Podman fault-inject | NEG-01/03 |
| I-T25-008 | Probes e APIs nunca ecoam token | BR-008 / BDD-014 | todos |

## 2. `CatalogIssueStore`

```python
class CatalogIssueStore(Protocol):
    """Porta de issues locais do último sync (BDD-018).

    Responsabilidade
        Expor e atualizar o snapshot de ``LocalDiscoveryIssue`` observável
        pela Management UI após o bootstrap/sync do catálogo.

    Motivo da separação
        O sync (T07) produz ``CatalogSyncResult.local_issues`` antes da UI
        ser materializada ou em momento distinto do wire; a porta mutável
        desacopla ordem de boot (D-T25-001) da serialização HTTP e evita
        acoplar rotas FastAPI ao ``CatalogSync`` concreto.
    """

    def replace(self, issues: Sequence[LocalDiscoveryIssue]) -> None: ...
    def list_issues(self) -> tuple[LocalDiscoveryIssue, ...]: ...
```

### `InMemoryCatalogIssueStore`

```python
@dataclass
class InMemoryCatalogIssueStore:
    """Store default em memória para issues locais.

    Responsabilidade
        Implementar ``CatalogIssueStore`` com snapshot imutável por
        ``replace`` (tuple interna).

    Motivo da separação
        Persistência de issues de volume não é requisito de catálogo PG
        (T03); in-memory basta para bootstrap + UI do MVP e testes.
    """
```

## 3. Serialização / rota

```python
def issue_to_view(issue: LocalDiscoveryIssue) -> dict[str, str]:
    """LocalDiscoveryIssue → JSON UI.

    Responsabilidade: projetar connection_name/path/message sem extras.
    Motivo da separação: serialize ≠ store ≠ discovery.
    """

# Em create_app:
# GET /api/catalog/issues → {"issues": [issue_to_view(...), ...]}
```

Assinatura estendida (default seguro):

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
) -> FastAPI: ...
```

`issue_store is None` → store vazio interno (compat T18).

## 4. Delivery wire

```python
def wire_ui_app(
    *,
    catalog: Any,
    orchestrator: Any,
    scheduler: Any,
    query: Any,
    issue_store: Any | None = None,
) -> Any:
    """Composition UI; propaga issue_store (I-T25-005)."""
```

`DefaultContainerRuntime.boot` (trecho):

1. `_ensure_wired` cria `self._issue_store = InMemoryCatalogIssueStore()` se ausente e passa a `wire_ui_app`.
2. `result = run_catalog_sync(config, self._sync)`.
3. `self._issue_store.replace(result.local_issues)`.

## 5. `NegativeIntegralProbes` (e2e)

```python
# github_rag/e2e/negative_probes.py

def run_bdd008_partial_failure_probe() -> int:
    """Indução controlada BDD-008 via UI TestClient + orquestrador.

    Responsabilidade
        Reproduzir falha parcial → histórico → reindex total; exit 0 se
        todos os asserts passarem, senão 1. Sem imprimir secrets.

    Motivo da separação
        Robot green path precisa de evidência integral sem fault-inject
        no compose vivo (D-T25-002); o probe isola indução determinística
        do launcher Podman.
    """

def run_bdd022_config_path_probe() -> int:
    """Boot com CONFIG_PATH inválido; exit 0 se fail-fast sem parcial/leak.

    Responsabilidade
        Exercitar ``DefaultContainerRuntime.boot`` com path inválido e
        token no env; validar SystemExit(1), sync/reconcile/bind=0 e
        ausência do valor do token na saída capturada.

    Motivo da separação
        Separar prova Robot de CONFIG_PATH (texto BDD-022) dos casos de
        payload de index (regressão NEG-04 / D-T25-003).
    """

def main(argv: Sequence[str] | None = None) -> int:
    """CLI ``python -m github_rag.e2e.negative_probes <bdd008|bdd022>``."""
```

## 6. Dependências e não-objetivos

- Reutiliza `LocalDiscoveryIssue`, `CatalogSync`, IO-07 doubles, CD-03 helpers.
- Não adiciona CRUD de conexões; não altera contrato MCP.
- Não exige browser (T23).
