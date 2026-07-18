# Design — T03-catalog-persistence

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T03-catalog-persistence` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Base | `main` (T01 mesclado) |
| Modo | `autonomous-implementation-orchestrator` (aprovação do Architect substitui gates humanos intermediários) |
| Rastreabilidade | BR-001, BR-004; REQ-020, REQ-021, REQ-022, REQ-023; DEC-005; ENG-011; plano §1.3, §3, §8; BDD-004, BDD-005, BDD-007, BDD-008 (camada de persistência) |

## 0. Histórico de decisão

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | Candidato produzido | `0.1.0` | Primeiro design da T03; aguarda review do Architect (gate que substitui HITL no modo autônomo). Não auto-aprovado. |
| 2026-07-18 | tech-lead-architect (modo REVIEW) | `APPROVED_BY_ARCHITECT` | `0.1.0` | Review independente; sem achados BLOCKING/MAJOR; 3 SUGGESTION p/ próximos gates. Ver `reviews.md`. |

## 1. Contexto

T01 entregou a fundação (`src` layout, pacote `github_rag`, harness `pytest`+`pytest-cov` com `fail_under=95`, `settings.py` de bootstrap sem domínio) e T02 entrega a carga/validação do JSON de conexões. A fronteira `src/github_rag/catalog/` existe apenas como placeholder (docstring).

T03 estabelece **PostgreSQL como fonte de verdade (SoT)** do catálogo (BR-001, DEC-005): repositórios (GitHub e locais), origem, estado de indexação fechado (REQ-020), último commit processado (BR-004), progresso e etapas por arquivo (REQ-021/022) e histórico de execuções com mensagem e horário de erro (REQ-023). Entrega o modelo de domínio, o schema versionado (migrations desde o início) e a porta `CatalogRepository`.

Esta task **não** descobre repositórios (T05/T06), **não** sincroniza catálogo (T07), **não** indexa nem orquestra (T14) e **não** toca UI (T18) nem Qdrant/Zoekt (T10/T13). Entrega uma camada de persistência consumível.

### Consumidores (handoff)

| Consumidor | Uso da porta `CatalogRepository` |
|---|---|
| T07 (catalog-sync) | Upsert de repositórios descobertos; **desativação** (soft-delete) de repos ausentes da config atual, preservando histórico |
| T14 (indexing-orchestrator) | Transições de estado, progresso, etapas por arquivo, execução/histórico, **startup reconcile** (ENG-011) |
| T18 (management-ui) / T17 (mcp) | Leitura do catálogo ativo com estado + `last_processed_commit`; histórico de erros |

## 2. Problema

A persistência precisa suportar, com semântica PostgreSQL preservada:

1. Representar cada repositório do catálogo ativo com origem (`github`|`local`), conexão de origem, identificação (org/full name ou caminho local) e estado atual **fechado** (apenas REQ-020).
2. Comparar `commit atual da main` × `last_processed_commit` (BR-002/004; suporte a BDD-004/005 e ENG-011).
3. Listar o **catálogo ativo com estado + `last_processed_commit`** (leitura central do startup reconcile ENG-011 e das superfícies UI/MCP).
4. Registrar progresso da execução corrente: percentual, arquivos processados, etapa atual (REQ-021).
5. Registrar, **por arquivo**, a passagem pelas etapas `zoekt` | `tree_sitter` | `metadata_persisted` (REQ-022).
6. Manter **histórico de execuções** com mensagem e horário de erro (REQ-023; BDD-008).
7. Suportar **desativação** de repositório ausente da config atual (T07) sem apagar histórico, sem inventar estado fora de REQ-020.
8. Garantir transições de estado válidas e tratar update concorrente básico.

## 3. Solução proposta

### 3.1 Arquitetura hexagonal (porta + adaptador)

O módulo `github_rag.catalog` separa **domínio puro** (regras testáveis sem I/O) de **adaptador PostgreSQL** (SQLAlchemy/Alembic), atrás da porta `CatalogRepository`.

| Componente | Módulo (provável) | Papel |
|---|---|---|
| Enums e modelos de domínio | `catalog/models.py` | `RepoState`, `RepoOrigin`, `FileStage`, dataclasses imutáveis de leitura (`CatalogEntry`, `IndexingExecution`, `FileProgress`, `Progress`) |
| Regras de transição de estado | `catalog/transitions.py` (ou dentro de `models.py`) | Máquina de estados fechada (REQ-020); pura, sem I/O |
| Porta `CatalogRepository` | `catalog/repository.py` | Protocol com operações de sync/orquestrador/reconcile; comentários de responsabilidade e motivo da separação |
| Erros de domínio | `catalog/errors.py` (ou `repository.py`) | `CatalogError`, `RepositoryNotFoundError`, `InvalidStateTransitionError`, `ConcurrencyConflictError`, `CatalogPersistenceError` |
| Adaptador PostgreSQL | `catalog/postgres/` (tabelas, engine/session factory, `PostgresCatalogRepository`) | Implementa a porta usando SQLAlchemy 2.x |
| Fake in-memory | `catalog/memory.py` (ou em `tests/`) | Implementação in-memory da porta para testes de comportamento/domínio sem PG |
| Migrations | `migrations/` (Alembic) | Schema versionado desde a versão inicial |

**Motivo da separação:** o domínio (estados fechados, comparação de commit, transições, corner cases) deve ser 100% testável sem PostgreSQL e sem Docker — requisito para os ~50% da equipe em Windows sem PG local. O adaptador PG concentra I/O e é validado por testes de contrato/integração contra PG real. Isso preserva a semântica PostgreSQL (enum nativo, `FOR UPDATE`, transações) sem depender de SQLite, que não a reproduz.

### 3.2 Decisões de biblioteca

| Item | Decisão | Motivo |
|---|---|---|
| ORM/Core | **SQLAlchemy 2.x** (estilo declarativo tipado) | Padrão maduro; tipagem 2.x; mapeia enums nativos PG; permite Core para consultas de leitura do reconcile |
| Migrations | **Alembic** | Schema versionado desde a versão inicial (handoff T03); evita migrações ad hoc (plano §8) |
| Driver | **psycopg 3** (`psycopg[binary]`) síncrono | Driver moderno; código de catálogo síncrono (coerente com T01/T02 síncronos); paralelismo de indexação (T04/T14) usa pool + workers, não `asyncio` nesta task |
| URL de conexão | env **`DATABASE_URL`** (formato SQLAlchemy `postgresql+psycopg://...`) | Configuração por variável de ambiente (REQ-037 é sobre workers/token/CONFIG_PATH; `DATABASE_URL` é adição operacional necessária a esta task) |
| Testes de domínio | fake in-memory implementando a porta | Cobre transições/corner cases sem PG; roda em qualquer OS |
| Testes de contrato/adaptador PG | **testcontainers-python** (PostgreSQL) OU fixture de PG descartável | Preserva semântica PG real; marcados (`@pytest.mark.integration`) e separáveis do unit run |

