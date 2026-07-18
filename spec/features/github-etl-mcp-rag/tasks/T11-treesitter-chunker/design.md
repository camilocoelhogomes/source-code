# Design — T11-treesitter-chunker

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T11-treesitter-chunker` |
| Autor | Implementation Task Runner |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.2.0` |
| Branch | `feature/github-etl-mcp-rag-T11-treesitter-chunker` |
| Base | `main` |
| Rastreabilidade | DEC-003, DEC-015; BR-005, BR-023; REQ-014, REQ-022; ENG-008, ENG-013; BDD-007 (etapa Tree-sitter); BDD-024 |
| Trigger | Review humano PR #9 — expandir matriz MVP com yaml/json/xml/toml (configs) |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Correções: política nós aninhados/dedupe; `chunk_id` canônico; ERROR nodes; TS/TSX; invariante `len>=1`. |
| 2026-07-18 | Humano (`camilocoelhogomes`) | Escopo autorizado (PR #9) | — | Pedido em `design.md`: incluir yaml, json, xml e toml por arquivos de configuração das linguagens. Discussion: `https://github.com/camilocoelhogomes/source-code/pull/9#discussion_r3609409543` |
| 2026-07-18 | Tech Lead Architect | `PENDING` | `0.2.0` | Ampliação da matriz MVP + grammars oficiais de config; aguarda review. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.2.0` | Matriz config (yaml/json/xml/toml) + grammars PyPI; DEC-003/015 intactos; XML `language_xml`. |

## 1. Contexto

O pipeline RAG exige que a **única** unidade de chunk semântico seja produzida por Tree-sitter (DEC-003 / ENG-008). T11 entrega a porta `ContextualChunker` e a implementação default baseada no pacote oficial `tree-sitter` + grammars oficiais (DEC-015 / BR-023). Consumidores: T12 (metadados SLM por chunk), T13 (payload Qdrant), T14 (orquestração).

Fora de escopo: SLM, Qdrant, Zoekt, elegibilidade (T09), orquestração (T14), embeddings.

## 2. Problema

Arquivos elegíveis precisam ser decompostos em chunks estruturais estáveis (path, ranges, texto, id) sem usar chunking genérico por tamanho, janela deslizante ou linhas. Falhas (grammar ausente, parse quebrado, conteúdo binário, arquivo vazio) devem ser tipadas — sem fallback genérico de chunking — para o orquestrador aplicar BR-005.

## 3. Solução proposta

Módulo `github_rag.index.chunk` (alinhado a T01; brief “chunking” = sinônimo) com:

| Componente | Papel |
|---|---|
| `types` | `SemanticChunk`, `ChunkSourceFile`, enums de linguagem |
| `errors` | Erros tipados (`ChunkingError` e subclasses) |
| `ports` | Protocol `ContextualChunker` |
| `grammar_registry` | Mapa linguagem/extensão → grammar oficial carregável |
| `node_selectors` | Queries/seletores de nós semânticos por linguagem |
| `treesitter` | `TreeSitterContextualChunker` — implementação default |

Fluxo feliz:

```text
ChunkSourceFile(path, content: bytes, language?)
  → resolver linguagem (extensão / override explícito)
  → carregar grammar oficial (registry; variante TS vs TSX por extensão)
  → parse Tree-sitter
  → extrair nós semânticos (não por tamanho/linhas)
  → dedupe ranges idênticos; ordenar
  → materializar SemanticChunk[] (texto, ranges, chunk_id estável)
  → sucesso ⇒ tuple com len >= 1
```

Fluxo de erro (sem fallback de chunking):

```text
conteúdo vazio          → EmptySourceError
binário / NUL / decode  → BinarySourceError
linguagem sem grammar   → GrammarUnavailableError
falha de parse (exceção)→ ParseFailureError
```

Todos herdam `ChunkingError`. O orquestrador (T14) trata qualquer `ChunkingError` como falha da etapa Tree-sitter do arquivo/repo (BR-005).

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T11 | Fora de T11 |
|---|---|---|
| BDD-007 | Produzir chunks Tree-sitter não vazios; etapa `tree_sitter` alimentável | UI/progresso/percentual (T14/T18); Zoekt/metadata_persisted |
| BDD-024 | Integração via `tree-sitter` + grammars oficiais | Outros SDKs |
| DEC-003 | Nenhum caminho de produção usa split por tamanho/linhas | — |

## 4. Componentes

### 4.1 `ChunkSourceFile`

Entrada imutável:

- `path: str` — caminho relativo no snapshot (POSIX-style no contrato; sem normalização inventada aqui)
- `content: bytes` — bytes do arquivo no tip `main`
- `language: SourceLanguage | None` — override; se `None`, resolve por extensão

### 4.2 `SourceLanguage` (enum fechado MVP)

Linguagens com grammar oficial no MVP (REQ-014 menciona textuais/Markdown/Java; Python é baseline do stack; config languages adicionadas por review humano PR #9):

| Valor | Extensões | Grammar (pacote PyPI) | Variante Language | Origem do pacote |
|---|---|---|---|---|
| `python` | `.py`, `.pyi` | `tree-sitter-python` | única | tree-sitter oficial |
| `java` | `.java` | `tree-sitter-java` | única | tree-sitter oficial |
| `javascript` | `.js`, `.mjs`, `.cjs` | `tree-sitter-javascript` | única | tree-sitter oficial |
| `typescript` | `.ts` | `tree-sitter-typescript` | `language_typescript` | tree-sitter oficial |
| `typescript` | `.tsx` | `tree-sitter-typescript` | `language_tsx` | tree-sitter oficial |
| `markdown` | `.md`, `.markdown` | `tree-sitter-markdown` | única | grammar oficial mantida |
| `yaml` | `.yaml`, `.yml` | `tree-sitter-yaml` (`0.7.2`) | única | [tree-sitter-grammars/tree-sitter-yaml](https://github.com/tree-sitter-grammars/tree-sitter-yaml) — grammar comunitária oficial do ecossistema tree-sitter-grammars (não há `tree-sitter/tree-sitter-yaml` no org core; escolha alinhada DEC-015/BR-023) |
| `json` | `.json` | `tree-sitter-json` (`0.24.8`) | única | [tree-sitter/tree-sitter-json](https://github.com/tree-sitter/tree-sitter-json) |
| `xml` | `.xml` | `tree-sitter-xml` (`0.7.0`) | `language_xml` | [tree-sitter/tree-sitter-xml](https://github.com/tree-sitter/tree-sitter-xml) — pacote expõe também `language_dtd`; MVP usa só `language_xml` para `.xml` |
| `toml` | `.toml` | `tree-sitter-toml` (`0.7.0`) | única | [tree-sitter-grammars/tree-sitter-toml](https://github.com/tree-sitter-grammars/tree-sitter-toml) — idem yaml: grammar oficial do ecossistema tree-sitter-grammars |

Extensão desconhecida / sem grammar → `GrammarUnavailableError` (não chunka por linhas). Matriz MVP permanece fechada; ampliar além desta lista continua evolução futura — **proibido** split genérico (DEC-003).

### 4.3 `SemanticChunk`

Saída imutável, contrato estável para T12/T13/T14:

| Campo | Tipo | Descrição |
|---|---|---|
| `chunk_id` | `str` | Identidade estável (ver §4.3.1) |
| `path` | `str` | Igual ao source |
| `language` | `SourceLanguage` | Linguagem usada no parse |
| `kind` | `str` | Tipo estrutural (`function`, `class`, `method`, `section`, `module`, …) |
| `text` | `str` | Slice UTF-8 do conteúdo no range |
| `start_byte` | `int` | Inclusivo |
| `end_byte` | `int` | Exclusivo |
| `start_point` | `tuple[int,int]` | `(row, column)` Tree-sitter (0-based) |
| `end_point` | `tuple[int,int]` | idem |

Invariantes: `0 <= start_byte < end_byte`; `text` não vazio; `chunk_id` reproduzível; sucesso de `chunk()` ⇒ `len(result) >= 1`.

#### 4.3.1 Algoritmo de `chunk_id`

```text
payload = f"{path}\0{start_byte}\0{end_byte}\0{language.value}\0{kind}".encode("utf-8")
chunk_id = sha256(payload).hexdigest()  # 64 hex chars, lowercase
```

Sem sal, sem conteúdo do texto no hash (id estável a edições fora do range; muda se range/kind/path/language mudarem).

### 4.4 Seleção estrutural (não por tamanho)

| Linguagem | Nós-alvo (MVP) |
|---|---|
| Python | `function_definition`, `class_definition`, `decorated_definition` (envolvendo os anteriores) |
| Java | `class_declaration`, `interface_declaration`, `method_declaration`, `constructor_declaration` |
| JavaScript/TS | `function_declaration`, `class_declaration`, `method_definition`, `export_statement` com declaração interna |
| Markdown | `section` (ou heading + corpo via estrutura do grammar markdown) |
| YAML | `document`, `block_mapping_pair` (unidades de documento / pares chave–valor; root `stream` só como fallback) |
| JSON | `object`, `pair`, `array` (estrutura de objetos/arrays e pares; root `document` como fallback) |
| XML | `element` (elementos aninhados com ranges distintos → ambos; root `document` como fallback) |
| TOML | `table`, `pair` (tabelas e pares; root `document` como fallback) |

#### 4.4.1 Nós aninhados, overlap e dedupe

| Regra | Comportamento |
|---|---|
| Ninhos com ranges distintos | Emitir **ambos** (ex.: `class` e `method` interno) — unidades contextuais distintas para T12/T13 |
| Mesmo `(start_byte, end_byte)` | Dedupe: manter **um** chunk; prioridade de `kind` documentada em `node_selectors` (ex.: declaração interna > `export_statement` wrapper) |
| Ordem | Determinística: ordenar por `(start_byte, end_byte, kind)` crescente |
| Zero nós-alvo após parse OK | Emitir **um** chunk do nó raiz estrutural (`module` / `program` / `document` / `stream`); `kind` = nome do tipo raiz |
| Arquivo vazio | Continua `EmptySourceError` |

### 4.5 `ContextualChunker` (Protocol)

Responsabilidade: única porta de produção de chunks semânticos RAG a partir de um arquivo-fonte. Separação: isola Tree-sitter/grammars dos consumidores (T12/T13/T14) e impede chunking genérico fora do adaptador.

```python
class ContextualChunker(Protocol):
    def chunk(self, source: ChunkSourceFile) -> tuple[SemanticChunk, ...]: ...
```

- Sucesso: tuple imutável com `len >= 1`.
- Falha: levanta `ChunkingError` (subclasse); nunca retorna `()` nem faz split por tamanho/linhas.
- Implementação default: `TreeSitterContextualChunker(grammar_registry=...)`.

### 4.6 Detecção de binário

Antes do parse: se `b"\x00"` em `content` → `BinarySourceError`. Conteúdo deve ser decodificável como UTF-8 (com `strict`); falha de decode → `BinarySourceError` (tratado como não-textual para chunking). Elegibilidade (T09) já filtra a maioria; T11 defende a porta.

### 4.7 Grammar registry

`GrammarRegistry.resolve(language, path_extension) -> tree_sitter.Language` carrega grammars oficiais. Para `typescript`, escolhe `language_typescript` vs `language_tsx` pela extensão (`.ts` / `.tsx`). Para `xml`, usa `language_xml` (não `language_dtd` no MVP). Ausência/ImportError → `GrammarUnavailableError`. Injetável para testes (fake language/parser).

### 4.8 Parse e nós `ERROR`

Tree-sitter em geral **não** levanta em sintaxe inválida; produz nós `ERROR` / `MISSING`.

| Situação | Resultado |
|---|---|
| Exceção do parser / grammar | `ParseFailureError` |
| Árvore com nós `ERROR`, mas há nós-alvo (ou root fallback) com texto não vazio | Sucesso — extrair normalmente (DEC-003; sem fallback por linhas) |
| Parse “ok” mas impossível materializar qualquer chunk com texto não vazio | `ParseFailureError` |

## 5. Fluxo de dados

```text
T09 elegível → T14 lê bytes → ContextualChunker.chunk
  → SemanticChunk[] → T12 MetadataGenerator (por chunk)
  → T13 VectorStore.upsert
```

## 6. Erros

| Tipo | Quando | Fallback chunking? |
|---|---|---|
| `EmptySourceError` | `len(content)==0` | Não |
| `BinarySourceError` | NUL ou decode UTF-8 falha | Não |
| `GrammarUnavailableError` | linguagem/extensão sem grammar | Não |
| `ParseFailureError` | exceção do parser **ou** impossível materializar chunk não vazio | Não |

Mensagens incluem `path` e `language` quando souber; sem dados sensíveis. Base `ChunkingError` carrega `path: str | None` e `language: SourceLanguage | None`.

## 7. Segurança

- Sem I/O de rede; grammars empacotadas.
- Conteúdo do arquivo pode ser grande (REQ-019); parse in-memory — risco de memória documentado; sem limite funcional no MVP.
- Sem secrets nesta camada.

## 8. Compatibilidade

- Deps: `tree-sitter`, `tree-sitter-python`, `tree-sitter-java`, `tree-sitter-javascript`, `tree-sitter-typescript`, `tree-sitter-markdown`, **`tree-sitter-yaml`**, **`tree-sitter-json`**, **`tree-sitter-xml`**, **`tree-sitter-toml`** (pins no `pyproject`).
- Python 3.12+.
- Não altera contratos T01–T10; amplia o enum `SourceLanguage` e a matriz de extensões (consumidores T12/T13/T14 passam a aceitar os novos valores de `language`).

## 9. Observabilidade

- Sem logger obrigatório nesta task; erros tipados bastam para T14 registrar etapa `tree_sitter` com falha.
- Contagem de chunks retornada é observável pelo orquestrador.

## 10. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Grammar markdown com API diferente | Isolar seletor; testes BDD com fixture `.md` |
| Arquivos enormes | REQ-019 aceito; documentar; sem chunk por tamanho |
| Mudança de API tree-sitter | Pin de versões no pyproject |
| Id instável entre runs | Hash canônico §4.3.1 |
| REQ-014 “qualquer linguagem” vs enum MVP | Extensão sem grammar → `GrammarUnavailableError` → BR-005 no T14; ampliar grammars em tasks futuras — **proibido** split genérico |
| Overlap class/method aumenta N chunks SLM | Aceito (qualidade contextual); dedupe só range idêntico |

## 11. Rollback

Remover pacote `index.chunk` (exceto stub), deps tree-sitter do pyproject e testes T11. Sem migration de dados.

## 12. Decisões de design

| ID | Decisão | Motivo |
|---|---|---|
| D-T11-001 | Chunk só via Tree-sitter; proibido split tamanho/linhas | DEC-003, ENG-008 |
| D-T11-002 | SDK oficial `tree-sitter` + grammars | DEC-015, BR-023, BDD-024 |
| D-T11-003 | Erros tipados sem fallback genérico | BR-005 alinhado; DoD corner cases |
| D-T11-004 | `chunk_id` = SHA-256 hex canônico §4.3.1 | Contrato estável T12/T13/T14 |
| D-T11-005 | Root estrutural quando sem nós-alvo | Evita “zero chunks” em arquivo válido sem inventar split por linhas |
| D-T11-006 | Conteúdo em `bytes` na entrada | Alinha snapshot Git; decode controlado |
| D-T11-007 | Registry injetável | Testabilidade sem grammars reais em unitários de erro |
| D-T11-008 | Ninhos com ranges distintos → ambos; range idêntico → dedupe | Contrato estável + evita double-index do mesmo span |
| D-T11-009 | Nós `ERROR` não invalidam sozinhos o parse | Comportamento real do Tree-sitter; só falha se não houver chunk materializável |
| D-T11-010 | TS vs TSX via variante Language no registry | Pacote oficial `tree-sitter-typescript` expõe ambas |
| D-T11-011 | Matriz MVP inclui yaml/json/xml/toml | Review humano PR #9 — configs de linguagens; grammars oficiais PyPI (DEC-015) |
| D-T11-012 | XML usa só `language_xml` no MVP | `.dtd` fora do escopo pedido; evita ambiguidade de variante |

## 13. Arquivos previstos

```text
src/github_rag/index/chunk/
  __init__.py
  types.py
  errors.py
  ports.py
  grammar_registry.py
  node_selectors.py
  treesitter.py
tests/unit/index/chunk/
tests/bdd/test_treesitter_chunker.py
spec/.../tasks/T11-treesitter-chunker/*
```
