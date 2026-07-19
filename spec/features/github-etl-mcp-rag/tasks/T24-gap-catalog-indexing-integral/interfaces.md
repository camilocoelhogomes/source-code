# Interfaces — T24-gap-catalog-indexing-integral

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T24-gap-catalog-indexing-integral` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T24-gap-catalog-indexing-integral` |
| Escopo desta etapa | Contratos Robot (`catalog_indexing.resource` + suites) + helpers Python e2e (cron UTC / MCP parse / fixture prepare) + extensão `ensure_local_git_fixture` — **sem** Protocols de domínio novos |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-19 (modo autônomo) |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Keywords C-T24-02 + library leve + seed launcher; sem Protocols de domínio; D-T24-002/007/010. |

## 1. Escopo e exclusões

### Em escopo

| Superfície | Artefato | Papel |
|---|---|---|
| Suite Robot | `e2e/robot/catalog_indexing.robot` | Cenários CI-T24-003/005/006/017 (tags `bdd003`/`bdd005`/`bdd006`/`bdd017`) |
| Resource Robot | `e2e/robot/resources/catalog_indexing.resource` | Keywords partilhadas cron-tick, MCP commits, fixture host, asserts ausência |
| Library Robot | `e2e/robot/libraries/CatalogIndexingKeywords.py` (novo) | Cron UTC, parse MCP commits, prepare/commit fixture no host |
| Reuso MCP | `e2e/robot/libraries/McpKeywords.py` (T21) | Transporte SSE; **sem** mudança de contrato |
| Seed launcher | `src/github_rag/e2e/launcher.py` → `ensure_local_git_fixture` | Extensão idempotente árvore BDD-006/017 (superfície e2e) |
| Fixture | `e2e/fixtures/repos/sample-local` | Paths/markers seed (sem secrets) |

### Fora de escopo

| Item | Motivo |
|---|---|
| Novos `Protocol` em `src/github_rag/{catalog,indexing,schedule,eligibility,…}` | D-T24-007; domínio intocado |
| Endpoints UI novos / `POST /api/scheduler/tick` | Plano primário D-T24-007; contingência D-T24-008 só com flakiness |
| Browser (T23) / compose zoekt (T22) | Fora da task |
| Alterar assinaturas `E2eStackLauncher` / `RobotMvpSuite` | T21 estável; só seed fixture |
| Soft-pass / tag `manual_or_partial` | Proibido como único gate |

## 2. Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T24-001 | **Não** introduzir Protocols de domínio | Escopo = e2e asserts; APIs/MCP existentes bastam | D-T24-007; design §4 |
| I-T24-002 | Keywords T24 vivem em `catalog_indexing.resource`; suite só orquestra cenários | Evita inchamento do `.robot` (C-T24-02) | design §3.6 |
| I-T24-003 | Library Python `CatalogIndexingKeywords` para cron UTC, parse JSON MCP e mutação Git host quando Robot puro for verboso/frágil | Mesmo padrão `McpKeywords.py`; I/O tipado testável unitariamente | design §3.6; R-T24-01 |
| I-T24-004 | Observar commits **somente** via MCP `list_repos` (`last_processed_commit` / `current_main_commit`) | Evita campos novos na UI | D-T24-002; CI-T24-003/005/017 |
| I-T24-005 | Mutações Git **somente no host** sob `e2e/fixtures/repos/sample-local` | Volume `:ro` no container | D-T24-009 |
| I-T24-006 | Extender `ensure_local_git_fixture` com seed idempotente include/exclude/branches base; keywords Robot completam uncommitted / commits de janela | Seed estável no up + prepare fino no cenário | D-T24-010; CI-T24-006/017 |
| I-T24-007 | BDD-003: `Put Cron Firing Soon Utc` + poll **sem** `POST /api/repos/index` pós-mutação; teardown restaura cron | Texto integral “quando o horário chegar” | D-T24-003; CI-T24-003 |
| I-T24-008 | Poll scheduler tick: timeout ≥ 120s (variável dedicada); intervalo estável (ex. 5s) | Mitiga R-T24-01 | design §3.2; bdd PRE |
| I-T24-009 | Markers de fixture são constantes exportadas (prefixo `T24_` / `MAIN_ONLY_` etc.); tokens únicos estáveis entre reruns | Asserts de presença/ausência reproduzíveis | R-T24-05; CI-T24-006/017 |
| I-T24-010 | Reusar `McpKeywords.mcp_call_tool` sem alterar contrato; parse de commits é wrapper T24 | Transporte ≠ semântica de catálogo | C-T24-04 |
| I-T24-011 | Tag `bdd005` **não** permanece só colada em BDD-002; gate integral = caso CI-T24-005 | Fecha gap inventário | bdd CI-T24-005 |
| I-T24-012 | Contingência `POST /api/scheduler/tick` **fora** dos contratos desta etapa | Só com evidência de flakiness | D-T24-008 |