**Sobre `DATABASE_URL` e o contrato T01 (congelado):** o `settings.py` de T01 (`AppSettings`/`load_settings`) está congelado e cobre apenas bootstrap. Para **não reabrir** o contrato T01, a leitura de `DATABASE_URL` fica na fronteira `catalog` (fábrica de engine/sessão), lendo `os.environ` via `Mapping` injetável — mesmo padrão OS-agnostic de T01. Uma futura consolidação em `AppSettings` é possível, mas fora do escopo desta task.

### 3.3 Estratégia de teste sem PostgreSQL real

| Camada | Como testar | Cobertura alvo |
|---|---|---|
| Domínio (enums, transições, comparação de commit, corner cases) | Unit tests puros + **fake in-memory** da porta | Alta; carrega o grosso dos 95% |
| Contrato da porta | Suíte de contrato aplicada ao fake **e** ao adaptador PG | Garante paridade semântica |
| Adaptador PostgreSQL (SQL, enum nativo, lock, upsert, soft-delete) | Testcontainers/PG real, marcados `integration` | Semântica PG verificada; excluível do run que exige só CPU |

Para o gate de cobertura ≥95% sem exigir Docker no unit run, o adaptador PG que depender de PG real fica sob marcador `integration`; se necessário, trechos não cobríveis sem PG são declarados em `[tool.coverage.run] omit`/`# pragma: no cover` de forma justificada, mantendo a lógica de decisão fora do adaptador (no domínio, coberto). Preferência: cobrir o adaptador via testcontainers no CI.

