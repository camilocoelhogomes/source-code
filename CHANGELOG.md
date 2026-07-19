# Changelog

Todas as mudanças relevantes do projeto são registradas neste arquivo.

## [Unreleased]

### Adicionado

- Evidência browser na suíte Robot e2e (T23 / `gap-ui-browser`): suite
  `e2e/robot/ui_browser.robot` + resource `browser.resource` (Browser Library /
  Playwright) cobrindo BDD-001, 002, 007, 009, 010, 016, 019, 023 na UI;
  `robotframework-browser` em deps `[e2e]`; `ui_browser` no green path
  (`GREEN_PATH_SUITES`); fixture `config.e2e.json` com wildcard de inclusão
  `camilocoelhogomes/source-*`; docs `rfbrowser init` em `e2e/README.md` e
  `docs/runbook-local.md`. Suites RequestsLibrary (T21) preservadas — API HTTP
  sozinha não encerra a lacuna. Gate manifesto:
  `tests/bdd/test_ui_browser_gap.py` + `tests/unit/e2e/test_ui_browser_manifest.py`.
- Pacote de fechamento da auditoria (T07 / `mvp-e2e-audit-hardening`): contrato
  `AuditClosurePack` em
  `spec/features/mvp-e2e-audit-hardening/audit/closure-pack.md` — índice de
  evidências T01–T06, métricas de sucesso, backlog pai T22–T27, ordem
  run-first → falha → gap-fill, status `CLOSURE_READY` (encerrável /
  aguardando merge); MVP de produto **não** entregue; BDD
  `tests/bdd/test_mvp_e2e_audit_closure_pack.py`. Sem fix de produto
  (`src/github_rag/**`, `e2e/robot/**`, composes).
- Inventário de cobertura MVP e2e (T01 / feature `mvp-e2e-audit-hardening`):
  matriz documental `CoverageInventory` em
  `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md`
  (BDD-001–024 exc. 015; inspeção estática; SoT de lacunas para T06). Sem
  alteração de `e2e/` nem produto.
- Auditoria HITL env prep (T02 / `mvp-e2e-audit-hardening`): checklist
  versionado `spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md`
  (PAT operador, `cp .env.example .env`, `GITHUB_TOKEN`/`E2E_GITHUB_TOKEN`,
  gate T04 READY/BLOCKED sem secrets); link em `e2e/README.md`; testes BDD
  `tests/bdd/test_mvp_e2e_audit_hitl_env_prep.py`. `.env` permanece gitignored.
- Auditoria run-first pytest (T03 / `mvp-e2e-audit-hardening`): evidência
  versionável `ParentPytestRun` em
  `spec/features/mvp-e2e-audit-hardening/runs/pytest-all-tasks.md` (comando
  canônico `python -m pytest tests/ -q --tb=line`, exit/contagens/falhas do pai
  com superfície candidata, `coverage_gate`, soft-dep T01, sem secrets) +
  contrato BDD `tests/bdd/test_mvp_e2e_audit_pytest_run.py`. Sem alteração de
  produto (`src/github_rag/**`) nem `e2e/robot/**`.
- Auditoria run-first Robot green path (T04 / `mvp-e2e-audit-hardening`):
  evidência versionável `RobotGreenPathRun` em
  `spec/features/mvp-e2e-audit-hardening/runs/e2e-robot-green-path.md`
  (comando canônico `python -m github_rag.e2e`, Podman + compose e2e, exit/
  fases/suítes, falhas F-T04-* com superfície, soft-dep T03 independente, sem
  secrets) + contrato BDD `tests/bdd/test_mvp_e2e_audit_e2e_robot_run.py`.
  Sem expansão Robot/browser e sem alteração de produto (`src/github_rag/**`,
  `e2e/robot/**`).
- Backlog de falhas run-first (T05 / `mvp-e2e-audit-hardening`): contrato
  `ParentFailureBacklog` — índice
  `spec/features/mvp-e2e-audit-hardening/audit/failure-backlog-index.md` + task
  pai `T22-fix-tooling-e2e-compose-zoekt` (superfície `tooling-e2e`;
  classificação combinada REQ-017: F-T04-001=`flakiness`, F-T04-002=`produto`,
  F-T04-003=consequência); pytest T03 com zero falhas (sem task inventada);
  BDD `tests/bdd/test_mvp_e2e_audit_failure_backlog.py`. Sem fix de produto
  nesta feature (`src/github_rag/**`, `e2e/robot/**`, composes).
