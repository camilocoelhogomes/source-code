# BDD — T03-catalog-persistence

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T03-catalog-persistence` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão BDD | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Escopo desta etapa | Somente BDD da **camada de persistência** (sem interfaces, unitários ou implementação) |

## Histórico de revisão BDD

| Data | Autor | Decisão | Observações |
|---|---|---|---|
| 2026-07-18 | QA Engineer | candidato `0.1.0` | BDD inicial — 12 cenários (CP-01..12) cobrindo BDD-004/005/007/008, ENG-011, REQ-020 e corner cases |
| 2026-07-18 | tech-lead-architect (modo REVIEW) | `APPROVED_BY_ARCHITECT` | Review independente do gate BDD; 14 critérios OK; RED reproduzido (12 falhas pela razão esperada); sem BLOCKING/MAJOR; 3 SUGGESTION. Ver `reviews.md`. |

## Rastreabilidade

| Cenário | Critério de aceite / requisito | Design |
|---|---|---|
| CP-01 | BDD-004: tip main == `last_processed_commit` ⇒ permanece `up_to_date` | §4.2, §5.2 |
| CP-02 | BDD-005 / ENG-011: novo commit em main ⇒ volta a `not_indexed` | §4.2 (`up_to_date → not_indexed`) |
| CP-03 | BDD-004/005: concluir indexação grava `last_processed_commit` e `current_main_commit` iguais | §4.2, §6 (`mark_updated`) |
| CP-04 | BDD-007 / REQ-021: progresso (percentual, arquivos, etapa) persistido e legível | §5.1, §6 (`update_progress`) |
| CP-05 | BDD-007 / REQ-022: etapas por arquivo (`zoekt`,`tree_sitter`,`metadata_persisted`) idempotentes | §4.1, §5.1, §6 (`record_file_stage`) |
| CP-06 | BDD-008 / REQ-023: estado `error` com mensagem + horário | §4.2, §6 (`mark_error`) |
| CP-07 | BDD-008 / REQ-023: histórico retém falha entre tentativas (BR-005) | §5.1, §6 (`list_execution_history`) |
| CP-08 | ENG-011: `list_active_catalog` só ativos, com estado + `last_processed_commit` | §5.2, §6 |
| CP-09 | REQ-020: exatamente 5 estados; sem `desatualizado`/`indisponível` | §4.1 (D-T03-004) |
| CP-10 | REQ-020: transição ilegal rejeitada; estado preservado | §4.2 (D-T03-007) |
| CP-11 | Corner: repositório inexistente ⇒ `RepositoryNotFoundError` | §7 |
| CP-12 | Corner: update concorrente ⇒ `ConcurrencyConflictError` | §7 (D-T03-008) |

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Feature Gherkin | `tests/bdd/features/catalog_persistence.feature` |
| Steps / asserts | `tests/bdd/test_catalog_persistence.py` |

## API futura exercida (indicativa; formalizada no gate `interfaces.md`)

Os testes importam de `github_rag.catalog` os enums (`RepoState`, `RepoOrigin`,
`FileStage`), os erros (`CatalogError`, `RepositoryNotFoundError`,
`InvalidStateTransitionError`, `ConcurrencyConflictError`) e o fake
`InMemoryCatalogRepository` (design §3). Os valores dos enums são acessados por
`RepoState("not_indexed")` etc. (independe do nome do membro Python). Os verbos
de operação usam listas de candidatos equivalentes (`_invoke`), tolerando
refinamento de nomenclatura no gate de interfaces sem enfraquecer as asserções
de comportamento. Assinaturas exatas serão fixadas em `interfaces.md` (design §16).

## Como executar

```bash
# Preferido (venv ativo com pytest):
python -m pytest tests/bdd/test_catalog_persistence.py -q

# Greenfield / sem pytest (stdlib):
PYTHONPATH=src python3 -m unittest tests.bdd.test_catalog_persistence -v
```

## Evidência RED (pré-implementação)

Execução em 2026-07-18 (venv `../github_rag/.venv`, `PYTHONPATH=src`):

```
12 failed in 0.10s
```

Todos os 12 cenários falham pela razão esperada: `github_rag.catalog` ainda não
expõe enums/erros/`InMemoryCatalogRepository`
(`AssertionError: API do catálogo incompleta — RED esperado ...`). Nenhum erro
de coleta: a ausência da API é convertida em falha de cenário legível.

## Bloqueios preexistentes de execução

| ID | Bloqueio | Evidência (2026-07-18) | Impacto |
|---|---|---|---|
| BLK-01 | Workspace T03 sem `.venv` próprio | `ls .venv` → ausente | Execução usa `../github_rag/.venv` com `PYTHONPATH=src` |
| BLK-02 | Launcher `python` ausente no host (macOS); `python3` disponível | comando canônico pós-venv permanece `python -m pytest` | Checks QA no greenfield usam `python3 -m unittest` |

**Não são bloqueios:** as 12 falhas por API do catálogo ausente — RED esperado até a implementação.

## Cenários

### CP-01 — BDD-004: commit igual mantém "atualizado"

```gherkin
  Scenario: Repositório permanece "atualizado" quando o tip da main iguala o último commit processado
    Given um catálogo persistido com um repositório GitHub recém-cadastrado
    And o repositório concluiu a indexação do commit "C1" e está no estado "up_to_date"
    When o tip conhecido da main é registrado como "C1"
    And o reconcile do repositório é executado
    Then o estado permanece "up_to_date"
    And o último commit processado continua sendo "C1"
