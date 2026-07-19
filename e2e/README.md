# E2E — Robot MVP proof (T21 / T23)

Ownership: **T21-mvp-e2e-robot** + browser gap **T23-gap-ui-browser** (`github-etl-mcp-rag`).  
Runtime: **Podman** + `docker-compose.e2e.yml` (T19).  
Reference GitHub repo: `camilocoelhogomes/source-code` (this project).

## Pré-requisitos (F-T04-001)

- **Podman** instalado e em execução.
- Provider Compose no `PATH`: binário **`podman-compose`**, ou o subcomando
  `podman compose` com um compose provider resolvido no `PATH`.

Verifique:

```bash
command -v podman-compose
# ou, se usar o plugin/subcomando:
podman compose version
```

Instalação típica (macOS Homebrew):

```bash
brew install podman-compose
```

Sem o provider no `PATH`, `podman compose -f docker-compose.e2e.yml ...` falha
antes do stack subir.

## HITL local (obrigatório para prova real)

Checklist operacional da auditoria (gate T04, sem secrets):
[`spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md`](../spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md).

1. Copie o exemplo de env e **não** faça commit do `.env`:

```bash
cp .env.example .env
# Edite .env e defina um token GitHub real com acesso ao repo de referência:
#   GITHUB_TOKEN=ghp_...
# Opcional: E2E_GITHUB_TOKEN=... (preferido se ambos existirem)
```

2. Instale deps e2e no `.venv` (inclui Browser Library / Playwright):

```bash
python -m pip install -e ".[e2e]"
# ou: python -m pip install -r requirements-e2e.txt
```

3. Inicialize os binários do browser (obrigatório para a suite `ui_browser.robot`):

```bash
rfbrowser init
```

Sem `rfbrowser init`, a suite Browser Library falha por falta do Chromium Playwright.
O default da suite é **headless** (`${BROWSER_HEADLESS}=${True}` em `browser.resource`).
Para debug headed: `robot -v BROWSER_HEADLESS:False e2e/robot/ui_browser.robot`.

4. Rode a prova canônica:

```bash
export $(grep -v '^#' .env | xargs)   # ou: set -a; source .env; set +a
python -m github_rag.e2e
```

Equivalente manual (infra + app no host, **sem** `--build`):

```bash
podman compose -f docker-compose.dev.yml up -d
export $(grep -v '^#' .env | xargs)
python -m github_rag.delivery   # outro terminal, ou deixe o launcher subir
robot --exclude bdd015 --outputdir e2e/results \
  e2e/robot/health.robot \
  e2e/robot/catalog_indexing.robot \
  e2e/robot/ui.robot \
  e2e/robot/ui_browser.robot \
  e2e/robot/mcp.robot \
  e2e/robot/negative.robot
podman compose -f docker-compose.dev.yml down
```

`python -m github_rag.e2e` faz o mesmo (compose dev + app host + Robot + down).

## CI

- Secret obrigatório: `E2E_GITHUB_TOKEN` (mapeado para `GITHUB_TOKEN` no container pelo compose T19).
- **Não** usar o `GITHUB_TOKEN` default do GitHub Actions como substituto do token de produto.
- Job e2e precisa de `pip install -e ".[e2e]"` **e** `rfbrowser init` antes de `python -m github_rag.e2e`.
- Consumidor: `docs-cicd-e2e-release` invoca `DefaultRobotMvpSuite` / `python -m github_rag.e2e` (sem ownership da suíte).

## Layout

| Path | Papel |
|------|--------|
| `e2e/robot/*.robot` | Suites green path (health, catalog_indexing, ui, ui_browser, mcp, negative) |
| `e2e/robot/ui_browser.robot` | Evidência browser (Browser Library / Playwright) — T23 |
| `e2e/robot/resources/common.resource` | URLs, waits HTTP, redaction de token |
| `e2e/robot/resources/browser.resource` | Lifecycle Browser (Open/Close/Wait) + helpers UI |
| `e2e/robot/resources/` | Keywords HTTP/auth (nunca logam token) |
| `e2e/robot/libraries/CatalogIndexingKeywords.py` | Helpers T24 (cron UTC, MCP parse, tip host, eligibility, main-only) |
| `e2e/probes/negative_probes.py` | Indução controlada BDD-008/022 (T25; fora de `github_rag.e2e`) |
| `e2e/fixtures/config.e2e.json` | Config sem secrets (`token.env=GITHUB_TOKEN`; inclusão wildcard; volume ausente BDD-018) |
| `e2e/fixtures/repos/` | Volume local (repo `sample-local` inicializado no `up`; seed BDD-006/017) |
| `e2e/results/` | Artefatos Robot (gitignored) |

## catalog_indexing (T24)

Suíte `e2e/robot/catalog_indexing.robot` — asserts integrais vs inventário gap-fill:

| Tag | Cenário (resumo) |
|-----|------------------|
| `bdd003` | Cron dispara tick; indexa sem POST `/api/repos/index` pós-tip |
| `bdd005` | Mudança de tip na main → `last_processed_commit` via MCP |
| `bdd006` | Include Java/MD; exclude CSV, imagem e paths `.gitignore` |
| `bdd017` | Somente main; branch `other` e uncommitted ausentes nos hits |

Resource: `e2e/robot/resources/catalog_indexing.resource`.

## Timeouts / rate limit

| Fase | Default |
|------|---------|
| compose + healthy | 600s |
| indexação | 900s (poll 5s) |
| busca | 60s |
| HTTP 429 | até 3 retries, wait 30–60s |

## BDD-015

Narrativa Discovery no Cursor **fora** do Robot (`--exclude bdd015`).

## Contratos Python (handoff)

```python
from github_rag.e2e import DefaultRobotMvpSuite, PodmanE2eStackLauncher

raise SystemExit(DefaultRobotMvpSuite(launcher=PodmanE2eStackLauncher()).run())
```