## 3. Layout alvo

```text
e2e/robot/
  catalog_indexing.robot              # cenários CI-T24-* (+ regressão T21 restante)
  resources/
    common.resource                   # reuso timeouts/HTTP (T21); opcional var SCHEDULER_TICK_*
    catalog_indexing.resource         # NOVO — keywords I-T24-*
  libraries/
    McpKeywords.py                    # T21 — sem mudança de API
    CatalogIndexingKeywords.py        # NOVO — helpers cron/MCP/fixture

e2e/fixtures/repos/sample-local/      # árvore seed (paths I-T24-006)

src/github_rag/e2e/launcher.py        # ensure_local_git_fixture estendido (seed)
```

**Sem** novos módulos em `src/github_rag/` fora de `e2e/launcher.py`.

---

## 4. Constantes / markers (contrato de dados)

**Responsabilidade:** congelar paths e tokens usados nos asserts de elegibilidade e snapshot.  
**Motivo da separação:** evita magic strings espalhadas entre seed, keywords e cenários; permite unitários do prepare.

| Constante | Valor canônico | Uso |
|---|---|---|
| `SAMPLE_LOCAL_REL` | `sample-local` | Path sob `HOST_REPOS` / fixture dir |
| `MARKER_INCLUDE_JAVA` | `T24_INCLUDE_JAVA_A1B2` | `src/Hello.java` |
| `MARKER_INCLUDE_PY` | `T24_INCLUDE_PY_C3D4` | `src/app.py` (opcional se Java presente) |
| `MARKER_INCLUDE_MD` | `T24_INCLUDE_MD_E5F6` | `docs/notes.md` |
| `MARKER_EXCLUDE_CSV` | `T24_EXCLUDE_CSV_G7H8` | `data/report.csv` |
| `MARKER_EXCLUDE_GITIGNORE` | `T24_EXCLUDE_GITIGNORE_I9J0` | `ignored_dir/secret_marker.txt` |
| `MARKER_MAIN_ONLY` | `MAIN_ONLY_MARKER` | commit na `main` |
| `MARKER_OTHER_BRANCH` | `OTHER_BRANCH_MARKER` | commit só em `other` |
| `MARKER_UNCOMMITTED` | `UNCOMMITTED_MARKER` | working tree não staged |
| `OTHER_BRANCH_NAME` | `other` | branch não-main |
| `SCHEDULER_TICK_TIMEOUT_SECONDS` | `≥ 120` | poll CI-T24-003 |
| `SCHEDULER_TICK_POLL_SECONDS` | `5` (ou igual `INDEXING_POLL_SECONDS`) | intervalo poll |

Paths seed (BDD-006):

| Path | Papel |
|---|---|
| `src/Hello.java` e/ou `src/app.py` | include |
| `docs/notes.md` | include |
| `data/report.csv` | exclude CSV |
| `img/photo.png` | exclude imagem (binário mínimo) |
| `.gitignore` → `ignored_dir/` | pathspec |
| `ignored_dir/secret_marker.txt` | exclude gitignore |