## 4. Modelo de domínio

### 4.1 Enums fechados

**`RepoOrigin`** (origem):

| Valor (DB/enum) | Significado |
|---|---|
| `github` | Repositório GitHub |
| `local` | Repositório local montado (`file://`) |

**`RepoState`** (REQ-020 — **exatamente 5, sem extras**):

| Valor (DB/enum, slug estável) | Rótulo REQ-020 |
|---|---|
| `not_indexed` | `não indexado` |
| `queued` | `na fila` |
| `indexing` | `indexando` |
| `up_to_date` | `atualizado` |
| `error` | `erro` |

**Proibido** qualquer outro valor. Especificamente **não** existem `desatualizado` nem `indisponível` (plano §3; T07). Novo commit em `main` ⇒ `up_to_date` deixa de valer e o repo volta a `not_indexed` (ENG-011). Repo ausente da config ⇒ **desativação** (soft-delete), não um estado.

> Decisão: valores de enum são slugs ASCII estáveis em inglês; o rótulo em português de REQ-020 é responsabilidade de apresentação (T18). Isso evita acentuação em identificadores de banco/código. Mapeamento 1:1 documentado acima.

**`FileStage`** (REQ-022 — etapas por arquivo):

| Valor | Significado |
|---|---|
| `zoekt` | Arquivo enviado ao índice exato Zoekt |
| `tree_sitter` | Arquivo processado pelo Tree-sitter (chunks) |
| `metadata_persisted` | Metadados SLM por chunk + persistência Qdrant concluídos |

### 4.2 Máquina de estados (fechada)

Transições permitidas (qualquer outra ⇒ `InvalidStateTransitionError`):

```text
not_indexed  → queued
queued       → indexing
indexing     → up_to_date        (execução concluída com sucesso; grava last_processed_commit)
indexing     → error             (falha em qualquer etapa; grava mensagem + horário)
error        → queued            (nova tentativa reinicia o repo inteiro — BR-005)
error        → not_indexed       (reconcile/limpeza)
up_to_date   → not_indexed       (novo commit em main ≠ last_processed_commit — ENG-011)
```

- `up_to_date` **exige** `last_processed_commit == current_main_commit` (BR-004). A comparação é regra pura de domínio, testável sem PG.
- Reentrância idempotente: transicionar para o mesmo estado quando já nele deve ser tratado (no-op explícito ou erro) — decisão registrada em `interfaces.md`/unit tests; preferência: no-op idempotente para `queued`/`not_indexed` no reconcile, e erro para transições ilegais.

### 4.3 Modelos de leitura (dataclasses imutáveis)

| Modelo | Campos principais |
|---|---|
| `CatalogEntry` | `id`, `connection_name`, `origin`, `github_org` \| `local_path`, `repo_identifier`, `state`, `last_processed_commit`, `current_main_commit`, `active`, timestamps |
| `Progress` | `percent`, `files_processed`, `files_total`, `current_stage` (nome livre da etapa corrente; REQ-021) |
| `IndexingExecution` | `id`, `repository_id`, `status`, `started_at`, `finished_at`, `commit_target`, `error_message`, `error_at` |
| `FileProgress` | `execution_id`, `file_path`, `zoekt_at`, `tree_sitter_at`, `metadata_persisted_at` |

## 5. Dados / schema (PostgreSQL, versionado via Alembic)

### 5.1 Tabelas

