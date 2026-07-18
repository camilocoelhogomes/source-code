Feature: Persistência do catálogo — camada de dados (T03)
  Como orquestrador de indexação e superfícies de leitura (sync, UI, MCP)
  Quero uma camada de persistência do catálogo com estados fechados, commits,
  progresso, etapas por arquivo e histórico de execuções
  Para comparar o tip da main com o último commit processado e reconciliar o estado

  # Rastreabilidade: BR-001, BR-004; REQ-020..023; ENG-011; DEC-005;
  # design T03 §3 (porta CatalogRepository + fake in-memory), §4 (domínio), §6 (operações), §7 (erros).
  # Escopo: apenas persistência (BDD-004/005/007/008 na camada de dados).

  Scenario: CP-01 (BDD-004) Repositório permanece "atualizado" quando o tip da main iguala o último commit processado
    Given um catálogo persistido com um repositório GitHub recém-cadastrado
    And o repositório concluiu a indexação do commit "C1" e está no estado "up_to_date"
    When o tip conhecido da main é registrado como "C1"
    And o reconcile do repositório é executado
    Then o estado permanece "up_to_date"
    And o último commit processado continua sendo "C1"

  Scenario: CP-02 (BDD-005) Repositório volta a "não indexado" quando surge um novo commit na main
    Given um catálogo persistido com um repositório no estado "up_to_date" e último commit processado "C1"
    When o tip conhecido da main é registrado como "C2"
    And o reconcile do repositório é executado
    Then o estado passa a ser "not_indexed"
    And o último commit processado registrado continua sendo "C1" como base de comparação

  Scenario: CP-03 (BDD-004/005) Marcar "atualizado" grava commit processado e tip iguais
    Given um repositório no estado "indexing" com uma execução aberta para o commit "C1"
    When a indexação é concluída com sucesso para o commit "C1"
    Then o estado passa a ser "up_to_date"
    And o último commit processado é "C1"
    And o tip conhecido da main registrado é "C1"

  Scenario: CP-04 (BDD-007) Progresso da execução corrente é persistido e legível
    Given um repositório no estado "indexing" com uma execução aberta
    When o progresso é atualizado para 50 por cento, 5 de 10 arquivos, etapa "tree_sitter"
    Then o catálogo ativo expõe percentual 50, 5 de 10 arquivos e etapa corrente "tree_sitter"

  Scenario: CP-05 (BDD-007) Etapas por arquivo (zoekt, tree_sitter, metadata_persisted) são registradas de forma idempotente
    Given um repositório no estado "indexing" com uma execução aberta
    When o arquivo "src/app.py" passa pelas etapas "zoekt", "tree_sitter" e "metadata_persisted"
    And a etapa "zoekt" do mesmo arquivo é registrada novamente
    Then o progresso do arquivo "src/app.py" possui horário registrado para as três etapas
    And o novo registro da etapa "zoekt" não gera erro nem duplica o arquivo

  Scenario: CP-06 (BDD-008) Estado de erro guarda mensagem e horário
    Given um repositório no estado "indexing" com uma execução aberta
    When a indexação falha com a mensagem "tree-sitter crashed" no horário informado
    Then o estado passa a ser "error"
    And a mensagem de erro persistida é "tree-sitter crashed"
    And o horário do erro persistido é o informado

  Scenario: CP-07 (BDD-008) Histórico de execuções retém falhas entre novas tentativas
    Given um repositório que falhou uma execução com a mensagem "boom"
    When uma nova execução é iniciada após a falha
    Then o histórico de execuções contém a execução falha com a mensagem "boom" e seu horário de erro
    And o histórico contém a nova execução aberta

  Scenario: CP-08 (ENG-011) list_active_catalog retorna apenas ativos com estado e último commit processado
    Given um catálogo com um repositório ativo "up_to_date" (último commit "C1") e um repositório desativado
    When o catálogo ativo é listado
    Then somente o repositório ativo é retornado
    And o item retornado expõe o estado "up_to_date" e o último commit processado "C1"

  Scenario: CP-09 (REQ-020) O domínio expõe exatamente os cinco estados fechados
    Given o enum de estados do catálogo
    When os valores possíveis são inspecionados
    Then existem exatamente os estados "not_indexed", "queued", "indexing", "up_to_date" e "error"
    And não existem os estados "desatualizado" nem "indisponível"

  Scenario: CP-10 (REQ-020) Transições inválidas da máquina de estados são rejeitadas
    Given um repositório recém-cadastrado no estado "not_indexed"
    When é solicitada a transição direta de "not_indexed" para "up_to_date"
    Then a operação é rejeitada com erro de transição inválida
    And o estado permanece "not_indexed"

  Scenario: CP-11 (Corner) Operação sobre repositório inexistente falha explicitamente
    Given um catálogo sem o repositório de id inexistente
    When uma leitura do repositório inexistente é solicitada
    Then a operação falha com erro de repositório não encontrado

  Scenario: CP-12 (Corner) Update concorrente com versão desatualizada é rejeitado
    Given um repositório cujo estado foi alterado por outro processo após a leitura
    When uma transição é aplicada usando a versão antiga (expected_version desatualizado)
    Then a operação é rejeitada com erro de conflito de concorrência