---

## 5. Resource Robot — `catalog_indexing.resource`

**Responsabilidade:** expor keywords de orquestração e assert para CI-T24-003/005/006/017 reutilizando UI session + MCP.  
**Motivo da separação:** suite descreve Gherkin; resource isola I/O e waits (C-T24-02).

### 5.1 Cron / tick (BDD-003)

#### `Capture Scheduler Cron`

| Campo | Contrato |
|---|---|
| Entrada | sessão UI existente |
| Saída | dict/body com `cron` atual (`cron_original`) |
| Efeito | `GET /api/scheduler/cron`; `Response Must Not Contain Token` |
| Erro | status ≠ 200 → falha |

#### `Put Cron Firing Soon Utc`

| Campo | Contrato |
|---|---|
| Entrada | — (calcula expressão UTC) |
| Saída | expressão aplicada (string 5 campos) |
| Efeito | chama helper `Cron Expression Firing Soon Utc` → `PUT /api/scheduler/cron` → HTTP 200; body `cron` == expressão |
| Erro | 400/≠200 → falha explícita (não soft-pass) |
| Nota | Preferir minuto absoluto UTC (corrente ou +1); `*/1 * * * *` só se produto aceitar |

#### `Restore Scheduler Cron`

| Campo | Contrato |
|---|---|
| Entrada | `cron_original` (dict ou string compatível com PUT) |
| Efeito | `PUT /api/scheduler/cron` restaura valor pré-teste; HTTP 200 |
| Uso | teardown obrigatório CI-T24-003 |

#### `Wait Repo Indexed By Scheduler Tick`

| Campo | Contrato |
|---|---|
| Entrada | `repo_id`; timeout default `${SCHEDULER_TICK_TIMEOUT_SECONDS}` |
| Efeito | poll `GET /api/repos/{id}` até `state == up_to_date` (e `state_label == atualizado`) |
| Proibição | **não** chama `POST /api/repos/index` |
| Erro | timeout → falha BDD-003 |

### 5.2 MCP commits (BDD-003/005/017)

#### `Mcp Repo Commits`

| Campo | Contrato |
|---|---|
| Entrada | `repo_id` **ou** `repo_identifier` local |
| Saída | dict com `last_processed_commit`, `current_main_commit` (strings; podem ser vazias só se pré-condição falhar) |
| Efeito | `mcp_call_tool list_repos` → parse helper; localiza repo; sem logar token |
| Erro | repo ausente / parse inválido → falha |

#### `Mcp Capture Last Processed Commit`

| Campo | Contrato |
|---|---|
| Entrada | identificador do repo local |
| Saída | `SHA_A` não vazio |
| Erro | vazio → falha (pré-condição indexação) |

#### `Mcp Assert Last Processed Equals`

| Campo | Contrato |
|---|---|
| Entrada | repo + `expected_sha` |
| Assert | `last_processed_commit == expected_sha == current_main_commit` |

### 5.3 Host git / index sob demanda (BDD-005 + prep 003)

#### `Host Commit On Main`

| Campo | Contrato |
|---|---|
| Entrada | path fixture (default sample-local); conteúdo/mensagem únicos opcionais |
| Saída | `SHA_B` (tip `main` pós-commit) |
| Efeito | mutação **no host**; cria/altera arquivo + `git commit` na `main` |
| Erro | falha git → Fail antes dos asserts |

#### `Index Repo And Wait Up To Date`

| Campo | Contrato |
|---|---|
| Entrada | `repo_id` |
| Efeito | `POST /api/repos/index` com `repository_ids=[id]` → 202 → `Wait Repo State` `up_to_date` |
| Uso | CI-T24-005/006/017 e **prep** de CI-T24-003 (antes da mutação); **proibido** no caminho de prova pós-mutação de CI-T24-003 |

### 5.4 Fixture prepare + asserts elegibilidade / main-only

