# Reviews — T14-indexing-orchestrator

## Review — Design (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (gate Architect substitui HITL) |
| Resultado | `CHANGES_REQUIRED` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Escopo T14 (orquestrador só portas; fila+WorkerLimiter; REQ-020; ENG-011/012/013; BR-005) | Parcial | §1–§3, §3.6–§3.7, §12 — intenção alinhada; lacunas BLOCKING/MAJOR abaixo |
| Sem expansão indevida | OK | §14: UI/MCP/compose/cron fora |
| Compatível com portas T03–T13 na main | Falha | Zoekt set-replace (T10) e política Qdrant (T13) vs D-T14-006 / §3.1–§3.4 |
| Decisões claras e rastreáveis | Parcial | D-T14-001..010 ok; D-T14-006 contradiz ENG-012+T13 |
| Riscos/rollback | Parcial | §10; risco de wipe vetorial incremental não mitigado |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| `BLOCKING` | Pipeline chama `ExactCodeIndex.index` **por arquivo** (`FileToIndex` singular no loop), mas a porta T10 tem semântica de **substituição do conjunto tip**: cada `index` bem-sucedido faz paths não reenviados sumirem (I-T10-013 / D-T10-006 / ZOEKT-08). Indexar arquivo a arquivo apaga o restante do índice Zoekt. | `design.md` §3.1 L86–87; §3.4 L124; `src/github_rag/index/zoekt/port.py` L32–38; `spec/.../T10-zoekt-adapter/interfaces.md` I-T10-013 | Definir política Zoekt: **uma** chamada `index(repo, tip, files=conjunto_elegível_completo_no_tip)` por execução de repo (first-index e tip novo). RAG (TS→SLM→Qdrant) permanece só para add/mod (ENG-012). `record_file_stage(ZOEKT)` por path após o index do conjunto (ou ao incluir o path no conjunto). Proibir `index` com subconjunto parcial salvo restart/`delete_repository` + full rebuild. |
| `BLOCKING` | D-T14-006 manda `upsert` só dos arquivos da leva + `purge_other_commits` no sucesso. Em tip novo com reindex incremental, arquivos **não** alterados ficam só no `commit_sha` antigo; o purge remove esses pontos → perda de vetores de paths inalterados (quebra ENG-012 + busca semântica). | `design.md` §3.4 L129–132; D-T14-006 L296; `src/github_rag/index/vector/ports.py` L55–63 | Reescrever política vetorial coerente com T13, por exemplo: (A) tip novo / first-index / restart → `replace_repo_commit` com **todos** os elegíveis do tip; ou (B) incremental: `delete_paths` no scope do commit anterior para paths deleted+modified, `upsert` no tip só add/mod, e **não** chamar `purge_other_commits` nesse caminho (documentar invariante de search/tip); ou (C) outra política explícita testável. Incluir “substituir pontos daquele path” (task T14 ENG-012) via `delete_paths` no scope correto antes do upsert do path modificado. |
| `MAJOR` | Startup reconcile (ENG-011) só enfileira `not_indexed` \| `error`. Após kill/restart do container, repos em `queued` ou `indexing` no PostgreSQL ficam órfãos (fila in-memory some); `mark_queued` não aceita `indexing → queued` (máquina T03). | `design.md` §3.2 L105–106; `src/github_rag/catalog/transitions.py` L34–39, L150–159 | Em `StartupIndexReconcile`: tratar `queued` (re-enqueue idempotente) e `indexing` órfão (ex.: `mark_error` ou transição documentada → depois `mark_queued`), além de tip≠processado / `not_indexed` / `error`. Alinhar a “não está atualizado com tip=processado”. |
| `SUGGESTION` | `IndexingOrchestrator.reconcile_and_enqueue_stale` vs porta `StartupIndexReconcile` ambíguo (“ou delega”). | `design.md` §4.1 L195; §4.2 | Congelar: reconcile só em `StartupIndexReconcile.run`; orquestrador expõe `enqueue` + `run_until_idle` (+ `index_repository`); T15/T19 chamam a porta de reconcile, não um método duplicado. |
| `SUGGESTION` | Fluxo cita `enqueue_from_selection` sem contrato na Protocol. | `design.md` §3.1 L70; §4.1 L193–198 | Remover do fluxo ou adicionar método explícito na porta (thin wrapper de `enqueue`). |

### Achados sem bloqueio (escopo OK)

- Estados só REQ-020 / slugs T03: OK (§3.6).
- ENG-013 / imports só portas: OK (§3.7).
- BR-005 restart total + wipe Zoekt/Qdrant: intenção OK (§3.5); depende da correção Zoekt/Qdrant acima.
- Fora de escopo UI/MCP/T15/T19 wiring: OK (§14).
- Mapeamento metadata T12→T13: OK (§3.8 / D-T14-009).
- Rollback sem schema: OK (§10).

### Decisão

`CHANGES_REQUIRED` — design v0.1.0 **não** aprovado. Corrigir achados `BLOCKING` e `MAJOR` e resubmeter design (bump de versão) antes de BDD/interfaces.

---

## Review — Design (v0.1.1)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (gate Architect substitui HITL) |
| Resultado | `CHANGES_REQUIRED` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Escopo T14 | OK | §1–§3, §12, §14 |
| Sem expansão indevida | OK | §14 |
| Compatível T03–T13 (Zoekt set-replace; Qdrant incremental) | OK | §3.1 L91–108; §3.3; §3.4 D-T14-006; I-T10-013 |
| ENG-011 recover queued/indexing | Parcial | §3.2: `queued` re-enqueue OK; branch `indexing` não enfileira (ver MAJOR) |
| Decisões rastreáveis | OK | D-T14-003/006/011/012; §15 |
| Riscos/rollback | OK | §10 |

