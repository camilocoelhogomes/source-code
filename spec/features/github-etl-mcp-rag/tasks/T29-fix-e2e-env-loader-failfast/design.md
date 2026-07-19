# Design — T29 fix-e2e-env-loader-failfast

| Campo | Valor |
|---|---|
| Task | `T29-fix-e2e-env-loader-failfast` |
| Feature | `github-etl-mcp-rag` |
| Versão | `0.1.0` |
| Estado | `APPROVED_BY_ARCHITECT` |

## Contexto

Evidência `e2e-run-20260719.md`:

1. **F-T01-001**: `source .env` em zsh falha com `INDEX_CRON=0 2 * * *` (espaços interpretados como comandos).
2. **F-T01-003**: `PodmanE2eStackLauncher.wait_healthy` faz poll de `/healthz` por ~600s mesmo quando `github_rag.delivery` já exitou (zombie); fail-fast só no início do método, não no loop.

## Solução

### D-T29-001 — `.env.example` com aspas

`INDEX_CRON="0 2 * * *"` no `.env.example` canônico.

### D-T29-002 — Loader Python seguro

Novo módulo `github_rag.e2e.env_loader`:

- `parse_dotenv_text(text) -> dict[str, str]` — parser linha-a-linha sem shell.
- `load_dotenv_file(path, *, override=False) -> dict[str, str]` — lê arquivo e aplica em `os.environ`.
- Suporta valores com espaços (com ou sem aspas), comentários `#`, linhas vazias.
- Não executa expansão shell (`$VAR`, backticks).

Entrypoint `python -m github_rag.e2e` chama `load_dotenv_file(".env")` best-effort (arquivo ausente → noop).

### D-T29-003 — Fail-fast no poll loop

Extrair `_check_host_app_exited()` em `PodmanE2eStackLauncher`:

- Chamado no início de `wait_healthy` e **a cada iteração** do loop de poll.
- Se `poll() != None`: ler stderr (truncado), redigir secrets via `E2eStackError.from_stderr`, levantar `E2eStackError` imediato.

## Componentes

| Componente | Arquivo | Mudança |
|---|---|---|
| Env example | `.env.example` | aspas em `INDEX_CRON` |
| Env loader | `src/github_rag/e2e/env_loader.py` | novo |
| Entry | `src/github_rag/e2e/__main__.py` | chama loader |
| Launcher | `src/github_rag/e2e/launcher.py` | fail-fast no loop |
| Docs | `e2e/README.md` | comando seguro |

## Fluxo

```
python -m github_rag.e2e
  → load_dotenv_file(".env")  [best-effort]
  → DefaultRobotMvpSuite.run()
    → up() → start host app
    → wait_healthy()
      → loop: check exit → poll healthz → sleep
      → exit != 0 → E2eStackError (segundos, não 600s)
```

## Erros

| Cenário | Comportamento |
|---|---|
| `.env` ausente | noop; credencial resolver segue DEC-020 |
| `.env` malformado (sem `=`) | linha ignorada |
| host app exit durante poll | `E2eStackError` com stderr sanitizado |
| host app exit antes do poll | idem (já parcial; consolidado em helper) |

## Segurança

- Loader não loga valores.
- Fail-fast usa `E2eStackError.from_stderr` com redaction de tokens.

## Compatibilidade

- Sem breaking change em Protocols T21.
- `source .env` continua possível se `.env` tiver aspas; docs passam a recomendar loader Python.

## Observabilidade

- Mensagem de erro inclui `exit code` e trecho stderr (≤500 chars no fail-fast host).

## Riscos

| Risco | Mitigação |
|---|---|
| Parser dotenv incompleto vs python-dotenv | Escopo mínimo: KEY=VALUE, aspas, comentários |
| Race host exit entre poll e check | check a cada iteração (~50ms) |

## Rollback

Reverter branch; sem migration.

## Aprovação

| Gate | Decisão | Autor | Data |
|---|---|---|---|
| Architect design review | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-19 |
