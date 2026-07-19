# Task T32 — fix-e2e-robot-venv-executable

| Campo | Valor |
|---|---|
| Task ID | `T32-fix-e2e-robot-venv-executable` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Superfície | `tooling-e2e` |
| Origem | W1 pós-T31 — `FileNotFoundError: robot` |
| Evidência | `orchestrator-status-20260719-w3.md` |

## Objetivo

Invocar `robot` do `.venv/bin` em `python -m github_rag.e2e` sem depender de `PATH`.

## Critérios de aceite

- [ ] `resolve_robot_executable()` retorna `.venv/bin/robot` quando presente
- [ ] `python -m github_rag.e2e` avança à fase Robot (não exit 1 por FileNotFoundError)
- [ ] Testes unitários UT-P07 + runner subprocess
