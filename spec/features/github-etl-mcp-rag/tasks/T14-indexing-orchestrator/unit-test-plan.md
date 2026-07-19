# Unit test plan — T14-indexing-orchestrator

| Campo | Valor |
|---|---|
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Interfaces | `0.1.0` APPROVED |
| BDD | `0.1.0` APPROVED |
| Data aprovação Architect | 2026-07-18 |

## Cobertura planejada

| Área | Cenários extremos |
|---|---|
| `compute_progress_percent` | total 0, negativo, clamp 100, mid |
| `to_vector_metadata` | mapeia summary/keywords/symbols; ignora intent/extra |
| `FileRagPipeline` | chunks vazios; sucesso; falha SLM → IndexingPipelineError |
| `snapshot_source_for` | local ok; github sem token; github com token |
| Orchestrator | skip up_to_date; dedupe enqueue; first-index replace; incremental delete_paths; falha+restart wipe; gitignore root |
| Startup reconcile | stale enqueue; orphan indexing/queued |
| ENG-013 | AST sem SDKs |

## Artefatos

- `tests/unit/indexing/`
- `tests/bdd/test_indexing_orchestrator.py`
