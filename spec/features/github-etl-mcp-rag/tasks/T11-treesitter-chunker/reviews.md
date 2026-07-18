# Reviews — T11-treesitter-chunker

## Review — Design (v0.1.0 → v0.1.1)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Escopo T11 (só chunker; sem SLM/Qdrant/Zoekt/T14) | OK | §1 fora de escopo; §5 handoff |
| DEC-003 / ENG-008 — sem chunk por tamanho/linhas | OK | §3 fluxo erro; D-T11-001; §4.4 root estrutural |
| DEC-015 / BR-023 / BDD-024 — SDK oficial + grammars | OK | §3, §4.7, §8; D-T11-002 |
| Erros tipados alinhados a BR-005 | OK | §3, §6; subclasses de `ChunkingError` |
| Contrato estável T12/T13/T14 | OK | `SemanticChunk` §4.3; `chunk_id` §4.3.1; `len>=1` |
| Corner cases DoD (vazio, binário, grammar) | OK | §3 fluxo erro; §4.6; §6 |

### Achados (v0.1.0) — corrigidos em v0.1.1

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | Política de nós aninhados/overlap/dedupe ausente — ambígua para N chunks SLM/Qdrant | design v0.1.0 §4.4 | Definir: ranges distintos → ambos; range idêntico → dedupe; ordem determinística | Corrigido §4.4.1 / D-T11-008 |
| `MAJOR` | `chunk_id` “hash determinístico” sem algoritmo/canônico | design v0.1.0 §4.3 | SHA-256 hex de payload canônico | Corrigido §4.3.1 / D-T11-004 |
| `MAJOR` | `ParseFailureError` vs nós `ERROR` do Tree-sitter indefinido | design v0.1.0 §6 | ERROR não falha sozinho; falha só se não materializar chunk | Corrigido §4.8 / D-T11-009 |
| `MAJOR` | `.tsx` mapeado a typescript sem variante Language | design v0.1.0 §4.2 | Registry resolve `language_tsx` vs `language_typescript` | Corrigido §4.2 / §4.7 / D-T11-010 |
| `SUGGESTION` | Diagrama §3 citava `bytes\|str` inconsistente com `content: bytes` | design v0.1.0 §3 | Unificar em `bytes` | Corrigido §3 |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.1. Prosseguir para BDD/interfaces (QA) sem alteração de escopo.

---

## Review — BDD (v0.1.0 → v0.1.1)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| BDD-007 — chunks Tree-sitter não vazios | OK | TS-01, TS-02, TS-03; root fallback TS-08 |
| BDD-024 — SDK oficial `tree-sitter` | OK | TS-10 |
| DEC-003 — sem chunk por tamanho/linhas | OK | TS-04; reforço em TS-02/TS-05–07/TS-14 |
| Corner tipados (vazio, binário, grammar) | OK | TS-05, TS-06, TS-07 (+ ParseFailure TS-14) |
| Contrato estável `chunk_id` T12/T13/T14 | OK | TS-09 com algoritmo §4.3.1 + fixture hex |
| Alinhamento design v0.1.1 (ninhos/dedupe/ERROR/TSX) | OK | TS-11, TS-12, TS-13, TS-15 |

### Achados (v0.1.0) — corrigidos em v0.1.1

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | `chunk_id` só assertava reprodutibilidade/tamanho, sem fórmula canônica §4.3.1 nem fixture hex — contrato T12/T13/T14 frágil | bdd v0.1.0 TS-09 | Assertar payload SHA-256 exato + hex pré-computado | Corrigido TS-09 |
| `MAJOR` | Dedupe de range idêntico (design §4.4.1 / D-T11-008) sem cenário BDD | bdd v0.1.0 (só TS-12 ninhos) | Cenário: mesmo `(start_byte, end_byte)` → um chunk com prioridade de `kind` | Corrigido TS-13 |
| `MAJOR` | `ParseFailureError` (design §4.8/§6) ausente nos corners tipados | bdd v0.1.0 TS-05–07 | Cenário parser exception / impossível materializar | Corrigido TS-14 |
| `SUGGESTION` | Nós `ERROR` não invalidam sozinhos (D-T11-009) sem cobertura | design §4.8 | Cenário sintaxe parcial com chunk materializável | Corrigido TS-15 |
| `SUGGESTION` | Campos `start_point`/`end_point` do contrato `SemanticChunk` não citados | design §4.3; bdd TS-01 | Incluir presença das tuplas no happy path | Corrigido TS-01 |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — bdd v0.1.1. Prosseguir para interfaces (Architect) / testes unitários (QA) sem alteração de escopo.

