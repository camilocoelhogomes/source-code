# BDD — T27-gap-sdk-dec015-conformity

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T27-gap-sdk-dec015-conformity` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Execução | `tests/bdd/test_dec015_conformity.py` (novo) + suítes referenciadas; sem Robot/e2e/GitHub real/Docker |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Escrito e aprovado pelo próprio Architect por instrução explícita do orquestrador (modo autônomo, pipeline T27); cobre texto integral BDD-024 conforme design §2–§4. |

## Convenções

- Texto-fonte: `requirements.md` §BDD-024 (citado literalmente no cabeçalho de cada
  cenário-cláusula), §DEC-015 (tabela), BR-024, DEC-016, DT-001.
- Camada de prova = **pytest / inspeção estática** (`inspect.getsource`, AST, leitura
  de `pyproject.toml`) — mesmo método já validado pelo inventário T01
  (`coverage-inventory.md`, campo `Método`). **Nenhum** cenário sobe GitHub real,
  Docker, Zoekt/Qdrant real nem Robot.
- Nomenclatura: `DEC015-01`..`DEC015-12` (uma cláusula/integração cada),
  `DEC015-13` (cobertura de texto integral, agregador), `DEC015-14` (consistência
  do artefato de auditoria da feature filha).
- Para integrações já providas com evidência BDD-024 explícita em suítes
  existentes (Git/GitPython, pathspec, Tree-sitter, Qdrant/openai, pins no
  manifesto), o cenário desta task **referencia** essa suíte como evidência
  primária e só acrescenta o assert incremental que falta (ex.: faixa de versão).
  Não reimplementa a asserção de comportamento já provada.
- Sem segredos em nenhum assert; strings de URL/token usadas são sempre fixtures
  sintéticas já presentes em testes existentes (nunca `.env` real).

---

## DEC015-01 — Matriz de pins DEC-015 no manifesto (faixa de versão)

**Dado** `pyproject.toml` (`[project.dependencies]`)
**Quando** cada linha da tabela DEC-015 (`requirements.md` §DEC-015) for verificada
**Então** todos os pacotes da tabela estão presentes: `PyGithub`, `GitPython`,
`pathspec`, `tree-sitter` (+ grammars `tree-sitter-python/java/javascript/typescript/
markdown/yaml/json/xml/toml`), `qdrant-client`, `openai`, `apscheduler`, `mcp`,
`fastapi`, `sqlalchemy`, `alembic`, `psycopg`
**E** cada pacote tem faixa de versão declarada (não `*`/sem versão) coerente com o
default DEC-015 (ex.: `sqlalchemy>=2`, `mcp>=1.27,<2`, `apscheduler>=3.10,<4`)
**E** nenhum desses nomes aparece como dependência **transitiva apenas** — todos
estão em `[project].dependencies` direto (evita drift silencioso de major version)

**Camada pytest:** reusa `DEC015_RUNTIME_PACKAGES` / `DEC015_TREE_SITTER_GRAMMARS` /
`_pyproject_deps` / `_dep_name` de `tests/bdd/test_container_delivery.py::TestCD05SdkManifest`
(import direto — sem reimplementar o parser TOML) e acrescenta o assert de faixa de
versão por pacote.

**Corner cases:**
- Pacote presente sem faixa de versão (`"mcp"` sem operador) → falha.
- Pacote com faixa que permite major incompatível com a tabela (ex.: `apscheduler>=4`) → falha.

---

## DEC015-02 — GitHub API via PyGithub (sem cliente HTTP caseiro)

**Dado** os módulos de produção `src/github_rag/sources/github/client.py` e
`src/github_rag/snapshot/github.py`
**Quando** o código-fonte desses módulos for inspecionado
**Então** ambos importam `Github`/`Auth` de `github` (PyGithub oficial)
**E** nenhum dos dois importa `requests`, `httpx`, `urllib.request` ou `urllib3`
para falar com a API REST do GitHub
**E** a porta pública (`GitHubApiClient`) não expõe parâmetros de paginação manual
(`page`, `per_page`) — a paginação é responsabilidade nativa do PyGithub

**Camada pytest:** `inspect.getsource` dos dois módulos + `inspect.signature` da
porta pública.

**Corner cases:**
- Reintrodução de `requests.get("https://api.github.com/...")` em qualquer um dos
  dois módulos → falha.
- Import indireto de `github` ausente (ex.: alguém substitui por stub próprio sem
  o pacote oficial instalado) → falha ao `import github` no próprio teste.

---

## DEC015-03 — Git local via GitPython / eliminação de DT-001 (referência)

**Dado** `tests/bdd/test_local_discovery_git_sdk.py::TestLocalDiscoveryGitSdkBdd`
(T20-SDK-01..03) já executável e verde
**Quando** a suíte consolidada for executada
**Então** ela declara essa suíte como evidência primária de GitPython
(DEC-015 linha "Git (local, snapshot, diff)")
**E** não duplica os asserts de `Repo.init`/bare/packed-refs/gitdir já cobertos —
apenas garante (import) que o módulo continua existindo e importável

**Camada pytest:** `importlib.import_module("tests.bdd.test_local_discovery_git_sdk")`
dentro de `TestDEC015CoordinatedReferences` (ver DEC015-13).

**Corner cases:**
- Módulo removido/renomeado sem atualizar a referência → falha no import.

---

## DEC015-04 — `.gitignore` via pathspec (referência)

**Dado** `tests/bdd/test_file_eligibility.py::TestELIG06PathspecNotHomemade` já
executável e verde
**Quando** a suíte consolidada for executada
**Então** ela declara essa suíte como evidência primária de `pathspec`
(DEC-015 linha "Matching de `.gitignore`")
**E** não duplica os asserts de GitWildMatch/negation/glob já cobertos

**Camada pytest:** mesma estratégia de referência de DEC015-03.

---

## DEC015-05 — Tree-sitter oficial (referência)

**Dado** `tests/bdd/test_treesitter_chunker.py::TestTS10OfficialSdk` já executável
e verde
**Quando** a suíte consolidada for executada
**Então** ela declara essa suíte como evidência primária de `tree-sitter` +
`OfficialGrammarRegistry`
**E** acrescenta apenas o assert de que **todas** as 9 grammars pinadas no
`pyproject.toml` (DEC015-01) resolvem via `OfficialGrammarRegistry` para o
`SourceLanguage` correspondente (prova que o pin não é "declarado mas não usado")

**Camada pytest:** reusa `OfficialGrammarRegistry` + itera `SourceLanguage` mapeado
a cada grammar pinada.

**Corner cases:**
- Grammar pinada no `pyproject.toml` sem `SourceLanguage`/extensão associada em
  `OfficialGrammarRegistry` → falha (pin órfão).

---

## DEC015-06 — Qdrant + embeddings OpenAI-compatible (referência)

**Dado** `tests/bdd/test_qdrant_vector_store.py::TestVS05QdrantOfficialSdk` e
`TestVS06OpenAIEmbedderSdk` já executáveis e verdes
**Quando** a suíte consolidada for executada
**Então** ela declara essas classes como evidência primária de `qdrant-client` e
`openai` (embeddings-only, sem chat/completions)
**E** não duplica os asserts de ausência de `requests`/`httpx`/`urllib` já cobertos

**Camada pytest:** mesma estratégia de referência de DEC015-03/04.

---

## DEC015-07 — Cron via APScheduler (sem parser caseiro)

**Dado** `src/github_rag/schedule/scheduler.py` e `src/github_rag/schedule/cron_expr.py`
**Quando** o código-fonte desses módulos for inspecionado
**Então** ambos importam de `apscheduler.*` (`BackgroundScheduler`, `CronTrigger`,
`JobLookupError`)
**E** nenhum dos dois implementa parsing manual de expressão cron (sem regex de
5/6 campos nem aritmética de dia-da-semana/dia-do-mês escrita à mão)
**E** a validação de expressão cron (`cron_expr.py`) delega a validação sintática ao
próprio `CronTrigger.from_crontab` (ou equivalente APScheduler), não a uma
implementação paralela

**Camada pytest:** `inspect.getsource` dos dois módulos; assert de presença de
`apscheduler` e ausência de padrões de parser manual (ex.: `split(" ")` seguido de
validação numérica de 5 campos fora do APScheduler).

**Corner cases:**
- `cron_expr.py` passa a validar com regex própria "por performance", sem
  `CronTrigger` → falha (viola DEC-015 "cliente caseiro").

---

## DEC015-08 — Servidor MCP via SDK oficial `mcp`

**Dado** `src/github_rag/mcp/server.py` e o helper `MCP_PKG`/`collect_imports`/
`FORBIDDEN_IMPORTS` de `tests/unit/mcp/helpers.py`
**Quando** os imports do pacote `github_rag.mcp` forem coletados (AST)
**Então** `mcp` está entre os imports coletados
**E** `mcp.server.fastmcp.FastMCP` é o binding usado para construir o servidor
(callable, instanciável)
**E** nenhum import de `FORBIDDEN_IMPORTS` (`qdrant_client`, `openai`, `httpx`,
`requests`, `github`, `git`, `fastmcp` solto, `urllib`, `urllib3`) aparece no
pacote `mcp`
**E** o `pyproject.toml` pina `mcp` em `>=1.27,<2` (reforça DEC015-01 nesta
integração específica)

**Camada pytest:** importa `MCP_PKG`, `collect_imports`, `FORBIDDEN_IMPORTS` de
`tests.unit.mcp.helpers` (sem reescrever o AST walk) + framing explícito BDD-024
que hoje só existe em `tests/unit/mcp/test_imports.py` (sem esse framing).

**Corner cases:**
- Pacote `mcp` passa a coexistir com biblioteca de terceiros `fastmcp` (não
  oficial) → falha (`fastmcp` solto banido).

---

## DEC015-09 — API HTTP da UI via FastAPI

**Dado** `src/github_rag/ui/app.py`, `src/github_rag/ui/api.py` e as constantes
`UI_PKG`/`DOMAIN_MODULES`/`FASTAPI_MODULES`/`FORBIDDEN_IN_DOMAIN`/
`FORBIDDEN_HOMEMADE` de `tests/unit/ui/test_imports.py`
**Quando** os imports desses módulos forem inspecionados
**Então** `app.py` e `api.py` importam `fastapi`
**E** os módulos de domínio puro (`ports.py`, `labels.py`, `serialize.py`,
`errors.py`) não importam `fastapi`/`starlette`/`uvicorn`/`httpx`
**E** nenhum módulo do pacote `ui` importa cliente HTTP caseiro
(`urllib`/`urllib3`/`aiohttp`/`requests`)

**Camada pytest:** importa as constantes/helpers de `tests.unit.ui.test_imports`
diretamente (sem reescrever o AST walk) + framing explícito BDD-024.

**Corner cases:**
- `ports.py` (domínio) passa a importar `fastapi` só para tipar um `Request` "de
  conveniência" → falha (viola separação domínio/transporte).

---

## DEC015-10 — PostgreSQL via SQLAlchemy 2.x + Alembic + psycopg3 (BR-024)

**Dado** `src/github_rag/catalog/postgres/models.py`,
`src/github_rag/catalog/postgres/factory.py`, `src/github_rag/schedule/postgres.py`
e `src/github_rag/delivery/wiring.py::run_alembic_upgrade`
**Quando** esses módulos forem inspecionados
**Então** os modelos ORM usam a API SQLAlchemy **2.x** (`DeclarativeBase`,
`Mapped`, `mapped_column`, `Session`) — não a API legada
(`sqlalchemy.ext.declarative.declarative_base()`)
**E** `run_alembic_upgrade` invoca `alembic.command.upgrade(cfg, "head")` — nenhuma
DDL manual (`CREATE TABLE`/`ALTER TABLE` via `text()`) substitui a migration
**E** toda fixture/exemplo de `DATABASE_URL` usada nos testes de produção usa o
driver `postgresql+psycopg://` (psycopg **3**), nunca `postgresql+psycopg2://`
**E** `pyproject.toml` pina `psycopg[binary]` (pacote `psycopg`, não `psycopg2`/
`psycopg2-binary`) e `sqlalchemy>=2`

