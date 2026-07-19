# Checklist HITL — preparação de `.env` (T02)

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T02-hitl-env-prep` |
| Contrato | `HitlEnvPrep` |
| Data do registro | 2026-07-18 |
| Operador / executor | implementation-task-runner (prep documental); token = HITL humano |
| Repo de referência | `camilocoelhogomes/source-code` |
| Rastreabilidade | REQ-004, REQ-011–012; BR-004; DEC-005; ENG-005; BDD-002 |

> **Segurança:** este arquivo **nunca** contém valores de token. Evidência de credencial = apenas `present=true` / `present=false` ou `PASS`/`FAIL`.

## 1. Pré-requisitos

- [ ] **Podman** instalado e funcional (`command -v podman` + `podman info`).
- [ ] Acesso ao repositório de referência GitHub: `camilocoelhogomes/source-code`.
- [ ] Leitura de `.env.example` (raiz) e `e2e/README.md` (procedimento canônico T21).
- [ ] Working tree na raiz do clone deste projeto.

## 2. Passo PAT (operador humano)

1. O **operador humano** gera um Personal Access Token (PAT) GitHub com acesso de leitura ao repo `camilocoelhogomes/source-code`.
2. **Não** cole o valor do PAT neste checklist, em `spec/`, em commits, em runs versionados nem em issues/PRs.
3. Guarde o PAT apenas no `.env` local (próximo passo) ou no cofre do operador.

## 3. Passo `.env` a partir do example

```bash
cp .env.example .env
```

Edite `.env` e preencha **pelo menos uma** das variáveis (preferir `E2E_GITHUB_TOKEN` se ambas existirem — alinhado a T21 / `e2e/README.md`):

- `E2E_GITHUB_TOKEN=<seu-pat>`
- e/ou `GITHUB_TOKEN=<seu-pat>`

Demais vars canônicas podem permanecer como em `.env.example`. O token deve permitir acesso a `camilocoelhogomes/source-code`.

Se o `.env` for criado sem PAT ainda disponível: deixe `E2E_GITHUB_TOKEN=` vazio (como no example). **Proibido inventar token.** Gate T04 permanece `BLOCKED` até preenchimento humano.

## 4. Proibições (BR-004)

- **Nunca** `git add .env` nem commit do `.env`.
- **Nunca** colar/versionar o valor do token no checklist, em `spec/`, em commits ou em resumos de run.
- **Nunca** despejar o conteúdo do arquivo `.env` nem ecoar variáveis de token no shell como evidência versionada.
- Fixtures e artefatos sob `spec/` ficam sem PAT em claro.

## 5. Comandos de verificação (operador)

Execute na raiz do repositório. Registre apenas exit codes / booleans (sem conteúdo do `.env`).

```bash
# .env existe
test -f .env

# .env ignorado pelo git
git check-ignore -q .env

# falha (exit ≠ 0) se estiver trackeado — esperado: arquivo NÃO trackeado
! git ls-files --error-unmatch .env 2>/dev/null

# presença de token sem ecoar valor (HITL)
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
print(f"present={str(present).lower()}")
raise SystemExit(0 if present else 1)
PY

# Podman disponível
command -v podman >/dev/null && podman info >/dev/null
```

## 6. Tabela de gate T04

Preenchido em 2026-07-18 após verificação local (sem secrets).

| Check | Critério | Status (`PASS`/`FAIL`/`N/A`) | Evidência permitida |
|---|---|---|---|
| `.env` existe | arquivo na raiz | `PASS` | `test -f .env` exit 0 (criado via `cp .env.example .env`) |
| `.env` ignorado | `git check-ignore` | `PASS` | `.gitignore` linha `.env`; `git check-ignore -q .env` exit 0 |
| `.env` não trackeado | ausente de `git ls-files` | `PASS` | `git ls-files --error-unmatch .env` falha (não trackeado) |
| Token presente | `GITHUB_TOKEN` **ou** `E2E_GITHUB_TOKEN` não vazio no `.env` | `PASS` | `present=true` (valor **não** registrado) |
| Podman disponível | `podman` no PATH + `podman info` ok | `PASS` | `podman` em `/opt/homebrew/bin/podman`; `podman info` ok |
| **Gate T04** | todos os checks acima `PASS` | **`READY`** | 2026-07-18 — Podman ok + token presente no `.env` local (não versionado) |

### Como desbloquear T04

1. Operador preenche `E2E_GITHUB_TOKEN` e/ou `GITHUB_TOKEN` no `.env` local (não versionar).
2. Reexecuta a verificação de presença → `present=true`.
3. Atualiza a linha “Token presente” para `PASS` e o **Gate T04** para `READY` (data + operador), **sem** colar o valor do token.

T04 (`python -m github_rag.e2e`) só inicia com Gate = `READY`. Validade do PAT perante a API GitHub é exercitada em T04 (runtime T21), não neste checklist.

## 7. Referências

- `.env.example` — nomes canônicos sem secrets
- `e2e/README.md` — HITL local e entrypoint `python -m github_rag.e2e`
- Design T02: `spec/features/mvp-e2e-audit-hardening/tasks/T02-hitl-env-prep/design.md`
