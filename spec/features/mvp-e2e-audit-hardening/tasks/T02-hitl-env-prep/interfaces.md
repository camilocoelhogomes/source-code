# Interfaces — T02-hitl-env-prep

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T02-hitl-env-prep` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/mvp-e2e-audit-hardening-T02-hitl-env-prep` |
| Natureza | **100% documental** (D-T02-001) |
| Escopo desta etapa | Contrato lógico `HitlEnvPrep` — checklist + gate T04; **sem** Protocol/ABC Python, **sem** código de produção |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Interface lógica única alinhada design §3 e BDD HITL-01..10; zero runtime Python. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Forma | Papel |
|---|---|---|
| `HitlEnvPrep` | Artefato Markdown canônico | Checklist operacional HITL + registro do gate T04 (sem secrets) |

Path canônico (design §3.3):

```text
spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md
```

### Explicitamente fora de escopo — sem interfaces Python de runtime

| Item | Motivo |
|---|---|
| `typing.Protocol` / ABC / classes Python | D-T02-001: checklist only; sem superfície de runtime |
| Módulos em `src/` (incl. validador `HitlEnvPrep`) | Redundante com `E2eCredentialResolver` (T21); plano §1.2 |
| Alteração de compose / Robot / domínio | Fora do escopo T02 |
| Validação de PAT na API GitHub | Escopo T04 (runtime T21) |
| Secrets CI / Actions | BR-009 / `docs-cicd-e2e-release` |

**Não serão criados** arquivos `.py` de interface nesta task. O único “contrato” é a estrutura documental abaixo, validada pelos testes BDD HITL-01..10.

## 2. Interface lógica: `HitlEnvPrep`

```text
# HitlEnvPrep — interface lógica (documental)
#
# Responsabilidade:
#   Orientar o operador a preparar o ambiente HITL local (.env a partir de
#   .env.example, PAT para camilocoelhogomes/source-code, Podman) e registrar
#   de forma observável o gate T04 (READY | BLOCKED) usando apenas booleans /
#   status — nunca o valor do token.
#
# Motivo da separação:
#   - Isola a preparação HITL documental da feature filha do runtime de
#     credencial (E2eCredentialResolver / T21) e da execução e2e (T04).
#   - Congela um checklist versionável e auditável (BDD-002 / ENG-005) sem
#     introduzir Protocol/ABC Python onde D-T02-001 escolheu superfície zero
#     de produto.
#   - Impõe BR-004: secrets ficam só na máquina do operador; o contrato
#     versionado só admite evidência present=true/false e PASS/FAIL.
#
# Forma:
#   Artefato Markdown único no path canônico acima.
#   Sem métodos, sem tipos Python, sem serialização além de Markdown/tabela.
```

### Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T02-001 | Única interface lógica: `HitlEnvPrep` | Contrato da task | design §3.2 |
| I-T02-002 | Materialização = Markdown em `audit/hitl-env-checklist.md` | SoT versionável | HITL-01 |
| I-T02-003 | Sem Protocol/ABC/classes Python | D-T02-001 checklist only | design §3.1 |
| I-T02-004 | Gate agregado `READY` \| `BLOCKED` | Pré-condição dura de T04 | HITL-07 |
| I-T02-005 | Checks individuais `PASS` \| `FAIL` \| `N/A` | Observabilidade sem secrets | design §3.3.6 |
| I-T02-006 | Token: presença booleana apenas | BR-004 / ENG-005 | HITL-05/08 |
| I-T02-007 | Aceita `GITHUB_TOKEN` **ou** `E2E_GITHUB_TOKEN` (preferir E2E) | Alinhamento T21 / REQ-049 | HITL-04/06 |
| I-T02-008 | Consumidor canônico do gate = T04 | Handoff | design §5 |

## 3. Estrutura obrigatória do checklist

O artefato **deve** conter as seções abaixo (ordem recomendada = design §3.3). Conteúdo sem valores secretos.

### 3.1 Pré-requisitos (HITL-02)

| Elemento | Obrigatório |
|---|---|
| Podman disponível | sim |
| Repo de referência `camilocoelhogomes/source-code` | sim |
| Referência a `.env.example` | sim |
| Referência a `e2e/README.md` | sim |

### 3.2 Passo PAT (HITL-03)

| Elemento | Obrigatório |
|---|---|
| Instrução para o **operador humano** gerar PAT | sim |
| Acesso ao repo de referência | sim |
| Valor do token / placeholder secreto | **proibido** |

### 3.3 Passo `.env` (HITL-04)

| Elemento | Obrigatório |
|---|---|
| Comando `cp .env.example .env` | sim |
| Preencher `GITHUB_TOKEN` e/ou `E2E_GITHUB_TOKEN` | sim |
| Menção ao repo de referência no fluxo | sim |
| Preferência documental por `E2E_GITHUB_TOKEN` se ambos | recomendado (alinhamento T21) |

