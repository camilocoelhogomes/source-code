# Design — T01-project-foundation

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T01-project-foundation` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `PENDING_HUMAN_DESIGN_APPROVAL` |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Rastreabilidade | REQ-007; cobertura ≥95%; ENG-001; ENG-009; plano §1.3 |

## 1. Contexto

Repositório greenfield: existe apenas `spec/` e metadados do workflow Cursor. Não há código de aplicação, `pyproject.toml`, testes nem README.

T01 cria a **fundação** para o implementation-pipeline: layout de pacotes alinhado às fronteiras do plano, toolchain Python 3.12+, `venv` como padrão de desenvolvimento local, harness de testes com cobertura mínima 95%, e skeleton de settings por variáveis de ambiente **sem lógica de domínio**.

Fora de escopo nesta task: parser de config (T02), PostgreSQL (T03), workers (T04), descoberta, indexação, UI, MCP, Dockerfile/compose (T19).

## 2. Solução técnica

### 2.1 Estratégia geral

1. Empacotar a aplicação como pacote instalável sob `src/` (`src` layout).
2. Declarar metadados e dependências em `pyproject.toml` (fonte única); opcionalmente gerar/espelhar `requirements*.txt` se necessário para CI/documentação — preferência: um `pyproject.toml` com grupos `dev` / `test`.
3. Isolar dependências locais em `.venv/` via `python3.12 -m venv`.
4. Configurar `pytest` + `coverage`/`pytest-cov` com falha automática abaixo de 95%.
5. Criar pacotes vazios (ou `__init__.py` mínimos) espelhando as fronteiras do plano §1.3.
6. Expor um skeleton `settings` que apenas lê/defaults de env — sem validar JSON Sourcebot, sem I/O de domínio.
7. Documentar no README de desenvolvimento: create/activate/install/test no venv; e que containers (T19) **não** usam o `.venv` do host.

### 2.2 Toolchain Python 3.12+

| Item | Escolha | Motivo |
|---|---|---|
| Runtime | Python ≥ 3.12 | ENG-001 |
| Empacotamento | `pyproject.toml` (PEP 621) + build backend padrão (`hatchling` ou `setuptools`) | Um manifesto; instalável em modo editável no venv |
| Layout | `src/<pacote_raiz>/...` | Evita import acidental do cwd; padrão moderno |
| Testes | `pytest` | Consenso Python; integração com coverage |
| Cobertura | `pytest-cov` + `fail_under = 95` | Restrição do projeto / pipeline |
| Lint (mínimo, opcional nesta task) | Não obrigatório no aceite T01; pode ficar para tasks posteriores | Escopo T01 não exige linter |
| Tipagem | Type hints nos módulos skeleton; `mypy` não é gate de T01 | Evita escopo extra |

Nome do pacote raiz proposto: `github_rag` (espelha o repositório; ajustável no gate de interfaces se houver preferência humana).

### 2.3 Estratégia de venv (ENG-009)

| Aspecto | Decisão |
|---|---|
| Diretório | `.venv/` na raiz do repo |
| Criação | `python3.12 -m venv .venv` |
| Ativação | `source .venv/bin/activate` (Unix) / `.venv\Scripts\activate` (Windows, best-effort) |
| Install | Com venv ativo: `pip install -e ".[dev]"` (ou equivalente declarado no `pyproject.toml`) |
| Testes | Com venv ativo: `pytest` (cobertura embutida via config) |
| Git | `.venv/` em `.gitignore` — nunca versionar |
| CI | Recria ambiente isolado (venv ou equivalente); não depende de `.venv` do desenvolvedor |
| Containers (T19) | Imagem instala deps no runtime da imagem; **não** monta nem usa `.venv` do host. Coexistência explícita no README |

Fluxo local esperado:

```text
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

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

### 2.6 Layout de pacotes

Espelha fronteiras do `implementation-plan.md` §1.3. Pacotes são **placeholders** em T01; implementação real nas tasks seguintes.

```text
.
├── .venv/                          # local; gitignored
├── .gitignore                      # inclui .venv/
├── pyproject.toml                  # projeto + pytest/coverage
├── README.md                       # dev local: venv + testes; nota T19
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
    ├── conftest.py                 # fixtures mínimas (venv-aware paths se preciso)
    └── unit/
        └── test_settings.py        # QA escreverá nos gates seguintes
```

Notas de layout:

- Portas/interfaces de domínio **não** são criadas em T01 (gate posterior `interfaces.md`).
- `delivery/` no pacote é placeholder de fronteira; Dockerfile/compose vivem na raiz em T19.
- UI pode ser SPA/templates fora de `src` no futuro; em T01 basta o pacote `ui/` como fronteira lógica.

### 2.7 Componentes desta task

| Componente | Função em T01 |
|---|---|
| `pyproject.toml` | Metadados, deps runtime mínimas, extras `dev`/`test`, config pytest/coverage |
| `.gitignore` | Ignorar `.venv/`, artefatos de coverage, `__pycache__`, etc. |
| Pacotes `src/github_rag/...` | Fronteiras vazias + `settings.py` |
| `tests/` | Estrutura pronta para BDD/unit do pipeline |
| `README.md` | Comandos venv + nota containers |

### 2.8 Fluxo (dev local)

```text
[Dev] cria .venv → ativa → pip install -e ".[dev]"
    → edita código em src/
    → pytest (fail se cobertura < 95%)
[CI] cria ambiente isolado equivalente → mesmos testes
[T19 futuro] build da imagem instala deps no container; sem .venv do host
```

### 2.9 Dados

Nenhum dado persistido. Settings são valores efêmeros lidos do ambiente do processo.

### 2.10 Erros

- Python < 3.12: documentar requisito; `requires-python = ">=3.12"` no `pyproject.toml`.
- Install fora do venv: README instrui o fluxo correto; não há enforcement de runtime além de documentação.
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
| OS de desenvolvimento | macOS/Linux primários; Windows best-effort nos comandos de activate |
| Python | 3.12+ |
| Dev vs delivery | venv local ≠ imagem container (ENG-009); sem contradição |
| Tasks seguintes | Layout e settings não devem forçar imports circulares; pacotes independentes por fronteira |
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
| CI futuro | Terá comando único de teste com threshold 95% |
| Documentação | README de dev; nota explícita sobre T19/containers |
| Runtime produto | Sem mudança de comportamento de negócio — só fundação |

## 5. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Layout desalinhado às tasks futuras | Espelhar 1:1 o §1.3 do plano; ajustes só com mudança de plano |
| Cobertura 95% difícil com pacotes vazios | Medir só código real (`settings`); omitir `__init__` vazios da medição se necessário via `omit` explícito e documentado |
| Confusão venv × Docker | README com seção dedicada ENG-009 |
| Antecipar domínio em settings | Critério de aceite: sem parser/descoberta/DB; review Architect na implementação |
| Nome do pacote raiz contestado | Decisão provisória `github_rag`; HITL pode renomear antes da implementação |

## 6. Decisões de design (T01)

| ID | Decisão | Motivo |
|---|---|---|
| D-T01-001 | `src` layout com pacote raiz `github_rag` | Isolamento de imports; nome alinhado ao repo |
| D-T01-002 | `pyproject.toml` como fonte única de deps e config de teste/cobertura | Menos arquivos; padrão moderno |
| D-T01-003 | `.venv/` + gitignore + README (create/activate/install/test) | ENG-009 / aceite T01 |
| D-T01-004 | `pytest` + `pytest-cov` com `fail_under=95` | Restrição do projeto |
| D-T01-005 | Pacotes placeholder por fronteira do plano §1.3 | Habilita T02–T19 sem redesign de pastas |
| D-T01-006 | `settings.py` só bootstrap de env; sem lógica de domínio | Aceite T01; domínio em tasks donas |
| D-T01-007 | Documentar que T19 não usa `.venv` do host | ENG-009 / REQ-036 |
| D-T01-008 | Interfaces de produção adiadas ao gate de interfaces | Pedido explícito desta etapa de design |

## 7. Rollback

Greenfield: rejeitar o design ou a branch sem efeito em produção. Após merge, rollback = reverter commit na `main` (sem dados a migrar).

## 8. Critérios de pronto do design (para HITL)

- [ ] Layout de pacotes aprovado.
- [ ] Estratégia venv + cobertura 95% aprovadas.
- [ ] Skeleton de settings (sem domínio) aprovado em conceito.
- [ ] Fronteira clara: sem implementação nesta etapa; interfaces de produção no gate seguinte.

## 9. Próximo passo no pipeline

Após **aprovação humana** deste design: QA escreve BDD executáveis da fundação → review Architect → HITL BDD → Architect define interfaces de bootstrap → HITL interfaces → unit tests → implementação.