---

## Review — Interfaces (v0.1.0 → v0.1.1)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Comentários responsabilidade + motivo da separação em cada interface | OK | §3.1–§3.12 (após correção: `OfficialGrammarRegistry`, `SelectedNode`, `language_from_path`) |
| `chunk_id` canônico §4.3.1 | OK | §3.4; handoff §5; I-T11-009 |
| Erros tipados alinhados design §6 / BDD TS-05–07/14/15 | OK | §3.6 com matriz quando + política ERROR |
| Registry TS vs TSX | OK | §3.8–§3.9; `path_extension` com ponto; variantes `language_typescript` / `language_tsx` |
| Sem API de tamanho/linhas (DEC-003) | OK | I-T11-008; §3.7; §3.12 |
| Alinhamento design/BDD (ninhos, dedupe, `len>=1`, root) | OK | §3.11–§3.12; I-T11-007 |

### Achados (v0.1.0) — corrigidos em v0.1.1

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | `language_from_path` retornava `SourceLanguage` mas o texto dizia que o caller levantava em extensão desconhecida — contrato ambíguo | interfaces v0.1.0 §3.8 | `-> SourceLanguage \| None`; `None` ⇒ chunker levanta `GrammarUnavailableError` | Corrigido §3.5 / I-T11-010 |
| `MAJOR` | `OfficialGrammarRegistry` no escopo sem seção própria (responsabilidade/motivo/TS-TSX) | interfaces v0.1.0 §1 vs §3.7 | Seção dedicada com variantes `.ts`/`.tsx` | Corrigido §3.9 |
| `SUGGESTION` | `SelectedNode` sem responsabilidade/motivo explícitos; fora da tabela de escopo | interfaces v0.1.0 §3.9 | Documentar e incluir no escopo | Corrigido §3.10 + §1 |
| `SUGGESTION` | Formato de `path_extension` (com/sem ponto) implícito | interfaces v0.1.0 §3.7 | Exigir sufixo lowercase com ponto | Corrigido I-T11-011 / §3.8 |
| `SUGGESTION` | `ChunkingError.__init__` e matriz ERROR/ParseFailure só por referência | interfaces v0.1.0 §3.5 | Assinatura + quando de cada subclass + TS-15 | Corrigido §3.6 |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces v0.1.1. Prosseguir para testes unitários (QA) sem alteração de escopo.

---

## QA — Unit + BDD red (v0.1.1)

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Artefatos | `unit-test-plan.md` v0.1.1; `tests/unit/index/chunk/*`; `tests/bdd/test_treesitter_chunker.py` |
| Resultado | `TESTS_READY_FOR_REVIEW` |

