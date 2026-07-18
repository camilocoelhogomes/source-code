# Interfaces — T10-zoekt-adapter

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T10-zoekt-adapter` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T10-zoekt-adapter` |
| Escopo desta etapa | Contratos de comunicação T10 **somente** (stubs sem comportamento completo) |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `FileToIndex` | `index/zoekt/models.py` | Entrada de arquivo integral a indexar |
| `ExactMatch` | `index/zoekt/models.py` | Hit de busca exata com metadados |
| `ExactSearchQuery` | `index/zoekt/models.py` | Query de busca na porta de domínio |
| `ExactCodeIndexError` | `index/zoekt/errors.py` | Erro tipado para T14 |
| `ExactCodeIndex` | `index/zoekt/port.py` | Protocol / porta de domínio |
| `ZoektSearchTransport` | `index/zoekt/client.py` | Protocol HTTP oficial `POST /api/search` |
| `HttpZoektSearchTransport` | `index/zoekt/client.py` | Implementação stdlib HTTP |
| `ZoektIndexRunner` | `index/zoekt/runner.py` | Protocol invocador CLI oficial |
| `SubprocessZoektIndexRunner` | `index/zoekt/runner.py` | Implementação `subprocess` |
| `ZoektExactCodeIndex` | `index/zoekt/index.py` | Adaptador que implementa a porta |
| `FakeExactCodeIndex` | `index/zoekt/fake.py` | Double injetável em memória |
| Re-exports | `index/zoekt/__init__.py` | Superfície pública |

### Fora de escopo

| Item | Dono |
|---|---|
| Orquestração ENG-012 / restart de repo | T14 |
| `QueryService` / apresentação de resultados | T16 / T18 |
| MCP tools | T17 |
| Compose / imagem `zoekt` | T19 |
| Tree-sitter / Qdrant / SLM | outras tasks |
| `remove_paths` na porta | proibido (D-T10-006) |
| Expansão de `AppSettings` (T01) | D-T10-007 — factory local |
| gRPC Zoekt como API default | fora MVP |
| Parser/escritor de shards `.zoekt` | proibido (DEC-016) |

## 2. Decisões de contrato

| ID | Decisão | Motivo |
|---|---|---|
| I-T10-001 | Porta `ExactCodeIndex` com `index` / `search` / `delete_repository` | D-T10-002; handoff T14/T16; D-T10-006 |
| I-T10-002 | Modelos frozen: `FileToIndex`, `ExactMatch`, `ExactSearchQuery` | D-T10-003; imutabilidade de evidência |
| I-T10-003 | `repository` é `str` estável no formato que T14 já usa (default sugerido: `full_name` estilo `org/repo`) | Fecha SUGGESTION do design §17 sem UUID paralelo |
| I-T10-004 | Invariante `index(repository, commit, files)`: cada `FileToIndex` deve ter `repository`/`commit` iguais aos args; divergência → `ExactCodeIndexError` | D-T10-003 |
| I-T10-005 | `files` vazio em `index` → no-op sucesso | design §8; ZOEKT-06 |
| I-T10-006 | `pattern` vazio em `search` → sequência vazia (sem erro) | design §8; ZOEKT-07 |
| I-T10-007 | Erros via `ExactCodeIndexError` com `operation`; sem segredos na mensagem | D-T10-004; ZOEKT-03 |
| I-T10-008 | Transporte HTTP e CLI em Protocols separados; implementação stdlib/`subprocess` | D-T10-001/002; DEC-016; mockável |
| I-T10-009 | MVP de indexação: materializar árvore temp + `zoekt-index -index <dir> <tree>`; `zoekt-git-index` só otimização de construtor | D-T10-001 |
| I-T10-010 | Escape literal Zoekt: quote o `pattern` com sintaxe literal oficial (preferir `content:"…"` / quoting documentado) antes de anexar `repo:`/`file:` | design §5.4; evita regex acidental |
| I-T10-011 | `ExactMatch.commit` nunca `""` em índice populado; mapa interno `repository → last_commit` se shard não expuser SHA | D-T10-003 |
| I-T10-012 | `delete_repository` remove artefatos do repo no `index_dir` por associação de nome; ausência = no-op; sem parse binário de shard | D-T10-006; ZOEKT-05 |
| I-T10-013 | Reindex do conjunto tip substitui o conjunto de paths do repo (paths ausentes somem) | ENG-012 / D-T10-006; ZOEKT-08 |
| I-T10-014 | Envs `ZOEKT_*` via construtor/`from_environ`; não alterar `AppSettings` T01 | D-T10-007 |
| I-T10-015 | `FakeExactCodeIndex` satisfaz o Protocol em memória; `fail_operations` opcional | D-T10-005; BDD-024 |
| I-T10-016 | Resultados de `search` ordenados deterministicamente por `(repository, path, line_number or 0, snippet)` | design §6.2 |

