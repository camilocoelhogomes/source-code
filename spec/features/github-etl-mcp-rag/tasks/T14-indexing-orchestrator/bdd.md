# BDD — T14-indexing-orchestrator

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T14-indexing-orchestrator` |
| Autor | Implementation Task Runner (QA step) |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão BDD | `0.1.0` |
| Design base | `0.1.2` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T14-indexing-orchestrator` |
| Rastreabilidade | REQ-005,012,016,018–022,024; BR-002–005; BDD-002,004,005,007,008; ENG-011,012,013; design D-T14-001..012 |

## Rastreabilidade

| Cenário | Aceite / requisito |
|---|---|
| IO-01 | BDD-002 — seleção → `queued` → `indexing` → `up_to_date` |
| IO-02 | BDD-002 — paralelismo ≤ `WorkerLimiter.capacity` (`INDEX_WORKERS`) |
| IO-03 | BDD-004 / BR-002–004 — tip == último processado → sem reprocessamento; permanece `up_to_date` |
| IO-04 | BDD-005 — tip ≠ processado → processa snapshot; carimba novo commit |
| IO-05 | BDD-007 / REQ-021 — progresso % / arquivos / etapa durante indexação |
| IO-06 | BDD-007 / REQ-022 — stages por arquivo: `zoekt`, `tree_sitter`, `metadata_persisted` |
| IO-07 | BDD-008 / BR-005 — falha parcial → `error` + mensagem/horário; retry reinicia repo inteiro |
| IO-08 | ENG-011 — startup reconcile enfileira `not_indexed` / tip≠processado / `error` |
| IO-09 | ENG-011 — recover `queued` e `indexing` órfãos no startup (enqueue) |
| IO-10 | ENG-012 — add/mod: `read_file` retorna arquivo **inteiro**; não hunk |
| IO-11 | ENG-012 / I-T10-013 — Zoekt: **uma** `index(all_eligible)` por execução |
| IO-12 | ENG-012 — deleted → `VectorStore.delete_paths`; incremental **sem** `purge_other_commits` |
| IO-13 | REQ-020 — estados usados ⊆ enum fechado (5 valores); sem extras |
| IO-14 | ENG-013 — pacote `github_rag.indexing` não importa SDKs de integração |

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Steps / asserts | `tests/bdd/test_indexing_orchestrator.py` |
| Fakes / harness | `tests/unit/indexing/helpers.py` (após interfaces) |

## Como executar

```bash
python -m pytest tests/bdd/test_indexing_orchestrator.py -q
```

## Escopo e exclusões

### Em escopo

- `IndexingOrchestrator` + fila + `WorkerLimiter`
- `StartupIndexReconcile`
- Pipeline via portas (Zoekt conjunto tip → TS → SLM → Qdrant)
- Estados REQ-020; skip; restart BR-005; ENG-011/012/013

### Fora de escopo

| Item | Dono |
|---|---|
| UI checkbox visual | T18 |
| APScheduler / cron | T15 |
| Compose boot wiring | T19 |
| Adaptadores SDK | T08–T13 |
| Sync de catálogo | T07 |

## Cenários

### IO-01 — Indexar selecionados (BDD-002)

**Dado** repositórios ativos em `not_indexed` com tip `main` conhecido  
**Quando** `enqueue(ids)` + `run_until_idle()`  
**Então** cada um transita `queued` → `indexing` → `up_to_date`  
**E** `last_processed_commit` igual ao tip.

### IO-02 — Workers respeitados (BDD-002)

**Dado** `WorkerLimiter` com `capacity == 1` e ≥2 repos enfileirados  
**Quando** `run_until_idle()`  
**Então** o pico de indexações simultâneas observadas é ≤ 1  
**E** ambos concluem `up_to_date`.

### IO-03 — Skip reprocessamento (BDD-004)

**Dado** repo `up_to_date` com `last_processed_commit == tip`  
**Quando** startup reconcile ou tentativa de indexação verificar o repo  
**Então** portas Zoekt/chunker/SLM/vector **não** são chamadas para processar conteúdo  
**E** estado permanece `up_to_date`.

### IO-04 — Novo snapshot (BDD-005)

**Dado** repo com `last_processed_commit == C1` e tip atual `C2`  
**Quando** indexação executar  
**Então** o snapshot `C2` é processado  
**E** ao sucesso `last_processed_commit == C2` e estado `up_to_date`.