- Backlog de lacunas / gap-fill (T06 / `mvp-e2e-audit-hardening`): contrato
  `ParentGapFillBacklog` — índice
  `spec/features/mvp-e2e-audit-hardening/audit/gap-fill-backlog-index.md` +
  tasks pai T23–T27 (`gap-ui-browser`, `gap-catalog-indexing-integral`,
  `gap-negative-integral`, `gap-mcp-parallel-slo`, `gap-sdk-dec015-conformity`);
  UI exige browser (API sozinha insuficiente); classificação `gap-teste` /
  `assert-fraco`; sem duplicar T22; BDD
  `tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py`. Sem keywords/browser/
  produto nesta feature (`src/github_rag/**`, `e2e/robot/**`, composes).
- Prova e2e do MVP (T21): pacote `github_rag.e2e` com contratos
  `E2eStackLauncher` / `RobotMvpSuite` (`PodmanE2eStackLauncher`,
  `DefaultRobotMvpSuite`, `E2eCredentialResolver`), suíte Robot Framework em
  `e2e/robot/` (health, catalog_indexing, ui, mcp, negative; `--exclude bdd015`),
  fixtures sem secrets, `e2e/README.md`, optional-deps `[e2e]` +
  `requirements-e2e.txt`. Runtime Podman + `docker-compose.e2e.yml`; CI exige
  `E2E_GITHUB_TOKEN`; local HITL via `.env` não versionado / `GITHUB_TOKEN`.
  Entry: `python -m github_rag.e2e`.
- Entrega local por container (T19): pacote `github_rag.delivery`
  (`ContainerRuntime` / `DefaultContainerRuntime` / `run_container_boot`),
  `Dockerfile` + **três** composes (`docker-compose.yml` usuário,
  `docker-compose.e2e.yml` para T21/CI com alias `E2E_GITHUB_TOKEN`→`GITHUB_TOKEN`,
  `docker-compose.dev.yml` com `./src`), `.env.example` e `docs/runbook-local.md`.
  Boot ordenado ENG-011 (settings → config → migrate → sync →
  `StartupIndexReconcile` → scheduler → UI/MCP); fail-fast BDD-022; `/healthz`;
  plataforma `linux/amd64`; deps DEC-015 + `uvicorn` + `git` na imagem; sem
  `.venv` do host. Gate T19 = manifesto/doubles (sem Robot). MCP compose via
  SSE/HTTP; stdio em `python -m github_rag.delivery.mcp_stdio`.
- Management UI (T18): porta `ManagementUiApi` / `DefaultManagementUiApi` via
  **FastAPI** (`fastapi>=0.115,<1`) + frontend estático em `web/`. Listagem de
  repos (origem/estado REQ-020 com labels PT), indexação por checkbox,
  progresso e flags por arquivo, histórico de falhas (mensagem/horário),
  configuração de expressão cron (`DailyScheduler.set_cron`), buscas exact e
  semantic via `QueryService`. Sem CRUD de conexões/token (BDD-023). Dependência
  de dev `httpx` para TestClient.
- Agenda cron de indexação (T15): `DailyScheduler` / `DefaultDailyScheduler` via
  **APScheduler** (DEC-015/BDD-024); `CronPreferenceStore` (memória + SQLAlchemy);
  env `INDEX_CRON` → `AppSettings.index_cron` (default `0 2 * * *`); preferência
  UI em `scheduler_preference` prevalece em runtime (ENG-004); tick serializado
  (`run_tick_once` + lock) reusa `StartupIndexReconcile` + orquestrador T14;
  expressão inválida → `InvalidCronExpressionError`; migration Alembic
  `0002_scheduler_preference`. Dependência `apscheduler>=3.10,<4`.

- Orquestrador de indexação (T14): `IndexingOrchestrator` + `StartupIndexReconcile`
  só via portas (ENG-013). Fila com `WorkerLimiter`; estados REQ-020; startup
  reconcile (ENG-011) com recover de `queued`/`indexing`; reindex arquivo inteiro
  (ENG-012); Zoekt set-replace do conjunto tip; pipeline Tree-sitter → SLM por
  chunk → Qdrant; falha parcial → `error` + restart wipe Zoekt+Qdrant (BR-005).

### Alterado

- Fix tooling e2e compose/zoekt (T22): serviço `zoekt` nos três composes
  (`docker-compose.yml`, `docker-compose.e2e.yml`, `docker-compose.dev.yml`)
  declara `command: ["zoekt-webserver", "-index", "/data/index", "-rpc"]`
  (preserva ENTRYPOINT `tini`; mitiga F-T04-002 exit 1 por `tini` sem filho).
  Pré-req de compose provider no `PATH` (`podman-compose` / `podman compose`)
  documentado em `e2e/README.md` e `docs/runbook-local.md` (F-T04-001). Sem
  alteração de domínio (`src/github_rag/**`) nem expansão Robot/browser.
