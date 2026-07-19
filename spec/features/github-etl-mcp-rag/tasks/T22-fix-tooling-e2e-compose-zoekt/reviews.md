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

---

## Review — Interfaces `0.1.0` — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` |
| Data | 2026-07-19 |
| Pipeline | autonomous (aprovação Architect substitui HITL intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Gate manifesto (D-T22-006) — sem Protocols novos | OK | I-T22-001; §1 exclusões |
| Contratos M-T22 shape zoekt nos 3 composes | OK | M-T22-001..007; §4 |
| `command` preservando ENTRYPOINT `tini` | OK | I-T22-006; M-T22-002; shape §4.1 |
| Paridade 3 composes (D-T22-002) | OK | M-T22-004 |
| Docs pré-req provider (F-T04-001) | OK | M-T22-010..014; §5 |
| Reuso T21 `E2eStackLauncher` / `RobotMvpSuite` sem mudança | OK | I-T22-002/003; §3 |
| Helper parse só em testes (se existir) + responsabilidade/motivo | OK | I-T22-007; §6 |
| Comentários ricos (responsabilidade + motivo da separação) | OK | §§3–6 |
| Sem secrets / escopo tooling | OK | M-T22-006/014; §1 |
| Mapeamento BDD → contratos | OK | §8 EZ-01..05 |
| Idioma português | OK | artefato completo |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `SUGGESTION` | Healthcheck zoekt permanece não-bloqueante (I-T22-008) | interfaces §2; design R-T22-02 | Developer escolhe probe disponível ou mantém `service_started` + wait T21 | Aberto residual — não bloqueia |
| `SUGGESTION` | Extração opcional para `tests/support/compose_manifest.py` | interfaces §6 | Só se unitários duplicarem regex do BDD | Aberto residual — não bloqueia |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces.md `0.1.0` documenta M-T22-* / I-T22-* com responsabilidade e motivo da separação; sem Protocols novos; T21 reusado. Prosseguir para unit-test-plan (QA).

---

## Review — Unit test plan `0.1.0` — QA (handoff; sem auto-aprovação)

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Artefato | `unit-test-plan.md` + `tests/unit/delivery/test_zoekt_compose_manifest.py` + `tests/support/compose_manifest.py` |
| Data | 2026-07-19 |
| Pipeline | autonomous T22 |
| Resultado | `TESTS_READY_FOR_REVIEW` (aguarda Architect; QA não auto-aprova) |

### Casos

| Grupo | IDs | Foco |
|---|---|---|
| Contratos repo | UT-Z01..Z05 | `command` / paridade / entrypoint / volume / papéis |
| Docs | UT-Z06, Z20, Z21 | pré-req provider (M-T22-010..013) |
| Secrets | UT-Z07 | negativos |
| Extremos sintéticos | UT-Z10..Z19, Z22 | command ausente, só tini, flags, path, multilinha, vazio |

### Evidência red (pré-implementação)

```text
.venv/bin/python -m pytest tests/unit/delivery/test_zoekt_compose_manifest.py -q --tb=line --no-cov
# 4 failed, 16 passed
# Razão canônica: serviço zoekt sem `command` (F-T04-002: tini help → exit 1)
#   nos 3 composes — UT-Z01 / Z02 / Z03
# Docs: UT-Z06 falha (sem binário podman-compose)
# Extremos sintéticos UT-Z10..Z22: PASS (helper)
# UT-Z04/Z05/Z07: PASS (volume/papéis/secrets já ok no status quo)
```

### Contagem

| Item | Valor |
|---|---|
| Métodos de teste | 20 |
| Falhas repo/docs (RED) | UT-Z01, Z02, Z03, Z06 |
| Helper só testes | `tests/support/compose_manifest.py` (I-T22-007) |
| Produção alterada | nenhuma (composes/docs intactos) |

---

## Review — Unit test plan `0.1.0` — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` + `tests/unit/delivery/test_zoekt_compose_manifest.py` + `tests/support/compose_manifest.py` |
| Data | 2026-07-19 |
| Pipeline | autonomous (aprovação Architect substitui HITL intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Contratos M-T22-001..005 nos 3 composes | OK | UT-Z01..Z05; `assert_zoekt_webserver_command` |
| M-T22-002 / I-T22-006 (sem entrypoint; só command) | OK | UT-Z03 |
| Docs M-T22-010..013 | OK | UT-Z06 + Z20/Z21 |
| Secrets M-T22-006/014 | OK | UT-Z07; `assert_no_embedded_secrets` |
| Extremos/corners | OK | UT-Z10..Z19, Z22 (ausente, tini-only, index, ordem, `-rpc`, path, vazio, multilinha) |
| Helper só em `tests/` (I-T22-007) | OK | `tests/support/compose_manifest.py`; sem `src/` |
| Não enfraquece BDD | OK | unitário endurece ordem lógica + multilinha vs EZ-02/03 |
| Sem compose up / sem produção | OK | só leitura; composes/docs intactos |
| RED pré-implementação | OK | `4 failed, 16 passed` — Z01/Z02/Z03/Z06 |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `SUGGESTION` | UT-Z02 valida tokens canônicos + ordem por arquivo; não compara igualdade byte-a-byte dos blobs entre composes | `test_ut_z02_parity_across_user_e2e_dev` | Suficiente p/ M-T22-004 (mesmo argv efetivo); igualdade estrita opcional | Aberto residual — não bloqueia |
| `SUGGESTION` | `canonical_argv_present` no helper não é usado pelos testes | `compose_manifest.py` L205–207 | Remover ou usar em Z02 se desejado | Aberto residual — não bloqueia |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — unit-test-plan + suíte cobrem M-T22-*/extremos/secrets; helper só em tests/; RED canônico F-T04-002 + docs. Prosseguir para implementação Developer (sem alterar testes para obter verde).

---

## Review — Implementation — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `docker-compose.yml`, `docker-compose.e2e.yml`, `docker-compose.dev.yml`, `e2e/README.md`, `docs/runbook-local.md` |
| Data | 2026-07-19 |
| Pipeline | autonomous (aprovação Architect substitui HITL intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| D-T22-001 `command` webserver preservando ENTRYPOINT `tini` | OK | `command: ["zoekt-webserver", "-index", "/data/index", "-rpc"]` nos 3 YAML; sem `entrypoint:` |
| D-T22-002 paridade nos 3 composes | OK | mesmo argv em user / e2e / dev |
| F-T04-001 docs (M-T22-010..013) | OK | `e2e/README.md` + `docs/runbook-local.md`: `podman-compose`, `command -v`, `podman compose version`, `brew install` |
| Sem secrets (M-T22-006/014) | OK | diff só argv + markdown; sem PAT/`ghp_` |
| Sem expansão Robot / domínio | OK | working tree: só 5 arquivos compose/docs; sem `src/` nem `e2e/robot/**` |
| Testes intactos e verdes (subset T22) | OK | `35 passed, 16 subtests` — BDD + unit zoekt + `test_manifest` |
| Alinhamento M-T22-001..007 | OK | tokens/ordem/volume `/data/index`/porta 6070 herdados; forma JSON inline |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| — | Nenhum | — | — | — |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Evidência de testes

```text
.venv/bin/python -m pytest tests/bdd/test_e2e_compose_zoekt_fix.py \
  tests/unit/delivery/test_zoekt_compose_manifest.py \
  tests/unit/delivery/test_manifest.py -q --tb=line --no-cov
# 35 passed, 16 subtests passed in 0.04s
```

### Decisão

`APPROVED_BY_ARCHITECT` — implementação materializa D-T22-001/002/004 e contratos M-T22-*; escopo tooling-only; subset T22 verde. Prosseguir para Blue/docs se aplicável no pipeline.

---

## Review — Blue / refactoring — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `refactoring.md` + `tests/support/compose_manifest.py` |
| Data | 2026-07-19 |
| Pipeline | autonomous (aprovação Architect substitui HITL intermediário) |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Baseline subset T22 registrado | OK | 35 passed, 16 subtests, 0.04s (pré e pós) |
| Sem otimização especulativa | OK | sem hot path; performance N/A |
| Simplificação só com evidência | OK | produção composes/docs N/A; helper: API morta removida |
| Sem mudança de comportamento/contratos | OK | asserts intactos; composes/docs não tocados nesta etapa |
| Cobertura de contratos preservada | OK | mesmo subset verde pós-remoção |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| — | Nenhum `BLOCKING` / `MAJOR` | — | — | — |

### Mudança Blue

| Arquivo | Delta | Motivo |
|---|---|---|
| `tests/support/compose_manifest.py` | remove `canonical_argv_present` + `typing.Sequence` | código morto (SUGGESTION residual unit review) |

### Evidência pós-Blue

```text
.venv/bin/python -m pytest tests/bdd/test_e2e_compose_zoekt_fix.py \
  tests/unit/delivery/test_zoekt_compose_manifest.py \
  tests/unit/delivery/test_manifest.py -q --tb=line --no-cov
# 35 passed, 16 subtests passed in 0.04s
```

### Decisão

`BLUE_APPROVED_BY_ARCHITECT` — baseline **35 passed / 16 subtests / 0.04s**; simplificação estrutural de produção N/A; Blue mínima no helper de teste aprovada.

---

## Review — Docs / changelog — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `CHANGELOG.md` + `e2e/README.md` + `docs/runbook-local.md` |
| Data | 2026-07-19 |
| Pipeline | autonomous (aprovação Architect substitui HITL intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| CHANGELOG `[Unreleased]` entrada T22 | OK | seção Alterado: `command` zoekt + pré-req compose provider |
| Docs F-T04-001 (M-T22-010..014) | OK | `e2e/README.md` + `docs/runbook-local.md` (já na implementação; sem delta nesta etapa) |
| Sem secrets em docs/changelog | OK | só nomes de variáveis / paths |
| Spec T22 completo | OK | design, bdd, interfaces, unit-test-plan, refactoring, reviews, approvals |
| Cobertura global ≥95% | OK | **1215 passed**, 2 skipped; **TOTAL 96.53%** |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| — | Nenhum `BLOCKING` / `MAJOR` | — | — | — |

### Evidência de cobertura

```text
1215 passed, 2 skipped
TOTAL coverage: 96.53% (≥95%)
```

### Decisão

`APPROVED_BY_ARCHITECT` — docs/changelog T22; gate `ARCHITECT_DOCS` aprovado.
