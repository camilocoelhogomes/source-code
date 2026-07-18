# Design — T07-catalog-sync

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T07-catalog-sync` |
| Autor | Implementation Task Runner |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T07-catalog-sync` |
| Base | `main` (T03/T05/T06 mesclados) |
| Rastreabilidade | REQ-035; BR-001, BR-016, BR-017; REQ-020; BDD-001, BDD-016, BDD-021, BDD-023; ENG-011 (handoff) |

## 1. Contexto

T02 entrega `AppConfig` tipado. T05/`GitHubRepoDiscovery` e T06/`LocalRepoDiscovery` produzem candidatos com origem e conexão. T03/`CatalogRepository` persiste o catálogo (PostgreSQL SoT) com upsert, soft-delete e estados fechados REQ-020.

T07 é o **serviço de bootstrap do catálogo**: config válida → discovery (GitHub + local) → sincronizar SoT. Não indexa. Após o sync, T14 (wire em T14/T19) executa o **startup reconcile** (ENG-011).

Fora de escopo: indexação; edição de config; busca; UI/MCP; novos estados; reconcile de tip `main`.

## 2. Problema

Na inicialização, o catálogo ativo deve refletir exatamente os repositórios descobertos da config atual (`CONFIG_PATH` — BR-016):

1. Upsert de cada repo descoberto com origem (`github`|`local`), nome da conexão e org/path.
2. Preservar estado/commits já conhecidos no upsert (T03 — não reprocessar commits).
3. Remover do catálogo **ativo** repos presentes antes e ausentes agora (soft-delete); histórico retido.
4. **Não** inventar estado `indisponível` nem qualquer valor fora de REQ-020.
5. Expor origem e conexão para UI/MCP (REQ-035; BDD-021/023 — catálogo derivado, sem CRUD de definições).

## 3. Solução proposta

Módulo `github_rag.catalog.sync` + helper fino de bootstrap:

| Componente | Papel |
|---|---|
| `CatalogSync` | Orquestra discoveries + `CatalogRepository` |
| `CatalogSyncResult` | Snapshot imutável do sync (ativos, desativados, issues locais) |
| `CatalogSyncError` | Falha fatal de sync (ex.: discovery GitHub) sem aplicar desativações |
| `run_catalog_sync` (`app/bootstrap.py`) | Helper de boot: chama `CatalogSync.sync(config)`; **não** reconcile/indexa |

Fluxo feliz:

```text
AppConfig (T02, já válido)
  → para cada conexão type=github:
        GitHubRepoDiscovery.discover(name, conn) → DiscoveredGitHubRepo*
  → LocalRepoDiscovery.discover(config) → repos + issues (não fatal)
  → chave canônica: (connection_name, repo_identifier)
  → para cada descoberto: CatalogRepository.upsert_repository(...)
       github: origin=GITHUB, repo_identifier=full_name, github_org=org
       local:  origin=LOCAL,  repo_identifier, local_path
  → list_active_catalog(); para cada ativo cuja chave ∉ descobertos:
        deactivate_repository(id)   # soft-delete; sem estado extra
  → CatalogSyncResult (entries ativas + deactivated + local_issues)
```

Fluxo de erro fatal (GitHub):

