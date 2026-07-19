# Handoff orquestrador — W3 onda T33

| Campo | Valor |
|---|---|
| Data | 2026-07-19 |
| Base main | `d70fdab` |
| W1 | reutilizado `e2e-run-20260719-r3.md` (main inalterada) |

```yaml
feature_id: github-etl-mcp-rag
stop_criterion: .venv/bin/python -m github_rag.e2e exit 0
tasks: [T33-fix-e2e-zoekt-index-host-bin]
dependency_waves:
  - wave: 1
    tasks: [T33-fix-e2e-zoekt-index-host-bin]
architect_gate: true
robot_files_frozen: true
venv: reuse .venv
```