#### `Prepare Eligibility Fixture Tree`

| Campo | Contrato |
|---|---|
| Efeito | garante árvore BDD-006 commitada na `main` (idempotente); delega a helper Python / seed |
| Saída | markers include/exclude disponíveis para busca |

#### `Prepare MainOnly Fixture Branches`

| Campo | Contrato |
|---|---|
| Efeito | garante `MAIN_ONLY_MARKER` na `main`; branch `other` com `OTHER_BRANCH_MARKER`; arquivo uncommitted com `UNCOMMITTED_MARKER` (não staged) |
| Idempotência | reruns não deixam estado ambíguo (recria uncommitted; branch other existe) |

#### `Assert Exact Search Hits`

| Campo | Contrato |
|---|---|
| Entrada | `pattern`, `repository_id`, path esperado opcional |
| Assert | `POST /api/search/exact` → `len(hits) >= 1`; path coerente se informado; sem token |

#### `Assert Exact Search Empty`

| Campo | Contrato |
|---|---|
| Entrada | `pattern`, `repository_id` |
| Assert | `hits` vazio (`[]` ou equivalente) |

#### `Assert Repo Files Paths Eligible`

| Campo | Contrato |
|---|---|
| Entrada | `repo_id`, lista includes, lista excludes |
| Assert | `GET /api/repos/{id}` → `files[].path` ⊇ includes; ∩ excludes = ∅ |

#### `Assert Main Marker Indexed`

| Campo | Contrato |
|---|---|
| Entrada | `repository_id`, tip MCP |
| Assert | busca `MAIN_ONLY_MARKER` → hits; `commit` do hit == tip main (`last_processed_commit` / `current_main_commit`) |

#### `Assert Marker Absent From Exact Search`

| Campo | Contrato |
|---|---|
| Entrada | `pattern`, `repository_id` |
| Assert | zero hits (wrapper semântico de `Assert Exact Search Empty`) |

---

## 6. Library Python — `CatalogIndexingKeywords.py`

**Responsabilidade:** operações tipadas difíceis/frágeis em Robot puro (UTC cron, JSON MCP, git host).  
**Motivo da separação:** testável com pytest (≥95%); Robot só chama; não é domínio ETL.

Módulo: `e2e/robot/libraries/CatalogIndexingKeywords.py`  
Exposição: keywords Robot (funções públicas snake_case → Robot Title Case).

### 6.1 `cron_expression_firing_soon_utc`

```python
def cron_expression_firing_soon_utc(now: datetime | None = None) -> str:
    """Calcula expressão cron de 5 campos que dispara na janela do teste (UTC).

    Responsabilidade
        Produzir cron reproduzível (minuto corrente ou próximo minuto UTC)
        para PUT /api/scheduler/cron sem esperar 24h.

    Motivo da separação
        Relógio/fuso em Robot puro é flaky (R-T24-01); Python fixa UTC.
    """
```

| Contrato | Detalhe |
|---|---|
| Retorno | string `m h dom mon dow` (minuto 0–59 absoluto preferido) |
| Default `now` | `datetime.now(timezone.utc)` |
| Não faz | HTTP; só calcula expressão |

### 6.2 `parse_mcp_list_repos_commits`

```python
def parse_mcp_list_repos_commits(
    list_repos_json: str,
    *,
    repo_id: str | None = None,
    repo_identifier: str | None = None,
) -> dict[str, str]:
    """Extrai last_processed_commit e current_main_commit de um repo.

    Responsabilidade
        Normalizar o JSON retornado por mcp_call_tool('list_repos') e
        localizar o repo alvo.

    Motivo da separação
        Formato MCP (structured/content) não deve ser parseado ad hoc
        em cada caso Robot; um parser único evita asserts fracos.
    """
```

