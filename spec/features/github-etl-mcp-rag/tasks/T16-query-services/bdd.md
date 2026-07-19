# BDD — T16-query-services

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T16-query-services` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Rastreabilidade | BDD-009, BDD-010, BDD-012, BDD-024; REQ-002, REQ-026–027, REQ-030; BR-011, BR-023; ENG-007; D-T16-001–012 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `READY_FOR_ARCHITECT_REVIEW` | `0.1.0` | QS-01..QS-12: camada serviço com fakes (sem Zoekt/Qdrant reais). |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Cenários alinhados ao design APPROVED; projeção BDD-012; reformulador no-op D-T16-007. |

## Escopo

Camada de serviço `QueryService` / `DefaultQueryService` (pacote `github_rag.query`): orquestra portas `ExactCodeIndex` (T10), `Embedder`+`VectorStore` (T13), `MainSnapshotProvider` (T08) e `CatalogRepository` (T07/T03). Superfícies UI/MCP (tools, FastAPI, WorkerLimiter) ficam em T17/T18.

## Fixtures de teste (design §11 / §4.7)

| Double | Origem | Uso |
|---|---|---|
| `FakeExactCodeIndex` | `github_rag.index.zoekt.fake` | Busca exata in-memory; `fail_operations={"search"}` |
| `InMemoryCatalogRepository` | `github_rag.catalog.memory` | Catálogo ativo/inativo + `last_processed_commit` |
| Fake `Embedder` / `VectorStore` | doubles da task (ou `github_rag.query.fake`) | Embed + search sem Qdrant/openai reais |
| Fake `MainSnapshotProvider` | double da task | `read_file` / `list_tree` sem Git real |
| Fake `SnapshotSourceResolver` | double da task | `CatalogEntry` → `SnapshotSource` estável |
| Fake `QueryReformulator` | double da task | Só devolve `str`; nunca hit |

- Sem Zoekt CLI/HTTP, sem `QdrantClient`, sem `openai` real no gate BDD.
- `repo_key` = `CatalogEntry.repo_identifier` (mesma string em Exact/Vector/catálogo — D-T16-001).
- `DetailFields` default: todos `False`.

## Cenários executáveis

### QS-01 — BDD-009: `search_exact` devolve correspondências do ExactCodeIndex

**Rastreabilidade:** BDD-009; REQ-002; REQ-026; D-T16-002

**Dado** um `DefaultQueryService` com `FakeExactCodeIndex` indexado para `repo_key="acme/api"` no commit `abc123` com arquivo `src/auth.py` contendo o texto literal `def authenticate`  
**E** um `InMemoryCatalogRepository` com entrada ativa `repo_identifier="acme/api"`  
**E** um `ExactSearchRequest(pattern="def authenticate", details=DetailFields(repository=True, path=True, commit=True, snippet=True), repo_key="acme/api")`  
**Quando** `service.search_exact(request)` é executado  
**Então** retorna `QueryHits` com `len(hits) >= 1`  
**E** todo hit tem `kind == "exact"`  
**E** ao menos um hit tem `repository == "acme/api"`, `path == "src/auth.py"`, `commit == "abc123"` e `snippet` contendo `def authenticate`  
**E** o serviço chamou `ExactCodeIndex.search` (não inventa matches fora do fake)  
**E** `score` do hit exact é `None`

**Critérios de verificação**
- `assert len(result.hits) >= 1`
- `assert all(h.kind == "exact" for h in result.hits)`
- `assert any(h.path == "src/auth.py" and "def authenticate" in (h.snippet or "") for h in result.hits)`

---

### QS-02 — BDD-010: `search_semantic` via Embedder+VectorStore (evidências, sem prosa SLM)

**Rastreabilidade:** BDD-010; REQ-002; REQ-027; BR-011; D-T16-006

**Dado** um `DefaultQueryService` com Embedder fake e VectorStore fake pré-carregado com um `SemanticHit` para `repo_id="acme/api"`, `commit_sha="abc123"`, path `src/auth.py`, texto de chunk contendo `login flow`  
**E** o Embedder, ao receber a query `"how does login work"`, devolve um vetor controlado que o VectorStore associa a esse hit  
**E** um `SemanticSearchRequest(query="how does login work", details=DetailFields(repository=True, path=True, commit=True, snippet=True), repo_key="acme/api", reformulate=False)`  
**Quando** `service.search_semantic(request)` é executado  
**Então** retorna `QueryHits` com ao menos um hit `kind == "semantic"`  
**E** o hit tem `score` numérico (não `None`) e campos projetados iguais aos do `SemanticHit` (repo/path/commit/snippet ← `chunk.text`)  
**E** o fluxo chama `Embedder.embed` e em seguida `VectorStore.search` com o vetor retornado  
**E** nenhum componente SLM de prosa / `MetadataGenerator` / chat completions é invocado no caminho (BR-011)  
**E** o hit não contém texto gerado pelo reformulador como evidência

**Critérios de verificação**
- `assert result.hits[0].kind == "semantic"`
- `assert isinstance(result.hits[0].score, float)`
- `assert embedder.call_count == 1 and vector_store.search_call_count == 1`
- `assert slm_prose_spy.call_count == 0` (ou ausência de dependência SLM no construtor do serviço)

---

### QS-03 — BDD-012: detalhes omitidos quando `DetailFields` default (todos False)

**Rastreabilidade:** BDD-012; REQ-030; D-T16-003; D-T16-004

**Dado** backends fake que devolvem matches/hits com repository, path, commit e snippet preenchidos  
**E** `ExactSearchRequest(pattern="authenticate", details=DetailFields())` — default todos `False`  
**E** `SemanticSearchRequest(query="login", details=DetailFields())` — default todos `False`  
**Quando** `search_exact` e `search_semantic` são executados  
**Então** cada `QueryHit` resultante tem `repository is None`, `path is None`, `commit is None`, `snippet is None`  
**E** `kind` permanece presente (`"exact"` / `"semantic"`)  
**E** em semantic, `score` permanece presente (não é um dos quatro campos BDD-012)

**Critérios de verificação**
- Para cada hit: `assert hit.repository is None and hit.path is None and hit.commit is None and hit.snippet is None`
- `assert hit.kind in {"exact", "semantic"}`

---

### QS-04 — BDD-012: detalhes incluídos quando solicitados

**Rastreabilidade:** BDD-012; REQ-030; D-T16-003

**Dado** os mesmos backends fake de QS-03 com evidências conhecidas  
**E** `details = DetailFields(repository=True, path=True, commit=True, snippet=True)` em exact e semantic  
**Quando** `search_exact` e `search_semantic` são executados  
**Então** os hits incluem os quatro campos com valores vindos das portas (não inventados)  
**E** matriz parcial: com só `path=True` (demais False), apenas `path` é não-`None`; `repository`/`commit`/`snippet` são `None`

**Critérios de verificação**
- Com todos True: `assert hit.repository == expected_repo and hit.path == expected_path and hit.commit == expected_commit and hit.snippet == expected_snippet`
- Com só `path=True`: `assert hit.path == expected_path and hit.repository is None and hit.commit is None and hit.snippet is None`

---

### QS-05 — BDD-024: nenhum client paralelo ad-hoc em `github_rag.query`

**Rastreabilidade:** BDD-024; BR-023; ENG-007; D-T16-002; D-T16-010

**Dado** o pacote de produção `github_rag.query` (módulos `service`, `ports`, `projection`, `resolve`, `types`, `errors`)  
**Quando** a superfície pública e as importações de produção são inspecionadas / o serviço é exercido só com fakes injetados  
**Então** `DefaultQueryService` depende apenas das portas `ExactCodeIndex`, `VectorStore`, `Embedder`, `MainSnapshotProvider`, `CatalogRepository`, `SnapshotSourceResolver` e opcionalmente `QueryReformulator`  
**E** não há import/uso de `qdrant_client`, `openai`, cliente Zoekt HTTP/CLI, `PyGithub`, `git.Repo` / GitPython, nem `httpx`/`requests` como transporte de busca dentro de `github_rag.query`  
**E** a orquestração não instancia adaptadores concretos T10/T13/T08 — só consome Protocols injetados

**Critérios de verificação**
- AST/import scan do pacote `github_rag.query`: ausência dos módulos proibidos acima
- Construtor de `DefaultQueryService` aceita apenas as dependências listadas no design §4.7

---

### QS-06 — `read_file` via MainSnapshotProvider + `last_processed_commit` default

**Rastreabilidade:** REQ-028 (browse); D-T16-005; BR-015

**Dado** catálogo com repo ativo `repo_key="acme/api"`, `last_processed_commit="abc123"`  
**E** fake `MainSnapshotProvider` que, para `commit_sha="abc123"` e `path="src/auth.py"`, devolve `b"secret = 1\n"`  
**E** `ReadFileRequest(repo_key="acme/api", path="src/auth.py", commit_sha=None, details=DetailFields(repository=True, path=True, commit=True))`  
**Quando** `service.read_file(request)` é executado  
**Então** retorna `FileContent` com `content == b"secret = 1\n"`  
**E** o provider foi chamado com `commit_sha="abc123"` (default do catálogo)  
**E** com details True: `repository == "acme/api"`, `path == "src/auth.py"`, `commit == "abc123"`  
**E** com `DetailFields()` default: esses três campos opcionais são `None` (conteúdo `content` permanece)

**Critérios de verificação**
- `assert result.content == b"secret = 1\n"`
- `assert snapshot.read_file_calls[-1]["commit_sha"] == "abc123"`
- Projeção: flags False → `repository/path/commit is None`

---

### QS-07 — `list_tree` via MainSnapshotProvider + `path_prefix` opcional

**Rastreabilidade:** REQ-028 (browse); D-T16-005

**Dado** catálogo com repo ativo e `last_processed_commit="abc123"`  
**E** fake snapshot cujo `list_tree` para esse commit devolve `("src/a.py", "src/b.py", "docs/readme.md")`  
**E** `ListTreeRequest(repo_key="acme/api", commit_sha=None, path_prefix="src/")`  
**Quando** `service.list_tree(request)` é executado  
**Então** `paths` contém apenas entradas sob o prefixo (`src/a.py`, `src/b.py`) — `docs/readme.md` ausente  
**E** o provider foi chamado com `commit_sha="abc123"`  
**Quando** o mesmo pedido é feito com `path_prefix=None`  
**Então** `paths` inclui as três entradas completas do fake

**Critérios de verificação**
- Com prefix: `assert set(result.paths) == {"src/a.py", "src/b.py"}`
- Sem prefix: `assert set(result.paths) == {"src/a.py", "src/b.py", "docs/readme.md"}`

---

### QS-08 — Falhas de backends tipadas (Exact / Vector / Embedding / Snapshot)

**Rastreabilidade:** critério de aceite T16; D-T16-008

**Dado** um `DefaultQueryService` cujas portas podem falhar sob demanda  
**Quando** `ExactCodeIndex.search` levanta `ExactCodeIndexError`  
**Então** `search_exact` propaga `QueryExactIndexError` (subclasse de `QueryError`) com `__cause__` = erro original  

**Quando** `VectorStore.search` levanta `VectorStoreError`  
**Então** `search_semantic` propaga `QueryVectorError` com `__cause__` preservado  

**Quando** `Embedder.embed` levanta `EmbeddingError`  
**Então** `search_semantic` propaga `QueryEmbeddingError` com `__cause__` preservado  

**Quando** `MainSnapshotProvider.read_file` ou `list_tree` levanta `SnapshotError` (ou subclasse, ex. `FileNotFoundInCommitError`)  
**Então** browse propaga `QuerySnapshotError` com `__cause__` preservado  

**E** em todos os casos: não há fallback silencioso para `QueryHits(hits=())` / conteúdo inventado  
**E** a mensagem de erro não contém token/segredo (BR-008)

**Critérios de verificação**
- `assertRaises(QueryExactIndexError)` / `QueryVectorError` / `QueryEmbeddingError` / `QuerySnapshotError`
- `assert exc.__cause__ is original`
- `assert SECRET_TOKEN not in str(exc)`

---

### QS-09 — `QueryReformulator` opcional: no-op sem reformulador; com reformulador só muda texto

**Rastreabilidade:** REQ-027; BR-011; D-T16-006; D-T16-007

**Dado** `DefaultQueryService` **sem** `reformulator` (`None`) e Embedder/VectorStore fakes instrumentados  
**Quando** `search_semantic(SemanticSearchRequest(query="login", reformulate=True, ...))`  
**Então** o Embedder recebe exatamente o texto original `"login"` (no-op — D-T16-007)  
**E** não levanta `QueryReformulatorUnavailableError`  

**Dado** o mesmo serviço **com** fake reformulador que mapeia `"login"` → `"authentication session cookie"`  
**E** o VectorStore só encontra hit para o vetor da query reformulada  
**Quando** `search_semantic(..., reformulate=True)`  
**Então** `Embedder.embed` é chamado com `["authentication session cookie"]` (não com a string original)  
**E** os hits vêm exclusivamente do `VectorStore.search`  
**E** o texto reformulado **nunca** aparece como `QueryHit` inventado sem passar pelo store  
**E** `reformulate=False` nunca chama `reformulator.reformulate`

**Critérios de verificação**
- Sem reformulador: `assert embedder.last_texts == ("login",)`
- Com reformulador: `assert embedder.last_texts == ("authentication session cookie",)`
- `assert all(h.kind == "semantic" for h in result.hits)` e hits ⊆ evidências do fake store
- `assert reformulator.call_count == 0` quando `reformulate=False`

---

### QS-10 — Repo inexistente/inativo → `QueryRepositoryNotFoundError`

**Rastreabilidade:** design §4.3 / §6; D-T16-008

**Dado** `InMemoryCatalogRepository` sem entrada para `repo_key="missing/repo"`  
**Quando** qualquer operação (`search_exact` com escopo de repo, `search_semantic` com escopo, `read_file`, `list_tree`) usa esse `repo_key` ou `repository_id` inexistente  
**Então** levanta `QueryRepositoryNotFoundError`  

**Dado** um repo existente com `active=False` (soft-delete via `deactivate_repository`)  
**Quando** a mesma operação usa seu `repo_key` / `repository_id`  
**Então** levanta `QueryRepositoryNotFoundError`  
**E** backends Exact/Vector/Snapshot **não** são chamados

**Critérios de verificação**
- `assertRaises(QueryRepositoryNotFoundError)`
- `assert exact_index.search_call_count == 0` (e equivalentes nos outros backends)

---

### QS-11 — Browse sem commit e sem `last_processed_commit` → `QueryCommitUnavailableError`

**Rastreabilidade:** design §4.3; D-T16-005

**Dado** catálogo com repo ativo `repo_key="acme/api"` e `last_processed_commit is None` (nunca indexado)  
**E** `ReadFileRequest(repo_key="acme/api", path="src/a.py", commit_sha=None)`  
**Quando** `service.read_file(request)` é executado  
**Então** levanta `QueryCommitUnavailableError`  
**E** `MainSnapshotProvider.read_file` **não** é chamado  

**Quando** `list_tree` com `commit_sha=None` no mesmo repo  
**Então** levanta `QueryCommitUnavailableError`  
**E** `list_tree` do provider **não** é chamado  

**Quando** o caller passa `commit_sha="deadbeef"` explicitamente no mesmo repo sem `last_processed_commit`  
**Então** o browse **pode** prosseguir (commit explícito; não exige last_processed)

**Critérios de verificação**
- `assertRaises(QueryCommitUnavailableError)` nos casos sem commit
- `assert snapshot.call_count == 0` quando erro
- Com SHA explícito: operação chega ao provider com esse SHA

---

### QS-12 — Pattern vazio exact → hits vazios; query semântica vazia → `QueryValidationError`

**Rastreabilidade:** D-T16-012; paridade T10

**Dado** `DefaultQueryService` com fakes válidos e catálogo ativo  
**Quando** `search_exact(ExactSearchRequest(pattern=""))` ou `pattern` só whitespace  
**Então** retorna `QueryHits(hits=())` sem erro  
**E** espelha a semântica T10 (não levanta)  

**Quando** `search_semantic(SemanticSearchRequest(query=""))` ou `query` só whitespace  
**Então** levanta `QueryValidationError`  
**E** `Embedder.embed` e `VectorStore.search` **não** são chamados

**Critérios de verificação**
- Exact: `assert result.hits == ()`
- Semantic: `assertRaises(QueryValidationError)`; `assert embedder.call_count == 0`

## Fora de escopo destes BDD

- Tools MCP / envelope JSON (T17)
- Telas UI / FastAPI / WorkerLimiter (T18)
- Adaptador SLM real de `QueryReformulator` (só Protocol + fake)
- Zoekt/Qdrant/Git reais no gate
- `list_repos` como método de `QueryService`
- Narrativa MCP / chat completions no caminho de recuperação

## Execução

```bash
python -m pytest tests/bdd/test_query_services.py -q
```

## Architect Review

| Decisão | Status | Autor | Data |
|---|---|---|---|
| APPROVED_BY_ARCHITECT | aprovado | tech-lead-architect | 2026-07-18 |
