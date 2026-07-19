# Unit test plan — T18-management-ui

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T18-management-ui` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design / BDD / Interfaces | `0.1.0` |

## 0. Histórico Architect

| Data | Autor | Decisão | Observações |
|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | Plano cobre contratos, extremos, proibições CRUD e FastAPI. |

## 1. Arquivos

| Suíte | Path | Doubles |
|---|---|---|
| BDD | `tests/bdd/test_management_ui.py` | InMemoryCatalog, SpyOrchestrator, DailyScheduler+InMemory store, FakeQueryService |
| Unit labels | `tests/unit/ui/test_labels.py` | — |
| Unit serialize | `tests/unit/ui/test_serialize.py` | CatalogEntry fixtures |
| Unit API | `tests/unit/ui/test_api.py` | TestClient + spies |
| Unit imports | `tests/unit/ui/test_imports.py` | AST |

## 2. Casos unitários

| ID | Caso | Esperado |
|---|---|---|
| UT-L01 | Todos `RepoState` têm label PT distinto | bijective vs REQ-020 |
| UT-L02 | Label desconhecido → KeyError/ValueError explícito | não silencia |
| UT-S01 | serialize repo github/local | origin + state_label |
| UT-S02 | progress None | `progress: null` |
| UT-S03 | file flags False quando timestamps None | booleans |
| UT-S04 | execution failed com message/at | ISO strings |
| UT-A01 | GET /api/repos vazio | `repos: []` |
| UT-A02 | index ids vazios → 422 | validation |
| UT-A03 | index id inexistente → 404 | sem enqueue |
| UT-A04 | cron inválido → 400; store intacto | InvalidCronExpressionError |
| UT-A05 | semantic omite reformulate → False | spy request |
| UT-A06 | exact com pattern vazio → 422 | |
| UT-A07 | OpenAPI sem paths connections/token | BDD-023 |
| UT-A08 | drain_on_index=False não chama run_until_idle | spy |
| UT-I01 | ports/labels/serialize sem import fastapi | ENG-013 |
| UT-I02 | app/api importam fastapi | BDD-024 |
| UT-I03 | pacote ui sem urllib/requests server caseiro | |

## 3. Demonstração red

Antes da implementação: `ImportError` / `AttributeError` em `github_rag.ui.*` e falha de TestClient.

## 4. Cobertura

Gate global ≥95%; código novo em `github_rag.ui` coberto pelos testes acima + BDD.
