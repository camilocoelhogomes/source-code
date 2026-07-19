# Interfaces — T14-indexing-orchestrator

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T14-indexing-orchestrator` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.2` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T14-indexing-orchestrator` |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Portas + semântica alinhadas ao design/BDD |

## 1. Escopo

| Contrato | Módulo | Papel |
|---|---|---|
| Erros tipados | `indexing/errors.py` | Falhas do orquestrador |
| `to_vector_metadata` | `indexing/types.py` | Map T12→T13 |
| `compute_progress_percent` | `indexing/progress.py` | % puro |
| `IndexingOrchestrator` / `StartupIndexReconcile` | `indexing/ports.py` | Portas públicas |
| `FileRagPipeline` / `DefaultFileRagPipeline` | `indexing/pipeline.py` | RAG por arquivo |
| `DefaultIndexingOrchestrator` | `indexing/orchestrator.py` | Fila + index |
| `DefaultStartupIndexReconcile` | `indexing/startup_reconcile.py` | ENG-011 |

## 2. Decisões

| ID | Decisão |
|---|---|
| I-T14-001 | Portas Orchestrator e StartupReconcile distintas |
| I-T14-002 | API: `enqueue`, `run_until_idle`, `index_repository` |
| I-T14-003 | `repo_id` = `str(catalog id)` |
| I-T14-004 | Zoekt: 1× `index(all_eligible)` por execução |
| I-T14-005 | Qdrant incremental: `delete_paths`+`upsert`; sem `purge_other_commits` |
| I-T14-006 | Restart: `delete_repository` **e** `delete_repo` + rebuild |
| I-T14-007 | `FileRagPipeline` separado |
| I-T14-008 | Construtores keyword-only com portas |
| I-T14-009 | Token GitHub opcional; nunca em erros |
| I-T14-010 | Pacote sem imports SDK (ENG-013) |

## 3. Portas

### `IndexingOrchestrator`

```python
class IndexingOrchestrator(Protocol):
    def enqueue(self, repository_ids: Sequence[int]) -> None: ...
    def run_until_idle(self) -> None: ...
    def index_repository(self, repository_id: int) -> None: ...
```

- **Responsabilidade:** fila, estados REQ-020, pipeline, BR-005.
- **Motivo da separação:** único dono da indexação; não faz reconcile de boot.

### `StartupIndexReconcile`

```python
class StartupIndexReconcile(Protocol):
    def run(self) -> None: ...
```

- **Responsabilidade:** tip × processado, recover órfãos, enqueue (ENG-011).
- **Motivo da separação:** T07 sync-only; T19 chama após sync.

### `FileRagPipeline`

```python
class FileRagPipeline(Protocol):
    def process_file(self, *, path: str, content: bytes) -> tuple[VectorRecord, ...]: ...
```

- **Responsabilidade:** TS → SLM → embed → records.
- **Motivo da separação:** testável sem fila/Zoekt.

### `DefaultIndexingOrchestrator` deps

`catalog`, `snapshot`, `eligibility`, `exact_index`, `rag_pipeline`, `vector_store`, `limiter`, `github_token=None`.

### `DefaultStartupIndexReconcile` deps

`catalog`, `snapshot`, `orchestrator`, `github_token=None`.

## 4. ENG-013

Permitido: portas/DTOs `catalog`, `concurrency`, `snapshot`, `eligibility`, `index.*`.  
Proibido: `github`, `git`, `tree_sitter`, `openai`, `qdrant_client`, `pathspec`.