### IO-05 — Progresso agregado (BDD-007 / REQ-021)

**Dado** repo em indexação com N arquivos na leva RAG  
**Quando** arquivos avançam no pipeline  
**Então** `CatalogEntry.progress` expõe `percent`, `files_processed`, `files_total`, `current_stage`  
**E** `percent ∈ [0, 100]`.

### IO-06 — Etapas por arquivo (BDD-007 / REQ-022)

**Dado** execução de indexação com ao menos um arquivo elegível  
**Quando** o pipeline concluir o arquivo  
**Então** `list_file_progress` registra timestamps para `zoekt`, `tree_sitter` e `metadata_persisted`.

### IO-07 — Falha parcial e restart (BDD-008 / BR-005)

**Dado** falha de uma porta (ex.: SLM) após parte dos arquivos  
**Quando** a execução terminar  
**Então** estado = `error` com mensagem e horário na execução `FAILED`  
**E** `last_processed_commit` **não** avança para o tip falho  
**Quando** nova tentativa (`enqueue` + run)  
**Então** ocorre restart total: `ExactCodeIndex.delete_repository` e/ou wipe vetorial + reprocessamento completo do tip  
**E** não retoma só do arquivo que falhou.

### IO-08 — Startup reconcile enfileira stale (ENG-011)

**Dado** catálogo ativo com: (a) `not_indexed`, (b) `up_to_date` tip≠processado → reconcile → `not_indexed`, (c) `error`, (d) `up_to_date` tip==processado  
**Quando** `StartupIndexReconcile.run()`  
**Então** (a)(b)(c) são enfileirados (`queued`)  
**E** (d) permanece `up_to_date` sem enqueue de processamento.

### IO-09 — Recover órfãos queued/indexing (ENG-011)

**Dado** repo em `indexing` (órfão pós-restart) e outro em `queued`  
**Quando** `StartupIndexReconcile.run()`  
**Então** o `indexing` vai a `error` depois `queued` e é enfileirado  
**E** o `queued` é re-enfileirado (idempotente).

### IO-10 — Arquivo modificado = conteúdo integral (ENG-012)

**Dado** tip novo com path `src/a.py` em `modified`  
**Quando** o pipeline processar o path  
**Então** `MainSnapshotProvider.read_file(tip, path)` é chamado  
**E** o conteúdo passado ao chunker/Zoekt é o retorno completo (bytes do arquivo), não um patch/hunk.

### IO-11 — Zoekt set-replace do conjunto tip (ENG-012 / I-T10-013)

**Dado** tip com múltiplos arquivos elegíveis (incl. inalterados)  
**Quando** a indexação do repo executar  
**Então** há exatamente **uma** chamada `ExactCodeIndex.index(repo, tip, files)`  
**E** `files` contém o conjunto elegível completo do tip (não subconjunto só add/mod).

### IO-12 — Deleted e política Qdrant incremental (ENG-012)

**Dado** tip novo com path removido e path modificado; há `last_processed_commit`  
**Quando** indexação incremental concluir com sucesso  
**Então** `VectorStore.delete_paths` é chamado para paths deleted (e modified antes do upsert)  
**E** `purge_other_commits` **não** é chamado  
**E** `upsert` ocorre no scope do tip para add/mod.

### IO-13 — Enum REQ-020 fechado

**Dado** qualquer transição durante enqueue/index/reconcile/erro  
**Quando** o estado do repo for lido  
**Então** `state` ∈ {`not_indexed`,`queued`,`indexing`,`up_to_date`,`error`}  
**E** nenhum outro slug é introduzido pelo orquestrador.

### IO-14 — Sem SDKs no pacote indexing (ENG-013)

**Dado** o pacote fonte `src/github_rag/indexing/`  
**Quando** imports forem inspecionados (AST)  
**Então** não há imports de `github`, `git`, `tree_sitter`, `openai`, `qdrant_client`, `pathspec`  
**E** dependências de integração passam só por portas já injetadas.

## Critérios de pronto BDD

- [ ] Todos os cenários IO-01..IO-14 nomeados e rastreáveis
- [ ] Suite executável em `tests/bdd/test_indexing_orchestrator.py`
- [ ] RED reproduzível antes da implementação (falha por ausência de API/comportamento)
- [ ] Gate Architect sem BLOCKING/MAJOR abertos
