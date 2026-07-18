# Plano de testes unitários — T11-treesitter-chunker

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T11-treesitter-chunker` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.2.1` |
| Interfaces base | `0.2.0` |
| Trigger | Review humano PR #9 — yaml/json/xml/toml; correção MAJOR (kinds estruturais) |

## Artefatos

| Artefato | Caminho |
|---|---|
| Types / chunk_id / language | `tests/unit/index/chunk/test_types.py` |
| Errors | `tests/unit/index/chunk/test_errors.py` |
| Node selectors | `tests/unit/index/chunk/test_node_selectors.py` |
| Grammar registry | `tests/unit/index/chunk/test_grammar_registry.py` |
| Tree-sitter chunker | `tests/unit/index/chunk/test_treesitter.py` |
| BDD | `tests/bdd/test_treesitter_chunker.py` |

## Matriz

| ID | Foco | Entrada | Esperado | Rastreabilidade | Arquivo |
|---|---|---|---|---|---|
| UT-T01 | `compute_chunk_id` canônico | path/bytes/lang/kind fixos | hex 64 = SHA-256 payload `\0` | design §4.3.1, TS-09 | `test_types.py` |
| UT-T02 | `compute_chunk_id` estável | mesmas entradas 2x | ids iguais | contrato T12 | `test_types.py` |
| UT-T03 | `compute_chunk_id` sensível | muda start_byte | id muda | corner | `test_types.py` |
| UT-T04 | `language_from_path` MVP (incl. yaml/yml/json/xml/toml) | extensões MVP | enum correto | I-T11-010, TS-16..19 | `test_types.py` |
| UT-T05 | `language_from_path` desconhecida | `.rs` | `None` | GrammarUnavailable | `test_types.py` |
| UT-T06 | `ChunkSourceFile` / `SemanticChunk` frozen | mutate attr | FrozenInstanceError | I-T11-002 | `test_types.py` |
| UT-T07 | `SourceLanguage` enum fechado v0.2 | membros | inclui yaml/json/xml/toml | D-T11-011 | `test_types.py` |
| UT-E01 | hierarquia erros | subclasses | `issubclass(..., ChunkingError)` | DoD corners | `test_errors.py` |
| UT-E02 | mensagem com path | `EmptySourceError(path=...)` | path em str | observabilidade | `test_errors.py` |
| UT-N01 | Python class+method | árvore fake | ambos ranges distintos | TS-12 | `test_node_selectors.py` |
| UT-N02 | dedupe range idêntico | dois nós mesmo range | um SelectedNode, kind prioritário | TS-13 | `test_node_selectors.py` |
| UT-N03 | zero alvos → root | só import | um nó root | TS-08 | `test_node_selectors.py` |
| UT-N04 | ordenação | nós fora de ordem | sorted (start,end,kind) | design §4.4.1 | `test_node_selectors.py` |
| UT-G01 | resolve python | OfficialGrammarRegistry | Language não None | BDD-024 | `test_grammar_registry.py` |
| UT-G02 | TS vs TSX | `.ts` / `.tsx` | variantes distintas quando possível | TS-11 | `test_grammar_registry.py` |
| UT-G03 | language sem pacote | registry fake | GrammarUnavailableError | TS-07 | `test_grammar_registry.py` |
| UT-G06 | resolve yaml/json/xml/toml | OfficialGrammarRegistry | Language não None cada | TS-16..19, BDD-024 | `test_grammar_registry.py` |
| UT-N05 | seletores config | árvores fake yaml/json/xml/toml | alvos design §4.4 | TS-16..19 | `test_node_selectors.py` |
| UT-C20 | YAML feliz | mapping | len>=1; language yaml; kind ∈ {document, block_mapping_pair} (não só stream) | TS-16 | `test_treesitter.py` |
| UT-C21 | JSON feliz | object+pairs | len>=1; language json; kind ∈ {object, pair, array} (não só document) | TS-17 | `test_treesitter.py` |
| UT-C22 | XML feliz | elements aninhados | len>=1; ≥2 ranges `element` distintos | TS-18 | `test_treesitter.py` |
| UT-C23 | TOML feliz | tables+pairs | len>=1; language toml; kind ∈ {table, pair} (não só document) | TS-19 | `test_treesitter.py` |
| UT-C01 | Python feliz | class+def | len>=1, texts não vazios | TS-01 | `test_treesitter.py` |
| UT-C02 | vazio | `b""` | EmptySourceError | TS-05 | `test_treesitter.py` |
| UT-C03 | NUL | `b"a\x00b"` | BinarySourceError | TS-06 | `test_treesitter.py` |
| UT-C04 | invalid UTF-8 | `b"\xff\xfe"` | BinarySourceError | TS-06 | `test_treesitter.py` |
| UT-C05 | extensão `.rs` | content ok | GrammarUnavailableError | TS-07 | `test_treesitter.py` |
| UT-C06 | registry injeta falha | GrammarUnavailable | propaga | UT-G03 | `test_treesitter.py` |
| UT-C07 | parse impossível | registry/parser que falha | ParseFailureError | TS-14 | `test_treesitter.py` |
| UT-C08 | sintaxe parcial ERROR | py inválido parcial | sucesso len>=1 | TS-15 | `test_treesitter.py` |
| UT-C09 | sem API tamanho | inspect signature | sem max_chars/chunk_size/overlap | TS-04 | `test_treesitter.py` |
| UT-C10 | Markdown | seções | len>=1 markdown | TS-02 | `test_treesitter.py` |
| UT-C11 | Java | class+method | len>=1 | TS-03 | `test_treesitter.py` |
| UT-C12 | idempotência | 2x mesmo source | chunks iguais | TS-09 | `test_treesitter.py` |
| UT-C13 | Protocol runtime | isinstance chunker | True | I-T11-001 | `test_treesitter.py` |
| UT-C14 | override `language` | path `.rs` + `language=python` | sucesso PYTHON (ignora extensão) | I-T11 / §3.2 | `test_treesitter.py` |
| UT-C15 | precedência binário | NUL + path `.rs` | `BinarySourceError` (não Grammar) | design §3/§6 | `test_treesitter.py` |

## Extremos / concorrência

| ID | Caso | Esperado | Arquivo |
|---|---|---|---|
| UT-X01 | path vazio + content | `language_from_path("")` → `None`; chunker → `GrammarUnavailableError` | `test_types.py` / `test_treesitter.py` |
| UT-X02 | só whitespace UTF-8 | root chunk ou sucesso len>=1 (não Empty) | `test_treesitter.py` |
| UT-X03 | arquivo grande sintético (~50KB py) | completa sem split por tamanho | `test_treesitter.py` |
| UT-X04 | duas chamadas sequenciais independentes | sem estado cruzado no chunker | `test_treesitter.py` |

## Fixture canônica `chunk_id` (TS-09 / UT-T01)

```text
path=src/app.py start_byte=0 end_byte=10 language=python kind=function
payload = b"src/app.py\x000\x0010\x00python\x00function"
chunk_id = 3bde810075b3f01ce7c66f67d9a2fbc8bb76ff43f11c74b27b1a4e5ddd1904f2
```

## Red esperado

Antes da implementação, imports de `github_rag.index.chunk.*` falham (`ImportError` / `AttributeError`) ou asserções falham. Demonstrar com:

```bash
python -m pytest tests/unit/index/chunk tests/bdd/test_treesitter_chunker.py -q
```
