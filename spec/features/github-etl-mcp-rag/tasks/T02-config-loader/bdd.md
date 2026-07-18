# BDD — T02-config-loader

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T02-config-loader` |
| Autor | Tech Lead Architect (autonomous pipeline) |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão BDD | `0.1.0` |
| Design base | `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T02-config-loader` |
| Escopo desta etapa | Somente BDD (sem interfaces, unitários ou implementação do loader) |
| Modo | Autonomous — aprovação Architect substitui HITL |

## Histórico de revisão BDD

| Data | Autor | Decisão | Observações |
|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | candidato `0.1.0` → `APPROVED_BY_ARCHITECT` | Auto-review sem BLOCKING/MAJOR; ver `reviews.md` |

## Rastreabilidade

| Cenário | Critério | Cobertura T02 (design §3.1) |
|---|---|---|
| CFG-01 | BDD-021 (parcial) | JSON válido github+git → `AppConfig` tipado com todas as conexões nomeadas |
| CFG-02 | BDD-021 (parcial) / design §4.3 | `connections: {}` → `AppConfig` vazio válido |
| CFG-03 | BDD-021 (parcial) / BR-022 | Wildcards de inclusão em `repos` aceitos como forma (sem expansão) |
| CFG-04 | BDD-021 (parcial) / §4.4 | `file://` absoluto POSIX e Windows aceitos (sem I/O de volume) |
| CFG-05 | BDD-022 | `path is None` → rejeição total |
| CFG-06 | BDD-022 | Path inexistente → rejeição total |
| CFG-07 | BDD-022 | JSON malformado → rejeição total |
| CFG-08 | BDD-022 | Schema inválido (`connections` ausente/tipo errado, `type` desconhecido) → rejeição total |
| CFG-09 | BDD-022 | `env` ausente/blank → rejeição total |
| CFG-10 | BDD-022 / BR-021 | Uma conexão inválida entre válidas → zero conexões aplicadas (sem retorno parcial) |
| CFG-11 | BDD-022 / §4.4 | `file://` relativo / sem esquema → rejeição |
| CFG-12 | BDD-022 / ENG-T02-001 | `branches` sem `"main"` → rejeição |
| CFG-13 | BDD-014 (parcial) | Valor do token ausente de `str(exc)` em falha do loader/resolver |
| CFG-14 | BDD-014 (parcial) | Valor do token ausente de `str`/`repr` do `AppConfig`/conexões após carga ok |

**Fora de T02 (não cobrir nestes cenários):** descoberta de repositórios, identificação de origem na UI/catálogo, boot de container, logs UI/MCP.

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Feature Gherkin | `tests/bdd/features/config_loader.feature` |
| Steps / asserts | `tests/bdd/test_config_loader.py` |

## Superfície esperada (comportamental — gate interfaces refine)

Imports de `github_rag.config` (ainda não exportados — red esperado):

| Símbolo | Papel no BDD |
|---|---|
| `ConfigLoader` | Porta: `ConfigLoader().load(path: Path \| None) -> AppConfig`. Não relê workers/T01; path vem do caller (`AppSettings.config_path`) |
| `ConfigLoadError` | Exceção tipada de falha total (sem `AppConfig`) |
| `AppConfig` | Modelo imutável com mapa `connections` nome → conexão discriminada |
| `GitHubConnection` | Conexão `type="github"` tipada |
| `GitConnection` | Conexão `type="git"` tipada |

Segredos: resolução via `SecretResolver` (design); BDD controla o ambiente com `patch.dict(os.environ)` e **não** fixa assinatura de injeção no `ConfigLoader` (fica para `interfaces.md`).

## Como executar

```bash
# Preferido (venv ativo, pacote instalado):
python -m pytest tests/bdd/test_config_loader.py -q

# Stdlib / layout src:
PYTHONPATH=src python3 -m unittest discover -s tests/bdd -p "test_config_loader.py" -v
```

## Bloqueios / red esperado

| ID | Situação | Impacto |
|---|---|---|
| RED-01 | `github_rag.config` ainda não exporta `ConfigLoader` / modelos | `ImportError` ou falha de atributo — red até implementação |
| RED-02 | Loader não implementado | Cenários de carga/erro falham até Developer |

Falhas atuais são o red desejado; não bloqueiam aprovação do artefato BDD.

## Critérios de pronto do BDD

- [x] BDD-021 parcial (§3.1), BDD-022 e BDD-014 parcial cobertos por cenários nomeados
- [x] Given/When/Then mapeados a classes/métodos em `test_config_loader.py`
- [x] Sem descoberta de repos / UI / container
- [x] Testes executáveis sob `tests/bdd/` em red (módulo ausente)
- [x] Sem `interfaces.md`, unitários de contrato ou código de produção do loader
- [x] Auto-review Architect → `APPROVED_BY_ARCHITECT`

---

## Cenários

### CFG-01 — Carregar conexões github e git válidas (BDD-021 parcial)

```gherkin
  Scenario: CFG-01 arquivo válido carrega todas as conexões nomeadas em AppConfig
    Given um arquivo JSON com conexões nomeadas "github-microservices" (github) e "local-microservices" (git)
    And a variável de ambiente referenciada em token.env está definida e não-blank
    And o path do arquivo é passado ao ConfigLoader (como AppSettings.config_path faria)
    When o ConfigLoader carrega o path
    Then retorna AppConfig contendo exatamente essas conexões tipadas
    And a conexão github expõe orgs, repos (com wildcards), revisions.branches contendo "main"
    And a conexão git expõe url file:// absoluta e revisions.branches contendo "main"
    And nenhuma descoberta de repositório é exigida neste cenário
```

