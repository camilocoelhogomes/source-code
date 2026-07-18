# Interfaces — T11-treesitter-chunker

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T11-treesitter-chunker` |
| Autor | Implementation Task Runner + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `PENDING_ARCHITECT_REVIEW` |
| Versão | `0.2.0` |
| Design base | `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.2.0` (`PENDING_ARCHITECT_REVIEW`) |
| Branch | `feature/github-etl-mcp-rag-T11-treesitter-chunker` |
| Trigger | Review humano PR #9 — yaml/json/xml/toml |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Correções: `language_from_path` → `None`; `OfficialGrammarRegistry` + TS/TSX; `SelectedNode`; `path_extension` com ponto; `ChunkingError.__init__`. |
| 2026-07-18 | Tech Lead Architect | `PENDING` | `0.2.0` | Ampliação enum/extensões/registry/seletores para yaml/json/xml/toml. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `SourceLanguage` | `index/chunk/types.py` | Enum fechado MVP de linguagens |
| `ChunkSourceFile` | `index/chunk/types.py` | Entrada imutável do chunker |
| `SemanticChunk` | `index/chunk/types.py` | Saída imutável (contrato T12/T13/T14) |
| `compute_chunk_id` | `index/chunk/types.py` | Hash canônico design §4.3.1 |
| `language_from_path` | `index/chunk/types.py` | Resolução pura extensão → linguagem |
| `ChunkingError` (+ subclasses) | `index/chunk/errors.py` | Falhas tipadas sem fallback |
| `ContextualChunker` | `index/chunk/ports.py` | Porta de domínio |
| `GrammarRegistry` | `index/chunk/grammar_registry.py` | Resolução language→grammar oficial |
| `OfficialGrammarRegistry` | `index/chunk/grammar_registry.py` | Default com pacotes oficiais (TS/TSX) |
| `SelectedNode` | `index/chunk/node_selectors.py` | Nó estrutural selecionado (pré-materialização) |
| `select_semantic_nodes` | `index/chunk/node_selectors.py` | Seleção estrutural por linguagem |
| `TreeSitterContextualChunker` | `index/chunk/treesitter.py` | Implementação default |

### Fora de escopo

| Item | Dono |
|---|---|
| Elegibilidade de arquivos | T09 |
| Metadados SLM | T12 |
| Qdrant / embeddings | T13 |
| Orquestração / BR-005 restart | T14 |
| Zoekt | T10 |

## 2. Decisões de contrato

| ID | Decisão | Motivo |
|---|---|---|
| I-T11-001 | Porta `ContextualChunker` como `Protocol` | T14 injeta fake; DEC-003 isolado do orquestrador |
| I-T11-002 | `SemanticChunk` frozen dataclass | Contrato estável T12/T13; sem mutação pós-chunk |
| I-T11-003 | Entrada `content: bytes` | Alinha snapshot Git; decode UTF-8 estrito na porta |
| I-T11-004 | Erros tipados hierárquicos sob `ChunkingError` | Corner cases DoD; T14 mapeia para falha de etapa |
| I-T11-005 | `GrammarRegistry` separado do chunker | Testar grammar ausente sem mockar parser inteiro |
| I-T11-006 | Seletores de nós em módulo próprio | Regras estruturais testáveis sem I/O de grammar |
| I-T11-007 | Sucesso ⇒ `tuple` com `len >= 1`; nunca `()` | Invariante design; evita “chunk vazio” silencioso |
| I-T11-008 | Sem parâmetros de tamanho/overlap na porta | DEC-003 / ENG-008 — impossível pedi-los pela API |
| I-T11-009 | `chunk_id` via `compute_chunk_id` puro | Reproduzível e unit-testável sem Tree-sitter |
| I-T11-010 | `language_from_path` retorna `SourceLanguage \| None` | Regra pura; caller (chunker) levanta `GrammarUnavailableError` |
| I-T11-011 | `path_extension` com ponto (ex.: `.tsx`) | Alinha matriz design §4.2 e variante TS/TSX no registry |

## 3. Contratos detalhados

### 3.1 `SourceLanguage`

```python
class SourceLanguage(StrEnum):
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    MARKDOWN = "markdown"
    YAML = "yaml"
    JSON = "json"
    XML = "xml"
    TOML = "toml"
