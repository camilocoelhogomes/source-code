# BDD — T01-project-foundation

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T01-project-foundation` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `TESTS_READY_FOR_REVIEW` |
| Versão BDD | `0.2.0` (pós `CHANGES_REQUIRED` Architect) |
| Design base | `0.2.0` (aprovado; commit `3505880` / candidato design `30272cb`) |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Escopo desta etapa | Somente BDD (sem interfaces, unitários ou implementação) |

## Histórico de revisão BDD

| Data | Autor | Decisão | Observações |
|---|---|---|---|
| 2026-07-18 | QA Engineer | candidato `0.1.0` | BDD inicial — 10 cenários FND-01..10 |
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | Achados B-01, M-01, M-02 (bloqueantes/major); S-01..S-03 sugestões |
| 2026-07-18 | QA Engineer | candidato `0.2.0` | Correções B-01/M-01/M-02; S-01/S-02/S-03 aplicadas sem ampliar escopo de produto |

## Rastreabilidade

| Cenário | Critério de aceite / design |
|---|---|
| FND-01 | venv documentado — PowerShell (+ ExecutionPolicy / python.exe sem activate) |
| FND-02 | venv documentado — cmd |
| FND-03 | venv documentado — macOS/Linux (+ `.venv/bin/python` sem activate) |
| FND-04 | Docker/T19 não usa `.venv` do host; venv=dev local × Docker=entrega (ENG-009 / D-T01-007) |
| FND-05 | Python ≥ 3.12 (`requires-python`) |
| FND-06 | Layout de módulos = plano §1.3 / design §2.6 (+ `__init__.py` por fronteira) |
| FND-07 | pytest + coverage com `fail_under` 95% |
| FND-08 | Settings só bootstrap (sem domínio; **sem API prescrita** — D-T01-008) |
| FND-09 | Paths cross-platform (`pathlib`) + normalização EOL (`.gitattributes`) |
| FND-10 | `.venv/` gitignored; install **no venv**, não no Python do sistema |

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Feature Gherkin | `tests/bdd/features/project_foundation.feature` |
| Steps / asserts | `tests/bdd/test_project_foundation.py` |

## Como executar

```bash
# Preferido após fundação (venv ativo):
python -m pytest tests/bdd -q

# Greenfield / sem pytest ainda (stdlib):
python3 -m unittest discover -s tests/bdd -p "test_*.py" -v
```

## Bloqueios preexistentes de execução

| ID | Bloqueio | Evidência (2026-07-18) | Impacto |
|---|---|---|---|
| BLK-01 | Toolchain pytest/pytest-cov ainda não instalada no ambiente (fundação ausente) | `python3 -m pytest` → `No module named pytest` | Suite via pytest bloqueada até T01 instalar deps no venv |
| BLK-02 | Launcher `python` ausente neste host (macOS); `python3` disponível | `python` → command not found; `python3 --version` ok | Comando canônico pós-venv continua `python -m pytest` (após activate); checks QA usam `python3 -m unittest` no greenfield |
| BLK-03 | Ausência de `.venv/`, `pyproject.toml` e pacote instalável | Layout/`requires-python`/imports indisponíveis | Falhas FND-05..08 esperadas até implementação |

**Não são bloqueios:** falhas de `python3 -m unittest discover -s tests/bdd -p 'test_*.py' -v` por artefatos da fundação ausentes — red esperado pré-implementação.

## Respostas aos achados do Architect (`reviews.md`)

| ID | Resposta QA | Resolução em |
|---|---|---|
| B-01 | Removida antecipação de `load_settings` / `get_settings` / `Settings` / `AppSettings` e carga tipada. FND-08 passa a inspeção estática: existência de `settings.py`, nomes de env bootstrap no fonte, literais conceituais 2/4/ausente, ausência de domínio. Contrato de API adiado ao gate interfaces/unitários. | `bdd.md` FND-08; feature; `test_project_foundation.py` `TestFND08*` |
| M-01 | FND-10 exige install com interpretador do venv (`python -m pip` no fluxo activate e/ou caminho completo) **e** texto explícito de que o fluxo padrão **não** é instalar no Python do sistema. | feature FND-10; `TestFND10*` |
| M-02 | FND-04 exige (1) não monta/não usa `.venv` do host e (2) associação explícita venv↔dev local e Docker/T19↔entrega. Removida asserção fraca de mera coocorrência. | feature FND-04; `TestFND04*` |
| S-01 | Aceita: `__init__.py` exigido na raiz e em cada placeholder. | FND-06 / `TestFND06*` |
| S-02 | Aceita de forma leve (sem novo cenário de produto): asserts em FND-01 (ExecutionPolicy + `.venv\Scripts\python.exe`) e FND-03 (`.venv/bin/python`). | FND-01/03 |
| S-03 | Aceita: caminhos `.venv\Scripts\Activate.ps1` e `.venv\Scripts\activate.bat`. | FND-01/02 |

---

## Cenários

### FND-01 — venv: Windows PowerShell

```gherkin
  Scenario: README documenta fluxo completo de venv no Windows PowerShell
    Given o repositório possui README de desenvolvimento local
    When o desenvolvedor consulta a seção de ambiente virtual para Windows PowerShell
    Then o README contém criação com "py -3.12 -m venv .venv"
    And o README contém ativação com ".venv\Scripts\Activate.ps1"
    And o README contém instalação com 'python -m pip install -e ".[dev]"'
    And o README contém execução de testes com "python -m pytest"
    And o README documenta ExecutionPolicy/RemoteSigned e ".venv\Scripts\python.exe" sem activate
