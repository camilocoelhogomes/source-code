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
automaticamente abaixo desse limite. A suíte completa atual está em 117
testes com cobertura de 100% (T01+T02+T04).

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

## Entrega por container

O venv é exclusivo do desenvolvimento local. Docker/T19 é a entrega
padronizada: a imagem/container não monta nem usa o `.venv` do host. As
dependências são instaladas diretamente no runtime da imagem.
