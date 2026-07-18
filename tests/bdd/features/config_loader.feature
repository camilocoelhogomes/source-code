Feature: Config loader — JSON Sourcebot-like (T02)
  Como processo na inicialização
  Quero carregar e validar integralmente o arquivo apontado por CONFIG_PATH
  Para obter AppConfig tipado sem cadastro parcial e sem vazar token

  Scenario: CFG-01 arquivo válido carrega todas as conexões nomeadas em AppConfig
    Given um arquivo JSON com conexões nomeadas "github-microservices" (github) e "local-microservices" (git)
    And a variável de ambiente referenciada em token.env está definida e não-blank
    And o path do arquivo é passado ao ConfigLoader (como AppSettings.config_path faria)
    When o ConfigLoader carrega o path
    Then retorna AppConfig contendo exatamente essas conexões tipadas
    And a conexão github expõe orgs, repos (com wildcards), revisions.branches contendo "main"
    And a conexão git expõe url file:// absoluta e revisions.branches contendo "main"
    And nenhuma descoberta de repositório é exigida neste cenário

  Scenario: CFG-02 connections objeto vazio produz AppConfig vazio
    Given um arquivo JSON com "connections": {}
    When o ConfigLoader carrega o path
    Then retorna AppConfig com connections vazio

  Scenario: CFG-03 repos com wildcard de inclusão são aceitos sem expansão
    Given uma conexão github válida com repos contendo "my-org/microservice-*" e "my-org/*-api"
    And token.env resolvível
    When o ConfigLoader carrega o path
    Then AppConfig preserva as strings de repos com wildcard
    And o cenário não exige chamada à API GitHub nem expansão

  Scenario: CFG-04 urls file:// absolutas POSIX e Windows são aceitas
    Given conexões git válidas com url "file:///repos/*" e "file:///C:/repos/*"
    When o ConfigLoader carrega o path
    Then ambas entram no AppConfig tipadas como GitConnection
    And nenhuma verificação de existência de volume é exigida

  Scenario: CFG-05 path None rejeita carga total
    Given path de config None (CONFIG_PATH ausente no bootstrap)
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError
    And não retorna AppConfig

  Scenario: CFG-06 path inexistente rejeita carga total
    Given um Path que não existe no filesystem
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError
    And não retorna AppConfig

  Scenario: CFG-07 JSON malformado rejeita carga total
    Given um arquivo com conteúdo que não é JSON válido
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError

  Scenario: CFG-08 schema inválido rejeita carga total
    Given um JSON sem "connections" objeto, ou com type desconhecido
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError
    And não retorna AppConfig

  Scenario: CFG-09 variável token.env ausente ou blank rejeita carga total
    Given uma conexão github válida no JSON
    And a variável nomeada em token.env está ausente ou blank no ambiente do processo
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError citando o nome da env
    And não retorna AppConfig

  Scenario: CFG-10 uma conexão inválida impede qualquer AppConfig
    Given um JSON com uma conexão github válida e outra com type inválido
    And o token da conexão válida está resolvível
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError
    And nenhum AppConfig (nem subset) é retornado

  Scenario: CFG-11 url file:// relativa ou sem esquema é rejeitada
    Given conexões git com url "file://repos" ou "https://example.com/repo.git"
    When o ConfigLoader tenta carregar cada uma
    Then levanta ConfigLoadError em ambos os casos

  Scenario: CFG-12 revisions.branches sem main é rejeitado
    Given uma conexão válida exceto branches contendo só "develop"
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError

  Scenario: CFG-13 valor do token não aparece em ConfigLoadError
    Given environ com GITHUB_TOKEN igual a um valor secreto conhecido
    And um JSON com falha de schema além do token.env
    When o ConfigLoader falha ao carregar
    Then str(ConfigLoadError) não contém o valor secreto

  Scenario: CFG-14 valor do token não aparece em str/repr após carga ok
    Given JSON válido e environ com GITHUB_TOKEN secreto conhecido
    When o ConfigLoader carrega com sucesso
    Then str(AppConfig) e repr(AppConfig) não contêm o valor secreto
    And str/repr das conexões github também não contêm o valor secreto
