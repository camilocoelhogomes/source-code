# Changelog

Todas as mudanças relevantes do projeto são registradas neste arquivo.

## [Unreleased]

### Alterado

- Descoberta local (T20 / DT-001): `GitFilesystemInspector.inspect_repo` passa a
  usar **GitPython** (`git.Repo`) em vez de parse ad-hoc de `.git` / refs /
  `packed-refs` (BR-023, DEC-015). Contrato `LocalRepoDiscovery` e BDD-016/018
  preservados; bare continua rejeitado; runtime requer pacote GitPython e
  binário `git` no PATH.

### Adicionado

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
- Chunking semântico Tree-sitter (T11): porta `ContextualChunker` e
  implementação `TreeSitterContextualChunker` com grammars oficiais
  (`tree-sitter` + python/java/javascript/typescript/markdown) — única fonte
  de chunks RAG (DEC-003/015; BDD-007/024).
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
- Testes unitários e BDD: 416 testes aprovados (1 pulado sem Docker),
  161 subtests, cobertura de 98.57% (T01–T08 + T07/T20 na main; T11 na branch).
- Normalização cross-platform de EOL e ignores para `.venv`, cobertura,
  caches e `*.egg-info`.

### Documentado

- Docker/T19 como entrega padronizada, sem montar ou usar o `.venv` do host.
- Compatibilidade de desenvolvimento local Windows, macOS e Linux como
  plataformas de primeira classe.
