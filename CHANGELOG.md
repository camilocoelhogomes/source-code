# Changelog

Todas as mudanças relevantes do projeto são registradas neste arquivo.

## [Unreleased]

### Adicionado

- Sync do catálogo (T07): `CatalogSync` orquestra discovery GitHub + local →
  upsert/`deactivate` no `CatalogRepository`; `run_catalog_sync` no bootstrap
  sem indexação nem reconcile (handoff ENG-011 → T14). Origem/conexão no
  catálogo ativo (BDD-001/016/021/023); ausência = soft-delete sem estado
  extra fora de REQ-020.
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
- Testes unitários e BDD: 335 testes aprovados (1 pulado sem Docker),
  161 subtests, cobertura de 97.99% (T01–T07).
- Normalização cross-platform de EOL e ignores para `.venv`, cobertura,
  caches e `*.egg-info`.

### Documentado

- Docker/T19 como entrega padronizada, sem montar ou usar o `.venv` do host.
- Compatibilidade de desenvolvimento local Windows, macOS e Linux como
  plataformas de primeira classe.
