# Design — T01-project-foundation

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T01-project-foundation` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `HUMAN_DESIGN_APPROVED` |
| Versão do design | `0.2.0` (revisão pós-reprovação) |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Rastreabilidade | REQ-007; cobertura ≥95%; ENG-001; ENG-009; plano §1.3 |

## 0. Histórico de decisão HITL

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | camilocoelhogomes | **REPROVADO** | `0.1.0` (candidato anterior) | Feedback: “Preciso que desenvolvedores Windows também consigam trabalhar, metade da minha equipe usa Windows. Até por esse o motivo de entregar via docker.” |
| 2026-07-18 | Tech Lead Architect | Revisado → novo candidato | `0.2.0` | Windows elevado a plataforma de desenvolvimento local de **primeira classe** (não best-effort); Docker/T19 permanece entrega padronizada sem `.venv` do host. |
| 2026-07-18 | camilocoelhogomes | **APROVADO** | `0.2.0` / candidato `30272cb` | Design aprovado explicitamente; estado atualizado para `HUMAN_DESIGN_APPROVED`. |

Mudança de requisito de plataforma (Windows first-class no fluxo de **dev local**) não altera escopo de produto; reforça ENG-009 e o motivo de REQ-036/DEC-011 (entrega via containers).

## 1. Contexto

Repositório greenfield: existe apenas `spec/` e metadados do workflow Cursor. Não há código de aplicação, `pyproject.toml`, testes nem README.

T01 cria a **fundação** para o implementation-pipeline: layout de pacotes alinhado às fronteiras do plano, toolchain Python 3.12+, `venv` como padrão de desenvolvimento local em **Windows, macOS e Linux** com paridade de documentação e comandos, harness de testes com cobertura mínima 95%, e skeleton de settings por variáveis de ambiente **sem lógica de domínio**.

Fora de escopo nesta task: parser de config (T02), PostgreSQL (T03), workers (T04), descoberta, indexação, UI, MCP, Dockerfile/compose (T19).

## 2. Solução técnica

### 2.1 Estratégia geral

1. Empacotar a aplicação como pacote instalável sob `src/` (`src` layout).
2. Declarar metadados e dependências em `pyproject.toml` (fonte única); opcionalmente gerar/espelhar `requirements*.txt` se necessário para CI/documentação — preferência: um `pyproject.toml` com grupos `dev` / `test`.
3. Isolar dependências locais em `.venv/` via venv do Python 3.12+; documentar comandos **completos e equivalentes** para Unix, PowerShell e cmd.
4. Configurar `pytest` + `coverage`/`pytest-cov` com falha automática abaixo de 95%.
5. Criar pacotes vazios (ou `__init__.py` mínimos) espelhando as fronteiras do plano §1.3.
6. Expor um skeleton `settings` que apenas lê/defaults de env — sem validar JSON Sourcebot, sem I/O de domínio.
7. Documentar no README de desenvolvimento: create/activate/install/test no venv para **Windows (PowerShell + cmd) e Unix**; e que containers (T19) **não** usam o `.venv` do host — Docker é a entrega padronizada para a equipe (inclusive Windows).

### 2.2 Toolchain Python 3.12+

| Item | Escolha | Motivo |
|---|---|---|
| Runtime | Python ≥ 3.12 | ENG-001 |
| Launcher Windows | `py -3.12` (Python Launcher for Windows) como caminho preferido; fallback `python` se o launcher não estiver instalado | Paridade Windows first-class; evita ambiguidade de `python`/`python3` no PATH |
| Launcher Unix | `python3.12` preferido; fallback `python3` ≥ 3.12 | Paridade com Windows |
| Empacotamento | `pyproject.toml` (PEP 621) + build backend padrão (`hatchling` ou `setuptools`) | Um manifesto; instalável em modo editável no venv |
| Layout | `src/<pacote_raiz>/...` | Evita import acidental do cwd; padrão moderno |
| Paths no código | `pathlib.Path` (nunca hardcode `\` ou `/` em lógica de app) | Compatibilidade cross-platform |
| Line endings | `.gitattributes` recomendado: `* text=auto` e arquivos de texto com `eol=lf` onde fizer sentido; scripts de shell Unix com `lf` | Evita quebra de scripts no clone Windows↔Unix |
| Testes | `pytest` | Consenso Python; integração com coverage; mesmo comando após activate em todos os OS |
| Cobertura | `pytest-cov` + `fail_under = 95` | Restrição do projeto / pipeline |
| Lint (mínimo, opcional nesta task) | Não obrigatório no aceite T01; pode ficar para tasks posteriores | Escopo T01 não exige linter |
| Tipagem | Type hints nos módulos skeleton; `mypy` não é gate de T01 | Evita escopo extra |

Nome do pacote raiz proposto: `github_rag` (espelha o repositório; ajustável no gate de interfaces se houver preferência humana).

Dependências e scripts do projeto devem ser **OS-agnostic**: nenhum passo de T01 pode assumir só bash/`bin/activate`.

### 2.3 Estratégia de venv (ENG-009) — Windows first-class

| Aspecto | Decisão |
|---|---|
| Diretório | `.venv/` na raiz do repo (mesmo nome em todos os OS) |
| Criação Windows | `py -3.12 -m venv .venv` (preferido) |
| Criação Unix | `python3.12 -m venv .venv` |
| Ativação Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Ativação Windows cmd | `.venv\Scripts\activate.bat` |
| Ativação Unix | `source .venv/bin/activate` |
| Pip / pytest no venv | Após activate: `python` e `pip` apontam para o interpretador do `.venv` (em Windows: `.venv\Scripts\`; em Unix: `.venv/bin/`) |
| Install | Com venv ativo: `python -m pip install -e ".[dev]"` (preferir `python -m pip` para não chamar pip fora do venv) |
| Testes | Com venv ativo: `python -m pytest` (cobertura via config do projeto) |
| Sem activate (opcional, documentado) | Invocar executáveis pelo caminho completo: Windows `.venv\Scripts\python.exe -m pip ...` / `.venv\Scripts\python.exe -m pytest`; Unix `.venv/bin/python -m pip ...` / `.venv/bin/python -m pytest` |
| Git | `.venv/` em `.gitignore` — nunca versionar |
| CI | Recria ambiente isolado (venv ou equivalente) em runner Windows e/ou Linux; não depende de `.venv` do desenvolvedor |
| Containers (T19) | **Entrega padronizada** (REQ-036 / DEC-011): imagem instala deps no runtime da imagem; **não** monta nem usa o `.venv` do host (Windows, macOS ou Linux). Dev local com venv e entrega Docker coexistem sem contradição (ENG-009) |

#### Fluxo local — Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

Se a política de execução bloquear scripts: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (documentar no README; não alterar política da máquina silenciosamente).

#### Fluxo local — Windows cmd

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -e ".[dev]"
python -m pytest
```