### Fechamento dos achados v0.1.0

| ID | Severidade | Status | Evidência do fechamento |
|---|---|---|---|
| B-01 | `BLOCKING` | Fechado | §3.1/§3.3/D-T14-006: uma `index(all_eligible)` + `record_file_stage(ZOEKT)` por path |
| B-02 | `BLOCKING` | Fechado | §3.4 opção B: `delete_paths(scope_old)` + `upsert(tip)`; sem `purge_other_commits`; replace no first/restart |
| M-01 | `MAJOR` | **Reaberto (residual)** | §3.2 recupera `indexing→error→queued`, mas com `senão se` o `enqueue` do branch `queued` **não** executa após o recover |
| S-01 | `SUGGESTION` | Fechado | D-T14-003; §4.1 sem `reconcile_and_enqueue_stale` |
| S-02 | `SUGGESTION` | Fechado | D-T14-012; só `enqueue(ids)` |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| `MAJOR` | Recover de `indexing` deixa o repo em `queued` no SoT sem `orchestrator.enqueue` — fila in-memory continua vazia para esse id; ENG-011/D-T14-011 incompletos. | `design.md` §3.2 L129–135 (`se indexing: … mark_queued` seguido de `senão se queued: enqueue`) | No branch `indexing`, após `mark_error` + `mark_queued`, chamar `orchestrator.enqueue([id])` (ou usar `se` independentes de forma que o estado pós-recover entre no caminho de enqueue). |

### Achados sem bloqueio

- Invariante search multi-commit no incremental (§3.4): aceitável e documentado; handoff implícito a T16.
- Skip BDD-004 após `mark_indexing` (§3.1): comentário cobre `mark_updated` se veio da fila.

### Decisão

`CHANGES_REQUIRED` — design v0.1.1 **não** aprovado. Fechar o MAJOR residual do enqueue pós-recover `indexing` (bump patch) e resubmeter.

---

## Review — Design (v0.1.2)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (gate Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Escopo T14 | OK | §1–§3, §12, §14 |
| Sem expansão indevida | OK | §14 |
| Compatível T03–T13 | OK | Zoekt set-replace §3.1/§3.3; Qdrant incremental §3.4; D-T14-006 |
| ENG-011 recover + enqueue | OK | §3.2 L130–137: indexing→error→queued→`enqueue`; queued/not_indexed/error enqueue |
| Decisões rastreáveis | OK | D-T14-001..012; §15 |
| Riscos/rollback | OK | §10 |

### Fechamento dos achados

| ID | Severidade | Status | Evidência |
|---|---|---|---|
| B-01 | `BLOCKING` | Fechado | §3.1/§3.3/D-T14-006 (desde 0.1.1) |
| B-02 | `BLOCKING` | Fechado | §3.4 (desde 0.1.1) |
| M-01 / M-01b | `MAJOR` | Fechado | §3.2 L130–133: `mark_queued` + `orchestrator.enqueue([id])` no ramo `indexing` |
| S-01 | `SUGGESTION` | Fechado | D-T14-003 (desde 0.1.1) |
| S-02 | `SUGGESTION` | Fechado | D-T14-012 (desde 0.1.1) |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.2. Prosseguir para BDD/interfaces (QA).

---

## Review — BDD (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (gate Architect substitui HITL) |
| Design base | `0.1.2` (`APPROVED_BY_ARCHITECT`) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| BDD-002 | OK | IO-01 (queued→indexing→up_to_date); IO-02 (pico ≤ `WorkerLimiter.capacity`) |
| BDD-004 | OK | IO-03 — tip==processado → portas não chamadas; permanece `up_to_date` |
| BDD-005 | OK | IO-04 — tip≠processado → processa tip; carimba `last_processed_commit` |
| BDD-007 / REQ-021–022 | OK | IO-05 progresso agregado; IO-06 stages `zoekt`/`tree_sitter`/`metadata_persisted` |
| BDD-008 / BR-005 | OK | IO-07 — `error` + msg/horário; `last_processed` não avança; retry = restart total |
| ENG-011 | OK | IO-08 stale enqueue; IO-09 recover `indexing`→error→queued→enqueue + `queued` re-enqueue |
| ENG-012 + Zoekt set-replace | OK | IO-10 arquivo inteiro; IO-11 uma `index(all_eligible)`; IO-12 `delete_paths` + sem `purge_other_commits` |
| ENG-013 | OK | IO-14 — AST sem SDKs no pacote `indexing` |
| REQ-020 | OK | IO-13 — enum fechado 5 slugs; sem extras |
| Alinhamento design v0.1.2 | OK | D-T14-006/011; §3.2/§3.3/§3.4/§3.5; sem expansão (fora: T15/T18/T19) |
| Sem expansão de escopo | OK | Escopo/exclusões L49–64 alinhados à task |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Achados sem bloqueio

| Severidade | Achado | Evidência | Nota |
|---|---|---|---|
| `SUGGESTION` | IO-07 usa “e/ou” no wipe Zoekt/vetorial no retry | `bdd.md` IO-07 | Design §3.5 exige wipe Zoekt **e** Qdrant no restart; asserts de unit/interfaces podem tornar ambos obrigatórios. Não bloqueia aceite BDD (restart total vs resume já está assertado). |

### Decisão

`APPROVED_BY_ARCHITECT` — BDD v0.1.0 aprovado. Prosseguir para interfaces (Architect/QA).