```text
GitHubDiscoveryError em qualquer conexão
  → aborta ANTES de desativar ausentes
  → levanta CatalogSyncError (mensagem sem token)
  → upserts já feitos nesta execução podem existir (idempotentes);
    política: desativação só após discovery completo bem-sucedido
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T07 | Fora de T07 |
|---|---|---|
| BDD-001 | Repos GitHub descobertos entram no catálogo ativo com origem `github` + conexão | UI listagem (T18); filtro wildcard (T05) |
| BDD-016 | Repos locais descobertos entram com origem `local` + conexão/path | Validação Git/`main` (T06); checkbox/index (T14/T18) |
| BDD-021 | Catálogo identifica conexão e origem após sync a partir de `AppConfig` | Loader JSON (T02) |
| BDD-023 | Sync só deriva catálogo da config; sem API de CRUD de definições | Superfície UI (T18) |
| Ausência | Repo sumiu da discovery → `active=False`; estado REQ-020 inalterado; não listável em `list_active_catalog` | — |
| Não-indexação | Sync não chama mark_*/start_execution/reconcile | T14 |

## 4. Componentes

### 4.1 `CatalogSync`

- Dependências injetáveis: `GitHubRepoDiscovery`, `LocalRepoDiscovery`, `CatalogRepository`.
- Método principal: `sync(config: AppConfig) -> CatalogSyncResult`.
- Ordem: discovery completo → upserts → desativações → resultado.
- Novos repos: estado inicial vem do upsert T03 (`not_indexed`).
- Upsert existente: preserva `state`, `last_processed_commit`, progresso (contrato T03).
- Idempotente: re-sync com mesma discovery não altera estados além de metadados de origem/path.

### 4.2 `CatalogSyncResult`

Campos (frozen):

| Campo | Tipo | Semântica |
|---|---|---|
| `active` | `tuple[CatalogEntry, ...]` | Catálogo ativo pós-sync (`list_active_catalog`) |
| `upserted` | `tuple[CatalogEntry, ...]` | Entradas retornadas pelos upserts desta execução |
| `deactivated` | `tuple[CatalogEntry, ...]` | Soft-deleted nesta execução |
| `local_issues` | `tuple[LocalDiscoveryIssue, ...]` | Issues T06 (BDD-018); não abortam sync |

### 4.3 `run_catalog_sync` (bootstrap)

- Função em `github_rag.app.bootstrap`: recebe `AppConfig` + `CatalogSync` (ou deps) e devolve `CatalogSyncResult`.
- **Não** chama reconcile/indexação — handoff explícito para T14 (ENG-011).
- Motivo da existência: ponto de wire estável para T14/T19 sem espalhar orquestração.

### 4.4 Política de ausência (fechada)

| Situação | Ação | Estado REQ-020 |
|---|---|---|
| Repo na discovery, novo no PG | `upsert` → `active=True`, `not_indexed` | `not_indexed` |
| Repo na discovery, já no PG | `upsert` reativa se soft-deleted; preserva state/commits | inalterado |
| Repo ativo no PG, ausente da discovery | `deactivate_repository` | inalterado (não vira `indisponível`) |
| Repo soft-deleted, volta na discovery | `upsert` reativa | estado preservado |

## 5. Dados

| Campo catálogo | Fonte |
|---|---|
| `connection_name` | discovery |
| `origin` | `github` / `local` |
| `repo_identifier` | GitHub `full_name` ou local `repo_identifier` |
| `github_org` / `local_path` | discovery |
| `state` / commits / progresso | preservados no upsert (T03) |

Chave de identidade para sync: `(connection_name, repo_identifier)` — alinhada ao upsert T03.

## 6. Erros e segurança

- `CatalogSyncError`: envolve falha fatal (tipicamente `GitHubDiscoveryError`); mensagem sem valor de token (BDD-014).
- Issues locais: não levantam; seguem em `CatalogSyncResult.local_issues`.
- Desativação só após discovery completo OK (evita apagar catálogo GitHub por falha de API).
- Sem I/O de token além do já encapsulado em T05.

## 7. Compatibilidade

- Consome contratos T02/T03/T05/T06 sem alteração.
- Persistência continua via porta `CatalogRepository` (BR-024 — Sem SQL ad hoc em T07).
- Handoff T14: após `CatalogSyncResult`, reconcile + enqueue (fora desta task).

## 8. Observabilidade

- Resultado tipado com contagens implícitas (`len(active)`, `len(deactivated)`, issues).
- Sem logging de segredos. Logging estruturado de boot fica em T14/T19.

## 9. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Desativar repos por falha parcial de discovery | Desativação só após discovery completo; GitHub fatal aborta |
| Reintroduzir estado `indisponível` | Soft-delete `active=False`; testes negativos |
| Sync reprocessar commits | Upsert T03 preserva commits; testes de preservação |
| Bootstrap indexar cedo demais | `run_catalog_sync` sem reconcile; documentado no handoff |

## 10. Rollback

Remover `catalog/sync.py` e `app/bootstrap.py` (helper); sem migration nova (usa schema T03).

## 11. Decisões

| ID | Decisão | Motivo |
|---|---|---|
| D-T07-001 | Desativação somente após discovery completo bem-sucedido | Evitar wipe por falha de API |
| D-T07-002 | Issues locais não abortam sync | BDD-018 / T06 |
| D-T07-003 | Helper `run_catalog_sync` sem reconcile | ENG-011 pertence a T14 |
| D-T07-004 | Chave `(connection_name, repo_identifier)` | Paridade com upsert T03 |
| D-T07-005 | Estados exclusivamente REQ-020; ausência = soft-delete | Plano §; task DoD |