### 3.4 Proibições (HITL-05)

| Proibição | Obrigatório |
|---|---|
| Nunca `git add .env` / commit do `.env` | sim |
| Nunca colar/versionar valor do token no checklist, em `spec/` ou em commits | sim |
| Nunca inventar PAT | sim (implícito DEC-005) |

### 3.5 Comandos de verificação do operador (HITL-06)

Devem aparecer (ou equivalentes documentados) **sem** ecoar secrets:

| Check | Comando / forma mínima |
|---|---|
| `.env` existe | `test -f .env` |
| `.env` ignorado | `git check-ignore` |
| `.env` não trackeado | `git ls-files` (confirmação de ausência no índice) |
| Token presente (bool) | script/checagem de `GITHUB_TOKEN` / `E2E_GITHUB_TOKEN` não vazios → exit 0/1; **sem** `cat .env` / `echo $TOKEN` em artefato versionado |
| Podman | `command -v podman` e/ou `podman info` |

### 3.6 Tabela de gate T04 (HITL-07)

Colunas mínimas:

| Coluna | Domínio | Notas |
|---|---|---|
| Check | texto | Identifica o critério |
| Critério | texto | Condição observável |
| Status | `PASS` \| `FAIL` \| `N/A` | Por check |
| Evidência permitida | texto | Exit codes, `present=true/false`, confirmação textual — **nunca** valor do token |

Checks obrigatórios na tabela:

| Check | Critério |
|---|---|
| `.env` existe | arquivo na raiz |
| `.env` ignorado | `git check-ignore` ok |
| `.env` não trackeado | ausente de `git ls-files` |
| Token presente | `GITHUB_TOKEN` **ou** `E2E_GITHUB_TOKEN` não vazio → evidência só `present=true/false` (ou PASS/FAIL) |
| Podman disponível | `podman` no PATH + `podman info` ok |
| Gate T04 (agregado) | todos os checks acima `PASS` → `READY`; senão → `BLOCKED` |

Campos do gate agregado:

| Campo | Domínio | Versionado? |
|---|---|---|
| Status | `READY` \| `BLOCKED` | sim |
| Data | data ISO ou local | sim |
| Operador | identificador humano | sim |
| Valor do token | — | **nunca** |

## 4. Proibições de secrets (contrato de segurança)

| Regra | Severidade |
|---|---|
| Artefato versionado sem prefixos `ghp_` / `gho_` / `ghu_` / `ghs_` / `ghr_` | obrigatório (HITL-08) |
| Sem atribuição com valor longo a `GITHUB_TOKEN` / `E2E_GITHUB_TOKEN` no checklist | obrigatório (HITL-08) |
| `.env` permanece em `.gitignore` | obrigatório (HITL-09) |
| `.env.example` declara `E2E_GITHUB_TOKEN=` vazio (template) | obrigatório (HITL-10) |
| Testes de contrato não leem nem assertam valor de `.env` real | obrigatório |
| Se `.env` local criado na task: nunca versionar; token vazio ⇒ gate `BLOCKED` | obrigatório |

## 5. Alinhamento com artefatos existentes (não são interfaces desta task)

| Artefato | Relação |
|---|---|
| `.env.example` | Template canônico (nomes sem secrets) |
| `.gitignore` | Garante `.env` fora do git |
| `e2e/README.md` | Procedimento canônico T21; link cruzado opcional |
| `E2eCredentialResolver` (T21) | Runtime em T04; **não** reimplementar |

## 6. Contrato de consumo por T04

| Aspecto | Contrato |
|---|---|
| Input | Gate T04 = `READY` na tabela do checklist |
| Pré-condição | Todos os checks individuais `PASS` |
| Se `BLOCKED` | T04 **não** inicia |
| Runtime | Credencial/Podman exercitados por T21 / compose — fora deste contrato |
| Ownership | Operador preenche status; T02 não inventa PAT |

```text
HitlEnvPrep (audit/hitl-env-checklist.md)
        │  Gate = READY
        ▼
T04  python -m github_rag.e2e  (+ E2eCredentialResolver)
```

## 7. DoD do contrato (esta etapa)

- [x] Interface lógica `HitlEnvPrep` com responsabilidade e motivo da separação.
- [x] Estrutura do checklist (§3.1–3.5) congelada.
- [x] Campos do gate T04 (§3.6) congelados.
- [x] Proibições de secrets (§4) explícitas.
- [x] Explicitado: **nenhuma** interface Python de runtime (D-T02-001).
- [ ] Materialização do Markdown (implementação documental — etapa posterior do Developer).
