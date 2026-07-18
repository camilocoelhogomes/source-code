# BDD — T11-treesitter-chunker

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T11-treesitter-chunker` |
| Estado | `PENDING_ARCHITECT_REVIEW` |
| Versão | `0.2.0` |
| Design base | `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| Rastreabilidade | BDD-007 (etapa Tree-sitter); BDD-024; DEC-003, DEC-015; BR-005, BR-023; ENG-008 |
| Trigger | Review humano PR #9 — yaml/json/xml/toml |

## Cenários executáveis

### TS-01 — BDD-007: arquivo Python gera chunks Tree-sitter não vazios

**Dado** um `ChunkSourceFile` com path `src/app.py` e conteúdo UTF-8 contendo uma `class` e uma `def`  
**Quando** `TreeSitterContextualChunker().chunk(source)` é executado  
**Então** o resultado é uma `tuple` com `len >= 1`  
**E** cada `SemanticChunk` tem `text` não vazio, `path == "src/app.py"`, `language == SourceLanguage.python`  
**E** existem chunks cujos `kind` refletem estrutura (`class` e/ou `function`)  
**E** `0 <= start_byte < end_byte` e o slice de bytes decodificado coincide com `text`  
**E** `start_point` e `end_point` são tuplas `(row, column)` 0-based presentes em cada chunk

### TS-02 — BDD-007: Markdown gera chunks estruturais (não por linhas)

**Dado** um arquivo `.md` com duas seções (`# A` e `# B`) e parágrafos  
**Quando** o chunker processa o arquivo  
**Então** há pelo menos um chunk com `language == SourceLanguage.markdown` e texto não vazio  
**E** a produção não depende de split por quantidade de linhas ou tamanho fixo (DEC-003)

### TS-03 — BDD-007: Java gera chunks estruturais

**Dado** um arquivo `.java` com uma classe e um método  
**Quando** o chunker processa o arquivo  
**Então** há chunks com `language == SourceLanguage.java` e `len >= 1`  
**E** ao menos um `kind` estrutural (`class` ou `method`) aparece

### TS-04 — DEC-003: proibido caminho de chunking por tamanho/linhas

**Dado** a implementação de produção `TreeSitterContextualChunker`  
**Quando** inspecionada a superfície pública de chunking (`ContextualChunker.chunk` e construtor da implementação default)  
**Então** não existe API/parâmetro de `max_chars`, `chunk_size`, `overlap` ou split por linhas como fonte de chunks  
**E** o único caminho feliz usa parse Tree-sitter + seleção de nós

### TS-05 — Corner: arquivo vazio → erro tipado

**Dado** `ChunkSourceFile` com `content == b""`  
**Quando** `chunk(source)` é chamado  
**Então** levanta `EmptySourceError` (subclasse de `ChunkingError`)  
**E** não retorna chunks nem faz fallback genérico

### TS-06 — Corner: binário / NUL → erro tipado

**Dado** conteúdo contendo `b"\x00"` **ou** bytes não decodificáveis como UTF-8 strict  
**Quando** `chunk(source)` é chamado  
**Então** levanta `BinarySourceError` (subclasse de `ChunkingError`)  
**E** não produz chunks por split genérico

### TS-07 — Corner: grammar indisponível → erro tipado

**Dado** um path com extensão sem grammar MVP (ex.: `.rs`) **ou** registry sem a language  
**Quando** `chunk(source)` é chamado  
**Então** levanta `GrammarUnavailableError` (subclasse de `ChunkingError`)  
**E** não faz chunking por linhas/tamanho

### TS-08 — Arquivo sem nós-alvo: root estrutural

**Dado** um `.py` válido contendo apenas um import (sem `class`/`def`)  
**Quando** o chunker processa o arquivo  
**Então** retorna exatamente um chunk do nó raiz estrutural (`kind` de module/program)  
**E** `text` não vazio  
**E** `len(result) == 1` (invariante sucesso ⇒ `len >= 1` via root fallback, design §4.4.1)

### TS-09 — `chunk_id` estável e contrato T12/T13/T14

**Dado** o mesmo `ChunkSourceFile` processado duas vezes  
**Quando** os resultados são comparados  
**Então** a sequência de `(chunk_id, path, start_byte, end_byte, kind, language)` é idêntica  
**E** cada `chunk_id` é SHA-256 hex lowercase de 64 chars calculado exatamente como design §4.3.1:  
`sha256(f"{path}\0{start_byte}\0{end_byte}\0{language.value}\0{kind}".encode("utf-8")).hexdigest()`  
**E** fixture conhecida (path/range/kind/language fixos) produz o `chunk_id` hex esperado pré-computado (contrato estável para T12/T13/T14)

### TS-10 — BDD-024: integração via SDK oficial tree-sitter

