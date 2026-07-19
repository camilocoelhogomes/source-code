# Task T02 — hitl-env-prep

| Campo | Valor |
|---|---|
| Task ID | `T02-hitl-env-prep` |
| Feature | `mvp-e2e-audit-hardening` |
| Estado | `PENDING_PO_REVIEW` |
| Onda | W0 |
| Plano | v0.1.0 |

## Objetivo

Garantir preparação HITL do `.env` local não versionado (a partir de `.env.example`) com token GitHub válido para `camilocoelhogomes/source-code`, sem inventar nem commitá-lo.

## Escopo

- Checklist operacional: `cp .env.example .env`; vars mínimas `GITHUB_TOKEN` e/ou `E2E_GITHUB_TOKEN` + alinhamento a REQ-049 / `.env.example`.
- Documentar que o **operador humano** gera o PAT com acesso ao repo de referência.
- Verificar/registrar: `.env` existe localmente; está no `.gitignore` / não aparece em `git status` como tracked.
- Gate para T04: ambiente pronto (Podman disponível + token presente no env) — sem colocar o valor do token em artefato versionado.

## Fora de escopo

- Inventar, hardcodar ou versionar token.
- Rodar a suíte Robot (T04).
- Alterar compose T19 ou código de domínio.
- Secrets de CI (`docs-cicd-e2e-release`).

## Dependências

- Nenhuma task desta feature.
- **HITL humano:** geração do token e preenchimento do `.env`.

## Critérios de aceite

- Checklist HITL versionado e executável pelo operador (BDD-002).
- Confirmação registrada de que `.env` local existe e não será commitado (BR-004).
- Nenhum segredo em arquivos sob `spec/` ou commitáveis.

## Arquivos prováveis

- `spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md` (sem valores secretos)
- Referência: `.env.example`, `e2e/README.md`, `.gitignore`

## Rastreabilidade

- REQ-004, REQ-011–012; BR-004; DEC-005; ENG-005; BDD-002.

## Handoff

- Bloqueia T04 até checklist satisfeito.
- Token ausente na execução → falha explícita; classificação em T05 se ≠ contrato T21.