## 3. Contratos detalhados

### 3.1 `FileToIndex`

```python
@dataclass(frozen=True)
class FileToIndex:
    repository: str
    path: str
    commit: str
    content: bytes
```

- **Responsabilidade:** carregar o conteúdo integral de um arquivo elegível no tip a ser indexado (ENG-012: arquivo inteiro).
- **Motivo da separação:** DTO de entrada estável para a porta; T14 não acopla a argv CLI, temp dirs nem formato de shard Zoekt.
- **Invariantes:** `path` relativo estilo POSIX no contrato (normalização no adaptador); `content` é bytes do tip; sem `workdir` neste modelo.
- **Erros:** divergência de `repository`/`commit` vs args de `index` → `ExactCodeIndexError` (entrada inválida).

### 3.2 `ExactMatch`

```python
@dataclass(frozen=True)
class ExactMatch:
    repository: str
    path: str
    commit: str
    snippet: str
    line_number: int | None = None
```

- **Responsabilidade:** evidência de match exato com metadados mínimos para T16/UI/MCP (BDD-009).
- **Motivo da separação:** saída de domínio independente do JSON Zoekt (`FileMatches`/fragments).
- **Invariantes:** em índice populado por esta porta, `commit` e `snippet` não vazios; `snippet` contém o trecho ao redor do hit (`NumContextLines`); sem score/BM25 no MVP.
- **Erros:** N/A (valor de retorno).

### 3.3 `ExactSearchQuery`

```python
@dataclass(frozen=True)
class ExactSearchQuery:
    pattern: str
    repository: str | None = None
    path_prefix: str | None = None
    max_matches: int | None = None
    context_lines: int = 2
```

- **Responsabilidade:** descrever busca literal + filtros opcionais sem expor a query language Zoekt aos callers.
- **Motivo da separação:** T16 monta intenção de produto; só o adaptador conhece `Q` / `Opts` oficiais.
- **Invariantes:** `context_lines` default `2` → `Opts.NumContextLines`; `pattern == ""` → lista vazia na porta (I-T10-006).
- **Erros:** N/A no modelo; falhas de transporte sobem como `ExactCodeIndexError`.

### 3.4 `ExactCodeIndexError`

```python
class ExactCodeIndexError(Exception):
    def __init__(
        self,
        message: str,
        *,
        operation: str,
        repository: str | None = None,
        commit: str | None = None,
    ) -> None: ...

    @property
    def operation(self) -> str: ...  # "index" | "search" | "delete"

    @property
    def repository(self) -> str | None: ...

    @property
    def commit(self) -> str | None: ...
```

- **Responsabilidade:** falha tipada de indexação/busca/limpeza para T14 marcar erro e reiniciar o repositório.
- **Motivo da separação:** distinto de erros HTTP/subprocess crus; callers tratam um tipo estável (D-T10-004).
- **Invariantes:** `str(self)` / `repr(self)` **não** contêm tokens/segredos; podem citar host, exit code, status HTTP, path/repo/commit; `__cause__` preserva exceção de transporte quando houver.
- **Erros:** esta classe **é** o tipo.

### 3.5 `ExactCodeIndex` (Protocol)

```python
@runtime_checkable
class ExactCodeIndex(Protocol):
    def index(
        self,
        repository: str,
        commit: str,
        files: Sequence[FileToIndex],
    ) -> None: ...

    def search(self, query: ExactSearchQuery) -> Sequence[ExactMatch]: ...

    def delete_repository(self, repository: str) -> None: ...
```

- **Responsabilidade:** abstrair indexação e busca exata de código para o produto (T14 indexa; T16 busca; restart usa `delete_repository`).
- **Motivo da separação:** T14/T16 não acoplam a Zoekt (HTTP, CLI, shards); permite `FakeExactCodeIndex` e troca de backend oficial sem mudar orquestração/UI/MCP.
- **Invariantes:**
  - `index`: args `repository`/`commit` canônicos; `files` vazio = no-op; reindex do conjunto tip substitui paths do repo.
  - `search`: ordenação determinística (I-T10-016); `pattern` vazio → `()`.
  - `delete_repository`: ausência de artefatos = no-op sucesso.