```

- **Responsabilidade:** enumerar linguagens com grammar oficial no MVP e valor estável em `chunk_id`/payload.
- **Motivo da separação:** evita strings mágicas e documenta o conjunto fechado (extensão fora → `GrammarUnavailableError`).
- **Ampliação v0.2.0:** yaml/json/xml/toml — configs (review humano PR #9 / design D-T11-011).

### 3.2 `ChunkSourceFile`

```python
@dataclass(frozen=True)
class ChunkSourceFile:
    path: str
    content: bytes
    language: SourceLanguage | None = None
```

- **Responsabilidade:** carregar o arquivo-fonte a chunkar (path + bytes + override opcional de linguagem).
- **Motivo da separação:** desacopla o chunker de como T08/T14 obtêm bytes do snapshot.
- **Invariantes:** `path` não vazio; `content` pode ser vazio (erro tipado na porta).

### 3.3 `SemanticChunk`

```python
@dataclass(frozen=True)
class SemanticChunk:
    chunk_id: str
    path: str
    language: SourceLanguage
    kind: str
    text: str
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]
    end_point: tuple[int, int]
```

- **Responsabilidade:** unidade exclusiva de chunk semântico/RAG consumida por T12 (metadados) e T13 (payload).
- **Motivo da separação:** estabiliza o contrato entre Tree-sitter e o restante do pipeline; impede redefinição da unidade em T12/T13.
- **Invariantes:** `0 <= start_byte < end_byte`; `text` não vazio; `chunk_id == compute_chunk_id(...)`.

### 3.4 `compute_chunk_id`

```python
def compute_chunk_id(
    *,
    path: str,
    start_byte: int,
    end_byte: int,
    language: SourceLanguage,
    kind: str,
) -> str: ...
```

- **Responsabilidade:** produzir SHA-256 hex (64 chars, lowercase) do payload canônico  
  `f"{path}\0{start_byte}\0{end_byte}\0{language.value}\0{kind}".encode("utf-8")`  
  (design §4.3.1 / BDD TS-09).
- **Motivo da separação:** função pura testável; T12/T13 não recalculam com algoritmo divergente.

### 3.5 `language_from_path`

```python
def language_from_path(path: str) -> SourceLanguage | None: ...
```

- **Responsabilidade:** mapear a extensão do `path` para `SourceLanguage` MVP (sem I/O, sem levantar).
- **Motivo da separação:** regra pura unit-testável; o chunker traduz `None` em `GrammarUnavailableError` (design §4.2 / BDD TS-07).
- **Extensões:** `.py`/`.pyi`→`python`; `.java`→`java`; `.js`/`.mjs`/`.cjs`→`javascript`; `.ts`/`.tsx`→`typescript`; `.md`/`.markdown`→`markdown`; `.yaml`/`.yml`→`yaml`; `.json`→`json`; `.xml`→`xml`; `.toml`→`toml`.
- **Desconhecida / sem extensão:** retorna `None` (nunca inventa linguagem nem chunka por linhas).
- **Formato da extensão comparada:** sufixo lowercase com ponto (ex.: `.tsx`).

### 3.6 Erros (`ChunkingError`)

```python
class ChunkingError(Exception):
    def __init__(
        self,
        message: str = "",
        *,
        path: str | None = None,
        language: SourceLanguage | None = None,
    ) -> None: ...

    path: str | None
    language: SourceLanguage | None

