# BDD — T02-hitl-env-prep

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T02-hitl-env-prep` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Execução | `tests/bdd/test_mvp_e2e_audit_hitl_env_prep.py` — valida checklist documental `HitlEnvPrep` (sem Robot/e2e; sem ler valor de `.env` real) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | HITL-01..HITL-10; contrato documental BDD-002 / design §3.3; RED até existir `audit/hitl-env-checklist.md`. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Review BDD OK; 8 failed / 2 passed (artefato ausente); sem BLOCKING/MAJOR. Ver `reviews.md`. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **Artefato (pytest BDD)** | Existência/conteúdo de `audit/hitl-env-checklist.md`; alinhamento `.gitignore` / `.env.example` | CI unitário/BDD padrão |
| **Operador HITL** | Preenche `.env` local e marca tabela READY/BLOCKED | Humano; fora do CI |
| **Robot / e2e** | Fora do escopo desta task (T04) | Não executar |

- Path canônico: `spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md`.
- Testes **não** leem nem assertam o valor do token em `.env` real.
- Gate T04 documental: status `READY` \| `BLOCKED`; checks com `PASS`/`FAIL`/`N/A` e evidência sem secrets.
- Superfície: checklist only (D-T02-001); sem módulo em `src/`.

## Rastreabilidade

| Cenário | Feature BDD / REQ | Design |
|---|---|---|
| HITL-01 | BDD-002; REQ-004, REQ-011 | §3.3 artefato |
| HITL-02..HITL-04 | BDD-002; REQ-004, REQ-011–012; DEC-005 | §3.3 passos 1–3 |
| HITL-05 | BDD-002; BR-004; ENG-005 | §3.3 passo 4; §8 |
| HITL-06 | BDD-002; REQ-011–012 | §3.3 passo 5 |
| HITL-07 | BDD-002; REQ-012; ENG-005 | §3.3 passo 6; gate T04 |
| HITL-08 | BDD-002; BR-004 | §8; §7 secrets |
| HITL-09 | BDD-002; BR-004 | §3.4 `.gitignore` |
| HITL-10 | BDD-002; REQ-011; REQ-049 pai | §3.4 `.env.example` |

---

## HITL-01 — Artefato canônico existe

**Tipo:** artefato Markdown  
**Dado** a preparação HITL documental T02  
**Quando** o checklist for publicado  
**Então** existe o arquivo `spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md`

## HITL-02 — Pré-requisitos documentados

**Tipo:** artefato Markdown  
**Dado** o artefato `hitl-env-checklist.md`  
**Quando** a seção de pré-requisitos for lida  
**Então** menciona Podman  
**E** menciona o repo `camilocoelhogomes/source-code`  
**E** referencia `.env.example` e `e2e/README.md`

## HITL-03 — Passo PAT do operador

**Tipo:** artefato Markdown  
**Dado** o checklist HITL  
**Quando** o passo de credencial for inspecionado  
**Então** instrui o operador humano a gerar um PAT com acesso ao repo de referência  
**E** não documenta nem placeholder de valor secreto do token

## HITL-04 — Passo `.env` a partir do example

**Tipo:** artefato Markdown  
**Dado** o checklist HITL  
**Quando** o passo de criação do `.env` for lido  
**Então** inclui o comando `cp .env.example .env`  
**E** instrui preencher `GITHUB_TOKEN` e/ou `E2E_GITHUB_TOKEN`  
**E** menciona o repo `camilocoelhogomes/source-code` no fluxo de preparação

## HITL-05 — Proibições de secrets e commit

**Tipo:** artefato Markdown  
**Dado** o checklist HITL  
**Quando** as proibições forem lidas  
**Então** proíbe `git add .env` (ou commit do `.env`)  
**E** proíbe colar/versionar o valor do token no checklist, em `spec/` ou em commits

## HITL-06 — Comandos de verificação do operador

**Tipo:** artefato Markdown  
**Dado** o checklist HITL  
**Quando** a seção de verificação for inspecionada  
**Então** inclui checagem de existência do `.env` (`test -f .env` ou equivalente)  
**E** inclui `git check-ignore` para `.env`  
**E** inclui verificação de não-trackeado (`git ls-files`)  
**E** inclui verificação booleana de presença de token (`GITHUB_TOKEN` / `E2E_GITHUB_TOKEN`) sem ecoar o valor  
**E** inclui verificação de Podman (`command -v podman` / `podman info`)

## HITL-07 — Tabela de gate T04 READY/BLOCKED

**Tipo:** artefato Markdown  
**Dado** o checklist HITL  
**Quando** a tabela de gate T04 for lida  
**Então** contém checks: `.env` existe; `.env` ignorado; `.env` não trackeado; token presente (bool); Podman disponível  
**E** o gate agregado admite status `READY` e `BLOCKED`  
**E** a evidência de token é apenas presença booleana (`present=true/false` / `PASS`/`FAIL`), nunca o valor

## HITL-08 — Checklist sem padrões de token

**Tipo:** artefato Markdown  
**Dado** o artefato `hitl-env-checklist.md`  
**Quando** o conteúdo for varrido por padrões de segredo  
**Então** não contém prefixos de token GitHub (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`)  
**E** não contém atribuições com valor longo de `GITHUB_TOKEN` / `E2E_GITHUB_TOKEN`

## HITL-09 — `.gitignore` cobre `.env`

**Tipo:** artefato de repositório  
**Dado** o `.gitignore` na raiz  
**Quando** for inspecionado  
**Então** contém a entrada `.env`

## HITL-10 — `.env.example` declara `E2E_GITHUB_TOKEN=`

**Tipo:** artefato de repositório  
**Dado** o `.env.example` na raiz  
**Quando** for inspecionado  
**Então** contém a linha canônica `E2E_GITHUB_TOKEN=` (valor vazio no template)  
**E** não embute token real (`ghp_` etc.)

---

## Comando

```bash
python -m pytest tests/bdd/test_mvp_e2e_audit_hitl_env_prep.py -q
```

## Estado esperado (pré-implementação)

RED: artefato `audit/hitl-env-checklist.md` ausente → HITL-01 (e cenários dependentes do checklist) falham pela razão esperada (`artefato ausente`). HITL-09/HITL-10 podem já passar (guards de alinhamento já presentes no repo).
