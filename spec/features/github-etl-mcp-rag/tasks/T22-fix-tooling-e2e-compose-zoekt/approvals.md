# Aprovações — T22-fix-tooling-e2e-compose-zoekt

| Gate | Artefato | Decisão | Autor | Data | Observações |
|---|---|---|---|---|---|
| ARCHITECT_DESIGN | design.md `0.1.0` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-19 | Fix tooling e2e: D-T22-001..008; F-T04-001/002/003; alinhamento 3 composes; modo autônomo (sem HITL intermediário). |
| ARCHITECT_BDD | bdd.md `0.1.0` + `tests/bdd/test_e2e_compose_zoekt_fix.py` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-19 | EZ-01..EZ-05; F-T04-001/002/003; padrão T19; sem Robot/compose up; SUGGESTION residual parser YAML multilinha. Modo autônomo. |
| ARCHITECT_INTERFACES | interfaces.md `0.1.0` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-19 | I-T22-001..009; M-T22-001..007 + M-T22-010..014; sem Protocols novos; reuso T21; helpers só em tests/. Modo autônomo. |
| ARCHITECT_UNIT_TESTS | unit-test-plan.md `0.1.0` + `tests/unit/delivery/test_zoekt_compose_manifest.py` + `tests/support/compose_manifest.py` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-19 | UT-Z01..Z22; contratos/extremos/secrets; helper só tests/; RED 4f/16p; sem enfraquecer BDD. Modo autônomo. |
| ARCHITECT_IMPLEMENTATION | 3 composes + `e2e/README.md` + `docs/runbook-local.md` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-19 | D-T22-001/002/004; M-T22-001..007/010..014; sem secrets; sem Robot/domínio; subset T22 35 passed. Modo autônomo. |
| ARCHITECT_BLUE | `refactoring.md` + limpeza `tests/support/compose_manifest.py` | `BLUE_APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-19 | Baseline 35 passed / 16 subtests / 0.04s; simplificação estrutural produção N/A; Blue mínima: remove `canonical_argv_present` morto. Modo autônomo. |
| ARCHITECT_DOCS | `CHANGELOG.md` + docs T22 (e2e/README + runbook já em implementação) | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-19 | Entrada T22 em `[Unreleased]`/Alterado; M-T22-010..014 já materializados; cobertura suite **1215 passed, 2 skipped, TOTAL 96.53%** (≥95%). Modo autônomo. |
