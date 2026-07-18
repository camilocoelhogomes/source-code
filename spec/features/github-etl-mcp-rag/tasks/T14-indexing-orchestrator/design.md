# Design — T14-indexing-orchestrator

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T14-indexing-orchestrator` |
| Autor | Tech Lead Architect (candidato via Implementation Task Runner) |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.2` |
| Branch | `feature/github-etl-mcp-rag-T14-indexing-orchestrator` |
| Base | `main` |
| Rastreabilidade | REQ-005,012,016,018–022,024; BR-002–005,010,014,023; DEC-003,004,006; BDD-002,004,005,007,008; ENG-011, ENG-012, ENG-013 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | `0.1.0` | BLOCKING Zoekt set-replace + Qdrant purge; MAJOR recover queued/indexing |
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | `0.1.1` | B-01/B-02/S-01/S-02 OK; MAJOR residual: §3.2 branch `indexing` não chama `enqueue` após `mark_queued` |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.2` | M-01b fechado (§3.2 enqueue no ramo indexing); sem BLOCKING/MAJOR abertos |

## 1. Contexto

T01–T13 e T20 estão na `main`. As portas de domínio necessárias ao pipeline RAG e ao catálogo já existem:

| Porta / componente | Task | Papel para T14 |
|---|---|---|
| `WorkerLimiter` | T04 | Limita paralelismo de indexação (`INDEX_WORKERS`) |
| `CatalogRepository` | T03 | Estados REQ-020, execuções, progresso, etapas por arquivo, reconcile |
| `CatalogSync` / `run_catalog_sync` | T07 | Sync-only; boot chama sync **antes** do reconcile T14 |
| `MainSnapshotProvider` | T08 | Tip `main`, árvore, `read_file` completo, `diff_files` |
| `FileEligibilityFilter` | T09 | Filtra paths elegíveis |
| `ExactCodeIndex` | T10 | Indexação Zoekt por **conjunto tip** (set-replace) |
| `ContextualChunker` | T11 | Chunks Tree-sitter do arquivo completo |
| `MetadataGenerator` | T12 | Metadados SLM **por chunk** |
| `Embedder` + `VectorStore` | T13 | Embeddings + upsert / delete_paths / replace_repo_commit |

T14 materializa o pacote `github_rag.indexing`: orquestra fila + workers, startup reconcile (ENG-011), reindexação por arquivo inteiro modificado (ENG-012) e o pipeline Zoekt → Tree-sitter → SLM → Qdrant, **somente via portas** (ENG-013).

Consumidores: bootstrap/T19 (startup), T15 (cron), T18 (checkbox UI). Fora de escopo: UI visual, MCP, compose, APScheduler.

## 2. Problema

É preciso um orquestrador que:

1. Enfileire e indexe repos respeitando `WorkerLimiter` (BDD-002).
2. Use **apenas** os 5 estados REQ-020 (`not_indexed` \| `queued` \| `indexing` \| `up_to_date` \| `error`) — sem `desatualizado` nem extras.
3. No startup, reconcilie tip `main` × último processado e enfileire os não atualizados, **incluindo recover** de `queued`/`indexing` órfãos após restart (ENG-011).
4. Em commit novo: reindexe **arquivo inteiro** para add/mod elegíveis; remova paths deleted dos índices (ENG-012).
5. Skip quando tip = último processado (BDD-004 / BR-002–004).
6. Em falha parcial: estado `error` + nova tentativa reinicia o **repositório inteiro** (BR-005 / BDD-008).
7. Exponha progresso agregado e etapas por arquivo (BDD-007 / REQ-021–022).
8. **Não importe** SDKs de integração (ENG-013 / BR-023).
9. Respeite semântica T10 (Zoekt set-replace do conjunto tip) e T13 (sem purge que apague paths inalterados no caminho incremental).

## 3. Solução proposta

Pacote `github_rag.indexing`:

| Componente | Módulo | Papel |
|---|---|---|
| Tipos / erros | `types.py`, `errors.py` | DTOs; erros tipados |
| `IndexingOrchestrator` | `ports.py` + `orchestrator.py` | Porta + impl: `enqueue`, `run_until_idle`, `index_repository` |
| `StartupIndexReconcile` | `ports.py` + `startup_reconcile.py` | **Única** porta de reconcile de boot (ENG-011) |
| Pipeline RAG por arquivo | `pipeline.py` | TS → SLM → embed → Qdrant (só portas); Zoekt é etapa de conjunto |
| Progresso | `progress.py` | Helpers de percentual / stage text |
| Fila interna | `orchestrator.py` | Fila + slots via `WorkerLimiter` |

### 3.1 Fluxo feliz — enqueue + index

```text
enqueue(repository_ids):
  → para cada id com state ∈ {not_indexed, error} (ou queued idempotente):
       catalog.mark_queued(id)
       fila.append(id)   # dedupe se já na fila