**Camada pytest:** `inspect.getsource` dos módulos citados + regex sobre as
fixtures de URL já usadas em `tests/unit/delivery/test_wiring.py` e
`tests/integration/test_postgres_catalog_repository.py` + checagem de nomes de
pacote no `pyproject.toml` (reusa DEC015-01).

**Corner cases:**
- Qualquer fixture de teste de produção passa a usar `psycopg2` → falha (driver
  errado quebra BR-024, mesmo que só em teste, pois indicaria contrato de URL
  divergente do runtime).
- `models.py` reintroduz `declarative_base()` clássico → falha (não é a superfície
  2.0 exigida pela tabela DEC-015).

---

## DEC015-11 — Zoekt: adaptador fino sobre CLI/HTTP oficiais (DEC-016), adaptador **real**

**Dado** `src/github_rag/index/zoekt/index.py` (`ZoektExactCodeIndex`),
`client.py` (`HttpZoektSearchTransport`) e `runner.py` (`SubprocessZoektIndexRunner`)
**Quando** esses três módulos forem inspecionados
**Então** `HttpZoektSearchTransport.post_search` faz `POST {base_url}/api/search`
(endpoint HTTP **oficial** documentado do Zoekt) via `urllib.request` — sem SDK
proprietário nem protocolo reinventado
**E** `SubprocessZoektIndexRunner.run` invoca `subprocess.run` com `shell=False`
sobre um binário CLI **oficial** (`zoekt-index`/`zoekt-git-index`, conforme
`_DEFAULT_INDEX_BIN`/`_DEFAULT_GIT_INDEX_BIN`) — nunca via `shell=True`/string
**E** `ZoektExactCodeIndex` **não** lê/escreve bytes de shard (`.zoekt`) nem
implementa parsing binário de índice — delega 100% ao binário `zoekt-index` e ao
JSON de resposta `/api/search`
**E** o teste BDD já existente (`tests/bdd/test_zoekt_adapter.py::TestZOEKT04FakePortContractNoRealZoekt`)
prova o `FakeExactCodeIndex`/Protocol, mas **não** prova esta cláusula sobre o
adaptador real — este cenário fecha esse gap especificamente

