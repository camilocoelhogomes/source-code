# Plano de testes unitários — T10-zoekt-adapter

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T10-zoekt-adapter` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |
| Interfaces base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T10-zoekt-adapter` |
| Escopo | Testes unitários dos contratos T10 (modelos, erros, fake, transport HTTP, runner CLI, adaptador). Sem implementação de produção. |

## 1. Objetivo

Verificar, **antes da implementação**, o comportamento congelado em `interfaces.md`
§3: modelos imutáveis, `ExactCodeIndexError`, `FakeExactCodeIndex`,
`HttpZoektSearchTransport`, `SubprocessZoektIndexRunner` e `ZoektExactCodeIndex`.
A suíte deve falhar (RED) pela ausência dos módulos/símbolos sob
`github_rag.index.zoekt.*` (hoje só existe placeholder em `__init__.py`).

## 2. Superfície sob teste

| Símbolo | Módulo | Tipo |
|---|---|---|
| `FileToIndex` / `ExactMatch` / `ExactSearchQuery` | `index/zoekt/models.py` | frozen + defaults |
| `ExactCodeIndexError` | `index/zoekt/errors.py` | erro tipado; sem segredos |
| `FakeExactCodeIndex` | `index/zoekt/fake.py` | porta em memória |
| `HttpZoektSearchTransport` | `index/zoekt/client.py` | POST `/api/search` stdlib |
| `SubprocessZoektIndexRunner` / `ZoektIndexRunResult` | `index/zoekt/runner.py` | CLI via subprocess |
| `ZoektExactCodeIndex` | `index/zoekt/index.py` | adaptador porta ↔ transportes |

**Fora de escopo unitário:** container Zoekt real (T19), orquestração T14, QueryService T16, gRPC, parse de shards.

## 3. Matriz de casos

### 3.1 `test_models.py` — frozen + defaults

| ID | Caso | Expectativa | Contrato |
|---|---|---|---|
| M-01 | `FileToIndex` frozen | `FrozenInstanceError` em setattr | I-T10-002 |
| M-02 | `FileToIndex` guarda campos | repository/path/commit/content | D-T10-003 |
| M-03 | `ExactMatch` frozen | `FrozenInstanceError` | I-T10-002 |
| M-04 | `ExactMatch.line_number` default `None` | default | D-T10-003 |
| M-05 | `ExactSearchQuery` frozen | `FrozenInstanceError` | I-T10-002 |
| M-06 | `ExactSearchQuery` defaults | `repository/path_prefix/max_matches=None`, `context_lines=2` | I-T10-002 |

### 3.2 `test_errors.py` — ExactCodeIndexError

| ID | Caso | Expectativa | Contrato |
|---|---|---|---|
| E-01 | atributos `operation` / `repository` / `commit` | propriedades iguais ao ctor | I-T10-007 |
| E-02 | `operation` sem repo/commit | `None` nos opcionais | D-T10-004 |
| E-03 | `str`/`repr` sem segredo | token fixture ausente | I-T10-007 / ZOEKT-03 |
| E-04 | herda `Exception` | `isinstance` | D-T10-004 |
| E-05 | `__cause__` preservável | `raise ... from cause` | D-T10-004 |

### 3.3 `test_fake.py` — FakeExactCodeIndex

| ID | Caso | Expectativa | Contrato |
|---|---|---|---|
| F-01 | index + search substring | hit com repo/path/commit/snippet | ZOEKT-01/02 |
| F-02 | `fail_operations={"index"}` | `ExactCodeIndexError`, sem segredo | ZOEKT-03 |
| F-03 | `fail_operations={"search"}` | `ExactCodeIndexError` | ZOEKT-03 |
| F-04 | `fail_operations={"delete"}` | `ExactCodeIndexError` | I-T10-015 |
| F-05 | `delete_repository` remove só o repo | outro repo permanece | ZOEKT-05 |
| F-06 | delete ausente = no-op | sem raise | ZOEKT-05 |
| F-07 | `files=[]` no-op | search vazio depois | I-T10-005 / ZOEKT-06 |
| F-08 | `pattern=""` → `()` | sem erro | I-T10-006 / ZOEKT-07 |
| F-09 | reindex substitui conjunto | path ausente some; commit novo | I-T10-013 / ZOEKT-08 |
| F-10 | filtro `repository` | só hits do repo | I-T10-015 |
| F-11 | filtro `path_prefix` | só paths com prefixo | I-T10-015 |
| F-12 | mismatch FileToIndex repository | `ExactCodeIndexError` | I-T10-004 |
| F-12b | mismatch FileToIndex commit | `ExactCodeIndexError` | I-T10-004 |
| F-13 | satisfaz Protocol | `isinstance(..., ExactCodeIndex)` | I-T10-015 / ZOEKT-04 |
| F-14 | ordenação determinística | `(repo, path, line, snippet)` | I-T10-016 |

### 3.4 `test_client.py` — HttpZoektSearchTransport

| ID | Caso | Expectativa | Contrato |
|---|---|---|---|
| C-01 | POST `{base}/api/search` body JSON oficial | url termina em `/api/search`; body tem `Q` e `Opts` | I-T10-008 / DEC-016 |
| C-02 | resposta JSON → `Mapping` | dict parseado | §3.6 |
| C-03 | HTTP 500 → exceção envelopável | `OSError`/`URLError`/`HTTPError`/`ValueError` (não engolida) | §3.6 |
| C-04 | HTTP 404 → exceção envelopável | idem | §3.6 |
| C-05 | JSON inválido → envelopável | `ValueError`/`JSONDecodeError` | §3.6 |
| C-06 | `base_url` sem duplicar `/api/search` | path único | §3.6 |
| C-07 | timeout passado ao opener | kwargs/timeout refletido (mock) | §3.6 |

