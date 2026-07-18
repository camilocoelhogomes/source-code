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
automaticamente abaixo desse limite. A entrega T01 foi validada com 37 testes.
aprovados e cobertura de 100%.

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