| Contrato | Detalhe |
|---|---|
| Entrada | JSON string de `mcp_call_tool` |
| Retorno | `{"last_processed_commit": str, "current_main_commit": str, ...}` |
| Erro | repo não encontrado / shape inválido → `AssertionError` ou exceção clara |
| Segurança | não inclui tokens; caller já usa `_assert_no_token` do MCP |

### 6.3 `host_commit_on_main`

```python
def host_commit_on_main(
    fixture_dir: str | Path,
    *,
    relative_path: str = "t24_bump.txt",
    content: str | None = None,
    message: str | None = None,
) -> str:
    """Cria commit na main do fixture no host; retorna SHA tip.

    Responsabilidade
        Mutar tip da main para deixar o catálogo desatualizado (003/005).

    Motivo da separação
        Git no host (D-T24-009); subprocess + author env ficam fora do .robot.
    """
```

| Contrato | Detalhe |
|---|---|
| Retorno | SHA completo (40 hex) da tip `main` |
| Pré | `fixture_dir` é repo git com `main` |
| Erro | git ≠0 → exceção com stderr (sem secrets) |

### 6.4 `prepare_eligibility_tree`

```python
def prepare_eligibility_tree(fixture_dir: str | Path) -> dict[str, str]:
    """Garante árvore include/exclude commitada na main (idempotente).

    Responsabilidade
        Materializar paths/markers BDD-006 no fixture host.

    Motivo da separação
        Seed de arquivos + .gitignore + commit inicial/atualização
        é I/O; Robot só valida busca/files[].
    """
```

| Contrato | Detalhe |
|---|---|
| Retorno | mapa `{nome_marker: valor_marker}` dos tokens usados |
| Idempotência | rerun não duplica commits desnecessários se árvore já correta; se faltar arquivo, escreve + commit |
| Inclui | PNG mínimo em `img/photo.png` (bytes válidos mínimos) |

### 6.5 `prepare_main_only_branches`

```python
def prepare_main_only_branches(fixture_dir: str | Path) -> dict[str, str]:
    """Garante markers main / other branch / uncommitted (idempotente).

    Responsabilidade
        Estado git para BDD-017: tip main com MAIN_ONLY; branch other
        com OTHER; working tree com UNCOMMITTED não staged.

    Motivo da separação
        Checkout/branch/uncommitted é frágil em Robot; helper único
        documenta a ordem segura (voltar para main ao final).
    """
```

| Contrato | Detalhe |
|---|---|
| Pós-condição | HEAD em `main`; uncommitted presente no WT; `other` existe |
| Retorno | markers usados |
| Não faz | indexação UI/MCP |

### 6.6 Resolução do path do fixture

```python
def resolve_sample_local_dir(repos_root: str | Path | None = None) -> Path:
    """Resolve e2e/fixtures/repos/sample-local (HOST_REPOS ou default repo).

    Responsabilidade
        Um único resolvedor de path para keywords e unitários.

    Motivo da separação
        Evita hardcode divergente entre launcher e Robot library.
    """
```

---

## 7. Extensão — `ensure_local_git_fixture`

**Arquivo:** `src/github_rag/e2e/launcher.py`  
**Símbolo existente:** `ensure_local_git_fixture(repos_dir: Path) -> None`

**Responsabilidade (estendida):** além de garantir `.git` + `main` + README (T21), materializar de forma **idempotente** a árvore base BDD-006 (includes/excludes/gitignore) e marker `MAIN_ONLY` na `main`, compatível com prepare fino das keywords.  
**Motivo da separação:** seed no `up` da stack evita depender só do primeiro teste; keywords Robot cobrem uncommitted / branch `other` / commits de janela (estado volátil).

| Contrato | Detalhe |
|---|---|
| Assinatura | **inalterada** `(repos_dir: Path) -> None` |
| Compat T21 | se `.git` já existe, **não** early-return cego que impeça seed T24 — ou: early-return só do `git init`, depois chamar seed idempotente |
| Seed mínimo no launcher | paths include/exclude + `.gitignore` + commit na `main` se ausentes |
| Fora do launcher | branch `other`, arquivo uncommitted, commits “bump” de 003/005 → keywords/`CatalogIndexingKeywords` |
| Erros | continua `E2eStackError` (ou equivalente já usado) em falha git |
| Domínio | **não** tocar `src/github_rag/` fora de `e2e/` |

