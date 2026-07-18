# BDD — T07-catalog-sync

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T07-catalog-sync` |
| Autor | Implementation Task Runner (QA step) |
| Data | 2026-07-18 |
| Estado | `DRAFT` |
| Versão BDD | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T07-catalog-sync` |
| Rastreabilidade | REQ-035; REQ-020; BR-001, BR-016, BR-017; BDD-001, BDD-016, BDD-021, BDD-023; design D-T07-001..005; S-01 |

## Rastreabilidade

| Cenário | Aceite / requisito |
|---|---|
| CS-01 | BDD-001 / REQ-035 — repos GitHub descobertos no catálogo ativo com origem `github` + conexão |
| CS-02 | BDD-016 / REQ-035 — repos locais descobertos com origem `local` + conexão/path |
| CS-03 | BDD-021 — catálogo identifica conexão e origem a partir de `AppConfig` (github+git) |
| CS-04 | BDD-023 — sync só deriva catálogo; sem superfície de CRUD de definições |
| CS-05 | Ausência — repo sumiu da discovery → soft-delete; não listável; estado REQ-020 preservado (sem `indisponível`) |
| CS-06 | Upsert preserva `state` e `last_processed_commit` (não reprocessa commits) |
| CS-07 | Reativação — soft-deleted que volta na discovery fica `active=True` com estado preservado |
| CS-08 | S-01 / D-T07-001 — `GitHubDiscoveryError` aborta **antes** de qualquer `upsert`/`deactivate` nesta execução |
| CS-09 | Issues locais não abortam; seguem em `CatalogSyncResult.local_issues` |
| CS-10 | Sync não indexa — não chama `mark_*` / `start_execution` / `reconcile_repository` |
| CS-11 | Config vazia (`connections: {}`) → catálogo ativo vazio; desativa todos os ativos prévios |
| CS-12 | REQ-020 — entradas ativas/desativadas usam apenas estados do enum fechado |

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Steps / asserts | `tests/bdd/test_catalog_sync.py` |

## Como executar

```bash
python -m pytest tests/bdd/test_catalog_sync.py -q
```

## Escopo e exclusões

### Em escopo (T07)

- Orquestração discovery → upsert → desativação.
- Origem/conexão no catálogo ativo.
- Soft-delete de ausentes; preservação de estado/commits.
- Abort atomicidade de mutação em falha GitHub (S-01).

### Fora de escopo

| Item | Dono |
|---|---|
| Loader JSON / validação | T02 |
| Filtro wildcard / API GitHub | T05 |
| Validação Git/`main` local | T06 |
| Persistência PG / máquina de estados | T03 |
| Startup reconcile / indexação | T14 |
| UI / MCP | T18 / T17 |

## Cenários

### CS-01 — Catálogo GitHub com origem e conexão (BDD-001)

**Dado** um `AppConfig` com conexão GitHub nomeada `github-microservices`  
**E** a discovery GitHub retorna `my-org/microservice-auth` e `my-org/user-api`  
**Quando** `CatalogSync.sync(config)` for executado  
**Então** `list_active_catalog` deve conter ambos  
**E** cada entrada deve ter `origin == github`, `connection_name == "github-microservices"`  
**E** `github_org == "my-org"` e `repo_identifier` igual ao `full_name`.

### CS-02 — Catálogo local com origem e conexão (BDD-016)

**Dado** um `AppConfig` com conexão `git` nomeada `local-microservices`  
**E** a discovery local retorna um repo com `local_path` e `repo_identifier`  
**Quando** o sync for executado  
**Então** o catálogo ativo deve conter a entrada com `origin == local`  
**E** `connection_name`, `local_path` e `repo_identifier` refletindo a discovery.

### CS-03 — Origem e conexão mistas (BDD-021)

**Dado** `AppConfig` com uma conexão GitHub e uma `git`  
**E** discoveries retornam um repo de cada origem  
**Quando** o sync for executado  
**Então** o catálogo ativo deve listar ambas as entradas  
**E** cada uma identificada pela conexão e origem correspondentes.

### CS-04 — Sem CRUD de definições (BDD-023)

**Dado** o serviço `CatalogSync`  
**Quando** a superfície pública for inspecionada  
**Então** deve expor apenas sincronização derivada da config (`sync` / `run_catalog_sync`)  
**E** não deve expor operações de cadastrar/editar/remover definições de conexão ou repositório fora do fluxo de sync.

### CS-05 — Remover do catálogo ativo o ausente (sem estado extra)

**Dado** catálogo ativo com `my-org/old-service` (estado `up_to_date`, commit conhecido)  
**E** a discovery atual **não** inclui `my-org/old-service`  
**Quando** o sync for executado  
**Então** `my-org/old-service` não deve aparecer em `list_active_catalog`  
**E** a entrada desativada deve manter o mesmo `state` REQ-020 (não `indisponível`)  
**E** `active is False`.

### CS-06 — Upsert preserva estado e commit

**Dado** catálogo com `my-org/svc` em estado `up_to_date` e `last_processed_commit == "abc"`  
**E** a discovery ainda inclui `my-org/svc`  
**Quando** o sync for executado  
**Então** a entrada ativa deve permanecer `up_to_date` com `last_processed_commit == "abc"`.

### CS-07 — Reativar soft-deleted

**Dado** `my-org/svc` soft-deleted (`active=False`) com estado `error`  
**E** a discovery atual volta a incluir `my-org/svc`  
**Quando** o sync for executado  
**Então** a entrada deve estar ativa (`active=True`)  
**E** o estado deve permanecer `error`.

### CS-08 — Falha GitHub aborta sem mutar (S-01)

**Dado** catálogo ativo pré-existente com N entradas  
**E** a discovery GitHub levanta `GitHubDiscoveryError`  
**Quando** o sync for executado  
**Então** deve levantar `CatalogSyncError` (mensagem sem token)  
**E** nenhum `upsert_repository` nem `deactivate_repository` deve ter sido chamado nesta execução  
**E** o catálogo ativo permanece inalterado.

### CS-09 — Issues locais não abortam

**Dado** discovery local que retorna 1 repo válido e 1 `LocalDiscoveryIssue`  
**Quando** o sync for executado  
**Então** o repo válido deve estar no catálogo ativo  
**E** `CatalogSyncResult.local_issues` deve conter a issue  
**E** o sync não deve levantar exceção.

### CS-10 — Sync não indexa

**Dado** discoveries com repos novos  
**Quando** o sync for executado  
**Então** o repositório de catálogo não deve receber chamadas a `mark_queued`, `mark_indexing`, `mark_updated`, `mark_error`, `start_execution` nem `reconcile_repository`  
**E** novos repos ficam em `not_indexed`.

### CS-11 — Config vazia desativa todos

**Dado** catálogo ativo com repos  
**E** `AppConfig` com `connections: {}`  
**Quando** o sync for executado  
**Então** `list_active_catalog` deve estar vazio  
**E** os repos prévios devem estar desativados.

### CS-12 — Apenas estados REQ-020

**Dado** um sync bem-sucedido com upserts e desativações  
**Quando** os estados das entradas (ativas e desativadas) forem inspecionados  
**Então** cada `state` deve ser um dos cinco valores REQ-020  
**E** nenhum valor `indisponível` / `desatualizado` deve existir.

## Definition of Done (BDD)

- [ ] Cenários CS-01..12 cobrem BDD-001/016/021/023 e política de ausência
- [ ] S-01 (abort sem mutação) coberto por CS-08
- [ ] Sem indexação / reconcile no escopo (CS-10)
- [ ] Testes executáveis em `tests/bdd/test_catalog_sync.py`