### Evidência RED

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/index/chunk tests/bdd/test_treesitter_chunker.py -q
```

Resultado: `6 errors during collection` — todos `ModuleNotFoundError` em:
`github_rag.index.chunk.{types,errors,node_selectors,grammar_registry,treesitter}` (impl ainda inexistente; só stub `__init__.py`).

---

## Review — Unit + BDD red (v0.1.1 → v0.1.2)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` + `tests/unit/index/chunk/*` + `tests/bdd/test_treesitter_chunker.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Contratos interfaces 0.1.1 (`chunk_id`, frozen, erros, porta, registry, seletores) | OK | UT-T*, UT-E*, UT-N*, UT-G*, UT-C09/C13; BDD TS-04/09/10 |
| Extremos / corners (vazio, binário, grammar, parse, ERROR) | OK | UT-C02–C08, UT-C15; BDD TS-05–07/14/15; UT-X* |
| Alinhamento BDD TS-01..TS-15 | OK | `test_treesitter_chunker.py` cobre todos os cenários |
| RED pela razão correta (módulos ausentes) | OK | 6× `ModuleNotFoundError` em `github_rag.index.chunk.*` |
| DEC-003 não enfraquecido | OK | UT-C09 / TS-04 proíbem API tamanho/overlap/linhas; sem fallback genérico nos asserts |

### Achados corrigidos nesta review (v0.1.2)

| Severidade | Achado | Evidência | Correção | Status |
|---|---|---|---|---|
| `MAJOR` | Override `ChunkSourceFile.language` sem cobertura — risco de ignorar contrato §3.2 | plan/testes v0.1.1 | UT-C14: path `.rs` + `language=python` → sucesso | Corrigido |
| `MAJOR` | Precedência binário vs extensão desconhecida ausente | design §3 fluxo erro | UT-C15: NUL + `.rs` → `BinarySourceError` | Corrigido |
| `SUGGESTION` | `SelectedNode` frozen só lia campos | `test_node_selectors.py` | Assert `FrozenInstanceError` | Corrigido |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — unit-test-plan v0.1.2 e testes RED. Prosseguir para implementação (Developer) sem alteração de escopo.

---

## Review — Implementação (Developer)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `src/github_rag/index/chunk/*` + `pyproject.toml` (deps tree-sitter*) |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| DEC-003 / ENG-008 — sem chunk por tamanho/linhas | OK | Porta/`chunk` sem params proibidos; seletores só por tipo de nó; sem fallback genérico |
| DEC-015 / BDD-024 — SDK oficial + grammars | OK | `tree_sitter.Parser` + `OfficialGrammarRegistry` com pacotes `tree-sitter-*` pinados |
| Erros tipados (vazio/binário/grammar/parse) | OK | Fluxo §3 em `treesitter.py`; hierarquia `errors.py`; ERROR nodes não falham sozinhos |
| `chunk_id` canônico §4.3.1 | OK | `compute_chunk_id` + materialização; BDD TS-09 / UT-T01 |
| TS vs TSX (D-T11-010) | OK | `language_typescript` / `language_tsx` por `path_extension` |
| Corners (ninhos, dedupe, root, whitespace, override, precedência binário) | OK | seletores + materialize; testes UT-C*/UT-X*/TS-* verdes (56) |
| Contrato estável T12/T13/T14 | OK | `SemanticChunk` frozen; `len>=1`; ranges/texto/`chunk_id` alinhados |

### Achados corrigidos nesta review

| Severidade | Achado | Evidência | Correção | Status |
|---|---|---|---|---|
| `MAJOR` | Fallback whitespace expandia range vazio do root mas zerava `start_point`/`end_point` → `(0,0),(0,0)` inconsistente com bytes/texto (contrato §4.3) | `treesitter.py` materialize; root Python whitespace `start==end` | `_byte_point` recalcula pontos ao expandir | Corrigido |
| `MAJOR` | `GrammarUnavailableError` do registry chegava sem `path` embora o chunker soubesse (design §6) | `chunk()` após `registry.resolve` | Re-raise com `path=source.path` + `message` cru | Corrigido |
| `MAJOR` | Deps `tree-sitter*` sem pin — risco de quebra de API (design §8 / risco §10) | `pyproject.toml` | Pins nas versões validadas (0.26.0 / grammars) | Corrigido |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |
| `SUGGESTION` | `OfficialGrammarRegistry.__init__` resolve todas as grammars eagerly (incl. JS) — custo de startup; não altera contrato | `grammar_registry.py` | Avaliar lazy cache só se baseline Blue mostrar gargalo |