#### Fluxo local — macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

#### Nota PowerShell vs paths

- Separador de path no shell Windows: `\`.
- No código Python e em configs: `pathlib` / forward-slash em globs do pytest quando suportado — nunca documentar só caminhos Unix no README.
- `CONFIG_PATH` e demais envs que apontam para arquivos: aceitar paths nativos do OS do host; no container (T19) usam paths Linux da imagem.

### 2.4 Cobertura ≥ 95%

- Configurar `fail_under = 95` (em `pyproject.toml` `[tool.coverage.report]` e/ou `[tool.pytest.ini_options]` com `--cov-fail-under=95`).
- Relatório terminal + (opcional) XML/HTML para CI.
- Em T01, o código de produção é mínimo (settings + placeholders). Testes unitários do skeleton devem cobrir:
  - defaults de settings;
  - leitura de env presentes/ausentes;
  - tipos/conversões simples (ex.: workers como int);
  - ausência de lógica de domínio (asserts negativos conceituais nos testes posteriores do QA).
- Pacotes vazios (`__init__.py` só) não precisam de cobertura significativa; o gate aplica-se ao código executável introduzido.
- Se a suíte inicial for pequena demais para o threshold, incluir testes do módulo `settings` até atingir ≥95% do código mensurável da task — sem inflar código morto.
- Comandos de cobertura idênticos em Windows e Unix após o venv ativo (`python -m pytest`).

### 2.5 Skeleton de settings (sem domínio)

Responsabilidade: centralizar **nomes e defaults** de variáveis de ambiente usadas pelo produto, sem carregar `CONFIG_PATH` como parser, sem conectar a DB, sem descobrir repos.

Variáveis mínimas a declarar no skeleton (leitura + default; validação profunda fica nas tasks donas):

| Variável | Default conceitual | Dono futuro |
|---|---|---|
| `CONFIG_PATH` | ausente / `None` até definido | T02 |
| `INDEX_WORKERS` | `2` (ENG-003) | T04 |
| `QUERY_WORKERS` | `4` (ENG-003) | T04 |
| `INDEX_CRON` (ou nome fixado depois) | default de boot (ENG-004/010) | T15 |
| Conexão PostgreSQL (URL ou host/port/db/user) | placeholders | T03 |
| Endpoints/URLs Qdrant, Zoekt, SLM | placeholders | T10–T13 / T19 |

Regras do skeleton:

- Sem validação de JSON Sourcebot.
- Sem resolução de `{ "env": "..." }` de segredos (T02 / `SecretResolver`).
- Sem logging de valores sensíveis.
- Conversões tipadas simples (str → int) permitidas; falha de conversão pode sinalizar erro genérico de bootstrap, sem política de domínio.
- Paths vindos de env tratados como `str`/`Path` sem assumir separador Unix.

### 2.6 Layout de pacotes

Espelha fronteiras do `implementation-plan.md` §1.3. Pacotes são **placeholders** em T01; implementação real nas tasks seguintes.

```text
.
├── .venv/                          # local; gitignored (Windows/macOS/Linux)
├── .gitignore                      # inclui .venv/
├── .gitattributes                  # recomendado: eol/auto para cross-OS
├── pyproject.toml                  # projeto + pytest/coverage
├── README.md                       # dev: PowerShell + cmd + Unix; nota T19/Docker
├── src/
│   └── github_rag/
│       ├── __init__.py
│       ├── settings.py             # skeleton env (único código "real" de T01)
│       ├── config/                 # T02 — ConfigLoader, SecretResolver
│       ├── sources/
│       │   ├── github/             # T05
│       │   └── local/              # T06
│       ├── catalog/                # T03, T07
│       ├── snapshot/               # T08
│       ├── eligibility/            # T09
│       ├── index/
│       │   ├── zoekt/              # T10
│       │   ├── chunk/              # T11
│       │   ├── metadata/           # T12
│       │   └── vector/             # T13
│       ├── indexing/               # T14
│       ├── schedule/               # T15
│       ├── query/                  # T16
│       ├── mcp/                    # T17
│       ├── ui/                     # T18
│       └── delivery/               # T19 (docs/helpers se necessário; imagem em raiz depois)
└── tests/
    ├── __init__.py
    ├── conftest.py                 # fixtures mínimas; paths via pathlib
    └── unit/
        └── test_settings.py        # QA escreverá nos gates seguintes
