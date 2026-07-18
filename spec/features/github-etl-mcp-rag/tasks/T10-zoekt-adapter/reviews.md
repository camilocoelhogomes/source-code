# Reviews — T10-zoekt-adapter

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
| Escopo estrito (sem Tree-sitter/Qdrant/MCP/UI) | OK | `design.md` §1, §16; task T10 |
| DEC-016 / BDD-024 — adaptador fino HTTP/CLI oficial | OK | D-T10-001; proibição de formato/protocolo caseiro |
| Porta `ExactCodeIndex` vs transporte | OK | D-T10-002; §5.1–5.4 |
| Modelos com repo/path/commit/snippet | OK | D-T10-003; `ExactMatch` |
| Erro tipado para T14 restart | OK | D-T10-004; §8 |
| Fake/double injetável | OK | D-T10-005; `FakeExactCodeIndex` |
| ENG-012 remoção de paths / handoff | OK | D-T10-006; reindex do conjunto + `delete_repository` obrigatório |
| Envs sem inventar em `AppSettings` T01 | OK | D-T10-007; §5.5 |
| Aceite BDD-009 mapeado | OK | §3.1, §14 |

### Achados na revisão de v0.1.0 (corrigidos em v0.1.1)

| Severidade | Achado | Evidência | Correção aplicada |
|---|---|---|---|
| `MAJOR` | `delete_repository` marcado como opcional no Protocol — ambíguo para T14/Fake/interfaces | v0.1.0 §5.1, D-T10-006 | Tornado **obrigatório** no Protocol; Fake e restart §6.3 alinhados |
| `MAJOR` | Caminho CLI `zoekt-git-index` vs `zoekt-index` + `workdir` sem superfície no Protocol | v0.1.0 D-T10-001 | MVP fixo: materializar `content` + `zoekt-index`; git-index só otimização de construtor |
| `MAJOR` | Inconsistência `search_raw` vs `post_search` | v0.1.0 D-T10-002 vs §5.2 | Nome único `post_search` |
| `MAJOR` | Sem invariante `index(repository, commit, files)` vs campos em `FileToIndex` | v0.1.0 D-T10-003 | Invariante: args canônicos; divergência → `ExactCodeIndexError` |
| `SUGGESTION` | `ExactMatch.commit` podia ser `""` | v0.1.0 D-T10-003 | Mapa mínimo `repository → commit` na porta; proibido vazio em índice populado |

### Achados abertos (design)

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |
| `SUGGESTION` | Formato canônico de `repository` (full_name vs UUID catálogo) | `design.md` §17 | Fechar na etapa de interfaces com o identificador que T14 usar |
| `SUGGESTION` | Escape/quoting literal na query language Zoekt | `design.md` §5.4 | Detalhar na `interfaces.md` com exemplos de metacaracteres |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.1. Prosseguir para BDD/interfaces (QA) sem alteração de escopo de produto.

---

## Review — BDD (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `tests/bdd/test_zoekt_adapter.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| BDD-009 — index torna conteúdo buscável | OK | ZOEKT-01; `test_exact_match_after_index` |
| Metadados repo/path/commit/snippet | OK | ZOEKT-02; asserts em `hit.commit` / `snippet` |
| Falha tipada `ExactCodeIndexError` | OK | ZOEKT-03; fail em `index` e `search` |
| BDD-024 / DEC-016 — fake sem Zoekt real | OK | ZOEKT-04; `isinstance(fake, ExactCodeIndex)` |
| `delete_repository` + no-op | OK | ZOEKT-05 |
| Corner `files` vazio = no-op | OK | ZOEKT-06; design §8 |
| Corner `pattern` vazio = lista vazia | OK | ZOEKT-07; design §8 |
| Corner reindex remove path ausente | OK | ZOEKT-08; ENG-012 / D-T10-006 |
| Escopo T10 (sem UI/compose/T14) | OK | só porta + `FakeExactCodeIndex` |
| RED pré-implementação | OK | `ModuleNotFoundError: github_rag.index.zoekt.errors` |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |
| `SUGGESTION` | ZOEKT-03 não injeta `SECRET_TOKEN` no caminho de falha; só asserta ausência | `test_zoekt_adapter.py` L25, L101–102 | Cobrir redaction em unit tests da implementação real |
| `SUGGESTION` | Invariante `FileToIndex.repository/commit` ≠ args de `index` não está no BDD | design D-T10-003 | Cobrir em unit tests |
| `SUGGESTION` | Escape/metacaracteres na query Zoekt fora do BDD (correto: fake substring) | design §5.4 | Unit tests de `ZoektExactCodeIndex` |