**Camada pytest:** `inspect.getsource` dos três módulos; asserts positivos
(literais `zoekt-index`, `/api/search`, `subprocess.run`) e negativos (ausência de
manipulação de bytes/`struct.pack`/`mmap`/parsing de formato de shard próprio).

**Corner cases:**
- `ZoektExactCodeIndex` passa a chamar `shell=True` com string montada por
  concatenação → falha (risco de injeção + desvio do contrato "lista de args").
- Introdução de leitura direta de arquivo de shard (`*.zoekt`) para "otimização"
  → falha (reimplementação de formato proprietário, violação DEC-016 explícita).

---

## DEC015-12 — DT-001: eliminação do parsing ad-hoc de `.git`

**Dado** `src/github_rag/sources/local/git_fs.py`
**Quando** o código-fonte for inspecionado
**Então** o módulo importa `Repo` de `git` (GitPython) — `from git import Repo` ou
`from git.repo import Repo`
**E** usa `with Repo(...)` para abrir o repositório
**E** **não** contém as strings `"packed-refs"`, `_resolve_git_dir` nem
`_has_main_branch` (funções/parsing ad-hoc eliminados por T20)

**Camada pytest:** `inspect.getsource(git_fs)` com os mesmos literais já validados
comportalmente por `tests/bdd/test_local_discovery_git_sdk.py::test_t20_sdk01_production_uses_gitpython_no_adhoc_parse`
— repetição **mínima e deliberada** desta cláusula específica de BDD-024
(rastreabilidade clause-level), não da suíte comportamental completa de T20.

