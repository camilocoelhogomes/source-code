# Plano de testes unitários — T05-github-discovery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T05-github-discovery` |
| Autor | Implementation Task Runner (QA step) |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Interfaces base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |

## Artefatos

| Artefato | Caminho |
|---|---|
| Wildcard | `tests/unit/sources/github/test_wildcard.py` |
| Discovery | `tests/unit/sources/github/test_discovery.py` |
| Client (contrato) | `tests/unit/sources/github/test_client.py` |

## Matriz

| ID | Foco | Entrada | Esperado | Rastreabilidade |
|---|---|---|---|---|
| UT-W01 | prefixo | `my-org/foo-bar`, `my-org/foo-*` | True | BR-022 |
| UT-W02 | sufixo | `my-org/bar-api`, `my-org/*-api` | True | BR-022 |
| UT-W03 | exato | match exato | True | BR-022 |
| UT-W04 | org errada | org diferente | False | BR-022 |
| UT-W05 | `org/*` | qualquer repo da org | True | BR-022 |
| UT-W06 | sem match | nomes distintos | False | BR-022 |
| UT-W07 | padrão malformado | sem `/` | False | corner |
| UT-D01 | filtro inclusão | vários repos API | só matching | BDD-001 |
| UT-D02 | repos vazio | API com dados | tuple vazia | GH-04 |
| UT-D03 | dedup multi-org | mesmo full_name 2x | uma entrada | corner |
| UT-D04 | ordenação | unsorted input | sorted full_name | determinismo |
| UT-D05 | token ausente resultado | discover ok | secret not in repr | BDD-019 |
| UT-D06 | erro auth | client 401 | GitHubDiscoveryError, no leak | BDD-014 |
| UT-D07 | multi-org | 2 orgs | união filtrada | REQ-010 |
| UT-C01 | parse JSON page | mock HTTP 200 | repos parsed | contrato |
| UT-C02 | paginação | 2 páginas | all repos | GH-06 |
| UT-C03 | 401 HTTP | status 401 | error sem token | BDD-014 |

## Red esperado

Testes importam módulos `github_rag.sources.github.*` — falham com `ImportError` ou asserções até implementação TDD.
