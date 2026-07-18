# Aprovações — T10-zoekt-adapter

| Gate | Versão / Commit | Decisão | Autor | Data | Observações |
|---|---|---|---|---|---|
| Design | `0.1.1` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | Correções MAJOR de v0.1.0 aplicadas; sem BLOCKING/MAJOR abertos |
| BDD | `0.1.0` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | ZOEKT-01..08; RED por ModuleNotFoundError dos módulos de produção; sem BLOCKING/MAJOR |
| Interfaces | `0.1.0` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | Porta + modelos + transportes + Fake; I-T10-001..016; sem BLOCKING/MAJOR |
| Unit tests | `0.1.1` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | 56 testes; RED ModuleNotFoundError; MAJOR I-13b/I-16/F-12b corrigidos na review |
| Implementação | produção `index/zoekt` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | MAJOR delete unlink→`ExactCodeIndexError` corrigido; 67 T10 + 372 suite; cov 97.52% |
| Blue refactor | `refactoring.md` | `BLUE_APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 | Sem mudança estrutural necessária; baseline 67 passed / cov ≥97% |
| Gate humano | PR | pendente | — | — | Único gate humano: review/merge no GitHub |