### 3.5 `test_runner.py` — SubprocessZoektIndexRunner

| ID | Caso | Expectativa | Contrato |
|---|---|---|---|
| R-01 | `run(argv)` chama subprocess com lista | `shell=False`; argv idêntico | I-T10-008 |
| R-02 | exit 0 → `ZoektIndexRunResult` | returncode/stdout/stderr | §3.7 |
| R-03 | exit ≠ 0 → ainda retorna resultado | returncode propagado (adaptador envelopa) | §3.7 |
| R-04 | binário ausente → exceção envelopável | `FileNotFoundError`/`OSError` | §3.7 |
| R-05 | `ZoektIndexRunResult` frozen | `FrozenInstanceError` | §3.7 |

### 3.6 `test_index.py` — ZoektExactCodeIndex

| ID | Caso | Expectativa | Contrato |
|---|---|---|---|
| I-01 | `index` materializa tree + chama runner | argv contém `zoekt-index`, `-index`, `index_dir`, tree com arquivos | I-T10-009 |
| I-02 | conteúdo escrito no tree | path relativo → bytes do `FileToIndex` | D-T10-001 |
| I-03 | runner exit ≠ 0 → `ExactCodeIndexError(operation="index")` | tipado; sem segredo | I-T10-007 |
| I-04 | `files=[]` no-op | runner **não** chamado | I-T10-005 |
| I-05 | mismatch FileToIndex → erro; runner não chamado | `ExactCodeIndexError` | I-T10-004 |
| I-06 | `search` mapeia FileMatches → `ExactMatch` | repo/path/snippet; commit do mapa | I-T10-011 |
| I-07 | `pattern=""` → `()`; transport não chamado | I-T10-006 |
| I-08 | escape literal (metacaracteres) | `Q` usa quoting/`content:"…"`; não regex cru | I-T10-010 |
| I-09 | filtros `repo:` / `file:` em `Q` | presentes quando query tem filtros | §3.8 |
| I-10 | `Opts.NumContextLines` = `context_lines` | body oficial | §3.3/§3.8 |
| I-11 | ordenação determinística dos matches | I-T10-016 |
| I-12 | transport HTTP falha → `ExactCodeIndexError(operation="search")` | envelopado | §3.6/§3.8 |
| I-13 | `delete_repository` idempotente (ausência = no-op) | sem raise | I-T10-012 |
| I-13b | após index, planta sentinel associado ao nome do repo; delete remove | sentinel ausente; leftovers vazios; 2ª delete no-op | I-T10-012 |
| I-14 | delete I/O falha → `ExactCodeIndexError(operation="delete")` | tipado | I-T10-012 |
| I-15 | após index, search preenche `commit` via mapa interno | nunca `""` | I-T10-011 |
| I-16 | `from_environ` lê `ZOEKT_INDEX_DIR` / `ZOEKT_INDEX_BIN` | `-index` path + bin override | I-T10-014 |
| I-16b | `from_environ` defaults | `zoekt-index` + URL `127.0.0.1:6070/api/search` | I-T10-014 |

## 4. Extremos / corner / falhas / concorrência

| Tema | Cobertura |
|---|---|
| Entradas inválidas | mismatch repo/commit (F-12, F-12b, I-05); pattern vazio (F-08, I-07); files vazio (F-07, I-04) |
| Estados vazios | fake sem índice; delete ausente; search sem hits |
| Falhas | fail_operations; HTTP 4xx/5xx/JSON; CLI exit≠0; binário ausente; I/O delete |
| Idempotência | reindex substitui conjunto (F-09); delete no-op; files vazio no-op |
| Concorrência | N/A no MVP T10 (sem lock na porta); não coberta em unit |
| Segredos | E-03, F-02, I-03 — token nunca em str/repr |

## 5. Estratégia RED

- Imports de topo dos módulos ainda inexistentes (`models`, `errors`, `fake`,
  `client`, `runner`, `index`) ⇒ falha de coleta com `ModuleNotFoundError` /
  `ImportError`.
- Após o Developer criar stubs vazios, asserções devem falhar por comportamento
  ausente — **não** enfraquecer asserts.

## 6. Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Plano | `spec/features/github-etl-mcp-rag/tasks/T10-zoekt-adapter/unit-test-plan.md` |
| Helpers | `tests/unit/index/zoekt/helpers.py` |
| Modelos | `tests/unit/index/zoekt/test_models.py` |
| Erros | `tests/unit/index/zoekt/test_errors.py` |
| Fake | `tests/unit/index/zoekt/test_fake.py` |
| HTTP transport | `tests/unit/index/zoekt/test_client.py` |
| CLI runner | `tests/unit/index/zoekt/test_runner.py` |
| Adaptador | `tests/unit/index/zoekt/test_index.py` |

## 7. Como executar

```bash
python -m pytest tests/unit/index/zoekt/ -q
```

## 8. Contagem

| Arquivo | Métodos de teste |
|---|---|
| `test_models.py` | 6 |
| `test_errors.py` | 5 |
| `test_fake.py` | 15 |
| `test_client.py` | 7 |
| `test_runner.py` | 5 |
| `test_index.py` | 18 |
| **Total** | **56** |