```

Notas de layout:

- Portas/interfaces de domínio **não** são criadas em T01 (gate posterior `interfaces.md`).
- `delivery/` no pacote é placeholder de fronteira; Dockerfile/compose vivem na raiz em T19.
- UI pode ser SPA/templates fora de `src` no futuro; em T01 basta o pacote `ui/` como fronteira lógica.
- Layout de pastas usa `/` na documentação por convenção; no disco Windows o Git/checkout funciona com o mesmo tree.

### 2.7 Componentes desta task

| Componente | Função em T01 |
|---|---|
| `pyproject.toml` | Metadados, deps runtime mínimas, extras `dev`/`test`, config pytest/coverage |
| `.gitignore` | Ignorar `.venv/`, artefatos de coverage, `__pycache__`, etc. |
| `.gitattributes` | Normalização de EOL para clones Windows/Unix |
| Pacotes `src/github_rag/...` | Fronteiras vazias + `settings.py` |
| `tests/` | Estrutura pronta para BDD/unit do pipeline |
| `README.md` | Comandos venv em PowerShell, cmd e Unix + nota Docker/T19 |

### 2.8 Fluxo (dev local × entrega)

```text
[Dev Windows / macOS / Linux]
    cria .venv (py -3.12 ou python3.12) → ativa (Scripts\ ou bin/) → pip install -e ".[dev]"
    → edita código em src/
    → python -m pytest (fail se cobertura < 95%)