**`catalog_repository`** — repositório do catálogo (SoT):

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | `bigint` PK (identity) | |
| `connection_name` | `text NOT NULL` | conexão declarativa de origem |
| `origin` | `repo_origin` (enum nativo) `NOT NULL` | `github` \| `local` |
| `github_org` | `text NULL` | preenchido quando `origin='github'` |
| `local_path` | `text NULL` | preenchido quando `origin='local'` |
| `repo_identifier` | `text NOT NULL` | full name (`org/repo`) ou identificador do path |
| `state` | `repo_state` (enum nativo) `NOT NULL DEFAULT 'not_indexed'` | REQ-020 |
| `last_processed_commit` | `text NULL` | BR-004; null = nunca processado |
| `current_main_commit` | `text NULL` | tip conhecido da `main` (atualizado por T08/T14) |
| `progress_percent` | `smallint NULL` | 0–100 (REQ-021) |
| `files_processed` | `integer NULL` | REQ-021 |
| `files_total` | `integer NULL` | REQ-021 |
| `current_stage` | `text NULL` | etapa corrente exibível (REQ-021) |
| `current_execution_id` | `bigint NULL FK` | execução em andamento |
| `active` | `boolean NOT NULL DEFAULT true` | soft-delete (T07): `false` = fora do catálogo ativo |
| `deactivated_at` | `timestamptz NULL` | quando saiu do catálogo ativo |
| `row_version` | `integer NOT NULL DEFAULT 0` | lock otimista (update concorrente) |
| `created_at` / `updated_at` | `timestamptz NOT NULL` | auditoria |

- Restrições de integridade da origem via `CHECK` (ex.: `origin='github'` ⇒ `github_org NOT NULL`; `origin='local'` ⇒ `local_path NOT NULL`).
- Unicidade do catálogo ativo: índice único parcial em `(connection_name, repo_identifier) WHERE active` (permite reaproveitar/re-adicionar histórico ao reativar).

**`indexing_execution`** — histórico de execuções (REQ-023; BDD-008):

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | `bigint` PK | |
| `repository_id` | `bigint NOT NULL FK → catalog_repository(id)` | histórico permanece mesmo após soft-delete do repo |
| `status` | `text/enum NOT NULL` | ex.: `running`, `succeeded`, `failed` (status de execução ≠ estado REQ-020) |
| `commit_target` | `text NULL` | commit alvo/processado da execução |
| `started_at` | `timestamptz NOT NULL` | |
| `finished_at` | `timestamptz NULL` | |
| `error_message` | `text NULL` | mensagem de erro (REQ-023) |
| `error_at` | `timestamptz NULL` | horário do erro (REQ-023) |

**`file_processing`** — etapas por arquivo (REQ-022):

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | `bigint` PK | |
| `execution_id` | `bigint NOT NULL FK → indexing_execution(id)` | |
| `file_path` | `text NOT NULL` | |
| `zoekt_at` | `timestamptz NULL` | marca etapa `zoekt` |
| `tree_sitter_at` | `timestamptz NULL` | marca etapa `tree_sitter` |
| `metadata_persisted_at` | `timestamptz NULL` | marca etapa `metadata_persisted` |

- Único por `(execution_id, file_path)`; registrar etapa = setar o timestamp correspondente (idempotente).
- Alternativa considerada: linha-evento por `(execution_id, file_path, stage)` com enum `file_stage`. Escolhida a coluna-por-etapa por consulta de progresso mais barata; o enum `FileStage` permanece no domínio para a API `record_file_stage`.

### 5.2 Leitura central do reconcile (ENG-011)

`list_active_catalog()` retorna cada `CatalogEntry` com `state` e `last_processed_commit` (e `current_main_commit`), filtrando `active = true`. É a base para: comparar tip `main` × processado (T14), listar catálogo (T17/T18) e decidir enfileiramento.

### 5.3 Migrations

- Alembic inicializado com `migrations/` (`env.py`, `alembic.ini`, `versions/`), configurado para ler `DATABASE_URL`.
- Revisão inicial cria enums nativos (`repo_origin`, `repo_state`), as três tabelas, índices e constraints.
- Convenção de nomes de constraints/índices via `MetaData(naming_convention=...)` para migrações determinísticas.