- **Erros:** qualquer falha de infra/entrada inválida relevante → `ExactCodeIndexError`.

### 3.6 `ZoektSearchTransport` (Protocol) e `HttpZoektSearchTransport`

```python
@runtime_checkable
class ZoektSearchTransport(Protocol):
    def post_search(self, body: Mapping[str, Any]) -> Mapping[str, Any]: ...


class HttpZoektSearchTransport:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 30.0,
    ) -> None: ...

    def post_search(self, body: Mapping[str, Any]) -> Mapping[str, Any]: ...
```

- **Responsabilidade (Protocol):** enviar o body JSON oficial a `POST {base}/api/search` e devolver o mapping da resposta.
- **Motivo da separação:** isola URL, timeout e status HTTP; mockável em unit tests sem processo Zoekt (D-T10-002).
- **Implementação:** `HttpZoektSearchTransport` usa **stdlib** (`urllib.request` / `http.client`) — adaptador fino, sem SDK proprietário (DEC-016).
- **Invariantes:** `base_url` sem path `/api/search` duplicado na montagem; timeout configurável; não interpreta domínio além de JSON.
- **Erros:** rede / HTTP 4xx/5xx / JSON inválido — a **porta** (`ZoektExactCodeIndex`) envelopa em `ExactCodeIndexError(operation="search")`; o transport pode levantar exceções stdlib/`OSError`/`TimeoutError`/`ValueError` para o adaptador envelopar.

### 3.7 `ZoektIndexRunner` (Protocol) e `SubprocessZoektIndexRunner`

```python
@dataclass(frozen=True)
class ZoektIndexRunResult:
    returncode: int
    stdout: str
    stderr: str


@runtime_checkable
class ZoektIndexRunner(Protocol):
    def run(self, argv: Sequence[str]) -> ZoektIndexRunResult: ...


class SubprocessZoektIndexRunner:
    def __init__(self, *, timeout_seconds: float = 600.0) -> None: ...

    def run(self, argv: Sequence[str]) -> ZoektIndexRunResult: ...
```

- **Responsabilidade (Protocol):** executar argv da CLI oficial (`zoekt-index` / opcionalmente `zoekt-git-index`) e devolver exit + saídas capturadas.
- **Motivo da separação:** isola `subprocess`/PATH; mockável; não interpreta formato de shard (D-T10-002).
- **Implementação:** `SubprocessZoektIndexRunner` usa lista de args (nunca shell string); captura stdout/stderr truncáveis pelo adaptador na mensagem de erro.
- **Invariantes:** `argv[0]` é o binário; timeout configurável.
- **Erros:** binário ausente / timeout — adaptador envelopa em `ExactCodeIndexError(operation="index")`; `returncode != 0` também.

### 3.8 `ZoektExactCodeIndex`

```python
class ZoektExactCodeIndex:
    def __init__(
        self,
        *,
        search: ZoektSearchTransport,
        indexer: ZoektIndexRunner,
        index_dir: str | Path,
        index_bin: str = "zoekt-index",
        git_index_bin: str = "zoekt-git-index",
        git_workdir: str | Path | None = None,
    ) -> None: ...

    @classmethod
    def from_environ(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        search: ZoektSearchTransport | None = None,
        indexer: ZoektIndexRunner | None = None,
    ) -> ZoektExactCodeIndex: ...

    def index(
        self,
        repository: str,
        commit: str,
        files: Sequence[FileToIndex],
    ) -> None: ...

    def search(self, query: ExactSearchQuery) -> Sequence[ExactMatch]: ...

    def delete_repository(self, repository: str) -> None: ...
```