- Qdrant vector store (T13): no setup da collection, `QdrantVectorStore` solicita
  `create_payload_index` KEYWORD para `repo_id`, `commit_sha` e `path`. Setup
  idempotente (índice já existente / warning `:memory:` não aborta); filtros
  continuam válidos.
- Descoberta local (T20 / DT-001): `GitFilesystemInspector.inspect_repo` passa a
  usar **GitPython** (`git.Repo`) em vez de parse ad-hoc de `.git` / refs /
  `packed-refs` (BR-023, DEC-015). Contrato `LocalRepoDiscovery` e BDD-016/018
  preservados; bare continua rejeitado; runtime requer pacote GitPython e
  binário `git` no PATH.

### Adicionado

- Servidor MCP de evidências (T17): pacote `github_rag.mcp` com
  `DefaultMcpEvidenceServer` sobre SDK oficial **`mcp`** (`FastMCP`,
  `mcp>=1.27,<2`; transport stdio). Tools: `list_repos`, `search_code`,
  `semantic_search`, `read_file`, `list_tree` (REQ-028); delegação a
  catálogo + `QueryService` (T16); `DetailFields` / omit-null (BDD-012);
  paralelismo `QUERY_WORKERS` / `WorkerLimiter` (BDD-013); sem narrativa/SLM
  nem `ask_codebase` (DEC-008 / BR-011); redaction de token (BDD-014);
  erros tipados `McpToolError`. Handoff de processo para T19.

- QueryService compartilhado (T16): fachada `DefaultQueryService` com
  `search_exact`, `search_semantic`, `read_file` e `list_tree` sobre portas
  T10/T13/T08/T07; projeção `DetailFields` (BDD-012); `QueryReformulator`
  opcional (REQ-027/BR-011); erros tipados; fakes em `github_rag.query.fake`.
  Sem client paralelo (BR-023/BDD-024). Consumidores: T17/T18.

- Metadados contextuais SLM por chunk (T12): porta `MetadataGenerator` e
  adaptador `OpenAICompatibleMetadataGenerator` via SDK oficial `openai`
  (OpenAI-compatible local; DEC-015/BDD-024). Default de modelo Qwen Coder 3B
  (`qwen2.5-coder:3b`; DEC-006). Saída `ChunkMetadata` frozen + `to_payload()`
  JSON-safe; erros tipados (`MetadataConfigError`, `MetadataModelError`,
  `MetadataResponseParseError`); `FakeMetadataGenerator` para testes/T14.
  Dependência `openai`. Proibido inventar chunks ou prosa MCP (BR-010).
- Adaptador Zoekt (T10): porta `ExactCodeIndex` com `ZoektExactCodeIndex`
  (CLI `zoekt-index` + HTTP oficial `POST /api/search`) e `FakeExactCodeIndex`
  injetável — DEC-016 / BDD-009 / BDD-024; erros tipados `ExactCodeIndexError`
  para T14; envs `ZOEKT_*` via `from_environ` sem alterar `AppSettings`.
- Pacote `github_rag.index.zoekt` (`models`, `port`, `client`, `runner`,
  `index`, `fake`, `errors`).
- Snapshot da `main` (T08): `MainSnapshotProvider` / `DefaultMainSnapshotProvider`
  obtém tip, árvore, conteúdo completo de arquivo e diff de paths entre commits
  (BDD-005, BDD-017, ENG-012); local via GitPython; tip GitHub via PyGithub com
  `GitClonePort` mockável; `FirstIndexSignal` quando não há commit anterior;
  erros tipados (`MainBranchMissingError`, `CorruptRepositoryError`,
  `GitHubSnapshotNetworkError`, `CommitNotFoundError`, `FileNotFoundInCommitError`).
- Elegibilidade de arquivos (T09): porta `FileEligibilityFilter` com
  implementação `PathspecFileEligibilityFilter` — inclui textuais de
  desenvolvimento (Markdown, Java, etc.), exclui CSV/imagens e paths
  cobertos por `.gitignore` via **pathspec** GitWildMatch (BDD-006,
  DEC-015 / BR-023); sem caps de tamanho (REQ-019).
- Helper `load_gitignore_sources` para `.gitignore` aninhados; política
  documentada para arquivos sem extensão (include-by-default).
- Sync do catálogo (T07): `CatalogSync` orquestra discovery GitHub + local →
  upsert/`deactivate` no `CatalogRepository`; `run_catalog_sync` no bootstrap
  sem indexação nem reconcile (handoff ENG-011 → T14). Origem/conexão no
  catálogo ativo (BDD-001/016/021/023); ausência = soft-delete sem estado
  extra fora de REQ-020.
- Dependência de projeto `GitPython>=3.1`.
- Índice vetorial Qdrant + embeddings (T13): módulo `github_rag.index.vector`
  com portas `VectorStore` / `Embedder`, adaptadores `QdrantVectorStore`
  (`qdrant-client`) e `OpenAICompatibleEmbedder` (`openai`, só embeddings) —
  DEC-004/015, BR-023, BDD-010/024.
