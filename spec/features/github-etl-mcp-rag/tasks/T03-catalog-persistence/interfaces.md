# Interfaces — T03-catalog-persistence

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T03-catalog-persistence` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` (review independente — modo autônomo; ver `reviews.md`) |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Rastreabilidade | BR-001/002/004/005; REQ-020/021/022/023; DEC-005; ENG-011; BDD-004/005/007/008; design §4/§5/§6/§7; reviews S-1/S-2/S-3, B-2/B-3 |

## 0. Escopo desta etapa

Definir e **congelar** os contratos tipados do catálogo: enums, modelos de
leitura, erros, a porta `CatalogRepository` e a máquina de estados. Apenas
**stubs de Protocol/contratos** no código (`...`), **sem implementação**. O fake
`InMemoryCatalogRepository` e o adaptador `PostgresCatalogRepository` são
implementação (gate unit/impl) e **não** entram aqui — logo o BDD segue RED.

Arquivos de contrato entregues:

| Módulo | Papel |
|---|---|
| `src/github_rag/catalog/models.py` | Enums fechados + dataclasses imutáveis de leitura |
| `src/github_rag/catalog/errors.py` | Hierarquia de erros de domínio/infra |
| `src/github_rag/catalog/transitions.py` | Máquina de estados (contrato declarativo) + helper puro de commit |
| `src/github_rag/catalog/repository.py` | Porta `CatalogRepository` (Protocol) |
| `src/github_rag/catalog/__init__.py` | Reexports da superfície pública |

## 1. Resolução de ambiguidades do BDD (B-2 / B-3)

O BDD usa `_invoke(obj, candidates, ...)` com listas de verbos equivalentes.
Este gate **congela um nome canônico por operação** (primeiro candidato de cada
lista, salvo justificativa). Todos os nomes canônicos pertencem às listas de
candidatos do BDD, portanto **nenhum cenário quebra**.

| Operação (candidatos do BDD) | **Nome canônico** | Justificativa |
|---|---|---|
| `upsert_repository` | `upsert_repository` | único candidato |
| `get_repository` / `get` / `find` | `get_repository` | mais explícito |
| `list_active_catalog` / `list_active` | `list_active_catalog` | leitura central ENG-011 |
| `mark_queued` | `mark_queued` | único candidato |
| `mark_indexing` | `mark_indexing` | único candidato |
| `mark_updated` / `mark_up_to_date` | `mark_updated` | alinhado a design §6 |
| `mark_error` | `mark_error` | único candidato |
| `update_main_commit` / `record_main_commit` / `set_current_main_commit` | `update_main_commit` | verbo do design §6 |
| `reconcile` / `reconcile_repository` | `reconcile_repository` | escopo explícito (repo) |
| `start_execution` / `open_execution` | `start_execution` | verbo do design §6 |
| `update_progress` | `update_progress` | único candidato |
| `record_file_stage` | `record_file_stage` | único candidato |
| `list_file_progress` / `list_file_stages` | `list_file_progress` | retorna `FileProgress` |
| `list_execution_history` / `list_executions` | `list_executions` | conciso; retorna execuções |
| `deactivate_repository` / `deactivate` | `deactivate_repository` | mais explícito |
| `transition_state` / `transition` | `transition_state` | verbo do design §6 |

**Forma do progresso (resolve B-3):** o progresso é exposto como objeto agregado
em `CatalogEntry.progress: Progress | None`. O BDD (`_read_progress`) lê
`entry.progress.percent/...` primeiro — este é o contrato oficial; os campos
planos no `CatalogEntry` **não** existem.

**Nota sobre `complete_execution_success` / `fail_execution`:** os nomes sugeridos
na task são cumpridos pelos verbos canônicos do BDD `mark_updated` (sucesso:
carimba commits, fecha execução `SUCCEEDED`, vai a `up_to_date`) e `mark_error`
(falha: registra mensagem/horário, fecha execução `FAILED`, vai a `error`). Optou-se
pelos nomes do BDD aprovado para não quebrar cenários congelados.

## 2. Enums (`models.py`)

Todos herdam de `str` para suportar `RepoState("not_indexed")` e `member.value`
(contrato exercido pelo BDD CP-09).

### 2.1 `RepoOrigin`
| Membro | Valor | Significado |
|---|---|---|
| `GITHUB` | `github` | repositório GitHub (exige `github_org`) |
| `LOCAL` | `local` | repositório local (exige `local_path`) |

