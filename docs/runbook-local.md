# Runbook local — github-rag (T19)

Primary platform: **linux/amd64** (ENG-006). On Apple Silicon, Docker may
emulate amd64; expect slower SLM/Zoekt.

## Services and ports

| Service  | Host port | Role                          |
|----------|-----------|-------------------------------|
| app UI   | 8080      | Management UI + `/healthz`    |
| app MCP  | 8001      | MCP SSE/streamable HTTP       |
| postgres | 5432      | Catalog (optional expose)     |
| qdrant   | 6333      | Vector store                  |
| zoekt    | 6070      | Exact code index              |
| slm      | 11434     | OpenAI-compatible (Ollama)    |

## Volumes

| Mount                         | Inside container              |
|-------------------------------|-------------------------------|
| `${HOST_CONFIG}` → config     | `/config/config.json` (`CONFIG_PATH`) |
| `${HOST_REPOS}` → repos       | `/repos` (`file:///repos/...`) |
| named `zoekt_index`           | `/data/index` (app ↔ zoekt)   |

Do **not** mount a host `.venv` into the app container (ENG-009). The image
installs the package with `pip install .` during build.

## Suggested resources (MVP amd64)

- CPU: 4 vCPU
- RAM: 8 GiB minimum (16 GiB comfortable with SLM 3B)
- Disk: 20 GiB+ for PG/Qdrant/Zoekt/repos volumes
- Workers: defaults `INDEX_WORKERS=2`, `QUERY_WORKERS=4`

## Startup order (ENG-011)

`docker compose up` starts infra then `app`. The app entrypoint
`python -m github_rag.delivery` boots in this order:

1. `load_settings` / `CONFIG_PATH`
2. `ConfigLoader.load` (fail-fast if invalid — no partial apply)
3. wait for PostgreSQL + `alembic upgrade head`
4. wire adapters
5. `run_catalog_sync`
6. `StartupIndexReconcile.run()` (ENG-011)
7. `DailyScheduler.start()`
8. bind UI (8080) + MCP (8001); `/healthz` reports ready

## Quick start

```bash
cp .env.example .env
# set GITHUB_TOKEN if using github connections
mkdir -p repos
docker compose up --build
curl -s http://127.0.0.1:8080/healthz
```

## Cursor MCP (stdio)

Compose default uses MCP over HTTP/SSE on port 8001 (healthcheck-friendly).
For stdio (e.g. Cursor), use a process attached to the same infra/config; this
entry does **not** re-run full ENG-011 sync/reconcile (the main `app` process
owns that). It wires catalog + query and runs MCP `transport=stdio` only:

```bash
docker compose run --rm -i app python -m github_rag.delivery.mcp_stdio
```

## SLM model pull

After `slm` is up:

```bash
docker compose exec slm ollama pull qwen2.5-coder:3b
```
