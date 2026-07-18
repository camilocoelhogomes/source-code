Feature: Fundação do projeto — desenvolvimento local
  Como desenvolvedor em Windows, macOS ou Linux
  Quero uma fundação de repositório com venv, layout, testes e settings bootstrap
  Para iniciar as tasks seguintes sem ambiguidade de ambiente ou entrega

  Scenario: FND-01 README documenta fluxo completo de venv no Windows PowerShell
    Given o repositório possui README de desenvolvimento local
    When o desenvolvedor consulta a seção de ambiente virtual para Windows PowerShell
    Then o README contém criação com "py -3.12 -m venv .venv"
    And o README contém ativação com ".venv\Scripts\Activate.ps1"
    And o README contém instalação com 'python -m pip install -e ".[dev]"'
    And o README contém execução de testes com "python -m pytest"
    And o README documenta ExecutionPolicy/RemoteSigned e ".venv\Scripts\python.exe" sem activate

  Scenario: FND-02 README documenta fluxo completo de venv no Windows cmd
    Given o repositório possui README de desenvolvimento local
    When o desenvolvedor consulta a seção de ambiente virtual para Windows cmd
    Then o README contém criação com "py -3.12 -m venv .venv"
    And o README contém ativação com ".venv\Scripts\activate.bat"
    And o README contém instalação com 'python -m pip install -e ".[dev]"'
    And o README contém execução de testes com "python -m pytest"

  Scenario: FND-03 README documenta fluxo completo de venv no macOS/Linux
    Given o repositório possui README de desenvolvimento local
    When o desenvolvedor consulta a seção de ambiente virtual para macOS/Linux
    Then o README contém criação com "python3.12 -m venv .venv"
    And o README contém ativação com "source .venv/bin/activate"
    And o README contém instalação com 'python -m pip install -e ".[dev]"'
    And o README contém execução de testes com "python -m pytest"
    And o README documenta invoke sem activate via ".venv/bin/python"

  Scenario: FND-04 Documentação deixa explícito que entrega Docker/T19 não usa .venv do host
    Given o repositório possui README de desenvolvimento local
    When o desenvolvedor consulta a orientação de entrega por containers
    Then o README afirma que a imagem/container não monta nem usa o ".venv" do host
    And o README associa venv a desenvolvimento local
    And o README associa Docker/T19 a entrega padronizada

  Scenario: FND-05 Projeto declara runtime Python 3.12+
    Given o manifesto do projeto em pyproject.toml
    When a restrição de versão Python é lida
    Then requires-python exige ">=3.12"

  Scenario: FND-06 Layout src espelha fronteiras do plano
    Given o pacote raiz "github_rag" sob src/
    When a árvore de pacotes é inspecionada
    Then existem os pacotes placeholder de fronteira do plano
    And cada placeholder (e a raiz) possui "__init__.py"
    And existe o módulo bootstrap "settings.py"

  Scenario: FND-07 Harness de testes falha abaixo de 95% de cobertura
    Given a configuração de testes do projeto
    When a política de cobertura é inspecionada
    Then pytest está declarado como ferramenta de teste
    And a cobertura está configurada com fail_under igual a 95

  Scenario: FND-08 Settings é skeleton bootstrap sem lógica de domínio
    Given o arquivo src/github_rag/settings.py
    When o conteúdo do skeleton é inspecionado estaticamente
    Then o módulo declara/documenta INDEX_WORKERS, QUERY_WORKERS e CONFIG_PATH
    And o módulo reflete defaults conceituais 2 e 4 e CONFIG_PATH ausente/nulo sem API prescrita
    And o módulo não parseia JSON Sourcebot
    And o módulo não conecta a PostgreSQL nem resolve segredos de domínio
    And carga tipada e contratos de API ficam para o gate de interfaces/unitários

  Scenario: FND-09 Fundação garante paths portáveis e normalização de EOL
    Given o repositório da fundação
    When artefatos de compatibilidade cross-platform são inspecionados
    Then existe ".gitattributes" com normalização de fim de linha
    And o código de settings trata paths via pathlib

  Scenario: FND-10 .venv não é versionado e install ocorre no venv
    Given o repositório da fundação
    When .gitignore e README são inspecionados
    Then ".venv/" está listado em .gitignore
    And o README instrui instalar com o interpretador do venv
      (python -m pip após activate e/ou .venv\Scripts\python.exe / .venv/bin/python)
    And o README deixa explícito que o fluxo padrão não é instalar no Python do sistema