run_until_idle / workers (≤ INDEX_WORKERS via WorkerLimiter.acquire):
  index_repository(id):
    catalog.mark_indexing(id)
    tip = provider.get_main_tip(source).commit_sha
    catalog.update_main_commit(id, tip)
    if is_up_to_date(last_processed, tip) and state allows skip:
         # BDD-004: sem reprocessamento; permanece/volta up_to_date
         return  (se já up_to_date) / mark_updated se veio de fila indevida
    execution = catalog.start_execution(id, tip)
    tree = provider.list_tree(tip)
    all_eligible = eligibility.filter(tree, gitignores)
    diff = provider.diff_files(from=last_processed, to=tip)
      → FirstIndexSignal | FileDiffSet

    # --- Zoekt: UMA chamada com conjunto tip completo (I-T10-013) ---
    zoekt_files = [FileToIndex(..., path, content=read_file(tip,path)) for path in all_eligible]
    exact_index.index(repo_key, tip, zoekt_files)
    para cada path in all_eligible: record_file_stage(ZOEKT)

    # --- Vetorial + RAG: ver §3.4 (política A/B) ---
    se first-index OU restart_full:
         processar RAG para TODOS all_eligible
         vector.replace_repo_commit(scope(tip), all_records)
    senão (incremental tip novo):
         deleted_eligible / deleted paths → vector.delete_paths(scope_old, deleted)
         para cada path in (added ∪ modified) ∩ elegíveis:
              content = read_file(tip, path)  # arquivo INTEIRO
              records = rag_pipeline(content)  # TS→SLM→embed
              vector.delete_paths(scope_old, [path])  # substitui pontos do path
              vector.upsert(scope(tip), records)
              record_file_stage(TREE_SITTER, METADATA_PERSISTED)
         # NÃO chama purge_other_commits (paths inalterados ficam no commit anterior)
    catalog.mark_updated(id, tip)
```

`enqueue` é o único método de enfileiramento (checkbox UI/T18 e cron/T15 passam ids). Sem `enqueue_from_selection` separado.

### 3.2 Startup reconcile (ENG-011) — única porta

**Congelado:** reconcile de boot vive **somente** em `StartupIndexReconcile.run()`.  
`IndexingOrchestrator` **não** expõe `reconcile_and_enqueue_stale`. T15/T19 injetam e chamam `StartupIndexReconcile`.

```text
StartupIndexReconcile.run():
  entries = catalog.list_active_catalog()
  para cada entry:
    tip = provider.get_main_tip(source_for(entry)).commit_sha
    catalog.update_main_commit(entry.id, tip)
    entry = catalog.reconcile_repository(entry.id)
      # up_to_date + tip≠processado → not_indexed (preserva last_processed)

    # Recover pós-restart (fila in-memory some):
    se entry.state == indexing:
         catalog.mark_error(id, "orphaned indexing after restart", now)
         catalog.mark_queued(id)           # error → queued
         orchestrator.enqueue([id])        # obrigatório: senão if não reentra em queued
    senão se entry.state == queued:
         orchestrator.enqueue([id])        # re-enqueue idempotente
    senão se entry.state ∈ {not_indexed, error}:
         orchestrator.enqueue([id])
    senão se entry.state == up_to_date e tip == last_processed:
         skip  # BDD-004