### 2.2 `RepoState` (REQ-020 — exatamente 5, fechado)
| Membro | Valor | Rótulo REQ-020 |
|---|---|---|
| `NOT_INDEXED` | `not_indexed` | não indexado |
| `QUEUED` | `queued` | na fila |
| `INDEXING` | `indexing` | indexando |
| `UP_TO_DATE` | `up_to_date` | atualizado |
| `ERROR` | `error` | erro |

**Proibido** `desatualizado`/`indisponível` (D-T03-004). "Desatualizado" é
derivado (comparação de commit + reconcile); "ausente da config" é soft-delete.

### 2.3 `FileStage` (REQ-022)
`ZOEKT=zoekt`, `TREE_SITTER=tree_sitter`, `METADATA_PERSISTED=metadata_persisted`.

### 2.4 `ExecutionStatus` (resolve SUGGESTION S-2)
`RUNNING=running`, `SUCCEEDED=succeeded`, `FAILED=failed`.

Status de **execução** — **distinto** de `RepoState`. Decisão S-2: enum próprio no
domínio; no schema PG, mapeia para enum nativo `execution_status` (CHECK/enum) —
detalhado no gate de migrations.

## 3. Modelos de leitura imutáveis (`models.py`, `@dataclass(frozen=True)`)

### 3.1 `Progress` (REQ-021)
| Campo | Tipo | Nota |
|---|---|---|
| `percent` | `int \| None` | 0–100 quando presente |
| `files_processed` | `int \| None` | REQ-021 |
| `files_total` | `int \| None` | REQ-021 |
| `current_stage` | `str \| None` | texto livre exibível (não é `FileStage`) |

### 3.2 `CatalogEntry` (SoT; design §4.3)
| Campo | Tipo | Nota |
|---|---|---|
| `id` | `int` | PK |
| `connection_name` | `str` | conexão de origem |
| `origin` | `RepoOrigin` | github/local |
| `repo_identifier` | `str` | `org/repo` ou id do path |
| `state` | `RepoState` | REQ-020 |
| `active` | `bool` | soft-delete |
| `row_version` | `int` | lock otimista (`expected_version`) |
| `github_org` | `str \| None` | obrigatório se `origin=GITHUB` |
| `local_path` | `str \| None` | obrigatório se `origin=LOCAL` |
| `last_processed_commit` | `str \| None` | `None` = nunca processado (BR-004) |
| `current_main_commit` | `str \| None` | tip conhecido da main |
| `progress` | `Progress \| None` | forma congelada do progresso (B-3) |
| `current_execution_id` | `int \| None` | execução corrente |
| `deactivated_at` | `datetime \| None` | quando saiu do catálogo ativo |
| `created_at` / `updated_at` | `datetime \| None` | auditoria |

### 3.3 `IndexingExecution` (REQ-023; BDD-008)
| Campo | Tipo | Nota |
|---|---|---|
| `id` | `int` | PK |
| `repository_id` | `int` | FK; retido após soft-delete |
| `status` | `ExecutionStatus` | running/succeeded/failed |
| `started_at` | `datetime` | |
| `finished_at` | `datetime \| None` | |
| `commit_target` | `str \| None` | commit alvo/processado |
| `error_message` | `str \| None` | REQ-023 (BDD CP-06) |
| `error_at` | `datetime \| None` | REQ-023 (BDD CP-06) |

### 3.4 `FileProgress` (REQ-022; BDD CP-05)
| Campo | Tipo | Nota |
|---|---|---|
| `id` | `int` | PK |
| `execution_id` | `int` | FK |
| `file_path` | `str` | único por `(execution_id, file_path)` |
| `zoekt_at` | `datetime \| None` | marca etapa `zoekt` |
| `tree_sitter_at` | `datetime \| None` | marca etapa `tree_sitter` |
| `metadata_persisted_at` | `datetime \| None` | marca etapa `metadata_persisted` |

## 4. Erros (`errors.py`)

Hierarquia (raiz `CatalogError(Exception)`):

| Tipo | Base | Condição |
|---|---|---|
| `CatalogError` | `Exception` | raiz para captura ampla |
| `RepositoryNotFoundError` | `CatalogError` | repo/execução inexistente (CP-11) |
| `InvalidStateTransitionError` | `CatalogError` | transição fora da máquina (CP-10) |
| `ConcurrencyConflictError` | `CatalogError` | `expected_version` ≠ `row_version` (CP-12) |
| `CatalogPersistenceError` | `CatalogError` | falha de infra do adaptador PG (§8: sem credenciais) |