## 6. Porta `CatalogRepository` (nível conceitual; contrato formal em `interfaces.md`)

Operações previstas (assinaturas detalhadas e comentários de responsabilidade/motivo ficam no gate `interfaces.md`):

| Operação | Consumidor | Responsabilidade |
|---|---|---|
| `upsert_repository(...)` | T07 | Inserir/atualizar repo do catálogo preservando estado/commit conhecidos |
| `deactivate_missing(...)` / `deactivate_repository(id)` | T07 | Soft-delete de repos ausentes da config; histórico retido |
| `list_active_catalog()` | T07/T14/T17/T18 | Catálogo ativo com estado + `last_processed_commit` (ENG-011) |
| `get_repository(id)` / `find(...)` | T14/T18 | Leitura pontual; `RepositoryNotFoundError` se ausente |
| `transition_state(id, target, *, expected_version)` | T14 | Aplica transição válida (máquina de estados) com lock otimista |
| `mark_queued` / `mark_indexing` / `mark_updated(commit)` / `mark_error(message, at)` | T14 | Atalhos de transição com efeitos colaterais (grava commit/erro) |
| `update_progress(id, percent, files_processed, files_total, stage)` | T14 | REQ-021 |
| `start_execution(id, commit_target)` / `finish_execution(...)` | T14 | Abre/fecha execução; alimenta histórico |
| `record_file_stage(execution_id, file_path, stage)` | T14 | REQ-022 (idempotente) |
| `list_execution_history(id)` | T18 | REQ-023 / BDD-008 |

## 7. Erros

| Tipo | Condição |
|---|---|
| `CatalogError` (base) | Raiz da hierarquia do módulo |
| `RepositoryNotFoundError` | Operação sobre repo inexistente (corner case do aceite) |
| `InvalidStateTransitionError` | Transição fora da máquina de estados (REQ-020) |
| `ConcurrencyConflictError` | `expected_version` ≠ `row_version` (update concorrente) |
| `CatalogPersistenceError` | Falha de infraestrutura do adaptador PG (conexão/transação), com causa encadeada |

Invariantes: erros de domínio (not found, transição, concorrência) são independentes de PG e testáveis com o fake. Nenhuma mensagem inclui `DATABASE_URL` completa nem credenciais.

## 8. Segurança

- `DATABASE_URL` pode conter usuário/senha: **nunca** logar; `__repr__`/mensagens de erro do módulo redigem/omitirão a URL de credenciais.
- Catálogo **não** armazena token GitHub nem segredos (BR-008/BR-019); origem `github` guarda apenas org e identificação do repo.
- Sem telemetria externa nesta task.

## 9. Compatibilidade

| Dimensão | Posição |
|---|---|
| Novas deps de runtime | `sqlalchemy>=2`, `alembic`, `psycopg[binary]` (adicionar em `pyproject.toml`) |
| Novas deps de teste | `testcontainers[postgres]` (ou fixture PG) no grupo `dev` |
| OS de desenvolvimento | Domínio + fake rodam em Windows/macOS/Linux **sem** PG/Docker (herda first-class de T01) |
| Testes de contrato PG | Exigem Docker/PG (testcontainers); marcados `integration` e separáveis do unit run — não bloqueiam quem não tem Docker |
| Config | `DATABASE_URL` lido de env via `Mapping` injetável (OS-agnostic; não reabre contrato T01) |
| Python | 3.12+ (herdado) |
| Greenfield | Sem migração de dados legados; schema versionado desde a revisão inicial |

## 10. Observabilidade

- O histórico `indexing_execution` é, por si, trilha de auditoria (início/fim, status, erro + horário — REQ-023).
- Erros estruturados via exceções tipadas.
- Logger opcional; se adotado, reutiliza a política de redaction de credenciais (sem `DATABASE_URL`).

