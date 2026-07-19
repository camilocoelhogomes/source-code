# Unit Test Plan — T22-fix-tooling-e2e-compose-zoekt

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T22-fix-tooling-e2e-compose-zoekt` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design / BDD / Interfaces | `0.1.0` / `0.1.0` / `0.1.0` (todos `APPROVED_BY_ARCHITECT`) |
| Cobertura alvo | Gate manifesto/docs (sem código novo em `src/`); suite global ≥95% permanece |
| Branch | `feature/github-etl-mcp-rag-T22-fix-tooling-e2e-compose-zoekt` |
| Suíte | `tests/unit/delivery/test_zoekt_compose_manifest.py` + helper `tests/support/compose_manifest.py` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Plano + unitários TDD; RED por `command` zoekt ausente nos 3 composes + docs sem pré-req provider. |
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Review: contratos M-T22-* / extremos; helper só em tests/; RED 4 failed / 16 passed; sem BLOCKING/MAJOR. Modo autônomo. |

## 1. Estratégia

| Camada | Arquivo | Fronteira |
|---|---|---|
| Contratos repo (3 composes) | `test_zoekt_compose_manifest.py` UT-Z01..Z05 | leitura YAML real |
| Docs pré-req | UT-Z06 | `e2e/README.md`, `docs/runbook-local.md` |
| Secrets | UT-Z07 | negativos PAT/token |
| Extremos/corners | UT-Z10..Z22 | YAML/docs **sintéticos** via helper |
| Helper (só testes) | `tests/support/compose_manifest.py` | I-T22-007 — não é API de produção |

- Sem `compose up` / Podman / Robot (D-T22-006 / REQ-044 / DEC-017).
- BDD (`tests/bdd/test_e2e_compose_zoekt_fix.py` EZ-01..05) = superfície de aceite; unitários **não** duplicam cegamente — focam extremos do contrato de manifesto (command ausente, só tini, flags, path, multilinha, docs fracos).
- Sem alteração de `src/github_rag/**` nesta task (I-T22-001).
- Pré-implementação: falhas nos asserts de compose/docs reais — **RED esperado** (`command` ausente / F-T04-002).

## 2. Matriz unitária

### 2.1 Contratos nos composes reais (M-T22-001..005 / D-T22-002)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-Z01 | Em **cada** compose: `command` com `zoekt-webserver`, `-index`, `/data/index`, `-rpc` | tokens + ordem lógica | M-T22-001; EZ-02 |
| UT-Z02 | Paridade argv efetivo user / e2e / dev | mesmos tokens na ordem lógica nos 3 | M-T22-004; EZ-03 |
| UT-Z03 | Sem `entrypoint` no bloco `zoekt` (preserva tini) | `entrypoint` ausente; `command` presente | M-T22-002; I-T22-006 |
| UT-Z04 | Volume/env `/data/index` + porta `6070` | presentes no bloco | M-T22-003/005 |
| UT-Z05 | Papéis compose e2e vs user vs dev existem | 3 arquivos presentes | REQ-043; D-T22-002 |

### 2.2 Docs (M-T22-010..013) — leve

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-Z06 | README e2e + runbook com strings mínimas provider | `podman-compose` + verificação PATH + install | M-T22-010..012; EZ-01 |
| UT-Z20 | Doc que só menciona `docker-compose*.yml` / `podman compose` | rejeita (não substitui binário) | M-T22-013 |
| UT-Z21 | Doc vazio | rejeita | estado vazio |

### 2.3 Secrets

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-Z07 | Composes + docs sem PAT/`ghp_` real nem assignment de token | passa (já no status quo) | M-T22-006/014; EZ-05 |

### 2.4 Extremos / corners (YAML sintético)

| ID | Cenário | Esperado | Contrato |
|---|---|---|---|
| UT-Z10 | Ausência de `command` | `AssertionError` com F-T04-002 | M-T22-001 |
| UT-Z11 | `command` só tini (`/sbin/tini`) | rejeita (falta webserver) | F-T04-002 |
| UT-Z12 | `command` errado (`zoekt-index` sem `-rpc`) | rejeita | D-T22-003 / T10 |
| UT-Z13 | Imagem muda (`:5.0.0`) mas `command` ok | aceita | R-T22-01 |
| UT-Z14 | `command` multilinha YAML (`- item`) | aceita se tokens + ordem ok | SUGGESTION BDD; helper |
| UT-Z15 | Ordem de flags embaralhada (tokens presentes) | rejeita ordem lógica | M-T22-001 |
| UT-Z16 | `-rpc` ausente | rejeita | M-T22-001; T10 |
| UT-Z17 | Path de index diferente (`/tmp/index`) | rejeita (`/data/index` obrigatório) | M-T22-001/003 |
| UT-Z18 | Compose vazio / serviço `zoekt` ausente | rejeita | entradas inválidas |
| UT-Z19 | `command: []` | rejeita (vazio) | estado vazio |
| UT-Z22 | Happy path sintético canônico | aceita argv canônico | D-T22-001 |

## 3. Sobreposição com BDD

| Área | BDD | Unit |
|---|---|---|
| Docs provider | EZ-01 | UT-Z06 + UT-Z20/Z21 (docs fracos/vazios) |
| Command nos 3 composes | EZ-02 | UT-Z01 + extremos Z10..Z19 |
| Paridade | EZ-03 | UT-Z02 (ordem lógica / papéis Z05) |
| Runtime F-T04-003 | EZ-04 (pré-condições) | não reexecuta EZ-04; depende de Z01+Z06 |
| Secrets | EZ-05 | UT-Z07 |

Unitários **não** enfraquecem asserts BDD; helper compartilhado endurece multilinha/ordem (SUGGESTION Architect no review BDD).

## 4. Demonstração RED (TDD)

```bash
.venv/bin/python -m pytest tests/unit/delivery/test_zoekt_compose_manifest.py -q --tb=line --no-cov
```

Falhas esperadas pré-implementação (artefatos reais):

| Área | Razão |
|---|---|
| UT-Z01 / Z02 / Z03 | `serviço zoekt sem command` — F-T04-002 nos 3 composes |
| UT-Z06 | docs sem binário `podman-compose` / verificação PATH / install |
| UT-Z04 / Z05 / Z07 | devem **passar** (volume/porta/papéis/secrets já ok no status quo) |
| UT-Z10..Z22 | devem **passar** (exercitam helper com sintéticos) |

Evidência: `4 failed, 16 passed` (`pytest …/test_zoekt_compose_manifest.py --no-cov`).

Após implementação Developer (`command` nos 3 YAML + docs M-T22-010..012): suíte unitária verde.

## 5. Fora de escopo unitário

- `podman compose up` / `python -m github_rag.e2e` runtime (prova operacional T21)
- Expansão Robot / browser
- Alterar `docker-compose*.yml` / README / runbook nesta etapa QA
- Protocols novos em `src/`

## 6. Estado

`APPROVED_BY_ARCHITECT` — plano `0.1.0` + suíte unitária aprovados; sem BLOCKING/MAJOR. Prosseguir para implementação Developer (modo autônomo).