```

Critério ENG-011: enfileirar quem **não** está `up_to_date` com tip = último processado (inclui órfãos `queued`/`indexing`).

### 3.3 Reindex por arquivo (ENG-012)

| Situação | Zoekt | RAG / Qdrant |
|---|---|---|
| First-index | `index(repo, tip, all_eligible)` | `replace_repo_commit` com records de todos elegíveis |
| Tip novo (incremental) | `index(repo, tip, all_eligible)` — set-replace remove paths ausentes | RAG **só** add/mod elegíveis (arquivo inteiro); `delete_paths` deleted (+ modified antes do upsert); **sem** `purge_other_commits` |
| Restart BR-005 | `delete_repository` + `index(..., all_eligible)` | `delete_repo` ou `replace_repo_commit` com rebuild completo |
| Proibido | `index` com subconjunto parcial (apaga o resto do shard) | Indexar só hunk/delta; `purge_other_commits` no caminho incremental |

### 3.4 Pipeline RAG por arquivo (quando o arquivo entra na leva)

Ordem fixa para cada path da leva RAG (DEC-003; REQ-022):

1. **Tree-sitter** — `ContextualChunker.chunk(ChunkSourceFile` com bytes **completos**); `record_file_stage(TREE_SITTER)`.
2. **SLM por chunk** — `MetadataGenerator.generate(chunk)` para cada chunk.
3. **Qdrant** — mapear T12→T13 metadata; `Embedder.embed`; `upsert` / parte de `replace_repo_commit`; `record_file_stage(METADATA_PERSISTED)`.

Etapa Zoekt é **por execução/conjunto** (§3.3), não por arquivo isolado na porta; `record_file_stage(ZOEKT)` marca cada path elegível do tip após o `index` do conjunto.

#### Política vetorial (D-T14-006 v0.1.1) — opção B + A no restart

| Caminho | Operações VectorStore |
|---|---|
| **First-index** | Processar RAG todos elegíveis → `replace_repo_commit(scope_tip, all_records)` |
| **Incremental (tip novo)** | `delete_paths(scope_old, deleted∪modified)`; `upsert(scope_tip, records_add_mod)`; **não** `purge_other_commits` |
| **Restart total (BR-005)** | `delete_repo(repo_id)` (ou `replace_repo_commit` vazio + rebuild) + full first-index semantics |

Invariante search: paths inalterados permanecem com `commit_sha` anterior; conteúdo é idêntico ao tip (diff não os listou). Search por `repo_id` continua a encontrá-los. Tip “oficial” do catálogo = `last_processed_commit` só após sucesso.

### 3.5 Falha parcial (BR-005 / BDD-008)

Qualquer falha durante o processamento de um repo:

1. Interrompe a leva restante.
2. `catalog.mark_error(id, message, error_at)`.
3. **Não** carimba `last_processed_commit`.
4. Nova tentativa (`error → queued → indexing`): flag `restart_full=True` → wipe Zoekt (`delete_repository`) + wipe Qdrant (`delete_repo`) + rebuild completo do tip (first-index semantics). **Não** retoma do arquivo que falhou.

### 3.6 Estados (REQ-020) — exclusivo

Somente `RepoState` de T03. Transições via atalhos da porta:

| Origem | Destino | Quando |
|---|---|---|
| `not_indexed` / `error` | `queued` | enqueue |
| `queued` | `queued` | enqueue idempotente / recover startup |
| `queued` | `indexing` | worker adquire slot |
| `indexing` | `up_to_date` | sucesso + tip carimbado |
| `indexing` | `error` | falha **ou** orphan recover no startup |
| `error` | `queued` | nova tentativa / recover |
| `up_to_date` | `not_indexed` | `reconcile_repository` (tip ≠ processado) |

Proibido: inventar estados; pular `queued`; marcar `up_to_date` sem igualdade tip/processado.

### 3.7 ENG-013 — sem SDKs no orquestrador

`github_rag.indexing.*` **pode** importar apenas portas/DTOs de:

- `github_rag.catalog`, `concurrency`, `snapshot`, `eligibility`
- `github_rag.index.zoekt`, `.chunk`, `.metadata`, `.vector`

**Proibido:** `github`, `git`, `tree_sitter*`, `openai`, `qdrant_client`, clientes Zoekt, `pathspec` direto, etc. Teste AST valida a fronteira.

### 3.8 Mapeamento metadata T12 → T13

```python
def to_vector_metadata(meta: metadata.ChunkMetadata) -> vector.ChunkMetadata:
    return vector.ChunkMetadata(
        summary=meta.summary,
        keywords=meta.keywords,
        symbols=meta.symbols,
    )
```

## 4. Componentes detalhados

### 4.1 `IndexingOrchestrator` (Protocol)

```python
class IndexingOrchestrator(Protocol):
    def enqueue(self, repository_ids: Sequence[int]) -> None: ...
    def run_until_idle(self) -> None: ...
    def index_repository(self, repository_id: int) -> None: ...
```

- **Responsabilidade:** fila, estados REQ-020, skip de commit, pipeline e política BR-005.
- **Motivo da separação:** único dono da sequência de indexação; T15/T18 disparam enqueue/run; **não** faz reconcile de boot.

### 4.2 `StartupIndexReconcile` (Protocol)

```python
class StartupIndexReconcile(Protocol):
    def run(self) -> None: ...
```

- **Responsabilidade:** tip × processado, recover `queued`/`indexing`, enqueue via orquestrador (ENG-011).
- **Motivo da separação:** T07 sync-only; T19 chama reconcile após sync; evita duplicar método no orquestrador.

### 4.3 Resolução de origem snapshot

Helper interno: `CatalogEntry` → `SnapshotSource` (GitHub com token injetado / Local). Token nunca em logs.

### 4.4 Gitignore MVP (D-T14-008)

Root `.gitignore` via `read_file` se existir; senão `gitignore_sources=[]`.

### 4.5 Identificadores

| Conceito | Valor |
|---|---|
| `repo_id` Qdrant / Zoekt `repository` | `str(catalog_entry.id)` |
| `commit_sha` | tip `main` da execução |
| `scope_old` | `RepoCommitScope(repo_id, last_processed_commit)` quando existe |

## 5. Dados e persistência

Sem schema novo. Usa `CatalogRepository` (mark_*, update_main_commit, reconcile_repository, start_execution, update_progress, record_file_stage, list_active_catalog, get_repository).

Progresso: `percent = floor(100 * files_processed / max(files_total, 1))` com total = tamanho da leva RAG (ou all_eligible no first-index); stages texto livre.

## 6. Erros

```python
class IndexingOrchestratorError(Exception): ...
class RepositorySourceError(IndexingOrchestratorError): ...
class IndexingPipelineError(IndexingOrchestratorError): ...
```

Falhas de portas → boundary do repo → `mark_error` sem secrets.

## 7. Segurança

Token só em memória; mensagens sanitizadas; ENG-013 confina SDKs aos adaptadores.

## 8. Compatibilidade

- Não altera contratos T03–T13.
- T15/T18: `enqueue` + `run_until_idle`.
- T19: sync → `StartupIndexReconcile.run()` → workers.

## 9. Observabilidade

Progresso no catálogo (REQ-021/022). Logging opcional sem secrets.

## 10. Riscos e rollback

| Risco | Mitigação |
|---|---|
| Zoekt set-replace parcial | Sempre `index` com `all_eligible` do tip |
| Purge apaga inalterados | Incremental sem `purge_other_commits` |
| Índice parcial pós-falha | Não carimba commit; restart wipe+full |
| Órfãos queued/indexing | Recover no startup |
| Import SDK | Teste AST |

Rollback: reverter PR; sem schema.

## 11. Decisões

| ID | Decisão | Motivo |
|---|---|---|
| D-T14-001 | Orquestrador só portas (ENG-013) | Plano §5.3; BR-023 |
| D-T14-002 | Estados só REQ-020 via T03 | BDD-002 |
| D-T14-003 | Reconcile **só** em `StartupIndexReconcile` | ENG-011; T07 sync-only; S-01 |
| D-T14-004 | Reindex arquivo inteiro; nunca hunk | ENG-012 |
| D-T14-005 | Falha → `error` + restart total | BR-005 / BDD-008 |
| D-T14-006 | Zoekt: 1× `index(all_eligible)`/execução; Qdrant: replace no first/restart; incremental = delete_paths+upsert **sem** purge_other_commits | I-T10-013; ENG-012; review B-01/B-02 |
| D-T14-007 | `repo_id` = `str(catalog id)` | Estável/opaco |
| D-T14-008 | Gitignore MVP = root via snapshot | Sem I/O direto |
| D-T14-009 | Mapear T12→T13 no orquestrador | Dois tipos na main |
| D-T14-010 | `index_repository` síncrono + `run_until_idle` com slots | Testabilidade + BDD-002 |
| D-T14-011 | Startup recover: `indexing`→`error`→`queued`→`enqueue`; `queued` re-enqueue | MAJOR M-01 / M-01b |
| D-T14-012 | Único enqueue = `enqueue(ids)` | S-02 |

## 12. Escopo BDD nesta task

| Cenário produto | Cobertura T14 |
|---|---|
| BDD-002 | Enqueue → queued→indexing→up_to_date; workers ≤ capacity |
| BDD-004 | tip == processado → sem reprocessamento |
| BDD-005 | tip ≠ processado → processa; carimba commit |
| BDD-007 | Progresso + stages por arquivo |
| BDD-008 | Falha → error; retry = restart total |
| ENG-011 | Startup reconcile + recover órfãos |
| ENG-012 | Add/mod arquivo inteiro; deleted limpa; Zoekt conjunto tip |
| ENG-013 | Sem imports de SDKs |

## 13. Arquivos previstos

```
src/github_rag/indexing/
  __init__.py
  types.py
  errors.py
  ports.py
  progress.py
  pipeline.py
  orchestrator.py
  startup_reconcile.py
tests/bdd/test_indexing_orchestrator.py
tests/unit/indexing/...
spec/.../T14-indexing-orchestrator/{design,bdd,interfaces,unit-test-plan,reviews,refactoring,approvals}.md
```

## 14. Fora de escopo

- UI (T18), cron APScheduler (T15), compose/boot wiring (T19)
- Alterar adaptadores T08–T13
- Descoberta/sync (T05–T07)
- Chunking genérico (DEC-003)

## 15. Resolução dos achados

| Achado | Versão | Resolução |
|---|---|---|
| B-01 Zoekt por arquivo | 0.1.1 | §3.1/§3.3/D-T14-006: uma `index(all_eligible)` |
| B-02 purge incremental | 0.1.1 | §3.4 opção B: delete_paths+upsert; sem purge; replace no first/restart |
| M-01 órfãos queued/indexing | 0.1.1 | §3.2/D-T14-011 |
| M-01b enqueue após recover indexing | 0.1.2 | §3.2: `mark_queued` + `orchestrator.enqueue([id])` no ramo indexing |
| S-01 reconcile duplicado | 0.1.1 | D-T14-003: só `StartupIndexReconcile` |
| S-02 enqueue_from_selection | 0.1.1 | Removido; só `enqueue` (D-T14-012) |
