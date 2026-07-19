# Aprovações — T19-container-delivery

| Gate | Artefato | Decisão | Autor | Data | Observações |
|---|---|---|---|---|---|
| ARCHITECT_DESIGN | design.md `0.1.0` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | Composition root `delivery`; Dockerfile+compose; boot ENG-011; amd64; BDD-020/024. |
| ARCHITECT_BDD | bdd.md `0.1.1` + `tests/bdd/test_container_delivery.py` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | MAJOR CD-03/04/05 corrigidos na review; BDD-020/021/022/024 + ENG-011/D-T19-003. |
| ARCHITECT_INTERFACES | interfaces.md `0.1.0` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | `ContainerRuntime` / `run_container_boot` / wiring / health / `__main__` / mcp_stdio; manifesto M-T19-*; I-T19-001..020. |
| ARCHITECT_UNIT_TESTS | unit-test-plan.md `0.1.1` + `tests/unit/delivery/**` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | MAJOR wait/secret/skip_infra/patches/scheduler/URL/mcp_stdio/health pré-boot corrigidos na review. |
| ARCHITECT_IMPLEMENTATION | `src/github_rag/delivery/**` + Dockerfile/compose/env/runbook | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | BLOCKING binds sequenciais + MAJOR drain background corrigidos; diff unit = cobertura adicional. |
| ARCHITECT_BLUE | refactoring.md | `BLUE_APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | N/A simplificação (estrutura mínima); baseline 1010 passed / 96.38% cov. |
| ARCHITECT_DESIGN | design.md `0.2.0` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | Delta REQ-043: D-T19-020 três composes; gate manifesto-only REQ-044. |
| ARCHITECT_BDD | bdd.md `0.2.0` + CD-11 | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | Alias `E2E_GITHUB_TOKEN`→`GITHUB_TOKEN` assertado; MAJOR fechado. |
| ARCHITECT_INTERFACES | interfaces.md `0.2.0` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | Residual M-T19-007..009 + CD-11; sem Protocols novos. |
| ARCHITECT_UNIT_TESTS | unit-test-plan `0.2.0` + UT-M07/08/09 | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | Fórmula alias em UT-M07; MAJOR fechado. |
| ARCHITECT_IMPLEMENTATION | composes + `.env.example` + docs (delta 0.2.0) | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | Manifesto D-T19-020; Python delivery inalterado; 1021 passed / 96.59% cov. |
| ARCHITECT_BLUE | refactoring.md (pós-delta 0.2.0) | `BLUE_APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | N/A no manifesto; baseline 3 composes; 1021 passed / 96.59% cov. |
