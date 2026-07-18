# Reviews — T16-query-services

## Review — Design (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Escopo T16 (fachada QueryService; sem MCP/UI/indexação) | OK | §1, §16, D-T16-009/010 |
| ENG-007 / BR-023 / BDD-024 — só portas T10/T13/T08/T07 | OK | §3, §4.7, D-T16-002 |
| BDD-009 exact / BDD-010 semantic | OK | §4.5, §4.8, §15 |
| BDD-012 / REQ-030 — DetailFields + projection | OK | §4.2, §4.9, D-T16-003 |
| BR-011 — semantic sem prosa SLM; reformulador ≠ evidência | OK | §4.6, D-T16-006 |
| REQ-027 — QueryReformulator opcional; D-T16-007 no-op | OK | §4.6, D-T16-007 |
| Browse default last_processed_commit | OK | §4.3, D-T16-005 |
| Erros tipados por família | OK | §6, D-T16-008 |
| SnapshotSourceResolver + BR-008 | OK | §4.7, D-T16-011 |
| Handoff T17/T18 | OK | §17 |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING`, `MAJOR` ou `SUGGESTION` | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.0. Prosseguir para BDD e interfaces.

---

## Review — BDD (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário; aprovação Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| BDD-009 — search_exact → ExactCodeIndex | OK | QS-01 |
| BDD-010 — semantic Embedder+VectorStore; sem prosa SLM | OK | QS-02 |
| BDD-012 — omissão/inclusão DetailFields | OK | QS-03, QS-04 |
| BDD-024 — sem client paralelo em query/ | OK | QS-05 |
| Browse read_file / list_tree + last_processed_commit | OK | QS-06, QS-07 |
| Erros tipados + __cause__ + sem segredo | OK | QS-08 |
| Reformulator no-op / só texto | OK | QS-09 |
| Repo ausente/inativo | OK | QS-10 |
| Commit unavailable | OK | QS-11 |
| Pattern vazio vs query semântica vazia | OK | QS-12 |
| Fixtures fakes; sem Zoekt/Qdrant reais | OK | § Fixtures |
| Alinhamento design §4 / D-T16-* | OK | rastreabilidade por cenário |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `SUGGESTION` | Validação de browse sem `repo_key`/`repository_id` e conflito entre ambos (§4.3) não tem cenário BDD dedicado | design §4.3; bdd QS-* | Cobrir em unitários de validação (não bloqueia QS-01..12) | Aceito — unit QA |
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — bdd.md v0.1.0 alinhado ao design APPROVED. Prosseguir para interfaces.

---

## Review — Interfaces (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário; aprovação Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| DetailFields + requests/results frozen | OK | §3.1–3.7; I-T16-003/004/016 |
| QueryService 4 métodos | OK | §3.9; I-T16-002 |
| QueryReformulator + no-op D-T16-007 | OK | §3.10; I-T16-006/007 |
| SnapshotSourceResolver | OK | §3.11; I-T16-010 |
| Hierarquia QueryError | OK | §3.8; I-T16-008/013 |
| DefaultQueryService construtor keyword-only | OK | §3.13 |
| project_exact / project_semantic | OK | §3.12; I-T16-011 |
| Fakes de apoio + FakeQueryService | OK | §3.14; I-T16-015 |
| Mapeamento I-T16 ↔ D-T16 ↔ QS-* | OK | §5 |
| Comentários responsabilidade/motivo em cada contrato | OK | §3.* |
| Sem alteração de contratos T07/T08/T10/T13 | OK | §1 dependências externas |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING`, `MAJOR` ou `SUGGESTION` | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces.md v0.1.0 congelado. Prosseguir para unitários (QA) e implementação (Developer).

---

## Review consolidado — design + BDD + interfaces

| Artefato | Versão | Resultado | Data |
|---|---|---|---|
| `design.md` | `0.1.0` | `APPROVED_BY_ARCHITECT` | 2026-07-18 |
| `bdd.md` | `0.1.0` | `APPROVED_BY_ARCHITECT` | 2026-07-18 |
| `interfaces.md` | `0.1.0` | `APPROVED_BY_ARCHITECT` | 2026-07-18 |

Achados `BLOCKING`/`MAJOR` abertos: nenhum.

---

## Review — Implementação (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `src/github_rag/query/*` + testes T16 |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário; aprovação Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| `DefaultQueryService` keyword-only + deps I-T16-002/013 | OK | `service.py` L51–68 |
| `search_exact` → ExactCodeIndex + projection; pattern blank → `()` | OK | `service.py` L70–95; QS-01/12 |
| `search_semantic` → Embedder+VectorStore; reformulate no-op I-T16-007 | OK | `service.py` L97–140; QS-02/09 |
| Projeção BDD-012 (`None` quando flag False) | OK | `projection.py` L17–41; QS-03/04 |
| Browse `last_processed_commit` / `QueryCommitUnavailableError` | OK | `resolve.py` L75–87; `service.py` L142–199; QS-06/07/11 |
| Escopo repo: conflito / ausente / inativo | OK | `resolve.py` L22–72; QS-10; UT-V03/V04 |
| Erros tipados + `__cause__` (exact/vector/embed/snapshot/reformulator) | OK | `service.py` L91–92, L113–135, L160–161; QS-08 |
| Sem client paralelo (I-T16-014 / QS-05) | OK | AST BDD; imports só portas/domínio |
| Fakes I-T16-015 | OK | `fake.py`; BDD/unit |
| Cobertura pacote `query` ≥95% | OK | query 98–100%; suíte 767 passed / 98.86% |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `SUGGESTION` | `__init__.py` não reexporta `project_exact` / `project_semantic` listados em interfaces §4 | `query/__init__.py` L10–62 vs `interfaces.md` §4 | Reexport opcional no `__init__` (import direto de `projection` já funciona) | Aceito — não bloqueia T17/T18 |
| `SUGGESTION` | `TestCoverageCorners` declarado após `if __name__ == "__main__"` | `tests/unit/query/test_service.py` L248+ | Mover classe acima do bloco main (pytest já coleta) | Aceito — cosmético |
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — implementação aderente a design/interfaces/BDD; sem correção de código nesta review. Prosseguir Blue.

---

## Review consolidado — implementação + Blue

| Artefato | Versão | Resultado | Data |
|---|---|---|---|
| Implementação `github_rag.query` | `0.1.0` | `APPROVED_BY_ARCHITECT` | 2026-07-18 |
| Blue / `refactoring.md` | `0.1.0` | `BLUE_APPROVED_BY_ARCHITECT` | 2026-07-18 |

Achados `BLOCKING`/`MAJOR` abertos: nenhum.
