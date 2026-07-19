# E2E — Robot MVP proof (T21)

Ownership: **T21-mvp-e2e-robot** (`github-etl-mcp-rag`).  
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

2. Instale deps e2e no `.venv`:

```bash
python -m pip install -e ".[e2e]"
# ou: python -m pip install -r requirements-e2e.txt
```

3. Rode a prova canônica:

```bash
export $(grep -v '^#' .env | xargs)   # ou: set -a; source .env; set +a
python -m github_rag.e2e
```

Equivalente manual:

```bash
podman compose -f docker-compose.e2e.yml up -d --build
robot --exclude bdd015 --outputdir e2e/results \
  e2e/robot/health.robot \
  e2e/robot/catalog_indexing.robot \
  e2e/robot/ui.robot \
  e2e/robot/mcp.robot \
  e2e/robot/negative.robot
podman compose -f docker-compose.e2e.yml down
```

## CI

- Secret obrigatório: `E2E_GITHUB_TOKEN` (mapeado para `GITHUB_TOKEN` no container pelo compose T19).
- **Não** usar o `GITHUB_TOKEN` default do GitHub Actions como substituto do token de produto.
- Consumidor: `docs-cicd-e2e-release` invoca `DefaultRobotMvpSuite` / `python -m github_rag.e2e` (sem ownership da suíte).

## Layout

| Path | Papel |
|------|--------|
| `e2e/robot/*.robot` | Suites green path (health, catalog_indexing, ui, mcp, negative) |
| `e2e/robot/resources/` | Keywords HTTP/auth (nunca logam token) |
| `e2e/fixtures/config.e2e.json` | Config sem secrets (`token.env=GITHUB_TOKEN`) |
| `e2e/fixtures/repos/` | Volume local (repo `sample-local` inicializado no `up`) |
| `e2e/results/` | Artefatos Robot (gitignored) |

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