Pseudocontrato:

```python
def ensure_local_git_fixture(repos_dir: Path) -> None:
    """Garante sample-local com git + seed e2e T24 (BDD-006 base).

    Responsabilidade
        Preparar volume HOST_REPOS/sample-local para catálogo local:
        init main (legado T21) + árvore elegibilidade idempotente.

    Motivo da separação
        Superfície e2e (D-T24-010), não ETL; suite Robot assume fixture
        montada e legível pelo container (:ro).
    """
```

---

## 8. Reuso — `McpKeywords` (sem alteração de API)

**Responsabilidade:** transporte SSE + `mcp_call_tool` / `mcp_list_tools`.  
**Motivo da separação (reafirmado):** protocolo MCP ≠ parsing de commits de catálogo (I-T24-010).

| Função | Uso T24 |
|---|---|
| `mcp_call_tool("list_repos", …)` | entrada de `parse_mcp_list_repos_commits` / `Mcp Repo Commits` |
| `mcp_call_tool("list_tree" \| "read_file", …)` | opcional CI-T24-017 |
| Assert token | permanece |

**Proibido nesta task:** mudar assinaturas públicas de `McpKeywords.py` sem necessidade; wrappers T24 ficam em `CatalogIndexingKeywords` / resource.

---

## 9. Mapeamento cenário → interfaces

| Cenário | Keywords / helpers |
|---|---|
| CI-T24-003 | `Index Repo And Wait…` (prep) → `Host Commit On Main` → `Capture Scheduler Cron` → `Put Cron Firing Soon Utc` → `Wait Repo Indexed By Scheduler Tick` → `Mcp Assert Last Processed Equals` → `Restore Scheduler Cron` |
| CI-T24-005 | `Mcp Capture Last Processed Commit` → `Host Commit On Main` → `Index Repo And Wait Up To Date` → `Mcp Assert Last Processed Equals` |
| CI-T24-006 | `Prepare Eligibility Fixture Tree` → `Index Repo And Wait…` → `Assert Exact Search Hits/Empty` → `Assert Repo Files Paths Eligible` |
| CI-T24-017 | `Prepare MainOnly Fixture Branches` → `Index Repo And Wait…` → `Assert Main Marker Indexed` → `Assert Marker Absent…` (other + uncommitted) |

---

## 10. Unitários previstos (QA — gate seguinte)

Helpers cobertos por pytest sob `tests/unit/e2e/` (ou equivalente), sem stack:

| Função | Extremos |
|---|---|
| `cron_expression_firing_soon_utc` | virada de minuto; `now` injetado; formato 5 campos |
| `parse_mcp_list_repos_commits` | repo ausente; JSON aninhado; id vs identifier; campos vazios |
| `host_commit_on_main` | tip muda; mensagem única; falha se sem `.git` |
| `prepare_eligibility_tree` | idempotente 2ª chamada; paths exclude presentes |
| `prepare_main_only_branches` | HEAD main; other existe; uncommitted não staged |
| `ensure_local_git_fixture` | rerun com `.git` existente ainda aplica/seed idempotente |

Cobertura projeto ≥ 95%.

---

## 11. Fora de contrato (não implementar)

- `POST /api/scheduler/tick` (D-T24-008)
- Novos campos em `RepoDetailView` / serialize UI
- Protocols `DailyScheduler` / eligibility / snapshot
- Mudança de compose ou ownership T22/T23

## 12. Estado

`APPROVED_BY_ARCHITECT` — interfaces `0.1.0` alinhadas a design `0.1.0` e bdd `0.1.0`. Próximo: unit plan QA dos helpers → implementação Developer.