### Decisão

`APPROVED_BY_ARCHITECT` — BDD v0.1.0. Prosseguir para interfaces.

---

## Review — Interfaces (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (auto-review; sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Modelos `FileToIndex` / `ExactMatch` / `ExactSearchQuery` | OK | §3.1–3.3; frozen; campos D-T10-003 |
| `ExactCodeIndexError` tipado | OK | §3.4; `operation` + sem segredos |
| Protocol `ExactCodeIndex` completo | OK | §3.5; `index`/`search`/`delete_repository` |
| `ZoektSearchTransport` + HTTP stdlib | OK | §3.6; `post_search`; DEC-016 |
| `ZoektIndexRunner` + subprocess | OK | §3.7; `ZoektIndexRunResult` |
| `ZoektExactCodeIndex` + `from_environ` | OK | §3.8; MVP `zoekt-index`; I-T10-009/014 |
| Escape literal documentado | OK | I-T10-010; fecha SUGGESTION design |
| `repository` canônico | OK | I-T10-003; fecha SUGGESTION design §17 |
| `FakeExactCodeIndex` + `fail_operations` | OK | §3.9; D-T10-005; ZOEKT-03/04 |
| Comentários responsabilidade / motivo | OK | cada contrato §3 |
| Alinhamento BDD ZOEKT-01..08 | OK | I-T10-005/006/012/013/015 |
| Sem implementação de produção nesta etapa | OK | contratos/stubs apenas |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |
| `SUGGESTION` | Flags exatas de nome de repo na CLI dependem do help do binário pinado em T19 | §3.8 passo 1 | Confirmar argv na implementação contra binário oficial |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces v0.1.0. Prosseguir para unit tests (QA).

---

## Review — Unit tests (v0.1.0 → v0.1.1)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` + `tests/unit/index/zoekt/*` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Modelos frozen + defaults | OK | M-01..06; `test_models.py` |
| `ExactCodeIndexError` tipado / `__cause__` | OK | E-01..05; `test_errors.py` |
| `FakeExactCodeIndex` porta + fail_operations | OK | F-01..14 + F-12b; alinhado ZOEKT-01..08 / I-T10-004..016 |
| HTTP transport oficial `POST /api/search` | OK | C-01..07; mock urllib; DEC-016 |
| CLI runner `subprocess` sem shell | OK | R-01..05; `shell=False` |
| Adaptador index/search/delete/`from_environ` | OK | I-01..16b; transports fake |
| Extremos (vazio, mismatch, escape, ordenação) | OK | F-07..12b; I-04..08; I-11 |
| Sem implementação de produção | OK | só placeholder `index/zoekt/__init__.py` |
| RED pré-implementação | OK | `ModuleNotFoundError: github_rag.index.zoekt.{models,errors,fake,client,runner}` |

### Achados na revisão de v0.1.0 (corrigidos em v0.1.1)

| Severidade | Achado | Evidência | Correção aplicada |
|---|---|---|---|
| `MAJOR` | I-13b vácuo: com `RecordingIndexRunner` não há shard em `index_dir`; assert de leftovers vazios passava sem exercitar limpeza | `test_index.py` `test_delete_repository_after_index_clears_repo_association` | Planta sentinel `{repo_slug}_v16.00000.zoekt` pós-index; asserta remoção + 2ª delete no-op |
| `MAJOR` | I-16 só assertava `ZOEKT_INDEX_BIN`; plan pedia defaults + overrides `ZOEKT_*` | `test_from_environ_reads_zoekt_envs` | Assert `-index` = `ZOEKT_INDEX_DIR`; novo I-16b defaults `zoekt-index` + URL `127.0.0.1:6070` |
| `MAJOR` | Fake cobria mismatch só de `repository`, não de `commit` (I-T10-004 incompleto na porta fake) | `test_fake.py` F-12 | Novo F-12b `test_file_to_index_commit_mismatch_raises` |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |
| `SUGGESTION` | E-03 não embute `SECRET_TOKEN` na message para forçar redaction automática | `test_errors.py` L30–43; plan E-03 “token fixture ausente” | Se implementação fizer redaction, cobrir na suite pós-implementação |
| `SUGGESTION` | `max_matches` → `Opts` oficiais não exercitado | D-T10-003; sem caso no plan | Opcional na implementação se mapeamento for trivial |

### Decisão

`APPROVED_BY_ARCHITECT` — unit-test-plan v0.1.1 + suíte executável. RED confirmado (`ModuleNotFoundError` / `ImportError` na coleta). Prosseguir para implementação (Developer).
