# Aprovações — T14-indexing-orchestrator

| Gate | Versão / Commit | Decisão | Autor | Data | Observações |
|---|---|---|---|---|---|
| `ARCHITECT_DESIGN_APPROVAL` | `0.1.0` | `CHANGES_REQUIRED` | Tech Lead Architect | 2026-07-18 | BLOCKING Zoekt/Qdrant; MAJOR recover startup |
| `ARCHITECT_DESIGN_APPROVAL` | `0.1.1` | `CHANGES_REQUIRED` | Tech Lead Architect | 2026-07-18 | B-01/B-02/S-01/S-02 fechados; MAJOR residual enqueue indexing |
| `ARCHITECT_DESIGN_APPROVAL` | `0.1.2` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | M-01b fechado; design aprovado — seguir BDD/interfaces |
| `ARCHITECT_BDD_APPROVAL` | `0.1.0` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | IO-01..14 cobrem BDD-002/004/005/007/008 + ENG-011/012/013 + REQ-020; alinhado design 0.1.2 |
| `ARCHITECT_INTERFACES_APPROVAL` | `0.1.0` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | Portas + Zoekt set-replace / Qdrant sem purge / StartupIndexReconcile / ENG-013 |
| `ARCHITECT_UNIT_TESTS_APPROVAL` | `0.1.0` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | Plano + suite unit/BDD cobrem I-T14, extremos e ENG-013; sem BLOCKING/MAJOR |
| `ARCHITECT_IMPLEMENTATION_APPROVAL` | — | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | Contratos I-T14; Zoekt 1×; Qdrant incremental sem purge; restart wipe; StartupReconcile; ENG-013; 769 passed / 98.79% |
| `BLUE_APPROVED_BY_ARCHITECT` | — | `BLUE_APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | B-01/B-02; sem otimização especulativa; comportamento preservado |
| Gate humano | PR | pendente | — | — | Único gate humano: review/merge no GitHub |
