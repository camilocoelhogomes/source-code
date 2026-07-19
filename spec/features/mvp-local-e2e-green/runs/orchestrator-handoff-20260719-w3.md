# Handoff orquestrador — W3 onda T31

| Campo | Valor |
|---|---|
| Data | 2026-07-19 |
| Base main | `d4aab4b` |

```yaml
feature_id: github-etl-mcp-rag
stop_criterion: .venv/bin/python -m github_rag.e2e exit 0
tasks: [T31-fix-healthz-static-mount-order]
dependency_waves:
  - wave: 1
    tasks: [T31-fix-healthz-static-mount-order]
architect_gate: true
human_intermediate_gate: false
robot_files_frozen: true
venv: reuse .venv from W0; pip install only if pyproject.toml changed
```

## Contexto

Exit 3 fase `healthy`: `/healthz` 404 por StaticFiles em `/` antes de `register_health_routes`.

## Pós-onda

Re-run W1; se verde parcial, onda 2 T22 + gaps + T30.
