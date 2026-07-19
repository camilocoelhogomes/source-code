# Design — T02-hitl-env-prep

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T02-hitl-env-prep` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/mvp-e2e-audit-hardening-T02-hitl-env-prep` |
| Base | `main` @ `086f3b3` |
| Rastreabilidade | REQ-004, REQ-011–012; BR-004; DEC-005; ENG-005; BDD-002; contrato `HitlEnvPrep` |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Superfície mínima: checklist HITL versionado + gate documental T04; sem módulo Python de produto; secrets nunca versionados. |

## 1. Contexto

A feature filha `mvp-e2e-audit-hardening` audita e executa a prova e2e do MVP (T19/T21) sem corrigir produto. T04 (`python -m github_rag.e2e`) depende de ambiente HITL com:

- Podman disponível;
- `.env` local **não versionado** na raiz, derivado de `.env.example`;
- token GitHub válido para `camilocoelhogomes/source-code` via `GITHUB_TOKEN` e/ou `E2E_GITHUB_TOKEN`.

Já existem no repositório (somente consumo/alinhamento):

| Artefato | Estado atual |
|---|---|
| `.env.example` | Lista `E2E_GITHUB_TOKEN=` vazio + comentário sobre `GITHUB_TOKEN` no `.env` real |
| `.gitignore` | Já contém `.env` (linha 8) |
| `e2e/README.md` | HITL: `cp .env.example .env`; token; Podman; entrypoint canônico |
| `github_rag.e2e.E2eCredentialResolver` (T21) | Gate **runtime** de credencial HITL/CI — fora do escopo T02 alterar |

T02 **não** roda Robot, **não** altera compose/produto e **não** inventa PAT.

## 2. Problema

1. Operador precisa de um checklist versionado, executável e sem segredos (BDD-002).
2. Gate duro T04: “Podman + token presente” deve ficar registrado de forma observável **sem** colocar o valor do token em artefato versionado (BR-004 / ENG-005).
3. Confirmar que `.env` permanece fora do git (existência local ≠ trackeado).
4. Menor superfície possível: evitar código de produto novo nesta feature filha (plano §1.2: não altera domínio/composes/suíte).

## 3. Solução proposta

### 3.1 Decisão de superfície (D-T02-001)

| Opção | Avaliação |
|---|---|
| A — Só markdown (checklist + status gate) | Satisfaz BDD-002, ENG-005 e gate T04; zero superfície de produto; alinhado ao ownership da feature filha |
| B — Validador Python `HitlEnvPrep` em `src/` | Redundante com `E2eCredentialResolver` (T21) no runtime; viola “não altera código” do plano §1.2; aumenta manutenção sem ganho de prova |
| C — Script auxiliar fora de `src/` | Útil, mas não obrigatório; checklist com comandos shell cobrem a verificação |

**Escolha: opção A (checklist only), com asserts pytest de contrato documental opcionais no pipeline QA** — verificam presença/conteúdo do checklist, `.gitignore` contém `.env`, e `.env.example` / `e2e/README.md` permanecem alinhados. **Nenhum** módulo novo em `src/github_rag/**`.

Validação de “token válido perante GitHub API” **não** é escopo T02 (requer rede + PAT real). T02 exige **presença não vazia** da variável no `.env` local (booleano), registrada no checklist; validade funcional é exercitada em T04 via T21.

### 3.2 Contrato lógico `HitlEnvPrep`

| Responsabilidade | Motivo da separação |
|---|---|
| Orientar o operador a criar `.env` a partir de `.env.example` e preencher token | HITL humano gera PAT (DEC-005); artefatos nunca inventam token |
| Gate versionável: `.env` existe localmente, não trackeado, token presente (bool), Podman disponível | Desbloqueia T04 sem secrets no git (ENG-005) |
| Não gerar, logar, commitá-lo nem persistir valor do token | BR-004 |

Implementação do contrato = **estrutura e critérios do checklist**, não classe Python.

### 3.3 Artefato principal

`spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md`

Conteúdo obrigatório (sem valores secretos):

1. **Pré-requisitos** — Podman; repo `camilocoelhogomes/source-code`; leitura de `.env.example` e `e2e/README.md`.
2. **Passo PAT** — operador gera PAT com acesso ao repo de referência (não documentar o valor).
3. **Passo `.env`** — `cp .env.example .env`; preencher `GITHUB_TOKEN` e/ou `E2E_GITHUB_TOKEN` (preferir `E2E_GITHUB_TOKEN` se ambos; alinhar a T21 / `e2e/README.md`). Demais vars canônicas podem permanecer como no exemplo.
4. **Proibições** — nunca `git add .env`; nunca colar token no checklist, em `spec/`, em commits ou em runs versionados.
5. **Comandos de verificação (operador)** — exit codes / booleans apenas:

```bash
test -f .env
git check-ignore -q .env
# falha se estiver trackeado:
! git ls-files --error-unmatch .env 2>/dev/null
# presença sem ecoar valor (HITL):
python - <<'PY'
from pathlib import Path
text = Path(".env").read_text(encoding="utf-8")
keys = {"GITHUB_TOKEN", "E2E_GITHUB_TOKEN"}
present = False
for line in text.splitlines():
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        continue
    k, _, v = s.partition("=")
    if k.strip() in keys and v.strip():
        present = True
        break
raise SystemExit(0 if present else 1)
PY
command -v podman >/dev/null && podman info >/dev/null
```

6. **Tabela de gate T04** — campos booleanos/status apenas:

| Check | Critério | Status (`PASS`/`FAIL`/`N/A`) | Evidência permitida |
|---|---|---|---|
| `.env` existe | arquivo na raiz | | `test -f` exit 0 |
| `.env` ignorado | `git check-ignore` | | saída do comando (sem conteúdo do arquivo) |
| `.env` não trackeado | ausente de `git ls-files` | | confirmação textual |
| Token presente | `GITHUB_TOKEN` **ou** `E2E_GITHUB_TOKEN` não vazio no `.env` | | `present=true/false` **nunca** o valor |
| Podman disponível | `podman` no PATH + `podman info` ok | | versão/`info` ok sem secrets |
| Gate T04 | todos os checks acima `PASS` | `READY` / `BLOCKED` | data + operador |

7. **Se `.env` for criado localmente na task** — permitido somente como arquivo **não versionado**; se não houver token do operador, deixar `E2E_GITHUB_TOKEN=` vazio (como no exemplo) e marcar gate `BLOCKED` até o humano preencher. **Proibido inventar token.**

### 3.4 Alinhamento com artefatos existentes

| Artefato | Ação T02 |
|---|---|
| `.gitignore` | Verificar que `.env` permanece; alterar **somente** se estiver ausente (hoje já presente) |
| `.env.example` | Não remover `E2E_GITHUB_TOKEN=`; não adicionar valores secretos; mudança só se checklist exigir esclarecimento de comentário sem secret |
| `e2e/README.md` | Delta mínimo opcional: link para `audit/hitl-env-checklist.md` como checklist da auditoria; ownership HITL T21 permanece |
| `src/github_rag/**` | **Sem mudanças** |
| `docker-compose*.yml` | **Sem mudanças** |

## 4. Componentes

| Componente | Tipo | Papel |
|---|---|---|
| `hitl-env-checklist.md` | doc versionada | SoT operacional HITL + registro do gate T04 |
| `.env` (local) | arquivo operador | Contém token; gitignored; nunca commit |
| `.env.example` | template | Nomes canônicos sem secrets |
| `e2e/README.md` | doc T21 | Procedimento canônico de prova (referência cruzada) |
| `E2eCredentialResolver` (T21) | runtime existente | Consome env em T04; T02 não o reimplementa |
| Testes de contrato documental (QA) | pytest | Congelam checklist/gitignore/example — sem ler `.env` real com assert de valor |

## 5. Fluxo

```text
Operador
  1. Gera PAT (acesso camilocoelhogomes/source-code)
  2. cp .env.example .env
  3. Preenche GITHUB_TOKEN e/ou E2E_GITHUB_TOKEN
  4. Executa comandos de verificação do checklist
  5. Marca tabela PASS/FAIL → Gate T04 = READY | BLOCKED
       │
       ▼
T04 só inicia se Gate = READY
  (runtime: E2eCredentialResolver + Podman compose)
```

Fluxo paralelo: T01 não depende de T02; T03 não é bloqueado por T02; **T04 é bloqueado** até gate READY.

## 6. Dados

| Dado | Versionado? | Notas |
|---|---|---|
| Nomes de vars (`GITHUB_TOKEN`, `E2E_GITHUB_TOKEN`, …) | Sim (example/checklist/README) | Sem valores |
| Valor do PAT / conteúdo de `.env` | **Não** | Só máquina do operador |
| Status `PASS`/`FAIL`/`READY`/`BLOCKED` | Sim (checklist) | Booleans + data + operador |
| Saída `podman info` resumida | Opcional no checklist | Sem env dumps |

Repo de referência (documental): `camilocoelhogomes/source-code`.

## 7. Erros e estados