### Checks

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/index/chunk tests/bdd/test_treesitter_chunker.py -q --no-cov
# 56 passed, 14 subtests passed
```

### Decisão

`APPROVED_BY_ARCHITECT` — implementação alinhada a design/interfaces/BDD após correções MAJOR acima. Prosseguir para etapa Blue (`refactoring.md`).

---

## Review — Design (v0.2.0 — escopo config PR #9)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Trigger | Review humano PR #9 (`r3609409543`) — yaml/json/xml/toml |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Escopo autorizado pelo humano | OK | §0 histórico; Trigger; D-T11-011 |
| DEC-003 — sem fallback tamanho/linhas | OK | §3 fluxo erro; §3.1; §4.4.1 root estrutural (não genérico); D-T11-001 |
| DEC-015 / BR-023 — só grammars oficiais PyPI | OK | §4.2 pins + origens; yaml/toml = tree-sitter-grammars (sem pacote no org core); json/xml = tree-sitter; D-T11-002/011 |
| Matriz `SourceLanguage` MVP | OK | §4.2: python/java/js/ts/markdown + yaml/json/xml/toml; extensões e variantes |
| Nós-alvo config | OK | §4.4: yaml `document`/`block_mapping_pair` (+ root `stream`); json `object`/`pair`/`array`; xml `element`; toml `table`/`pair` — tipos existem nos grammars |
| XML `language_xml` | OK | §4.2 / §4.7 / D-T11-012; pacote expõe `language_xml` e `language_dtd` |
| Compatibilidade T12/T13/T14 | OK | §8 amplia enum; contratos `SemanticChunk`/`chunk_id` inalterados |
| Riscos / rollback | OK | §10–§11; pins §8 |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |
| `SUGGESTION` | YAML MVP omite `flow_pair` (só `block_mapping_pair`) — YAML flow-only cobre via `document`/root | design §4.4; node-types yaml | Incluir `flow_pair` se BDD de configs flow exigir |
| `SUGGESTION` | TOML MVP omite `table_array_element` — `[[tables]]` cobertos indiretamente via `pair` | design §4.4; node-types toml | Incluir se BDD de Cargo/pyproject exigir unidade de tabela-array |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.2.0. Prosseguir para atualização de BDD/interfaces/unitários/implementação alinhados à matriz ampliada.

---

## Review — BDD / Interfaces / Unit+BDD red (v0.2.0 — config PR #9)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `interfaces.md` + `unit-test-plan.md` + testes RED config |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Trigger | Review humano PR #9 — yaml/json/xml/toml |
| Resultado | `CHANGES_REQUIRED` |

### Decisão por artefato

| Artefato | Decisão | Notas |
|---|---|---|
| `bdd.md` v0.2.0 (TS-16..TS-19) | Conteúdo OK (não marcado APPROVED enquanto gate conjunto falha) | DEC-003 explícito; kinds estruturais alinhados design §4.4; XML `language_xml` (TS-18) |
| `interfaces.md` v0.2.0 | Conteúdo OK (idem) | `SourceLanguage` + extensões; `language_xml`; seletores config §3.11; I-T11-008 intacto |
| `unit-test-plan.md` v0.2.0 + testes executáveis | `CHANGES_REQUIRED` | UT-C20..C23 / BDD TS-16..19 enfraquecem kinds estruturais vs `bdd.md` / design §4.4 |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| DEC-003 — cenários config exigem chunking estrutural (sem fallback tamanho/linhas) | FALHA parcial | `bdd.md` TS-16..19 OK no texto; asserts executáveis aceitam só root (`stream`/`document`) — ver MAJOR |
| DEC-015 — grammars oficiais | OK (contratos) | interfaces §3.9; design §4.2; UT-G06 planejado |
| Alinhamento design v0.2.0 | FALHA parcial | seletores/enum/extensões OK nos docs; testes feliz path não fecham kinds §4.4 |
| Extremos/corners | OK no plano | UT-N05 cobre alvos; corners pré-existentes mantidos |
| RED pela razão esperada | OK | ver evidência abaixo |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| `MAJOR` | Asserts TS-16 / UT-C20 aceitam `stream` no conjunto de kinds — root-only passa sem `document`/`block_mapping_pair` (enfraquece DEC-003 / bdd TS-16) | `tests/bdd/test_treesitter_chunker.py` ~353; `test_treesitter.py` UT-C20 ~238 | Intersecção só com `{"document", "block_mapping_pair"}` (root `stream` só via fallback testado noutro caso, se necessário) |
| `MAJOR` | Asserts TS-17 / UT-C21 e TS-19 / UT-C23 aceitam `document` sozinho — root fallback satisfaz sem `object`/`pair`/`array` ou `table`/`pair` | BDD + unit happy paths | Exigir intersecção com alvos design §4.4 (sem contar root como suficiente no feliz path) |
| `MAJOR` | TS-18 / fixture aninhada: BDD exige ninhos com ranges distintos → ambos; teste só `len(element_ranges) >= 1` | `test_treesitter_chunker.py` TS-18 ~380–383; bdd TS-18 | `assertGreaterEqual(len(element_ranges), 2)` para `_XML_CFG` |
| `MAJOR` | `unit-test-plan.md` UT-C20..C23 coluna Esperado só `len>=1, language` — não rastreia kinds estruturais de TS-16..19 | `unit-test-plan.md` matriz | Atualizar Esperado + asserts para kinds §4.4 / BDD |
| `SUGGESTION` | TS-18 não prova variante `language_xml` vs `language_dtd` | resolve só `assertIsNotNone` | Comparar com `tree_sitter_xml.language_xml()` (e ≠ `language_dtd`) |
| `SUGGESTION` | Docstring do módulo BDD ainda cita TS-01..TS-15 | `test_treesitter_chunker.py` L1–7 | Atualizar para TS-01..TS-19 / v0.2.0 |

### Evidência RED (subset config)

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/unit/index/chunk/test_types.py::TestFrozenDataclasses::test_source_language_closed_values \
  tests/unit/index/chunk/test_types.py::TestLanguageFromPath::test_ut_t04_mvp_extensions \
  tests/unit/index/chunk/test_grammar_registry.py::TestOfficialGrammarRegistry::test_ut_g06_resolve_config_languages \
  tests/unit/index/chunk/test_node_selectors.py::TestSelectSemanticNodes::test_ut_n05_config_language_targets \
  tests/unit/index/chunk/test_treesitter.py::TestTreeSitterContextualChunker::test_ut_c20_yaml \
  tests/unit/index/chunk/test_treesitter.py::TestTreeSitterContextualChunker::test_ut_c21_json \
  tests/unit/index/chunk/test_treesitter.py::TestTreeSitterContextualChunker::test_ut_c22_xml \
  tests/unit/index/chunk/test_treesitter.py::TestTreeSitterContextualChunker::test_ut_c23_toml \
  tests/bdd/test_treesitter_chunker.py::TestTS16YamlStructural \
  tests/bdd/test_treesitter_chunker.py::TestTS17JsonStructural \
  tests/bdd/test_treesitter_chunker.py::TestTS18XmlStructural \
  tests/bdd/test_treesitter_chunker.py::TestTS19TomlStructural \
  -q --no-cov
```

