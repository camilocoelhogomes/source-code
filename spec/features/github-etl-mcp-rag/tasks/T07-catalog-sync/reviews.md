# Reviews — T07-catalog-sync

## Gate DESIGN — 2026-07-18

| Campo | Valor |
|---|---|
| Artefato | `design.md` v0.1.0 |
| Reviewer | Tech Lead Architect |
| Decisão | `APPROVED_BY_ARCHITECT` |

### Checklist

| # | Critério | Resultado |
|---|---|---|
| 1 | Sync-only; não indexa; sem ENG-011 neste escopo | OK |
| 2 | Soft-delete via T03 (`upsert`/`deactivate`/`list_active`); sem estado `indisponível` | OK |
| 3 | Estados somente REQ-020 | OK |
| 4 | Handoff reconcile → T14 | OK |
| 5 | Rastreabilidade BDD-001/016/021/023; REQ-035; BR-001/016/017 | OK |
| 6 | Coerência com T03/T05/T06 | OK |

### Achados

| ID | Severidade | Evidência | Correção esperada | Resultado |
|---|---|---|---|---|
| S-01 | SUGGESTION | `design.md` L60–68 vs L87 | Em interfaces/BDD: `GitHubDiscoveryError` aborta antes de qualquer `upsert`/`deactivate` nesta execução | Aberto → próximo gate |
| S-02 | SUGGESTION | `design.md` L52–55 | Em `interfaces.md`: mapear `RepoOrigin` e `LocalDiscoveryResult.repos`/`issues` | Aberto → próximo gate |

### Parecer

Gate DESIGN v0.1.0: sync-only (sem indexação/ENG-011); soft-delete via T03 (`upsert`/`deactivate`/`list_active`); BDD-001/016/021/023 + REQ-035/020 + BR-001/016/017 rastreados. Sem BLOCKING/MAJOR; S-01/S-02 em `reviews.md`.

## Gate BDD — 2026-07-18

| Campo | Valor |
|---|---|
| Artefato | `bdd.md` v0.1.0 |
| Reviewer | Tech Lead Architect |
| Decisão | `APPROVED_BY_ARCHITECT` |

### Checklist

| # | Critério | Resultado |
|---|---|---|
| 1 | BDD-001/016/021/023 cobertos (CS-01..04) | OK |
| 2 | Ausência/soft-delete + sem `indisponível` (CS-05, CS-12) | OK |
| 3 | Preservação estado/commit + reativação (CS-06, CS-07) | OK |
| 4 | Sem indexação/reconcile (CS-10); sem overscape UI | OK |
| 5 | S-01: `GitHubDiscoveryError` aborta antes de qualquer upsert/deactivate (CS-08) | OK |
| 6 | Issues locais não abortam; config vazia; estados REQ-020 (CS-09, CS-11, CS-12) | OK |

### Achados

| ID | Severidade | Evidência | Correção esperada | Resultado |
|---|---|---|---|---|
| S-01 | SUGGESTION | Gate DESIGN → CS-08 | Abort antes de qualquer `upsert`/`deactivate` nesta execução | **Resolvido** em CS-08 |
| — | — | — | Sem BLOCKING/MAJOR abertos | — |

### Parecer

Gate BDD v0.1.0: cenários CS-01..12 cobrem aceite, política de ausência, preservação, S-01 e exclusão de indexação/UI/reconcile. Sem BLOCKING/MAJOR. `APPROVED_BY_ARCHITECT`.

## Gate INTERFACES — 2026-07-18

| Campo | Valor |
|---|---|
| Artefato | `interfaces.md` v0.1.0 |
| Reviewer | Tech Lead Architect |
| Decisão | `APPROVED_BY_ARCHITECT` |

### Checklist

| # | Critério | Resultado |
|---|---|---|
| 1 | `CatalogSync` injeta discoveries + `CatalogRepository` | OK (`I-T07-001`, §3.3) |
| 2 | Comentários de responsabilidade e motivo da separação em cada contrato | OK (§3.1–3.4) |
| 3 | S-01: abort sem `upsert`/`deactivate` em `GitHubDiscoveryError` | OK (`I-T07-007`, algoritmo passo 1) |
| 4 | S-02: mapeamento GitHub/local → `upsert_repository` + `local_issues` | OK (§4; `I-T07-004`..006) |
| 5 | Sem CRUD de definições; sem indexação/reconcile | OK (§1, §5; `I-T07-009`) |
| 6 | Compatível com contratos T02/T03/T05/T06 | OK (§6; assinaturas alinhadas a `repository.py` / discoveries) |

### Achados

| ID | Severidade | Evidência | Correção esperada | Resultado |
|---|---|---|---|---|
| S-01 | SUGGESTION | Gate DESIGN → `interfaces.md` `I-T07-007` / algoritmo passo 1 | Abort antes de qualquer mutação nesta execução | **Resolvido** |
| S-02 | SUGGESTION | Gate DESIGN → `interfaces.md` §4 | Mapear `RepoOrigin` e `LocalDiscoveryResult.repos`/`issues` | **Resolvido** |
| — | — | — | Sem BLOCKING/MAJOR abertos | — |

### Parecer

Gate INTERFACES v0.1.0: superfície sync-only com DI hexagonal; S-01/S-02 fechados; sem CRUD/reconcile/indexação. Sem BLOCKING/MAJOR. `APPROVED_BY_ARCHITECT`.