| Situação | Comportamento T02 |
|---|---|
| `.env` ausente | Check FAIL; gate `BLOCKED` |
| Token ausente/blank em ambas as vars | Check FAIL; gate `BLOCKED`; T04 não inicia |
| `.env` trackeado ou staged | Check FAIL crítico (BR-004); remover do índice **sem** commit do arquivo; gate `BLOCKED` até corrigido |
| Podman ausente / `podman info` falha | Check FAIL; gate `BLOCKED` |
| Token presente mas inválido na API | Fora de T02; T04 falha explícita (T21); T05 classifica se ≠ contrato |
| Segredo colado no checklist | Violação BR-004; rejeitar PR; sanitizar histórico se necessário |

## 8. Segurança

- Nunca escrever, logar ou versionar o valor do token.
- Comandos de verificação não fazem `cat .env` nem `echo $GITHUB_TOKEN` em artefatos versionados.
- Checklist e qualquer run summary usam apenas `present=true/false`.
- Fixtures/testes de contrato não embutem PAT; usam `.env.example` / paths / gitignore.
- `.env` permanece em `.gitignore`; `*.secret` já coberto.

## 9. Compatibilidade

- Alinhado a REQ-049 / DEC-020 / T21: HITL aceita `E2E_GITHUB_TOKEN` **ou** `GITHUB_TOKEN` (preferir E2E).
- Compose e2e continua com alias `GITHUB_TOKEN: ${E2E_GITHUB_TOKEN:-${GITHUB_TOKEN:-}}` (T19) — T02 não altera.
- CI / secret Actions: fora de escopo (BR-009 / `docs-cicd-e2e-release`).
- Sem mudança de API, schema ou comportamento de produto.

## 10. Observabilidade

- Gate T04 observável na tabela do checklist (`READY`/`BLOCKED` + data).
- Evidências permitidas: exit codes, `git check-ignore`, booleano de presença, disponibilidade Podman.
- Sem telemetria nova; sem logs de processo com env dump.

## 11. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Operador não preenche token e T04 segue | Gate documental `BLOCKED` é pré-condição dura de T04 |
| Token vazado em markdown/commit | BR-004 + review; checklist proíbe valores; testes não leem `.env` real |
| Duplicar lógica de credencial em `src/` | D-T02-001: não implementar validador de produto |
| Checklist desatualizado vs README | Link cruzado + teste de contrato documental (nomes de vars / passos) |
| Assumir validade do PAT sem GitHub | Escopo: presença em T02; validade em T04 |

## 12. Rollback

- Reverter commits que adicionem/alterem `audit/hitl-env-checklist.md`, este `design.md` e qualquer delta mínimo em `e2e/README.md` / `.gitignore`.
- Remover `.env` local se desejado (`rm .env`) — nunca esteve no git.
- Sem migração de dados; sem impacto em runtime se gate não foi consumido.

## 13. Critérios de aceite técnicos (mapeamento BDD-002)

| Critério | Como T02 cobre |
|---|---|
| Existe caminho a partir de `.env.example` | Passo `cp` no checklist |
| `.env` local com token para o repo de referência | Passo PAT + check “token presente” + doc do repo |
| `.env` fora do versionamento | `.gitignore` + checks `check-ignore` / não trackeado |
| Nenhum segredo commitado | Proibição explícita + gate sem valores |
| Gate T04 Podman + token | Tabela READY/BLOCKED |

## 14. Arquivos a criar / alterar (implementação)

| Path | Ação |
|---|---|
| `spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md` | **Criar** (checklist + tabela de gate, sem secrets) |
| `spec/features/mvp-e2e-audit-hardening/tasks/T02-hitl-env-prep/design.md` | Este arquivo |
| `e2e/README.md` | **Opcional** — 1 link para o checklist da auditoria |
| `.gitignore` | **Somente se** `.env` não estiver listado (hoje: sem mudança) |
| `.env` (raiz, local) | **Opcional** criar via `cp .env.example .env` para o operador; **nunca** versionar; token vazio se humano não forneceu |
| `src/**`, `docker-compose*.yml`, `e2e/robot/**` | **Não alterar** |
| `tests/**` (contrato documental) | A definir pelo QA após aprovação deste design / BDD |

## 15. Fora de escopo (confirmação)

- Inventar, hardcodar ou versionar PAT.
- Rodar `python -m github_rag.e2e` / Robot (T04).
- Alterar compose T19 ou código de domínio.
- Secrets CI / workflow Actions.
- Validador Python de produto `HitlEnvPrep` em `src/`.

## 16. Handoff

- Próximo no pipeline: BDD (QA) cobrindo BDD-002 e critérios do gate sem secrets.
- Interfaces: contrato documental `HitlEnvPrep` (estrutura do checklist); sem Protocol Python obrigatório.
- T04 consome gate `READY` do checklist; runtime de credencial permanece T21.
- Aprovação humana / merge: único gate humano no modo autonomous (PR).