**Corner cases:**
- Regressão futura reintroduz leitura direta de `.git/packed-refs` "por
  performance" → falha nomeada (`DEC015-12`) além da falha em T20-SDK-01,
  reforçando o sinal de regressão de dívida técnica.

---

## DEC015-13 — Cobertura de texto integral de BDD-024 (agregador)

**Dado** o texto integral de BDD-024 (`requirements.md` §BDD-024: Dado/Quando/Então
+ 4 cláusulas "E")
**Quando** cada cláusula for mapeada a um ou mais módulos de teste responsáveis
**Então** existe um mapa explícito cláusula → módulo(s) no próprio arquivo de teste
(dict Python, não só comentário), cobrindo:

| Cláusula BDD-024 | Módulo(s) responsável(is) |
|---|---|
| SDK/cliente oficial por integração (GitHub/Git/gitignore/Tree-sitter/Qdrant/SLM/cron/MCP/PostgreSQL) | DEC015-02, 03, 04, 05, 06, 07, 08, 10 |
| PostgreSQL via SQLAlchemy 2.x + Alembic + psycopg3 (BR-024) | DEC015-10 |
| Zoekt via adaptador fino (DEC-016) | DEC015-11 |
| Nenhuma integração reinventa cliente/CLI/protocolo | DEC015-02, 07, 09, 11 (asserts negativos) |
| Eliminação de DT-001 | DEC015-12 |

**E** cada módulo referenciado no mapa é importável (`importlib.import_module`)
**E** o teste falha, nomeando a cláusula e o módulo, se qualquer entrada do mapa
deixar de importar (proteção contra lacuna silenciosa por rename/remoção)

**Camada pytest:** classe `TestBDD024FullTextCoverage` — percorre o mapa e chama
`importlib.import_module` por entrada; falha cedo com `ImportError` anotado.

**Corner cases:**
- Alguém remove `tests/bdd/test_zoekt_adapter.py` pensando ser redundante com
  DEC015-11 → falha nomeada na cláusula "Zoekt via adaptador fino", mesmo que
  DEC015-11 continue passando isoladamente (o mapa cobre os dois).

---

## DEC015-14 — Consistência do artefato de auditoria (feature filha) após fechamento

