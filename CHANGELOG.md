# Changelog

Todas as mudanças relevantes do projeto são registradas neste arquivo.

## [Unreleased]

### Adicionado

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
- Testes unitários e BDD da T03: 137 testes aprovados (1 pulado sem Docker),
  92 subtests, cobertura de 98.71%.
- Fundação Python 3.12+ da T01 com layout `src/github_rag` e fronteiras de
  pacotes para as próximas tasks.
- Contrato de bootstrap `AppSettings`, `load_settings` e
  `SettingsBootstrapError`, sem lógica de domínio.
- Desenvolvimento local com `.venv` documentado para Windows PowerShell,
  Windows cmd, macOS e Linux.
- Harness pytest/pytest-cov com falha automática abaixo de 95% de cobertura.
- Testes unitários e BDD: 37 testes aprovados, cobertura de 100%.
- Normalização cross-platform de EOL e ignores para `.venv`, cobertura,
  caches e `*.egg-info`.

### Documentado

- Docker/T19 como entrega padronizada, sem montar ou usar o `.venv` do host.
- Compatibilidade de desenvolvimento local Windows, macOS e Linux como
  plataformas de primeira classe.