[CI] cria ambiente isolado equivalente → mesmos testes

[T19 — entrega padronizada via Docker]
    build da imagem instala deps no container (linux/amd64 primário, ENG-006)
    NÃO monta / NÃO usa .venv do host (Windows, macOS ou Linux)
    Motivo alinhado ao feedback HITL: metade da equipe em Windows; Docker unifica runtime
```

### 2.9 Dados

Nenhum dado persistido. Settings são valores efêmeros lidos do ambiente do processo.

### 2.10 Erros

- Python < 3.12: documentar requisito; `requires-python = ">=3.12"` no `pyproject.toml`.
- Windows sem `py` launcher: README documenta instalação do Python 3.12 com “py launcher” habilitado e fallback `python -m venv .venv` se `python` já for 3.12+.
- PowerShell bloqueando `Activate.ps1`: documentar ajuste de `ExecutionPolicy` para `CurrentUser` ou uso do caminho completo `.venv\Scripts\python.exe -m ...` sem activate.
- Install fora do venv: README instrui o fluxo correto por OS; não há enforcement de runtime além de documentação.
- Cobertura < 95%: suite falha (`--cov-fail-under=95`).
- Env inválida para conversão numérica de workers: erro claro no skeleton (sem fallback silencioso ambíguo) — detalhe de contrato no gate de interfaces.

### 2.11 Segurança

- Não logar segredos.
- Não versionar `.env` com tokens; `.env` pode ser gitignored se usado localmente.
- Skeleton não carrega nem ecoa `GITHUB_TOKEN`.

### 2.12 Observabilidade

Fora de escopo profundo em T01. Opcional: logger padrão do stdlib no bootstrap futuro; não introduz stack de métricas.

### 2.13 Compatibilidade

| Dimensão | Posição |
|---|---|
| OS de desenvolvimento | **Windows, macOS e Linux — primeira classe** (comandos e README com paridade) |
| Shells Windows | PowerShell e cmd documentados de ponta a ponta |
| Launcher Windows | `py -3.12` preferido |
| Paths | `pathlib` no código; separadores nativos só na documentação de shell |
| Python | 3.12+ |
| Dev vs delivery | venv local (qualquer OS host) ≠ imagem container (ENG-009); Docker/T19 = entrega padronizada e **não** usa `.venv` do host |
| Arquitetura da imagem (T19) | `linux/amd64` primário; `arm64` best-effort (ENG-006) — distinto do OS de *desenvolvimento* |
| Tasks seguintes | Layout e settings não devem forçar imports circulares; pacotes independentes por fronteira; sem APIs só-Unix |
| Greenfield | Sem migração; rollback = descartar branch / não mergear |

## 3. Interfaces esperadas (nível conceitual apenas)

**Não criar** arquivos de interface de produção nesta etapa. Gate posterior (`interfaces.md`) formalizará contratos com comentários de responsabilidade/separação.

Conceitos previstos para T01 (bootstrap):

| Conceito | Responsabilidade conceitual | Por que separar |
|---|---|---|
| `Settings` / `AppSettings` | Agrupar defaults e leituras tipadas de env de bootstrap | Isola configuração de processo do domínio (config JSON, catálogo, indexação) |
| (não em T01) `ConfigLoader`, `SecretResolver`, demais portas do plano §2 | — | Pertencem a T02+; não antecipar no código de T01 |

Nenhuma porta de domínio do plano §2 entra no código de T01.

## 4. Impacto

| Área | Impacto |
|---|---|
| Código existente | Nenhum (greenfield) |
| Tasks W1 (`T02`–`T04`) | Podem iniciar em paralelo após merge de T01; dependem do layout e do harness |
| CI futuro | Comandos OS-agnostic (`python -m pytest`); runners Windows e Linux viáveis |
| Documentação | README com seções PowerShell, cmd e Unix; nota explícita Docker/T19 |
| Runtime produto | Sem mudança de comportamento de negócio — só fundação |
| Equipe Windows (~50%) | Fluxo de venv documentado e suportado como igual ao Unix; produto final via Docker |

## 5. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Layout desalinhado às tasks futuras | Espelhar 1:1 o §1.3 do plano; ajustes só com mudança de plano |
| Cobertura 95% difícil com pacotes vazios | Medir só código real (`settings`); omitir `__init__` vazios da medição se necessário via `omit` explícito e documentado |
| Confusão venv × Docker | README com seção dedicada ENG-009: venv = dev local; Docker/T19 = entrega padronizada sem `.venv` do host |
| Docs só Unix (reprovado em 0.1.0) | README e design com comandos completos PowerShell + cmd + Unix; review Architect barra regressão |
| `ExecutionPolicy` no PowerShell | Documentar RemoteSigned CurrentUser **ou** invocar `.venv\Scripts\python.exe` sem activate |
| `py` launcher ausente | Documentar instalação oficial Python 3.12 com launcher; fallback `python -m venv` |
| EOL / scripts quebrados no Windows | `.gitattributes`; evitar scripts bash obrigatórios em T01 |
| Antecipar domínio em settings | Critério de aceite: sem parser/descoberta/DB; review Architect na implementação |
| Nome do pacote raiz contestado | Decisão provisória `github_rag`; HITL pode renomear antes da implementação |

## 6. Decisões de design (T01)

| ID | Decisão | Motivo |
|---|---|---|
| D-T01-001 | `src` layout com pacote raiz `github_rag` | Isolamento de imports; nome alinhado ao repo |
| D-T01-002 | `pyproject.toml` como fonte única de deps e config de teste/cobertura | Menos arquivos; padrão moderno |
| D-T01-003 | `.venv/` + gitignore + README (create/activate/install/test) em **PowerShell, cmd e Unix** | ENG-009 / aceite T01 / feedback HITL Windows |
| D-T01-004 | `pytest` + `pytest-cov` com `fail_under=95`; invocar via `python -m pytest` | Restrição do projeto; funciona igual após activate em todos os OS |
| D-T01-005 | Pacotes placeholder por fronteira do plano §1.3 | Habilita T02–T19 sem redesign de pastas |
| D-T01-006 | `settings.py` só bootstrap de env; sem lógica de domínio; paths via `pathlib` | Aceite T01; domínio em tasks donas; cross-OS |
| D-T01-007 | Docker/T19 é a **entrega padronizada** e **não** usa `.venv` do host | ENG-009 / REQ-036 / DEC-011 / feedback HITL |
| D-T01-008 | Interfaces de produção adiadas ao gate de interfaces | Pedido explícito da etapa de design |
| D-T01-009 | Windows = plataforma de **dev local de primeira classe** (não best-effort) | Reprovação HITL 2026-07-18; metade da equipe em Windows |
| D-T01-010 | Launcher Windows preferido: `py -3.12`; pip/pytest via `python -m ...` | Paridade e isolamento do venv |
| D-T01-011 | Incluir `.gitattributes` recomendado para EOL cross-OS | Reduz atrito Windows↔Unix no clone |

## 7. Rollback

Greenfield: rejeitar o design ou a branch sem efeito em produção. Após merge, rollback = reverter commit na `main` (sem dados a migrar).

## 8. Critérios de pronto do design (para HITL)

- [ ] Layout de pacotes aprovado.
- [ ] Estratégia venv + cobertura 95% aprovadas.
- [ ] Windows, macOS e Linux tratados como **primeira classe** no fluxo de dev (PowerShell + cmd + Unix documentados).
- [ ] Launcher `py -3.12` e caminhos `Scripts\` vs `bin/` explícitos.
- [ ] Docker/T19 explícito como entrega padronizada **sem** `.venv` do host.
- [ ] Skeleton de settings (sem domínio) aprovado em conceito.
- [ ] Fronteira clara: sem implementação nesta etapa; interfaces de produção no gate seguinte.
- [ ] Histórico da reprovação 0.1.0 preservado neste artefato.

## 9. Próximo passo no pipeline

Após **aprovação humana** deste design (v0.2.0): QA escreve BDD executáveis da fundação → review Architect → HITL BDD → Architect define interfaces de bootstrap → HITL interfaces → unit tests → implementação.