**Dado** `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md`
(SoT de lacunas, T01) e as suítes de regressão dessa feature filha
(`tests/bdd/test_mvp_e2e_audit_coverage_inventory.py`,
`tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py`)
**Quando** DEC015-01..13 passarem (prova integral de BDD-024 registrada)
**Então** a linha `BDD-024` da matriz passa a `status=coberto-integral`,
`evidencia_pytest` referencia `tests/bdd/test_dec015_conformity.py` (+ suítes
coordenadas), `nota_parcial_t21=n/a`, `motivo_lacuna=—`
**E** `T21_KNOWN_PARTIAL_OR_SMOKE` (em `test_mvp_e2e_audit_coverage_inventory.py`)
não contém mais `"BDD-024"`, preservando `BDD-003`/`BDD-006`/`BDD-013` intocados
**E** `EXPECTED_LACUNA_BDDS` (em `test_mvp_e2e_audit_gap_fill_backlog.py`) não
contém mais `"BDD-024"`, preservando `DENYLIST_PARTIAL` intocado (T27 continua
citado no backlog como a task que fechou a lacuna)
**E** nenhuma outra linha/asserção dessas duas suítes muda de resultado

**Camada pytest:** as próprias suítes citadas, após edição pontual (não é um teste
novo — é o efeito esperado sobre testes já existentes de outra feature, tratado
como critério de aceite desta task; ver design §9/§10 para o racional do
cross-feature touch).

**Corner cases:**
- Editar `EXPECTED_LACUNA_BDDS`/`T21_KNOWN_PARTIAL_OR_SMOKE` além de `BDD-024`
  (ex.: remover `BDD-003` por engano) → fora de escopo; QA/Developer devem rodar
  o diff completo dessas duas suítes e confirmar que só a entrada `BDD-024` muda.

---

## Rastreabilidade

| Cenário | Cláusula BDD-024 / Regra | Evidência primária | Gap fechado |
|---|---|---|---|
| DEC015-01 | "SDK/cliente oficial listado em DEC-015" (pins) | `test_container_delivery.py::TestCD05SdkManifest` (reuso) + versão | faixa de versão por linha |
| DEC015-02 | GitHub → PyGithub | novo | binding real + framing BDD-024 |
| DEC015-03 | Git → GitPython / DT-001 | `test_local_discovery_git_sdk.py` (referência) | — (já integral) |
| DEC015-04 | `.gitignore` → pathspec | `test_file_eligibility.py` (referência) | — (já integral) |
| DEC015-05 | Tree-sitter | `test_treesitter_chunker.py` (referência) + grammars órfãs | grammar↔registry |
| DEC015-06 | Qdrant/SLM → qdrant-client/openai | `test_qdrant_vector_store.py` (referência) | — (já integral) |
| DEC015-07 | Cron → APScheduler | novo | binding real + framing BDD-024 |
| DEC015-08 | MCP → SDK `mcp` | novo (reusa helper unit/mcp) | framing BDD-024 |
| DEC015-09 | API HTTP UI → FastAPI | novo (reusa helper unit/ui) | framing BDD-024 |
| DEC015-10 | PostgreSQL → SQLAlchemy2/Alembic/psycopg3 (BR-024) | novo | prova integral consolidada |
| DEC015-11 | Zoekt → adaptador fino (DEC-016) | novo | adaptador **real**, não só Fake |
| DEC015-12 | DT-001 eliminado | novo (clause-level, mínimo) | rastreabilidade explícita |
| DEC015-13 | Texto integral (agregador) | novo | mapa cláusula→módulo |
| DEC015-14 | Consistência de auditoria pós-fechamento | edição de 2 suítes da filha | status refletido |

## Execução

```bash
python -m pytest tests/bdd/test_dec015_conformity.py -q
python -m pytest tests/bdd/test_mvp_e2e_audit_coverage_inventory.py tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py -q
```

Estado esperado **antes** da implementação Developer: `tests/bdd/test_dec015_conformity.py`
**não existe** (RED por ausência de artefato); as duas suítes de auditoria estão
**verdes** no estado atual (BDD-024 = `lacuna`).

Estado esperado **depois** da implementação: `test_dec015_conformity.py` **PASS**
(DEC015-01..13); as duas suítes de auditoria **PASS** com BDD-024 removido dos
conjuntos de lacuna/denylist (DEC015-14) e nenhuma outra asserção alterada.

---

**Decisão:** `APPROVED_BY_ARCHITECT`
**Data:** 2026-07-19
**Autor:** tech-lead-architect
**Versão:** v0.1.0