**Mapeamento:** `TestCFG01ValidGithubAndGitConnections`

### CFG-02 — connections vazio é válido

```gherkin
  Scenario: CFG-02 connections objeto vazio produz AppConfig vazio
    Given um arquivo JSON com "connections": {}
    When o ConfigLoader carrega o path
    Then retorna AppConfig com connections vazio
```

**Mapeamento:** `TestCFG02EmptyConnections`

### CFG-03 — Wildcards de inclusão em repos

```gherkin
  Scenario: CFG-03 repos com wildcard de inclusão são aceitos sem expansão
    Given uma conexão github válida com repos contendo "my-org/microservice-*" e "my-org/*-api"
    And token.env resolvível
    When o ConfigLoader carrega o path
    Then AppConfig preserva as strings de repos com wildcard
    And o cenário não exige chamada à API GitHub nem expansão
```

**Mapeamento:** `TestCFG03ReposWildcardsFormOnly`

### CFG-04 — file:// absoluto POSIX e Windows

```gherkin
  Scenario: CFG-04 urls file:// absolutas POSIX e Windows são aceitas
    Given conexões git válidas com url "file:///repos/*" e "file:///C:/repos/*"
    When o ConfigLoader carrega o path
    Then ambas entram no AppConfig tipadas como GitConnection
    And nenhuma verificação de existência de volume é exigida
```

**Mapeamento:** `TestCFG04FileUrlAbsolutePosixAndWindows`

### CFG-05 — Path ausente (BDD-022)

```gherkin
  Scenario: CFG-05 path None rejeita carga total
    Given path de config None (CONFIG_PATH ausente no bootstrap)
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError
    And não retorna AppConfig
```

**Mapeamento:** `TestCFG05PathNone`

### CFG-06 — Arquivo inexistente (BDD-022)

```gherkin
  Scenario: CFG-06 path inexistente rejeita carga total
    Given um Path que não existe no filesystem
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError
    And não retorna AppConfig
```

**Mapeamento:** `TestCFG06PathMissing`

### CFG-07 — JSON inválido (BDD-022)

```gherkin
  Scenario: CFG-07 JSON malformado rejeita carga total
    Given um arquivo com conteúdo que não é JSON válido
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError
    And a mensagem não faz dump completo do arquivo como segredo
```

**Mapeamento:** `TestCFG07InvalidJson`

### CFG-08 — Schema / type inválidos (BDD-022)

```gherkin
  Scenario: CFG-08 schema inválido rejeita carga total
    Given um JSON sem "connections" objeto, ou com type desconhecido
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError
    And não retorna AppConfig
```

**Mapeamento:** `TestCFG08InvalidSchemaAndType`

### CFG-09 — env de token ausente/blank (BDD-022)

```gherkin
  Scenario: CFG-09 variável token.env ausente ou blank rejeita carga total
    Given uma conexão github válida no JSON
    And a variável nomeada em token.env está ausente ou blank no ambiente do processo
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError citando o nome da env
    And não retorna AppConfig
```

**Mapeamento:** `TestCFG09MissingTokenEnv` (`test_missing_*`, `test_blank_*`)

### CFG-10 — Sem aplicação parcial (BDD-022 / BR-021)

```gherkin
  Scenario: CFG-10 uma conexão inválida impede qualquer AppConfig
    Given um JSON com uma conexão github válida e outra com type inválido
    And o token da conexão válida está resolvível
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError
    And nenhum AppConfig (nem subset) é retornado
```

**Mapeamento:** `TestCFG10NoPartialConfig`

### CFG-11 — file:// relativo rejeitado (BDD-022)

```gherkin
  Scenario: CFG-11 url file:// relativa ou sem esquema é rejeitada
    Given conexões git com url "file://repos" ou "https://example.com/repo.git"
    When o ConfigLoader tenta carregar cada uma
    Then levanta ConfigLoadError em ambos os casos
```

**Mapeamento:** `TestCFG11RejectRelativeOrNonFileUrl`

### CFG-12 — branches sem main (BDD-022 / ENG-T02-001)

```gherkin
  Scenario: CFG-12 revisions.branches sem main é rejeitado
    Given uma conexão válida exceto branches contendo só "develop"
    When o ConfigLoader tenta carregar
    Then levanta ConfigLoadError
```

**Mapeamento:** `TestCFG12BranchesRequireMain`

### CFG-13 — Token ausente em mensagem de erro (BDD-014 parcial)

```gherkin
  Scenario: CFG-13 valor do token não aparece em ConfigLoadError
    Given environ com GITHUB_TOKEN igual a um valor secreto conhecido
    And um JSON com falha de schema (ou conexão inválida) além do token.env
    When o ConfigLoader falha ao carregar
    Then str(ConfigLoadError) não contém o valor secreto
    And a mensagem pode citar o nome da variável de ambiente
```

**Mapeamento:** `TestCFG13SecretNotInErrorMessage`

### CFG-14 — Token ausente em str/repr do modelo (BDD-014 parcial)

```gherkin
  Scenario: CFG-14 valor do token não aparece em str/repr após carga ok
    Given JSON válido e environ com GITHUB_TOKEN secreto conhecido
    When o ConfigLoader carrega com sucesso
    Then str(AppConfig) e repr(AppConfig) não contêm o valor secreto
    And str/repr das conexões github também não contêm o valor secreto
```

**Mapeamento:** `TestCFG14SecretNotInModelString`
