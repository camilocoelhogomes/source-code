# Task T01 — project-foundation

| Campo | Valor |
|---|---|
| Task ID | `T01-project-foundation` |
| Feature | `github-etl-mcp-rag` |
| Estado | `IMPLEMENTATION_COMPLETE_AWAITING_DOCUMENTATION_HITL` |
| Onda | W0 |

## Objetivo

Criar a base do repositório de aplicação: layout de pacotes, **ambiente virtual Python (`venv`) como padrão para dependências locais de desenvolvimento**, toolchain de testes com cobertura ≥ 95%, convenções de env e estrutura para o implementation-pipeline.

## Escopo

- Estrutura de pacotes Python 3.12+ alinhada aos módulos do plano.
- **`venv` obrigatório para desenvolvimento local:** criar, ativar e instalar dependências apenas dentro do ambiente virtual (não instalar no Python do sistema como fluxo padrão).
- Documentação/comandos claros no README de desenvolvimento para:
  - criar o venv (ex.: `python3.12 -m venv .venv`);
  - ativar o venv;
  - instalar dependências a partir de `pyproject.toml` / `requirements*.txt` **no venv**;
  - executar testes/cobertura **com o venv ativo**.
- Incluir `.venv/` (ou diretório escolhido) em ignore do Git.
- Ferramenta de testes (ex.: pytest) + cobertura configurada (falha abaixo de 95%).
- Skeleton de settings por variáveis de ambiente (`CONFIG_PATH`, workers, DB, etc.) sem lógica de negócio.
- README mínimo de desenvolvimento local (sem delivery container completo — isso é T19).
- **Alinhamento com containers:** o `venv` é o padrão de **dev local**; a imagem de container (T19) instala dependências no runtime da imagem e **não** depende do `.venv` do host. Os dois fluxos coexistem sem contradição.

## Fora de escopo

- Parser de config, PostgreSQL, Zoekt, UI, MCP, indexação.
- Dockerfile/compose completos (T19).

## Dependências

- Nenhuma.

## Critérios de aceite

- Existe `venv` documentado como padrão; comandos de criação, ativação, install e testes estão no README de desenvolvimento.
- Dependências de desenvolvimento são instaladas e resolvidas **dentro do venv** (pacote/`site-packages` do ambiente virtual).
- Suite de testes executável no CI/local com relatório de cobertura (CI pode recriar o venv ou equivalente isolado).
- Cobertura mínima do projeto configurada em 95%.
- Layout de módulos espelha fronteiras do `implementation-plan.md`.
- Nenhuma lógica de domínio além de placeholders/settings.
- Documentação deixa explícito que delivery por containers (T19) não usa o `.venv` do host.

## Arquivos prováveis

- `pyproject.toml` / `requirements*.txt`
- `.venv/` (local; gitignored)
- `.gitignore` (entrada `.venv/`)
- `src/...` (pacotes vazios ou mínimos)
- `tests/`
- `pytest.ini` ou equivalente
- `.coveragerc` / config de coverage
- `README.md` (dev, com seção venv)

## Rastreabilidade

- Restrição: cobertura 95%; REQ-007 (base local); ENG-001 / ENG-009 (venv + containers).

## Handoff

- Feature: `github-etl-mcp-rag`
- Task: `T01-project-foundation`
- Próximas: `T02`, `T03`, `T04` em paralelo após conclusão.
- Interfaces esperadas: apenas bootstrap; portas de domínio nas tasks seguintes.
- Definição de pronto: harness verde + cobertura + **venv documentado e usável** + layout aprovado no pipeline.
