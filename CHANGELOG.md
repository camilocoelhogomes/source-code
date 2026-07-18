# Changelog

Todas as mudanças relevantes do projeto são registradas neste arquivo.

## [Unreleased]

### Adicionado

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