## 11. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| SQLite em teste divergir de PG (enum, lock) | **Não** usar SQLite; domínio testado com fake; adaptador testado contra PG real (testcontainers) |
| Cobertura 95% difícil com adaptador dependente de PG | Concentrar lógica no domínio (coberta por fake); adaptador via testcontainers no CI; `omit`/`pragma` justificados só para I/O não decidível |
| Introduzir estado fora de REQ-020 | Enum fechado + máquina de estados + testes negativos; sem `desatualizado`/`indisponível` |
| Perder histórico ao remover repo da config | Soft-delete (`active=false`) + FK de histórico preservada; T07 desativa, não deleta |
| Update concorrente corromper estado | Lock otimista (`row_version`) + `ConcurrencyConflictError`; opção de `SELECT ... FOR UPDATE` no adaptador |
| Schema instável quebra T07/T14 | Contrato `CatalogRepository` versionado em `interfaces.md`; Alembic desde o início |
| Vazamento de credenciais em log/erro | Redaction de `DATABASE_URL`; sem token no catálogo |

## 12. Rollback

Greenfield: reverter o merge do PR desta branch. Alembic permite `downgrade` da revisão inicial. Volumes PostgreSQL são descartáveis no MVP local (plano §8). Sem dados legados a migrar.

## 13. Decisões de design (T03)

| ID | Decisão | Motivo |
|---|---|---|
| D-T03-001 | SQLAlchemy 2.x + Alembic + psycopg3 síncrono | Stack madura, tipada, enums nativos, migrations versionadas; coerente com base síncrona |
| D-T03-002 | Porta `CatalogRepository` + adaptador PG + fake in-memory (hexagonal) | Domínio testável sem PG/Docker; semântica PG no adaptador |
| D-T03-003 | **Não** usar SQLite em teste | SQLite não reproduz enum nativo/`FOR UPDATE`/tipos PG |
| D-T03-004 | `RepoState` com 5 slugs estáveis (mapeados a REQ-020); sem extras | REQ-020 fechado; sem `desatualizado`/`indisponível` |
| D-T03-005 | Soft-delete (`active` + `deactivated_at`), histórico retido | T07 remove do catálogo ativo sem apagar execuções (REQ-023) |
| D-T03-006 | `DATABASE_URL` lido na fronteira `catalog`, não em `AppSettings` | Não reabre contrato T01 congelado |
| D-T03-007 | Máquina de estados explícita e pura | Corner cases/transições cobertos por unit tests |
| D-T03-008 | Lock otimista via `row_version` | Update concorrente básico (aceite) sem serialização global |
| D-T03-009 | Etapas por arquivo como colunas de timestamp por etapa | Consulta de progresso barata; enum `FileStage` na API |
| D-T03-010 | Testes de adaptador PG marcados `integration` (testcontainers) | Preserva semântica PG sem bloquear dev sem Docker |

## 14. Fora de escopo (explícito)

- Descoberta de repositórios (T05/T06); sync/upsert orquestrado (T07).
- Pipeline de indexação, fila, workers, startup reconcile propriamente dito (T04/T14).
- Snapshot/diff de `main` (T08); elegibilidade (T09); Zoekt/Qdrant/SLM (T10–T13).
- UI (T18) e MCP (T17).

## 15. Definição de pronto (design)

- [ ] Architect aprova este design (`APPROVED_BY_ARCHITECT`).
- [ ] Enums fechados (REQ-020, origem, file stages) sem extras.
- [ ] Schema versionado (Alembic) desde a revisão inicial.
- [ ] Estratégia de teste sem PG real (domínio+fake) + contrato PG (testcontainers) aprovada.
- [ ] `DATABASE_URL` na fronteira `catalog` sem reabrir T01.
- [ ] Suporte a soft-delete com retenção de histórico.
- [ ] Próximo gate: `bdd.md` cobrindo persistência de BDD-004/005/007/008.

## 16. Próximo passo no pipeline

Após aprovação do Architect (modo autônomo): QA escreve BDD executáveis da persistência → review Architect → Architect define `interfaces.md` (`CatalogRepository`, enums, erros) → unit tests (transições, corner cases: repo inexistente, update concorrente) → implementação (domínio + adaptador PG + migrations) → Blue → cobertura ≥95% → PR (único gate humano: merge).