Erros de domínio (not found, transição, concorrência) são independentes de PG —
testáveis com o fake. `CatalogPersistenceError` é exclusivo do adaptador.

## 5. Máquina de estados (contrato declarativo — `transitions.py`; resolve S-1)

### 5.1 Conjunto FECHADO de transições (`ALLOWED_TRANSITIONS`)
```text
not_indexed  → queued
queued       → indexing
indexing     → up_to_date        (sucesso; grava last_processed_commit)
indexing     → error             (falha; grava mensagem + horário — REQ-023)
error        → queued            (nova tentativa reinicia o repo — BR-005)
error        → not_indexed       (reconcile/limpeza)
up_to_date   → not_indexed       (novo commit em main ≠ processado — ENG-011)
```
Qualquer par ausente ⇒ `InvalidStateTransitionError` (estado preservado).

### 5.2 Política de reentrância idempotente (`IDEMPOTENT_SELF_STATES`)
Auto-transição (`target == current`):

| Estado atual | `target == current` |
|---|---|
| `not_indexed` | **no-op idempotente** (reconcile seguro) |
| `queued` | **no-op idempotente** (enfileiramento seguro) |
| `indexing` | ilegal ⇒ `InvalidStateTransitionError` |
| `up_to_date` | ilegal ⇒ `InvalidStateTransitionError` |
| `error` | ilegal ⇒ `InvalidStateTransitionError` |

Motivo: `not_indexed`/`queued` são pontos de reconcile/startup onde repetição é
esperada (ENG-011); reprocessar `indexing`/`up_to_date`/`error` para si mesmo
indica erro de fluxo.

### 5.3 Helper puro de comparação (`is_up_to_date`)
`is_up_to_date(last_processed_commit, current_main_commit) -> bool`:
`True` sse ambos não-nulos e iguais (BR-002/004). Não decide transição; o
rebaixamento é aplicado por `reconcile_repository`.

### 5.4 Semântica de `reconcile_repository` (BDD CP-01/CP-02)
- `state == up_to_date` e `not is_up_to_date(...)` ⇒ `up_to_date → not_indexed`,
  preservando `last_processed_commit` como base de comparação (CP-02).
- `state == up_to_date` e `is_up_to_date(...)` (ou tip ausente) ⇒ permanece
  `up_to_date` (CP-01).
- demais estados ⇒ no-op idempotente.

## 6. Porta `CatalogRepository` (`repository.py`, `Protocol` `@runtime_checkable`)

Assinaturas canônicas congeladas (todos os métodos retornam o snapshot atualizado):

```python
def upsert_repository(self, *, connection_name: str, origin: RepoOrigin,
                      repo_identifier: str, github_org: str | None = None,
                      local_path: str | None = None) -> CatalogEntry: ...
def deactivate_repository(self, repository_id: int) -> CatalogEntry: ...
def list_active_catalog(self) -> Sequence[CatalogEntry]: ...
def get_repository(self, repository_id: int) -> CatalogEntry: ...
def transition_state(self, repository_id: int, target_state: RepoState, *,
                     expected_version: int) -> CatalogEntry: ...
def mark_queued(self, repository_id: int) -> CatalogEntry: ...
def mark_indexing(self, repository_id: int) -> CatalogEntry: ...
def mark_updated(self, repository_id: int, commit: str) -> CatalogEntry: ...
def mark_error(self, repository_id: int, message: str,
               error_at: datetime) -> CatalogEntry: ...
def update_main_commit(self, repository_id: int, commit: str) -> CatalogEntry: ...
def reconcile_repository(self, repository_id: int) -> CatalogEntry: ...
def update_progress(self, repository_id: int, percent: int,
                    files_processed: int, files_total: int,
                    current_stage: str) -> CatalogEntry: ...
def start_execution(self, repository_id: int,
                    commit_target: str) -> IndexingExecution: ...
def list_executions(self, repository_id: int) -> Sequence[IndexingExecution]: ...
def record_file_stage(self, execution_id: int, file_path: str,
                      stage: FileStage) -> FileProgress: ...
def list_file_progress(self, execution_id: int) -> Sequence[FileProgress]: ...
```

