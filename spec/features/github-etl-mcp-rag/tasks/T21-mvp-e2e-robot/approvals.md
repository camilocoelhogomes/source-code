# Aprovações — T21-mvp-e2e-robot

| Gate | Artefato | Decisão | Autor | Data | Observações |
|---|---|---|---|---|---|
| ARCHITECT_DESIGN | design.md `0.1.1` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | MAJOR CI `E2E_GITHUB_TOKEN` + green path BDD-026 corrigidos na review; Podman + compose e2e; BDD-015 fora; handoff `E2eStackLauncher`/`RobotMvpSuite`. |
| ARCHITECT_BDD | bdd.md `0.1.1` + `tests/bdd/test_mvp_e2e_robot.py` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | MAJOR falsos verdes E2E-01/02, exclude bdd015 e redaction E2E-10 corrigidos; BDD-026–028; sem compose real no pytest; green path sem skip observável. |
| ARCHITECT_INTERFACES | interfaces.md `0.1.0` | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-18 | Pacote `github_rag.e2e`: Protocols + Podman/Default + resolver + erros + timeouts/paths; I-T21-001..020; sem `src/`. |