class EmptySourceError(ChunkingError): ...
class BinarySourceError(ChunkingError): ...
class GrammarUnavailableError(ChunkingError): ...
class ParseFailureError(ChunkingError): ...
```

- **Responsabilidade:** sinalizar falhas de chunking sem fallback genérico (vazio, binário, grammar, parse).
- **Motivo da separação:** distinto de erros de elegibilidade/catálogo; T14 trata qualquer `ChunkingError` como falha da etapa `tree_sitter` (BR-005).
- **Quando (alinhado design §6 / BDD TS-05–07, TS-14):**
  - `EmptySourceError` — `len(content) == 0`
  - `BinarySourceError` — `b"\x00"` em `content` **ou** decode UTF-8 `strict` falha
  - `GrammarUnavailableError` — extensão/linguagem sem grammar MVP **ou** registry sem pacote/variante
  - `ParseFailureError` — exceção do parser/grammar **ou** impossível materializar chunk com `text` não vazio
- **Invariantes:** mensagens podem citar `path`/`language`; nunca inventam chunks; nós `ERROR`/`MISSING` do Tree-sitter **não** implicam sozinhos `ParseFailureError` (design §4.8 / BDD TS-15).

### 3.7 `ContextualChunker` (Protocol)

```python
@runtime_checkable
class ContextualChunker(Protocol):
    def chunk(self, source: ChunkSourceFile) -> tuple[SemanticChunk, ...]:
        """Produz chunks semânticos Tree-sitter para um arquivo.

        Responsabilidade
            Única porta de produção de chunks RAG a partir de um arquivo-fonte.

        Motivo da separação
            Isola Tree-sitter/grammars dos consumidores (T12/T13/T14) e impede
            chunking genérico por tamanho/linhas fora do adaptador.
        """
        ...
```

- **Sucesso:** `tuple` imutável com `len >= 1`.
- **Falha:** levanta `ChunkingError` (subclasse); nunca retorna `()` nem split por tamanho/linhas.
- **Proibido na assinatura:** `max_chars`, `chunk_size`, `overlap`, `max_lines` (DEC-003 / BDD TS-04).

### 3.8 `GrammarRegistry` (Protocol)

```python
@runtime_checkable
class GrammarRegistry(Protocol):
    def resolve(
        self,
        language: SourceLanguage,
        *,
        path_extension: str,
    ) -> Any:  # tree_sitter.Language
        """Resolve a Language oficial para a linguagem/extensão.

        Responsabilidade
            Carregar grammar oficial (incl. variante TS vs TSX).

        Motivo da separação
            Permite injetar fake em testes de erro (grammar ausente) sem
            acoplar o chunker aos pacotes nativos.
        """
        ...
```

- **`path_extension`:** sufixo lowercase **com ponto** (ex.: `.ts`, `.tsx`), tipicamente derivado do `path` do source.
- **Erros:** `GrammarUnavailableError` se pacote/variante ausente ou `ImportError`.
- **Retorno:** instância `tree_sitter.Language` (tipada como `Any` no contrato para não forçar import nos stubs de teste).

### 3.9 `OfficialGrammarRegistry`

```python
class OfficialGrammarRegistry:
    def resolve(
        self,
        language: SourceLanguage,
        *,
        path_extension: str,
    ) -> Any:  # tree_sitter.Language
        ...
```

- **Responsabilidade:** implementação default que carrega grammars oficiais `tree-sitter-*` (DEC-015 / BDD-024 / TS-10).
- **Motivo da separação:** concentra binding nativo/import dos pacotes; o chunker depende só de `GrammarRegistry`.
- **Variantes TypeScript (design §4.2 / §4.7 / BDD TS-11):**
  - `language == typescript` e `path_extension == ".ts"` → `language_typescript`
  - `language == typescript` e `path_extension == ".tsx"` → `language_tsx`
- **Variante XML (design §4.2 / §4.7 / D-T11-012 / BDD TS-18):**
  - `language == xml` → `language_xml` (MVP não usa `language_dtd`)
- **Demais linguagens MVP** (incl. yaml/json/toml) → Language única do pacote correspondente (`tree-sitter-yaml`, `tree-sitter-json`, `tree-sitter-toml`, …)
- **Ausência:** `ImportError` / pacote ou atributo de variante inexistente → `GrammarUnavailableError`.

### 3.10 `SelectedNode`

```python
@dataclass(frozen=True)
class SelectedNode:
    kind: str
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]
    end_point: tuple[int, int]