Resultado: falhas pela razão esperada (impl v0.1 ainda sem config):
- `AttributeError: SourceLanguage has no attribute 'YAML'|'XML'` (enum incompleto)
- `AssertionError` em UT-T07 (faltam `yaml`/`json`/`xml`/`toml` no enum)
- `GrammarUnavailableError` nos happy paths chunker/BDD (extensão fora do mapa MVP atual)

### Decisão

`CHANGES_REQUIRED` — corrigir asserts/plan (MAJORs) e reapresentar o trio BDD/interfaces/unit-tests para aprovação Architect. Não avançar implementação config até gate limpo.

---

## Review — BDD / Interfaces / Unit+BDD red (v0.2.1 — re-review MAJOR)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` 0.2.0 + `interfaces.md` 0.2.0 + `unit-test-plan.md` 0.2.1 + testes RED |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Trigger | Correção MAJOR commits `02cc081` / follow-up `caa7fc3` |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| MAJORs anteriores fechados | OK | TS-16/C20: só `document`/`block_mapping_pair`; TS-17/C21: só `object`/`pair`/`array`; TS-18/C22: `len(element_ranges) >= 2`; TS-19/C23: só `table`/`pair`; plano UT-C20..C23 Esperado alinhado |
| DEC-003 — chunking estrutural config | OK | Asserts feliz path não aceitam root-only; BDD TS-16..19 + UT-N05 |
| DEC-015 — grammars oficiais | OK | interfaces §3.9; UT-G06; design §4.2 |
| Alinhamento design v0.2.0 | OK | enum/extensões/seletores/XML `language_xml` |
| RED | OK | `GrammarUnavailableError` / `AttributeError` (enum incompleto) — impl config ainda ausente |

