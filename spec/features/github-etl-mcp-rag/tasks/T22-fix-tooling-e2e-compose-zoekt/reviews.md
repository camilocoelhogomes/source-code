# Reviews — T22-fix-tooling-e2e-compose-zoekt

## Review — Design `0.1.0` — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-19 |
| Pipeline | autonomous (aprovação Architect substitui HITL intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Completude (contexto, problema, solução, componentes, fluxo, dados, erros, segurança, compat., obs., riscos, rollback) | OK | §§1–12 |
| Decisões D-T22-* registradas | OK | §13 D-T22-001..008 |
| Rastreabilidade F-T04-001 / 002 / 003 | OK | §2; §14; cabeçalho |
| Evidência runtime (tini / zoekt-webserver /healthz) | OK | §2; D-T22-001 |
| Alinhamento 3 composes | OK | D-T22-002; C-T22-01..03 |
| Separação indexação app vs webserver | OK | §1; D-T22-003; fluxo §5 |
| Docs pré-req provider (F-T04-001) | OK | §3.2; D-T22-004; C-T22-04/05 |
| F-T04-003 como consequência (sem task extra) | OK | §3.3; D-T22-005 |
| Escopo: sem domínio / sem expandir Robot / sem MVP | OK | §15; D-T22-007/008 |
| Gate testes manifesto (T19/REQ-044) | OK | §3.4; D-T22-006 |
| Estado `APPROVED_BY_ARCHITECT` + versão `0.1.0` | OK | cabeçalho; §18 |
| Idioma português | OK | artefato completo |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `SUGGESTION` | Pin de tag/digest da imagem `sourcegraph/zoekt` (hoje `latest`) | design §9; R-T22-01 | Considerar pin em task futura de hardening | Aberto residual — não bloqueia |
| `SUGGESTION` | Healthcheck depende de binário na imagem | design §3.1; R-T22-02 | Escolher probe disponível na implementação | Aberto residual — não bloqueia |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — design.md `0.1.0` adequado para BDD/interfaces/unitários e implementação de tooling. Prosseguir no pipeline da task.

---

## Review — BDD `0.1.0` — QA (handoff; sem auto-aprovação)

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Artefato | `bdd.md` + `tests/bdd/test_e2e_compose_zoekt_fix.py` |
| Data | 2026-07-19 |
| Pipeline | autonomous T22 |
| Resultado | `TESTS_READY_FOR_REVIEW` (aguarda Architect; QA não auto-aprova) |

### Cenários

| ID | Critério | Camada pytest |
|---|---|---|
| EZ-01 | F-T04-001 | docs `e2e/README.md` + `docs/runbook-local.md` |
| EZ-02 | F-T04-002 | `command` zoekt nos 3 composes |
| EZ-03 | F-T04-002 / D-T22-002 | paridade argv |
| EZ-04 | F-T04-003 | pré-condições manifesto/docs + rastreio prova T21 (sem compose up) |
| EZ-05 | sem secrets | negativos |

### Evidência red (pré-implementação)

```text
.venv/bin/python -m pytest tests/bdd/test_e2e_compose_zoekt_fix.py -q --tb=line --no-cov
# 7 failed, 2 passed
# EZ-01: e2e/README.md e runbook sem binário `podman-compose` / verificação PATH
# EZ-02/03/04: serviço zoekt sem `command` (tini sem filho) nos 3 composes
# EZ-05: PASS (sem PAT real nos artefatos)
```

---

## Review — BDD `0.1.0` — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `tests/bdd/test_e2e_compose_zoekt_fix.py` |
| Data | 2026-07-19 |
| Pipeline | autonomous (aprovação Architect substitui HITL intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Cobertura F-T04-001 | OK | EZ-01; asserts docs `podman-compose` + PATH + install |
| Cobertura F-T04-002 | OK | EZ-02/EZ-03; tokens `zoekt-webserver`, `-index`, `/data/index`, `-rpc` nos 3 composes |
| Cobertura F-T04-003 | OK | EZ-04; pré-condições manifesto/docs + prova canônica T21 documentada; runtime fora do pytest |
| Alinhamento D-T22-001..008 | OK | command preservando tini (D-001); 3 composes (D-002); docs (D-004); F-T04-003 consequência (D-005); gate manifesto T19 (D-006); sem Robot (D-007); produto não bloqueia tooling (D-008) |
| Sem expansão Robot/browser | OK | convenções bdd.md; nenhum import/`robot` no pytest |
| Sem secrets | OK | EZ-05; negativos `ghp_` / assignments de token |
| Padrão T19 (manifesto/docs; sem compose up) | OK | só leitura YAML/markdown; sem `compose up` |
| Estado red pré-implementação | OK | 7 failed / 2 passed (EZ-05); falhas batem com gaps de compose/docs |
| Idioma português (bdd.md) | OK | cenários e rastreabilidade |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `SUGGESTION` | Parser de `command` cobre forma inline `command: [...]` / scalar; forma YAML multilinha (`command:` + lista `-`) pode falso-falhar | `test_e2e_compose_zoekt_fix.py` `_zoekt_command_blob` L55–77 | Implementação deve usar argv JSON do design §3.1; opcional endurecer parser nos unitários | Aberto residual — não bloqueia (design fixa forma JSON) |
| `SUGGESTION` | EZ-03 revalida tokens canônicos sem comparar igualdade byte-a-byte dos blobs entre composes | `TestEZ03ZoektCommandParity` | Suficiente para D-T22-002 (mesmo argv efetivo); igualdade estrita opcional em unitários | Aberto residual — não bloqueia |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — BDD `0.1.0` cobre F-T04-001/002/003, alinha D-T22-*, respeita escopo (sem Robot/compose up/secrets) e padrão T19. Prosseguir para interfaces.