```

### FND-02 — venv: Windows cmd

```gherkin
  Scenario: README documenta fluxo completo de venv no Windows cmd
    Given o repositório possui README de desenvolvimento local
    When o desenvolvedor consulta a seção de ambiente virtual para Windows cmd
    Then o README contém criação com "py -3.12 -m venv .venv"
    And o README contém ativação com ".venv\Scripts\activate.bat"
    And o README contém instalação com 'python -m pip install -e ".[dev]"'
    And o README contém execução de testes com "python -m pytest"
```

### FND-03 — venv: macOS / Linux

```gherkin
  Scenario: README documenta fluxo completo de venv no macOS/Linux
    Given o repositório possui README de desenvolvimento local
    When o desenvolvedor consulta a seção de ambiente virtual para macOS/Linux
    Then o README contém criação com "python3.12 -m venv .venv"
    And o README contém ativação com "source .venv/bin/activate"
    And o README contém instalação com 'python -m pip install -e ".[dev]"'
    And o README contém execução de testes com "python -m pytest"
    And o README documenta invoke sem activate via ".venv/bin/python"
```

### FND-04 — Docker / T19 sem `.venv` do host

```gherkin
  Scenario: Documentação deixa explícito que entrega Docker/T19 não usa .venv do host
    Given o repositório possui README de desenvolvimento local
    When o desenvolvedor consulta a orientação de entrega por containers
    Then o README afirma que a imagem/container não monta nem usa o ".venv" do host
    And o README associa venv a desenvolvimento local
    And o README associa Docker/T19 a entrega padronizada
```

### FND-05 — Python 3.12+

```gherkin
  Scenario: Projeto declara runtime Python 3.12+
    Given o manifesto do projeto em pyproject.toml
    When a restrição de versão Python é lida
    Then requires-python exige ">=3.12"
```

### FND-06 — Layout de módulos

```gherkin
  Scenario: Layout src espelha fronteiras do plano
    Given o pacote raiz "github_rag" sob src/
    When a árvore de pacotes é inspecionada
    Then existem os pacotes placeholder de fronteira do plano
    And cada placeholder (e a raiz) possui "__init__.py"
    And existe o módulo bootstrap "settings.py"
```

### FND-07 — pytest e cobertura ≥ 95%

```gherkin
  Scenario: Harness de testes falha abaixo de 95% de cobertura
    Given a configuração de testes do projeto
    When a política de cobertura é inspecionada
    Then pytest está declarado como ferramenta de teste
    And a cobertura está configurada com fail_under igual a 95
```

### FND-08 — Settings apenas bootstrap (sem API prescrita)

```gherkin
  Scenario: Settings é skeleton bootstrap sem lógica de domínio
    Given o arquivo src/github_rag/settings.py
    When o conteúdo do skeleton é inspecionado estaticamente
    Then o módulo declara/documenta INDEX_WORKERS, QUERY_WORKERS e CONFIG_PATH
    And o módulo reflete defaults conceituais 2 e 4 e CONFIG_PATH ausente/nulo sem API prescrita
    And o módulo não parseia JSON Sourcebot
    And o módulo não conecta a PostgreSQL nem resolve segredos de domínio
    And carga tipada e contratos de API ficam para o gate de interfaces/unitários
```

### FND-09 — Paths cross-platform e EOL

```gherkin
  Scenario: Fundação garante paths portáveis e normalização de EOL
    Given o repositório da fundação
    When artefatos de compatibilidade cross-platform são inspecionados
    Then existe ".gitattributes" com normalização de fim de linha (text=auto e/ou eol=lf)
    And o código de settings trata paths via pathlib (sem hardcode de separador de OS)
```

### FND-10 — Isolamento do venv no Git e install no venv ≠ sistema

```gherkin
  Scenario: .venv não é versionado e install ocorre no venv
    Given o repositório da fundação
    When .gitignore e README são inspecionados
    Then ".venv/" está listado em .gitignore
    And o README instrui instalar com o interpretador do venv
      (python -m pip após activate e/ou .venv\Scripts\python.exe / .venv/bin/python)
    And o README deixa explícito que o fluxo padrão não é instalar no Python do sistema
```

## Critérios de pronto do BDD (para review Architect + HITL)

- [ ] Todos os critérios de aceite de T01 cobertos por cenário nomeado
- [ ] Cenários Windows (PowerShell + cmd) e Unix com paridade
- [ ] Docker/T19 sem `.venv` do host + distinção venv local × entrega
- [ ] FND-08 sem antecipação de interfaces/API
- [ ] Testes executáveis presentes sob `tests/bdd/`
- [ ] Falhas atuais atribuídas à fundação ausente ou a BLK-* documentados
- [ ] Achados B-01 / M-01 / M-02 resolvidos; S-* aplicados ou justificados
- [ ] Sem interfaces, unitários de contrato ou código de produção nesta etapa