```

- **Responsabilidade:** representar um nó estrutural escolhido antes da materialização em `SemanticChunk` (sem `text`/`chunk_id`/`path`).
- **Motivo da separação:** permite testar seleção/dedupe/ordem sem decodificar bytes nem calcular hash.

### 3.11 `select_semantic_nodes`

```python
def select_semantic_nodes(
    language: SourceLanguage,
    root_node: Any,  # tree_sitter.Node
) -> Sequence[SelectedNode]: ...
```

- **Responsabilidade:** escolher nós estruturais (e root fallback) conforme design §4.4 / §4.4.1 (ninhos, dedupe range idêntico, ordenação).
- **Motivo da separação:** política de chunking estrutural testável independentemente do carregamento de grammar.
- **Invariantes:**
  - sem split por linhas/bytes arbitrários
  - ninhos com ranges distintos → ambos (BDD TS-12)
  - mesmo `(start_byte, end_byte)` → um; prioridade de `kind`: declaração interna > wrapper (ex.: `export_statement`) (BDD TS-13)
  - ordem: `(start_byte, end_byte, kind)` crescente
  - zero nós-alvo → um `SelectedNode` do root estrutural (`module` / `program` / `document` / `stream`)
  - alvos config (design §4.4 / BDD TS-16..TS-19): yaml → `document`/`block_mapping_pair`; json → `object`/`pair`/`array`; xml → `element`; toml → `table`/`pair`

### 3.12 `TreeSitterContextualChunker`

```python
class TreeSitterContextualChunker:
    def __init__(self, grammar_registry: GrammarRegistry | None = None) -> None: ...

    def chunk(self, source: ChunkSourceFile) -> tuple[SemanticChunk, ...]: ...
```

- **Responsabilidade:** implementar `ContextualChunker` via parse oficial Tree-sitter + seletores.
- **Motivo da separação:** adaptador SDK (DEC-015) atrás da porta; único caminho de produção em runtime default.
- **Default de registry:** `OfficialGrammarRegistry()` quando `grammar_registry is None`.
- **Fluxo:** validar vazio → validar binário (NUL / UTF-8 strict) → resolver language (`source.language` ou `language_from_path`) → `registry.resolve(language, path_extension=...)` → parse → `select_semantic_nodes` → materializar `SemanticChunk` com `compute_chunk_id` → ordenar.
- **Sucesso:** `tuple` com `len >= 1`; cada `chunk_id` via §3.4.
- **Erros:** conforme §3.6 / design §4.8 / §6 (`ParseFailureError` se nada materializável; `ERROR` nodes sozinhos não falham).
- **Proibido:** parâmetros ou caminhos de `max_chars` / `chunk_size` / `overlap` / split por linhas.

## 4. Reexports (`index/chunk/__init__.py`)

```python
from github_rag.index.chunk.errors import (
    BinarySourceError,
    ChunkingError,
    EmptySourceError,
    GrammarUnavailableError,
    ParseFailureError,
)
from github_rag.index.chunk.ports import ContextualChunker
from github_rag.index.chunk.treesitter import TreeSitterContextualChunker
from github_rag.index.chunk.types import (
    ChunkSourceFile,
    SemanticChunk,
    SourceLanguage,
    compute_chunk_id,
)
```

`GrammarRegistry` / `OfficialGrammarRegistry` / `select_semantic_nodes` / `SelectedNode` / `language_from_path` são importáveis pelos submódulos para testes e injeção; não são obrigatórios na superfície mínima de bootstrap.

## 5. Handoff T12 / T13 / T14

| Consumidor | Usa |
|---|---|
| T12 `MetadataGenerator` | `SemanticChunk` (um por chamada) |
| T13 `VectorStore` | `chunk_id`, `path`, ranges, `text` + metadados SLM |
| T14 orquestrador | `ContextualChunker.chunk`; captura `ChunkingError` → etapa `tree_sitter` falha |

Contrato congelado nesta task: campos de `SemanticChunk`, algoritmo de `chunk_id` (§3.4 / design §4.3.1) e semântica de erros não devem mudar sem `SCOPE_CHANGE_REQUIRED`.
