# GitHub RAG

Requer Python 3.12 ou superior. O `.venv` é o ambiente padrão de
desenvolvimento local. Não instalar dependências no Python do sistema; use
sempre o interpretador do `.venv`.

## Windows — PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

Se a execução de scripts estiver bloqueada, use
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` ou execute sem ativar:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

Se o launcher `py` não estiver disponível, `python -m venv .venv` é aceito
quando esse interpretador for Python 3.12+.

## Windows — cmd

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -e ".[dev]"
python -m pytest
```

## macOS e Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

Sem ativar o ambiente:

```bash
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
```

## Testes e cobertura

Em qualquer sistema, após ativar o `.venv`:

```text
python -m pytest
```

O comando executa testes unitários e BDD com relatório de cobertura no
terminal. O projeto exige cobertura mínima de 95%; a execução falha
automaticamente abaixo desse limite. A suíte completa atual está em 416
testes (1 pulado sem Docker) com cobertura de 98.57% (T01–T08).

## Configuração de conexões (T02)

O arquivo JSON apontado por `CONFIG_PATH` (via `AppSettings.config_path`)
é carregado por `ConfigLoader` no pacote `github_rag.config`. Exemplo em
`examples/config.json`. Tokens GitHub usam somente `{ "env": "NOME" }` —
o valor fica na variável de ambiente, nunca no JSON. Config inválida é
rejeitada por completo (sem conexões parciais).

```python
from pathlib import Path
from github_rag.config import ConfigLoader, ConfigLoadError

loader = ConfigLoader()
try:
    config = loader.load(Path("/path/to/config.json"))
except ConfigLoadError as exc:
    raise SystemExit(exc) from exc
```

## Workers (T04)

Defaults de engenharia (via env / `load_settings`):

- `INDEX_WORKERS=2`
- `QUERY_WORKERS=4`

Capacidade `< 1` é rejeitada por `WorkerLimiterError`. Pools de indexação e
consulta são isolados (`create_index_limiter` / `create_query_limiter`).

## Descoberta GitHub (T05)

Repositórios remotos são descobertos a partir de conexões `type: "github"`
já validadas pelo `ConfigLoader`. A listagem usa PyGithub
(`PyGithubApiClient.iter_org_repos`). O token é lido somente via
`GitHubConnection.secret` (referência `{ "env": "..." }` resolvida em T02);
nunca aparece no resultado nem em mensagens de erro da descoberta.

```python
from github_rag.config import ConfigLoader
from github_rag.sources.github import GitHubRepoDiscovery

config = ConfigLoader().load(config_path)
discovery = GitHubRepoDiscovery()
for name, conn in config.connections.items():
    if conn.type != "github":
        continue
    repos = discovery.discover(name, conn)
```

Wildcards em `repos` são filtros exclusivos de inclusão (`prefix*`, `*suffix`,
`org/*`, exato). Lista vazia ⇒ nenhum repositório descoberto.

## Sync do catálogo (T07)

No bootstrap, `CatalogSync` sincroniza o catálogo SoT com as discoveries
GitHub (T05) e local (T06): upsert dos repositórios descobertos e soft-delete
dos ausentes da config atual. Não indexa nem executa o reconcile de tip
`main` (ENG-011 — T14). Helper de wire: `run_catalog_sync` em
`github_rag.app.bootstrap`.

```python
from github_rag.app import run_catalog_sync
from github_rag.catalog import CatalogSync, InMemoryCatalogRepository
from github_rag.config import ConfigLoader
from github_rag.sources.github import GitHubRepoDiscovery
from github_rag.sources.local import LocalRepoDiscovery

config = ConfigLoader().load(config_path)
sync = CatalogSync(
    catalog=InMemoryCatalogRepository(),  # ou adaptador PostgreSQL
    github_discovery=GitHubRepoDiscovery(),
    local_discovery=LocalRepoDiscovery(),
)
result = run_catalog_sync(config, sync)
# result.active / result.deactivated / result.local_issues
```

Repos ausentes saem do catálogo ativo (`active=False`); estados permanecem
somente os de REQ-020 (sem `indisponível`).

## Catálogo (PostgreSQL)

O catálogo de repositórios usa PostgreSQL como fonte de verdade (`src/github_rag/catalog/`).
O domínio (estados, transições, comparação de commit) é puro e testável sem PG via
fake in-memory; o adaptador PostgreSQL (`catalog/postgres/`) implementa a mesma
porta `CatalogRepository` com SQLAlchemy 2.x + psycopg3.

Configuração via variável de ambiente `DATABASE_URL`
(`postgresql+psycopg://usuario:senha@host:porta/banco`).

Schema versionado com Alembic:

```bash
alembic upgrade head
```

Os testes de integração contra PostgreSQL real usam o marcador `integration`
(`pytest -m integration`) e são pulados automaticamente quando não há PG/Docker
disponível; o run padrão (`python -m pytest`) cobre domínio e fake, sem exigir
PostgreSQL.

## Entrega por container

O venv é exclusivo do desenvolvimento local. Docker/T19 é a entrega
padronizada: a imagem/container não monta nem usa o `.venv` do host. As
dependências são instaladas diretamente no runtime da imagem.
