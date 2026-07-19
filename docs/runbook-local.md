# Runbook local — github-rag (T19)

Primary platform: **linux/amd64** (ENG-006). On Apple Silicon, Docker may
emulate amd64; expect slower SLM/Zoekt.

## Pré-requisitos Podman / Compose (F-T04-001)

Para stacks e2e com Podman: instale **Podman** e o binário **`podman-compose`**
(ou um compose provider no `PATH` usado por `podman compose`).

```bash
command -v podman-compose
# ou:
podman compose version
```

Instalação típica (macOS Homebrew): `brew install podman-compose`.

## Which compose file?

| File | Audience | Command |
|------|----------|---------|
| `docker-compose.yml` | End user / stable image | `docker compose up --build` |
| `docker-compose.dev.yml` | Dev + e2e local (infra only) | `podman compose -f docker-compose.dev.yml up -d` |
| `docker-compose.e2e.yml` | Alias infra e2e (mesmo modelo) | `podman compose -f docker-compose.e2e.yml up -d` |

**Dev/e2e:** app roda no host (`.venv`), sem rebuild de imagem:

```bash
podman compose -f docker-compose.dev.yml up -d
python -m github_rag.delivery          # ou python -m github_rag.e2e (Robot)
```

Do **not** treat T19 as the MVP e2e gate: Robot proof belongs to **T21**.

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

## Quick start (end user)

```bash
cp .env.example .env
# set GITHUB_TOKEN if using github connections
mkdir -p repos
docker compose up --build
curl -s http://127.0.0.1:8080/healthz
```

## Development compose

```bash
docker compose -f docker-compose.dev.yml up --build
```

Postgres is published on host `5432`. Source under `./src` and `./web` is
mounted into the app container (still no host `.venv`).

## E2E compose + Robot MVP proof (T21)

```bash
# Prefer Podman in CI/T21. Credentials: GITHUB_TOKEN or E2E_GITHUB_TOKEN (never commit).
podman compose -f docker-compose.e2e.yml up --build
```

Project name `github-rag-e2e` and `e2e_*` volumes isolate state from user/dev stacks.

Canonical MVP proof (after `cp .env.example .env` and setting a real token):

```bash
python -m pip install -e ".[e2e]"
rfbrowser init   # Chromium Playwright — obrigatório para ui_browser.robot (T23)
python -m github_rag.e2e
```

See `e2e/README.md` for suite layout (incl. Browser Library / `ui_browser.robot`),
timeouts, and CI secret `E2E_GITHUB_TOKEN`. Jobs e2e precisam de `rfbrowser init`
antes da prova canônica. BDD-015 (Cursor Discovery narrative) is excluded from Robot.

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