**Ordem de checagem congelada de `transition_state`:** existência →
`expected_version` (conflito ⇒ `ConcurrencyConflictError`) → validade da
transição (ilegal ⇒ `InvalidStateTransitionError`). Garante CP-12 mesmo quando o
destino é válido (`queued → indexing` com versão stale).

### 6.1 Mapa operação → critério de aceite → consumidor
| Método | Critério (BDD) | Consumidor |
|---|---|---|
| `upsert_repository` | CP-08 (setup) | T07 |
| `deactivate_repository` | CP-08 | T07 |
| `list_active_catalog` | CP-04, CP-08 | T07/T14/T17/T18 |
| `get_repository` | CP-01/02/03/06/10/11 | T14/T18 |
| `transition_state` | CP-10, CP-12 | T14 |
| `mark_queued` / `mark_indexing` | CP-03..07 (fluxo) | T14 |
| `mark_updated` | CP-01/02/03 | T14 |
| `mark_error` | CP-06/07 | T14 |
| `update_main_commit` | CP-01/02 | T08/T14 |
| `reconcile_repository` | CP-01/02 | T14 |
| `update_progress` | CP-04 | T14 |
| `start_execution` | CP-03/04/05/06/07 | T14 |
| `list_executions` | CP-06/07 | T18 |
| `record_file_stage` | CP-05 | T14 |
| `list_file_progress` | CP-05 | T14/UI |

## 7. Efeitos colaterais congelados dos atalhos `mark_*`

| Método | Transição | Efeitos adicionais |
|---|---|---|
| `mark_queued` | `not_indexed→queued`, `error→queued`, `queued→queued` (no-op) | — |
| `mark_indexing` | `queued→indexing` | par de `start_execution` |
| `mark_updated(commit)` | `indexing→up_to_date` | `last_processed_commit = current_main_commit = commit`; execução corrente → `SUCCEEDED`, `finished_at` |
| `mark_error(msg, at)` | `indexing→error` | execução corrente → `FAILED`, `error_message=msg`, `error_at=at` (REQ-023) |

Os `mark_*` **não** exigem `expected_version` (leem a versão corrente); o controle
otimista explícito é exclusivo de `transition_state` (CP-12).

## 8. Segurança (design §8)
Nenhuma mensagem de erro (`CatalogPersistenceError`, `__repr__`) inclui
`DATABASE_URL` completa nem credenciais. O catálogo não armazena token GitHub.

## 9. Rastreabilidade das SUGGESTIONs

| ID | Origem | Tratamento neste gate |
|---|---|---|
| S-1 | reviews (design) | Máquina de estados + política idempotente formalizadas (§5); constantes `ALLOWED_TRANSITIONS`/`IDEMPOTENT_SELF_STATES` |
| S-2 | reviews (design) | `ExecutionStatus` como enum próprio, distinto de `RepoState` (§2.4) |
| S-3 | reviews (design) | Fora desta task (config); `DATABASE_URL` permanece na fronteira do adaptador (gate impl) |
| B-2 | reviews (BDD) | Nomes canônicos congelados (§1, §6) |
| B-3 | reviews (BDD) | Forma do progresso congelada em `CatalogEntry.progress` (§1, §3.1/§3.2) |

## 10. Fora de escopo deste gate
- Implementação do fake `InMemoryCatalogRepository` e do adaptador PG (gate unit/impl).
- Migrations Alembic e schema físico (gate impl).
- Unit tests de transições/corner cases (próximo gate).

## 11. Definição de pronto (interfaces)
- [ ] Nomes canônicos congelados e dentro dos candidatos do BDD.
- [ ] Enums fechados (REQ-020 sem extras) + `ExecutionStatus` distinto.
- [ ] Forma de `CatalogEntry`/`Progress`/`IndexingExecution`/`FileProgress` congelada.
- [ ] Máquina de estados completa + política idempotente + `is_up_to_date` (S-1).
- [ ] Erros com responsabilidade e motivo da separação.
- [ ] Stubs de Protocol (`...`) sem implementação; `__init__` reexporta o necessário.
- [ ] Review de outro Architect (`APPROVED_BY_ARCHITECT`) — gate autônomo.

## 12. Próximo passo no pipeline
Review do Architect deste `interfaces.md` → unit tests (transições, corner cases:
repo inexistente, update concorrente, idempotência) → implementação (domínio +
fake + adaptador PG + migrations) → Blue → cobertura ≥95% → PR.