```

### CP-02 — BDD-005: novo commit reverte para "não indexado"

```gherkin
  Scenario: Repositório volta a "não indexado" quando surge um novo commit na main
    Given um catálogo persistido com um repositório no estado "up_to_date" e último commit processado "C1"
    When o tip conhecido da main é registrado como "C2"
    And o reconcile do repositório é executado
    Then o estado passa a ser "not_indexed"
    And o último commit processado registrado continua sendo "C1" como base de comparação
```

### CP-03 — BDD-004/005: concluir indexação grava commits iguais

```gherkin
  Scenario: Marcar "atualizado" grava commit processado e tip iguais
    Given um repositório no estado "indexing" com uma execução aberta para o commit "C1"
    When a indexação é concluída com sucesso para o commit "C1"
    Then o estado passa a ser "up_to_date"
    And o último commit processado é "C1"
    And o tip conhecido da main registrado é "C1"
```

### CP-04 — BDD-007: progresso persistido e legível

```gherkin
  Scenario: Progresso da execução corrente é persistido e legível
    Given um repositório no estado "indexing" com uma execução aberta
    When o progresso é atualizado para 50 por cento, 5 de 10 arquivos, etapa "tree_sitter"
    Then o catálogo ativo expõe percentual 50, 5 de 10 arquivos e etapa corrente "tree_sitter"
```

### CP-05 — BDD-007: etapas por arquivo idempotentes

```gherkin
  Scenario: Etapas por arquivo (zoekt, tree_sitter, metadata_persisted) são registradas de forma idempotente
    Given um repositório no estado "indexing" com uma execução aberta
    When o arquivo "src/app.py" passa pelas etapas "zoekt", "tree_sitter" e "metadata_persisted"
    And a etapa "zoekt" do mesmo arquivo é registrada novamente
    Then o progresso do arquivo "src/app.py" possui horário registrado para as três etapas
    And o novo registro da etapa "zoekt" não gera erro nem duplica o arquivo
```

### CP-06 — BDD-008: erro com mensagem e horário

```gherkin
  Scenario: Estado de erro guarda mensagem e horário
    Given um repositório no estado "indexing" com uma execução aberta
    When a indexação falha com a mensagem "tree-sitter crashed" no horário informado
    Then o estado passa a ser "error"
    And a mensagem de erro persistida é "tree-sitter crashed"
    And o horário do erro persistido é o informado
```

### CP-07 — BDD-008: histórico retido entre tentativas

```gherkin
  Scenario: Histórico de execuções retém falhas entre novas tentativas
    Given um repositório que falhou uma execução com a mensagem "boom"
    When uma nova execução é iniciada após a falha
    Then o histórico de execuções contém a execução falha com a mensagem "boom" e seu horário de erro
    And o histórico contém a nova execução aberta
```

### CP-08 — ENG-011: list_active_catalog

```gherkin
  Scenario: list_active_catalog retorna apenas ativos com estado e último commit processado
    Given um catálogo com um repositório ativo "up_to_date" (último commit "C1") e um repositório desativado
    When o catálogo ativo é listado
    Then somente o repositório ativo é retornado
    And o item retornado expõe o estado "up_to_date" e o último commit processado "C1"
```

### CP-09 — REQ-020: cinco estados fechados

```gherkin
  Scenario: O domínio expõe exatamente os cinco estados fechados
    Given o enum de estados do catálogo
    When os valores possíveis são inspecionados
    Then existem exatamente os estados "not_indexed", "queued", "indexing", "up_to_date" e "error"
    And não existem os estados "desatualizado" nem "indisponível"
```

### CP-10 — REQ-020: transição inválida rejeitada

```gherkin
  Scenario: Transições inválidas da máquina de estados são rejeitadas
    Given um repositório recém-cadastrado no estado "not_indexed"
    When é solicitada a transição direta de "not_indexed" para "up_to_date"
    Then a operação é rejeitada com erro de transição inválida
    And o estado permanece "not_indexed"
```

### CP-11 — Corner: repositório inexistente

```gherkin
  Scenario: Operação sobre repositório inexistente falha explicitamente
    Given um catálogo sem o repositório de id inexistente
    When uma leitura do repositório inexistente é solicitada
    Then a operação falha com erro de repositório não encontrado
```

### CP-12 — Corner: update concorrente

```gherkin
  Scenario: Update concorrente com versão desatualizada é rejeitado
    Given um repositório cujo estado foi alterado por outro processo após a leitura
    When uma transição é aplicada usando a versão antiga (expected_version desatualizado)
    Then a operação é rejeitada com erro de conflito de concorrência
```

## Critérios de pronto do BDD (para review Architect)

- [ ] Todos os critérios de persistência (BDD-004/005/007/008, ENG-011, REQ-020) cobertos por cenário nomeado
- [ ] Corner cases (repo inexistente, update concorrente) cobertos
- [ ] Enum fechado REQ-020 verificado sem `desatualizado`/`indisponível`
- [ ] Testes executáveis sob `tests/bdd/`, falhando RED pela razão esperada
- [ ] Fake in-memory da porta usado (sem PostgreSQL real)
- [ ] Sem interfaces, unitários de contrato ou código de produção nesta etapa
```
