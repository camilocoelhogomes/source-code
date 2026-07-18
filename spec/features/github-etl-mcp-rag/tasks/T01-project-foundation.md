# Task T01 — project-foundation

| Campo | Valor |
|---|---|
| Task ID | `T01-project-foundation` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W0 |

## Objetivo

Criar a base do repositório de aplicação: layout de pacotes, toolchain de testes com relatório de cobertura ≥ 95%, convenções de env e estrutura para o implementation-pipeline.

## Escopo

- Estrutura de pacotes Python 3.12+ alinhada aos módulos do plano.
- Ferramenta de testes (ex.: pytest) + cobertura configurada (falha abaixo de 95%).
- Skeleton de settings por variáveis de ambiente (`CONFIG_PATH`, workers, DB, etc.) sem lógica de negócio.
- README mínimo de desenvolvimento local (sem delivery container completo — isso é T19).

## Fora de escopo

- Parser de config, PostgreSQL, Zoekt, UI, MCP, indexação.

## Dependências

- Nenhuma.

## Critérios de aceite

- Suite de testes executável no CI/local com relatório de cobertura.
- Cobertura mínima do projeto configurada em 95%.
- Layout de módulos espelha fronteiras do `implementation-plan.md`.
- Nenhuma lógica de domínio além de placeholders/settings.

## Arquivos prováveis

- `pyproject.toml` / `requirements*.txt`
- `src/...` (pacotes vazios ou mínimos)
- `tests/`
- `pytest.ini` ou equivalente
- `.coveragerc` / config de coverage
- `README.md` (dev)

## Rastreabilidade

- Restrição: cobertura 95%; REQ-007 (base local).

## Handoff

- Feature: `github-etl-mcp-rag`
- Task: `T01-project-foundation`
- Próximas: `T02`, `T03`, `T04` em paralelo após conclusão.
- Interfaces esperadas: apenas bootstrap; portas de domínio nas tasks seguintes.
- Definição de pronto: harness verde + cobertura configurada + layout aprovado no pipeline.
