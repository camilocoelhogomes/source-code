# Unit Test Plan — T16-query-services

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T16-query-services` |
| Autor | QA / Implementation Task Runner |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Interfaces | `0.1.0` |
| Cobertura alvo | ≥95% em `github_rag.query` e gate global |

## 1. Estratégia

| Camada | Arquivo | Doubles |
|---|---|---|
| BDD serviço | `tests/bdd/test_query_services.py` | FakeExactCodeIndex, InMemoryCatalogRepository, fakes T16 |
| Unit projection | `tests/unit/query/test_projection.py` | ExactMatch / SemanticHit sintéticos |
| Unit service | `tests/unit/query/test_service.py` | DefaultQueryService + fakes |
| Unit resolve | `tests/unit/query/test_resolve.py` | FakeSnapshotSourceResolver / CatalogEntry |
| Conformidade | BDD QS-05 + AST/import | sem qdrant_client/openai/httpx/git/PyGithub |

## 2. Matriz unitária

| ID | Cenário | Esperado | BDD / contrato |
|---|---|---|---|
| UT-P01..P05 | Projection matriz DetailFields | campos None ou preenchidos | QS-03/04; I-T16-003/011 |
| UT-V01 | exact pattern whitespace | hits vazios | QS-12; I-T16-009 |
| UT-V02 | semantic query vazia | QueryValidationError | QS-12 |
| UT-V03 | browse sem escopo | QueryValidationError | I-T16-012 |
| UT-V04 | repo_key + id conflitantes | QueryValidationError | I-T16-012 |
| UT-V05 | path read vazio | QueryValidationError | I-T16-012 |
| UT-R01..R03 | repo missing/inactive | QueryRepositoryNotFoundError | QS-10 |
| UT-C01..C02 | browse commit | QueryCommitUnavailableError / OK | QS-11 |
| UT-E01..E05 | backend/reformulator fail | erros tipados + __cause__ | QS-08 |
| UT-F01..F03 | reformulate no-op / call | BR-011 | QS-09 |
| UT-S01..S06 | happy paths exact/semantic/browse | QueryHits / FileContent / Tree | QS-01/02/06/07 |
| UT-X01 | imports proibidos | AST limpo | QS-05; I-T16-014 |
| UT-Z01..Z02 | FakeQueryService / resolve | Protocol | I-T16-015/010 |

## 3. Demonstração red (TDD)

Suíte nova falha sem implementação; após `DefaultQueryService` + projection: verde + cobertura ≥95%.

## 4. Architect Review

| Decisão | Status | Autor | Data |
|---|---|---|---|
| APPROVED_BY_ARCHITECT | aprovado | tech-lead-architect | 2026-07-18 |
