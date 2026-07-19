# Unit Test Plan — T27-gap-sdk-dec015-conformity

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T27-gap-sdk-dec015-conformity` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `TESTS_READY_FOR_REVIEW` |
| Versão | `0.1.0` |
| Design / BDD / Interfaces | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Cobertura alvo | ≥95% global (run padrão); nenhum `src/github_rag/**` alterado por esta task |
| Branch | `feature/github-etl-mcp-rag-T27-gap-sdk-dec015-conformity` |
| Worktree | `github_rag-wt-T27` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Plano + suíte RED `tests/bdd/test_dec015_conformity.py` + `tests/bdd/support/dec015_pins.py` (I-T27-001) + promoção `tests/unit/ui/helpers.py` (I-T27-002). RED nomeado em DEC015-01 (alembic/psycopg sem faixa de versão no `pyproject.toml` — gap real, não estilístico). |

## 1. Estratégia

| Camada | Arquivo | Natureza |
|---|---|---|
| Pins/manifesto | `tests/bdd/support/dec015_pins.py` | módulo de dado/parse público (I-T27-001), sem lógica de asserção |
| Suíte consolidada | `tests/bdd/test_dec015_conformity.py` | 12 `TestCase` (DEC015-01..12) + `TestBDD024FullTextCoverage` (DEC015-13) |
| Helpers UI promovidos | `tests/unit/ui/helpers.py` | adição de `DOMAIN_MODULES`/`FASTAPI_MODULES`/`FORBIDDEN_IN_DOMAIN`/`FORBIDDEN_HOMEMADE`/`imports_of_file` (I-T27-002) |
| Refactor neutro | `tests/bdd/test_container_delivery.py::TestCD05SdkManifest` | passa a importar de `dec015_pins` em vez de `_pyproject_deps`/`_dep_name` locais — mesma asserção |
| Refactor neutro | `tests/unit/ui/test_imports.py::TestUiImports` | passa a importar de `tests.unit.ui.helpers` em vez de `_imports`/constantes locais — mesma asserção |

- 100% inspeção estática (`Path.read_text`, `ast`, `tomllib`) + `importlib.import_module`. Nenhum GitHub/Docker/Zoekt/Qdrant real, nenhum Robot.
- Nenhuma alteração em `src/github_rag/**`, `e2e/robot/**`, composes ou `coverage-inventory.md`/suítes de auditoria da feature filha (DEC015-14 fica fora do escopo desta etapa QA — ver design §2.5, mission item 4 do orquestrador).
- Os dois refactors (`dec015_pins`, `tests/unit/ui/helpers.py`) são comportamentalmente neutros: as suítes já existentes que os consomem devem continuar 100% verdes após o refactor — isso é verificado nesta etapa e citado como corner case (UT-DEC-R01/R02).
- RED esperado antes desta etapa: o arquivo `tests/bdd/test_dec015_conformity.py` **não existe** — qualquer coleta pytest sobre ele falha por `ModuleNotFoundError`. Após criado, a maior parte das classes passa de imediato porque a produção (T05/T08/T10/T15/T17/T18/T20) já usa os SDKs oficiais — a suíte é evidência consolidada, não implementação nova (design §2, §8). O RED nomeado e real que sobrevive à criação da suíte é **DEC015-01** para os pacotes `alembic` e `psycopg[binary]`, que hoje não declaram faixa de versão no `pyproject.toml` — gap genuíno que o Developer deve fechar (fora de `src/github_rag/**`).

## 2. Matriz — `tests/bdd/support/dec015_pins.py` (contrato de dado)

| ID | Cenário | Esperado | Corner case |
|---|---|---|---|
| UT-DEC-P01 | `read_pyproject_dependencies()` sobre o `pyproject.toml` real | lista não vazia de specs | — |
| UT-DEC-P02 | `read_pyproject_dependencies(path)` com `pyproject.toml` sem `[project].dependencies` | `AssertionError` | tabela ausente/vazia |
| UT-DEC-P03 | `dependency_name("mcp>=1.27,<2")` | `"mcp"` | operadores múltiplos (`>=`,`<`) |
| UT-DEC-P04 | `dependency_name("psycopg[binary]")` | `"psycopg"` | extra `[...]` sem operador de versão |
| UT-DEC-P05 | `dependency_name("tree-sitter==0.26.0")` | `"tree-sitter"` | pin exato `==` |
| UT-DEC-P06 | `dependency_spec("mcp", deps)` | linha completa `"mcp>=1.27,<2"` | — |
| UT-DEC-P07 | `dependency_spec("nao-existe", deps)` | levanta (nome ausente) | pacote não declarado |
| UT-DEC-P08 | `DEC015_RUNTIME_PACKAGES`/`DEC015_TREE_SITTER_GRAMMARS` importáveis e não vazios | `len(...) > 0` | módulo novo sem regressão de import |

## 3. Matriz — `tests/unit/ui/helpers.py` (promoção I-T27-002)

| ID | Cenário | Esperado | Corner case |
|---|---|---|---|
| UT-DEC-R01 | `tests/unit/ui/test_imports.py::TestUiImports` continua 100% verde após refactor para importar de `helpers.py` | 3/3 testes passam, mesmas asserções | regressão comportamental do refactor |
| UT-DEC-R02 | `imports_of_file(path)` sobre `ports.py` (domínio) | conjunto de imports sem `fastapi`/`starlette`/`uvicorn`/`httpx` | mesma extração que `_imports` privado antigo |
| UT-DEC-R03 | `imports_of_file(path)` sobre arquivo inexistente | `FileNotFoundError`/`OSError` propagada (sem swallow) | corner ausência de arquivo |

## 4. Matriz — `tests/bdd/test_dec015_conformity.py` (DEC015-01..13)

| ID | Classe | Cenário | Esperado | Corner case coberto |
|---|---|---|---|---|
| UT-DEC01-01 | `TestDEC01PinsVersionMatrix` | Todos os pacotes de `DEC015_RUNTIME_PACKAGES` + grammars presentes em `[project].dependencies` | sem `missing` | reusa CD-05, sem duplicar |
| UT-DEC01-02 | `TestDEC01PinsVersionMatrix` | Cada pacote tem faixa de versão coerente com `DEC015_VERSION_CONSTRAINTS`/regex mínima | todas as specs casam | **RED esperado**: `alembic`, `psycopg` sem operador de versão hoje |
| UT-DEC01-03 | `TestDEC01PinsVersionMatrix` | Pacote hipotético sem operador (`"mcp"` puro) | falharia (asserção simulada via fixture local, não via pyproject real) | pin removido |
| UT-DEC01-04 | `TestDEC01PinsVersionMatrix` | Pacote com major incompatível (`apscheduler>=4"`) via fixture local | falharia | drift de major version |
| UT-DEC02-01 | `TestDEC02GitHubPyGithubBinding` | `sources/github/client.py` e `snapshot/github.py` importam `from github import` | ambos casam | dois módulos, uma regra cada |
| UT-DEC02-02 | `TestDEC02GitHubPyGithubBinding` | Nenhum dos dois contém `requests.`/`httpx.`/`urllib.request` | forbidden ausente | cliente HTTP caseiro reintroduzido |
| UT-DEC02-03 | `TestDEC02GitHubPyGithubBinding` | `GitHubApiClient.iter_org_repos`/`list_org_repos` sem parâmetros `page`/`per_page` | `inspect.signature` sem esses nomes | paginação manual na porta pública |
| UT-DEC03-01 | `TestDEC03GitPythonReference` | `assert_module_importable("tests.bdd.test_local_discovery_git_sdk", clause=...)` | importa sem erro | suíte T20 já existe/verde |
| UT-DEC03-02 | `TestDEC03GitPythonReference` | Módulo dotted inexistente (`"tests.bdd.test_nao_existe"`) via chamada direta no teste de corner | `AssertionError` nomeando clause+módulo | módulo removido/renomeado |
| UT-DEC04-01 | `TestDEC04PathspecReference` | `assert_module_importable("tests.bdd.test_file_eligibility", ...)` | importa sem erro | ELIG-06 já cobre pathspec |
| UT-DEC05-01 | `TestDEC05TreeSitterGrammarWiring` | As 9 grammars de `DEC015_TREE_SITTER_GRAMMARS` resolvem via `OfficialGrammarRegistry` para `SourceLanguage` | todas resolvem sem `GrammarUnavailableError` | pin órfão (grammar sem `SourceLanguage`/extensão mapeada) |
| UT-DEC05-02 | `TestDEC05TreeSitterGrammarWiring` | Extensão fictícia sem grammar (`.rs`) — reaproveita TS-07 | levanta `GrammarUnavailableError` (referência, não redundante) | não duplica lógica já provada |
| UT-DEC06-01 | `TestDEC06QdrantOpenAiReference` | `assert_module_importable("tests.bdd.test_qdrant_vector_store", ...)` | importa sem erro | VS-05/06 já cobrem qdrant/openai |
| UT-DEC07-01 | `TestDEC07ApSchedulerBinding` | `scheduler.py` importa `apscheduler.*` (`BackgroundScheduler`, `CronTrigger`, `JobLookupError`) | todos presentes | binding real |
| UT-DEC07-02 | `TestDEC07ApSchedulerBinding` | `cron_expr.py` importa `CronTrigger` e delega `from_crontab` | presente | validação não é reimplementada |
| UT-DEC07-03 | `TestDEC07ApSchedulerBinding` | Nenhum dos dois módulos define parser manual de campo cron (`_parse_cron_field`, regex `\d{1,2}` fora do APScheduler) | ausente | reintrodução de parser caseiro "por performance" |
| UT-DEC08-01 | `TestDEC08McpSdkBinding` | `mcp` está entre os imports de `MCP_PKG` (via `collect_imports`) | presente | reaproveita helper unit/mcp |
| UT-DEC08-02 | `TestDEC08McpSdkBinding` | `mcp.server.fastmcp.FastMCP` é usado em `server.py` (regex no source) | presente | binding concreto, não só import solto |
| UT-DEC08-03 | `TestDEC08McpSdkBinding` | Nenhum import de `FORBIDDEN_IMPORTS` no pacote `mcp` (inclui `fastmcp` solto) | conjunto vazio | coexistência com `fastmcp` de terceiros |
| UT-DEC08-04 | `TestDEC08McpSdkBinding` | `pyproject.toml` pina `mcp` em `>=1.27,<2` | casa regex | reforço DEC015-01 nesta integração |
| UT-DEC09-01 | `TestDEC09FastApiBinding` | `DOMAIN_MODULES` sem `FORBIDDEN_IN_DOMAIN` (via `tests.unit.ui.helpers`) | conjunto vazio por módulo | domínio importando `fastapi` "de conveniência" |
| UT-DEC09-02 | `TestDEC09FastApiBinding` | `FASTAPI_MODULES` (`app.py`,`api.py`) importam `fastapi` | presente | binding real |
| UT-DEC09-03 | `TestDEC09FastApiBinding` | Nenhum módulo do pacote `ui` importa `FORBIDDEN_HOMEMADE` | conjunto vazio | cliente HTTP caseiro na UI |
| UT-DEC10-01 | `TestDEC10Br024Postgres` | `catalog/postgres/models.py` usa `DeclarativeBase`/`Mapped`/`mapped_column`, não `declarative_base()` legado | presente/ausente conforme | regressão para API 1.x |
| UT-DEC10-02 | `TestDEC10Br024Postgres` | `delivery/wiring.py::run_alembic_upgrade` chama `alembic.command.upgrade` (via source) | presente | DDL manual substituindo migration |
| UT-DEC10-03 | `TestDEC10Br024Postgres` | `run_alembic_upgrade` **não** contém `CREATE TABLE`/`ALTER TABLE` via `text(` | ausente | DDL manual paralelo |
| UT-DEC10-04 | `TestDEC10Br024Postgres` | Fixtures de `DATABASE_URL` em `test_wiring.py`/`test_postgres_catalog_repository.py` usam `postgresql+psycopg://`, nunca `+psycopg2://` | regex sobre arquivos de teste já existentes | fixture usando driver errado |
| UT-DEC10-05 | `TestDEC10Br024Postgres` | `pyproject.toml` pina `psycopg`/`sqlalchemy>=2` (reusa `dec015_pins`) | presente | — |
| UT-DEC11-01 | `TestDEC11Dec016ZoektRealAdapter` | `client.py::HttpZoektSearchTransport.post_search` contém `/api/search` + `urllib.request` | presentes | SDK proprietário reintroduzido |
| UT-DEC11-02 | `TestDEC11Dec016ZoektRealAdapter` | `runner.py::SubprocessZoektIndexRunner.run` usa `subprocess.run`; **nunca** `shell=True` | positivo+negativo | injeção via `shell=True` |
| UT-DEC11-03 | `TestDEC11Dec016ZoektRealAdapter` | `index.py` referencia `_DEFAULT_INDEX_BIN` (`zoekt-index`) e `post_search`; **sem** `struct.pack`/`struct.unpack`/`mmap`/literal `.zoekt` | positivo+negativo | leitura direta de shard binário |
| UT-DEC12-01 | `TestDEC12Dt001Elimination` | `sources/local/git_fs.py` importa `Repo` de `git`; usa `with Repo(` | presente | regressão DT-001 |
| UT-DEC12-02 | `TestDEC12Dt001Elimination` | **Ausência** de `"packed-refs"`, `_resolve_git_dir`, `_has_main_branch` no source | ausentes | reintrodução de parsing ad-hoc "por performance" |
| UT-DEC13-01 | `TestBDD024FullTextCoverage` | Cada módulo de `BDD024_CLAUSE_MODULE_MAP` é importável | sem erro | mapa completo |
| UT-DEC13-02 | `TestBDD024FullTextCoverage` | Entrada fictícia do mapa com módulo inexistente (teste isolado via `assert_module_importable` direto, não mutando o mapa real) | `AssertionError` nomeando clause+módulo | lacuna silenciosa por rename/remoção |
| UT-DEC13-03 | `TestBDD024FullTextCoverage` | `BDD024_CLAUSE_MODULE_MAP` cobre as 5 chaves de cláusula do design §12/bdd §DEC015-13 | `set(mapa.keys())` esperado | cláusula sem dono |

## 5. Matriz — helpers internos do módulo novo (`SourceConformityRule`/`assert_source_conforms`/`assert_module_importable`)

| ID | Cenário | Esperado | Corner case |
|---|---|---|---|
| UT-DEC-H01 | `assert_source_conforms` com todos `required_patterns` presentes e nenhum `forbidden_patterns` | retorna o source (`str`) sem levantar | fluxo feliz |
| UT-DEC-H02 | `assert_source_conforms` com `required_patterns` ausente | `AssertionError` citando `rule.clause` e o padrão faltante | required ausente |
| UT-DEC-H03 | `assert_source_conforms` com `forbidden_patterns` presente | `AssertionError` citando `rule.clause` e o padrão banido encontrado | forbidden presente |
| UT-DEC-H04 | `assert_source_conforms` com `module_path` inexistente | `AssertionError`/`FileNotFoundError` claro (não engolido) | arquivo ausente/renomeado |
| UT-DEC-H05 | `SourceConformityRule` com `forbidden_patterns` vazio (default) | não levanta por ausência de forbidden | default `field(default_factory=tuple)` |
| UT-DEC-H06 | `assert_module_importable` com dotted path válido | retorna o módulo importado | fluxo feliz |
| UT-DEC-H07 | `assert_module_importable` com dotted path malformado/vazio | `AssertionError` nomeando `clause` | entrada inválida |
| UT-DEC-H08 | `assert_module_importable` com módulo cujo import levanta `ImportError` por erro interno (não por ausência) | `AssertionError` encadeando a causa original (`raise ... from exc`) | erro interno do módulo referenciado, não só ausência |

## 6. Execução (estado RED antes da implementação completa)

```bash
python -m pytest tests/bdd/test_dec015_conformity.py -q
python -m pytest tests/bdd/support -q  # coleta indireta via test_dec015_conformity
python -m pytest tests/bdd/test_container_delivery.py::TestCD05SdkManifest -q
python -m pytest tests/unit/ui/test_imports.py -q
```

Resultado esperado nesta etapa: suíte nova criada e majoritariamente verde (produção já conforme desde T05/T08/T10/T15/T17/T18/T20); **falha nomeada** em `TestDEC01PinsVersionMatrix.test_all_dec015_packages_declare_a_version_range` citando `alembic` e `psycopg` — RED real e íntegro, não circundado. Refactors de `TestCD05SdkManifest`/`TestUiImports` permanecem verdes (comportamento idêntico).

## 7. Cobertura

- Nenhuma linha de `src/github_rag/**` é adicionada por esta task; cobertura global não deve regredir (design §8). `tests/bdd/support/dec015_pins.py` e os testes novos são código de teste, fora de `--cov=github_rag`.
- Gate de cobertura ≥95% do run padrão (`fail_under=95` já configurado em `pyproject.toml`) deve ser mantido — verificado via `python -m pytest -q` completo na etapa Developer (fora do escopo desta etapa QA, que roda só os módulos afetados para evidenciar o RED nomeado sem esperar a suíte completa a cada iteração).

## 8. Handoff

- Architect: revisar se `DEC015_INTEGRATION_RULES`/`BDD024_CLAUSE_MODULE_MAP` cobrem exatamente as cláusulas do design sem regra órfã, e se os dois refactors (`dec015_pins`, `tests/unit/ui/helpers.py`) preservam 100% o comportamento das suítes antigas.
- Developer: fechar o RED nomeado de `alembic`/`psycopg` (faixa de versão em `pyproject.toml` — fora de `src/github_rag/**`), confirmar que nenhuma outra classe precisa de ajuste de produção, e então tratar DEC015-14 (coverage-inventory + duas suítes de auditoria da feature filha) como etapa final documental.

---

**Decisão:** `TESTS_READY_FOR_REVIEW`
**Data:** 2026-07-19
**Autor:** QA Engineer
**Versão:** v0.1.0