- **Responsabilidade:** implementação default da porta — mapeia modelos ↔ CLI/HTTP oficiais e mantém mapa mínimo `repository → last_commit`.
- **Motivo da separação:** único lugar que conhece query language Zoekt, flags `-index`, materialização de árvore e JSON `FileMatches` (D-T10-002).
- **Comportamento contratado:**
  1. **`index` (MVP):** valida invariante I-T10-004; `files` vazio → return; materializa temp tree `path → content`; invoca  
     `indexer.run([index_bin, "-index", str(index_dir), …repo flags documentadas…, str(tree_dir)])`; atualiza mapa `repository → commit`; limpa temp best-effort.
  2. **`index` (otimização):** se `git_workdir` foi injetado no construtor e aponta tip no `commit`, pode usar `git_index_bin` (`zoekt-git-index`) em vez de rematerializar — **fora do Protocol**; T14 não depende disso.
  3. **`search`:** se `pattern == ""` → `()`; caso contrário monta `Q` com literal escapado (I-T10-010) + `repo:` / `file:` se filtros; `POST` via `search.post_search({"Q":…, "Opts":{"NumContextLines": context_lines, …}})`; mapeia → `ExactMatch` preenchendo `commit` via resposta ou mapa interno; ordena (I-T10-016).
  4. **`delete_repository`:** remove do `index_dir` apenas artefatos associados ao `repository` na indexação desta porta; sem parse binário; ausência = no-op; falha I/O → `ExactCodeIndexError(operation="delete")`.
- **Escape literal (I-T10-010):** metacaracteres em `pattern` (ex.: `foo.bar`, `a*b`, `x:y`) **não** devem virar regex acidental; usar quoting/sintaxe literal documentada pelo Zoekt (preferência: `content:"…"` com escape de aspas internas) e só então concatenar filtros `repo:` / `file:`.
- **Envs (`from_environ`):** `ZOEKT_URL` (default `http://127.0.0.1:6070`), `ZOEKT_INDEX_DIR`, `ZOEKT_INDEX_BIN`, `ZOEKT_GIT_INDEX_BIN` — sem tocar `AppSettings`.
- **Erros:** CLI/HTTP/JSON/binário/invariante → `ExactCodeIndexError` com `operation` adequado.

### 3.9 `FakeExactCodeIndex`

```python
class FakeExactCodeIndex:
    def __init__(
        self,
        *,
        fail_operations: AbstractSet[str] | None = None,
    ) -> None: ...

    def index(
        self,
        repository: str,
        commit: str,
        files: Sequence[FileToIndex],
    ) -> None: ...

    def search(self, query: ExactSearchQuery) -> Sequence[ExactMatch]: ...

    def delete_repository(self, repository: str) -> None: ...
```

- **Responsabilidade:** double injetável da porta em memória para BDD/unit/T14/T16 sem processo Zoekt.
- **Motivo da separação:** valida contrato da porta (BDD-024 / DEC-016) sem HTTP/CLI; simula falha tipada sob demanda.
- **Comportamento contratado:**
  - store: `dict[(repository, commit, path)] -> content` com semântica de **substituição do conjunto do `repository`** a cada `index` bem-sucedido (paths não reenviados somem — ZOEKT-08);
  - `search`: substring exata sobre `content` (decode lossy/`surrogateescape` aceitável); respeita filtros `repository` / `path_prefix`; `pattern == ""` → `()`;
  - `delete_repository`: remove todas as entradas daquele `repository`; ausência = no-op;
  - se `operation in fail_operations` → `ExactCodeIndexError` sem segredos;
  - **não** fala HTTP/CLI.
- **Erros:** somente `ExactCodeIndexError` quando configurado ou invariante I-T10-004 violada.

## 4. Reexports (`index/zoekt/__init__.py`)

```python
from github_rag.index.zoekt.errors import ExactCodeIndexError
from github_rag.index.zoekt.fake import FakeExactCodeIndex
from github_rag.index.zoekt.index import ZoektExactCodeIndex
from github_rag.index.zoekt.models import ExactMatch, ExactSearchQuery, FileToIndex
from github_rag.index.zoekt.port import ExactCodeIndex
from github_rag.index.zoekt.client import HttpZoektSearchTransport, ZoektSearchTransport
from github_rag.index.zoekt.runner import (
    SubprocessZoektIndexRunner,
    ZoektIndexRunResult,
    ZoektIndexRunner,
)
```

## 5. Handoff

| Consumidor | Uso |
|---|---|
| T14 `IndexingOrchestrator` | `index(repository, commit, files)`; em falha/`ExactCodeIndexError` ou BR-005 → `delete_repository` + reindex full; dono do diff ENG-012 |
| T16 `QueryService` | `search(ExactSearchQuery)` → evidências `ExactMatch` |
| T19 | garante `zoekt-webserver -rpc -index <ZOEKT_INDEX_DIR>` e envs alinhados |
| Testes T10 | fakes de transport/runner + `FakeExactCodeIndex`; BDD da porta sem container |