### Achados anteriores — status

| Severidade | Achado | Status |
|---|---|---|
| `MAJOR` | kinds YAML aceitam `stream` | Corrigido |
| `MAJOR` | kinds JSON/TOML aceitam `document` sozinho | Corrigido |
| `MAJOR` | XML ninhos `>= 1` | Corrigido (`>= 2`) |
| `MAJOR` | plano UT-C20..C23 sem kinds | Corrigido (v0.2.1) |
| `SUGGESTION` | docstring BDD TS-01..15 | Corrigido (TS-01..TS-19) |
| `SUGGESTION` | TS-18 não prova `language_xml` vs `language_dtd` | Aberto (não bloqueia) |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |
| `SUGGESTION` | TS-18 resolve só `assertIsNotNone` — não compara `language_xml` ≠ `language_dtd` | `test_treesitter_chunker.py` TS-18 | Opcional na impl/test GREEN |

### Decisão

`APPROVED_BY_ARCHITECT` — BDD 0.2.0, interfaces 0.2.0, unit-test-plan 0.2.1. Prosseguir para implementação config (Developer).

---

## Review — Implementação config (v0.2 / commit `1d0a37b`)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `src/github_rag/index/chunk/{types,grammar_registry,node_selectors}.py` + `pyproject.toml` (pins config) |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Trigger | Implementação expandida após design/BDD/interfaces/unit APPROVED v0.2.x |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| DEC-003 / ENG-008 — sem chunk por tamanho/linhas | OK | Sem `max_chars`/`chunk_size`/`overlap`/split por linhas no pacote; seletores só por tipo de nó |
| DEC-015 / BDD-024 — grammars oficiais PyPI | OK | `tree-sitter-yaml==0.7.2`, `json==0.24.8`, `xml==0.7.0`, `toml==0.7.0`; imports oficiais em `_language_ptr` |
| `SourceLanguage` + extensões §4.2 | OK | enum YAML/JSON/XML/TOML; `.yaml`/`.yml`/`.json`/`.xml`/`.toml` em `language_from_path` |
| Nós-alvo §4.4 | OK | `_TARGETS`: yaml `document`/`block_mapping_pair`; json `object`/`pair`/`array`; xml `element`; toml `table`/`pair` |
| XML `language_xml` (D-T11-012) | OK | `pkg.language_xml()`; runtime `Language` == `language_xml`, ≠ `language_dtd` |
| Eager registry inclui config | OK | `OfficialGrammarRegistry.__init__` resolve yaml/json/xml/toml |
| Alinhamento BDD TS-16..19 / UT-C20..C23 | OK | kinds estruturais (não root-only); XML ninhos `>= 2` ranges |
| Contrato T12/T13/T14 intacto | OK | `SemanticChunk` / `chunk_id` / erros tipados sem mudança de semântica |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |
| `SUGGESTION` | TS-18 resolve só `assertIsNotNone` — não compara `language_xml` ≠ `language_dtd` (já verificado em review runtime) | `test_treesitter_chunker.py` TS-18 | Opcional endurecer assert |
| `SUGGESTION` | Eager load de grammars (incl. config) — custo startup; sem medição | `grammar_registry.py` | Avaliar lazy só com baseline Blue |

### Checks

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q --cov=github_rag --cov-report=term-missing:skip-covered
# 594 passed, 1 skipped; Total coverage: 98.51%
# chunk modules ≥98% (node_selectors 98%; demais 100%)
```

### Decisão

`APPROVED_BY_ARCHITECT` — implementação config alinhada a design/interfaces/BDD v0.2.x (DEC-003/015). Prosseguir para etapa Blue.