**Dado** a implementação default  
**Quando** um arquivo suportado é processado com sucesso  
**Então** o parse usa o pacote `tree-sitter` e grammar oficial da linguagem  
**E** não há cliente HTTP/parser caseiro substituindo o SDK

### TS-11 — TypeScript vs TSX (variante de grammar)

**Dado** um arquivo `.ts` e um arquivo `.tsx` com declarações válidas  
**Quando** ambos são processados  
**Então** ambos produzem `language == SourceLanguage.typescript` e `len >= 1`  
**E** o registry seleciona variante `language_typescript` vs `language_tsx` pela extensão

### TS-12 — Ninhos: class e method ambos emitidos

**Dado** um `.py` com uma classe contendo um método  
**Quando** o chunker processa o arquivo  
**Então** há chunks distintos para a classe e para o método (ranges distintos)  
**E** ordenação por `(start_byte, end_byte, kind)` crescente

### TS-13 — Dedupe: mesmo `(start_byte, end_byte)` → um chunk

**Dado** um fonte cujo seletor produziria dois nós com o mesmo `(start_byte, end_byte)` (ex.: wrapper `export_statement` + declaração interna, via fixture/registry de teste)  
**Quando** o chunker processa o arquivo  
**Então** retorna exatamente um chunk para aquele range  
**E** o `kind` preservado segue a prioridade documentada em `node_selectors` (declaração interna > wrapper)

### TS-14 — Corner: falha de parse / impossível materializar → `ParseFailureError`

**Dado** um `ChunkSourceFile` cujo parser/grammar levanta exceção **ou** cujo parse não permite materializar nenhum chunk com `text` não vazio  
**Quando** `chunk(source)` é chamado  
**Então** levanta `ParseFailureError` (subclasse de `ChunkingError`)  
**E** não faz fallback por linhas/tamanho

### TS-15 — Nós `ERROR` do Tree-sitter não invalidam sozinhos

**Dado** um `.py` com sintaxe inválida parcial, mas com ao menos um nó-alvo (ou root) materializável com texto não vazio  
**Quando** o chunker processa o arquivo  
**Então** o resultado é sucesso com `len >= 1`  
**E** não levanta `ParseFailureError` apenas pela presença de nós `ERROR`/`MISSING`

### TS-16 — YAML: chunking estrutural (não por tamanho/linhas)

**Dado** um `ChunkSourceFile` com path `config/app.yaml` (ou `.yml`) e conteúdo UTF-8 com mapeamento (ex.: chaves top-level e aninhadas)  
**Quando** `TreeSitterContextualChunker().chunk(source)` é executado  
**Então** o resultado é `tuple` com `len >= 1`  
**E** cada chunk tem `language == SourceLanguage.yaml` e `text` não vazio  
**E** ao menos um `kind` estrutural (`document` e/ou `block_mapping_pair`) aparece  
**E** a produção usa parse Tree-sitter + seleção de nós (DEC-003 — sem split por linhas/tamanho)

### TS-17 — JSON: chunking estrutural (não por tamanho/linhas)

**Dado** um arquivo `.json` com objeto contendo pares (incl. objeto aninhado)  
**Quando** o chunker processa o arquivo  
**Então** há chunks com `language == SourceLanguage.json` e `len >= 1`  
**E** ao menos um `kind` estrutural (`object`, `pair` ou `array`) aparece  
**E** não há caminho de chunking por tamanho/linhas

### TS-18 — XML: chunking estrutural (não por tamanho/linhas)

**Dado** um arquivo `.xml` com elemento raiz e filho aninhado  
**Quando** o chunker processa o arquivo  
**Então** há chunks com `language == SourceLanguage.xml` e `len >= 1`  
**E** ao menos um `kind` `element` aparece (ninhos com ranges distintos → ambos, design §4.4.1)  
**E** o registry usa a variante `language_xml` do pacote oficial `tree-sitter-xml`

### TS-19 — TOML: chunking estrutural (não por tamanho/linhas)

**Dado** um arquivo `.toml` com duas tabelas e pares  
**Quando** o chunker processa o arquivo  
**Então** há chunks com `language == SourceLanguage.toml` e `len >= 1`  
**E** ao menos um `kind` estrutural (`table` e/ou `pair`) aparece  
**E** a produção não depende de split por quantidade de linhas ou tamanho fixo (DEC-003)

## Fora de escopo destes BDD

- UI percentual/etapa (BDD-007 perspectiva UI → T14/T18)
- Zoekt e `metadata_persisted` (T10/T12/T13)
- Orquestração BR-005 restart (T14 consome os erros tipados)

## Execução

```bash
python -m pytest tests/bdd/test_treesitter_chunker.py -q
```
