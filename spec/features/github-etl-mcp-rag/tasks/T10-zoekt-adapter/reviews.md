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

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |
| `SUGGESTION` | Formato canônico de `repository` (full_name vs UUID catálogo) | `design.md` §17 | Fechar na etapa de interfaces com o identificador que T14 usar |
| `SUGGESTION` | Escape/quoting literal na query language Zoekt | `design.md` §5.4 | Detalhar na `interfaces.md` com exemplos de metacaracteres |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.1. Prosseguir para BDD/interfaces (QA) sem alteração de escopo de produto.