- Contrato `EnrichedChunk` / `ChunkMetadata` (chunk Tree-sitter + metadados
  SLM), `replace_repo_commit` (substitui vetores do commit anterior), payload
  Qdrant com schema estável e point id UUID v5; erros tipados
  (`VectorStoreError`, `EmbeddingError` e subclasses).
- Dependências de projeto `qdrant-client>=1.12` e `openai>=1.40`.
- Chunking semântico Tree-sitter (T11): porta `ContextualChunker` e
  implementação `TreeSitterContextualChunker` com grammars oficiais
  (`tree-sitter` + python/java/javascript/typescript/markdown/**yaml/json/xml/toml**)
  — única fonte de chunks RAG (DEC-003/015; BDD-007/024). Matriz config
  ampliada por review humano PR #9.
- Contrato estável `SemanticChunk` (`chunk_id` SHA-256 canônico, path, ranges,
  kind, texto) para T12/T13/T14; erros tipados sem fallback por tamanho/linhas
  (`EmptySourceError`, `BinarySourceError`, `GrammarUnavailableError`,
  `ParseFailureError`).
- Dependência de projeto `GitPython>=3.1` (DEC-015 / BR-023).
- Descoberta GitHub (T05): `GitHubRepoDiscovery` lista repositórios por org
  via token resolvido em T02, filtra por wildcards de inclusão (BR-022) e
  expõe `DiscoveredGitHubRepo` sem serializar o segredo (BDD-001/014/019).
- Porta mockável `GitHubApiClient` com iteração de repositórios via PyGithub.
- `LocalRepoDiscovery` (T06): expande URLs `file://` com glob em volumes montados,
  valida repositório Git e branch `main`, identifica origem `local` e registra
  issues por conexão/path sem abortar outras conexões (BDD-016, BDD-018).
- Camada `github_rag.sources.local` com `GitFilesystemInspector` injetável para
  testes; convenção de mount `/repos` documentada (ENG-005).
- Camada de persistência do catálogo (T03): domínio puro (`RepoState`,
  `RepoOrigin`, `FileStage`, máquina de estados fechada REQ-020), porta
  `CatalogRepository`, fake in-memory e adaptador PostgreSQL (SQLAlchemy 2.x +
  psycopg3) atrás da mesma interface.
- Schema versionado com Alembic (`migrations/`) para `catalog_repository`,
  `indexing_execution` e `file_processing`, com enums nativos PostgreSQL.
- Suporte a `last_processed_commit`/reconcile (ENG-011), progresso de
  indexação (REQ-021), etapas por arquivo idempotentes (REQ-022) e histórico
  de execuções com mensagem/horário de erro (REQ-023).
- Soft-delete de repositórios com retenção de histórico e lock otimista
  (`row_version`) para update concorrente.
- Configuração via `DATABASE_URL`, lida na fronteira `catalog` sem reabrir o
  contrato de bootstrap da T01.
- Testes de integração contra PostgreSQL real sob marcador `integration`
  (`pytest -m integration`), separados do run padrão.
- `WorkerLimiter` (T04) com semáforos isolados de indexação e consulta
  (`INDEX_WORKERS` / `QUERY_WORKERS`), fila quando o limite é atingido e
  rejeição explícita de capacidade `< 1`.
- T02 config-loader: `ConfigLoader`, `SecretResolver`, schema tipado
  (`AppConfig`, conexões `github`/`git`) — carga integral do JSON
  Sourcebot-like em `CONFIG_PATH`, resolução `{ "env": "..." }` sem
  vazamento de segredo, rejeição total sem cadastro parcial.
- Exemplo de configuração em `examples/config.json`.
- Fundação Python 3.12+ da T01 com layout `src/github_rag` e fronteiras de
  pacotes para as próximas tasks.
- Contrato de bootstrap `AppSettings`, `load_settings` e
  `SettingsBootstrapError`, sem lógica de domínio.
- Desenvolvimento local com `.venv` documentado para Windows PowerShell,
  Windows cmd, macOS e Linux.
- Harness pytest/pytest-cov com falha automática abaixo de 95% de cobertura.
- Testes unitários e BDD com cobertura ≥95% (inclui T11 com yaml/json/xml/toml,
  T12 SLM e T13 Qdrant/embeddings).
- Normalização cross-platform de EOL e ignores para `.venv`, cobertura,
  caches e `*.egg-info`.

### Documentado

- Docker/T19 como entrega padronizada, sem montar ou usar o `.venv` do host.
- Compatibilidade de desenvolvimento local Windows, macOS e Linux como
  plataformas de primeira classe.
