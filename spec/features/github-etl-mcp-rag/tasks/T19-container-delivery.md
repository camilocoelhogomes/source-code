# Task T19 — container-delivery

| Campo | Valor |
|---|---|
| Task ID | `T19-container-delivery` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W8 |
| Plano | v0.1.7 |

## Objetivo

Empacotar o produto em imagem e **três** composes para uso local padronizado: `CONFIG_PATH`, secrets por env, volumes de repos locais, UI e MCP disponíveis, com **reconcile de indexação no startup** do container. Fechar o escopo de container da PR #19 **sem** prova Robot/e2e real.

## Escopo

- `Dockerfile` (build da imagem do produto) e instalação das **deps/SDKs** das tasks (PyGithub, GitPython, pathspec, tree-sitter + grammars, qdrant-client, openai, APScheduler, mcp, FastAPI, SQLAlchemy/Alembic/psycopg3, etc.) — sem omitir T20/GitPython.
- Três arquivos compose com testes de manifesto passando (REQ-043, BDD-025):
  - `docker-compose.yml` — usuário final / imagem pública;
  - `docker-compose.e2e.yml` — stack e2e (consumida por T21 e pela esteira);
  - `docker-compose.dev.yml` — desenvolvimento.
- `.env.example` com **somente** nomes/valores não secretos (REQ-048–049); documentar vars canônicas mínimas.
- Runbook local de empacotamento (docs/runbook ou seção equivalente).
- Montagem de volumes para JSON e `file:///repos/...` (ENG-005).
- Imagem primária `linux/amd64` (ENG-006).
- Healthchecks básicos para UI e MCP.
- **Boot do container (ENG-011):** após config válida + sync de catálogo, disparar validate/reconcile de indexação (tip `main` × PostgreSQL) e enfileirar repos que não estejam `atualizado` — via `IndexingOrchestrator` / startup reconcile (T14). Não inventar estados.
- Gate de testes: BDD/unitários de delivery com doubles/manifestos — **sem** `compose up` real obrigatório e **sem** Robot (REQ-044, DEC-017).

## Fora de escopo

- Suíte Robot Framework e prova e2e em stack real (ownership = **T21**).
- Declaração de “MVP entregue” (exige T19 **e** T21 verdes).
- Esteira GitHub Actions, docs EN, release GHCR (`docs-cicd-e2e-release`).
- Novas features de domínio; registro corporativo obrigatório.

## Dependências

- `T17-mcp-evidence-server`, `T18-management-ui`, `T20-refactor-local-discovery-git-sdk` (BDD-024 / DT-001 fechada na entrega; na prática T14 já integrado na app empacotada)

## Critérios de aceite

- BDD-020; smoke de BDD-021/022 no boot do container (doubles/manifesto ok).
- BDD-025: existem `Dockerfile`, os **3** composes e `.env.example` sem segredos; testes de manifesto/delivery passam.
- Com `CONFIG_PATH`, secrets e volumes corretos (cenário de manifesto/boot), UI e MCP sobem **e** o reconcile de startup é disparado.
- Config inválida falha de forma observável sem aplicar parcial.
- PR #19 permanece no escopo **container** (REQ-050 / BDD-028); não inclui Robot.

## Arquivos prováveis

- `Dockerfile`
- `docker-compose.yml`
- `docker-compose.e2e.yml`
- `docker-compose.dev.yml`
- `.env.example`
- `docs/runbook-local.md` ou seção no README
- `examples/config.json`
- testes de manifesto/delivery existentes sob `tests/bdd/` / módulo `delivery`

## Rastreabilidade

- REQ-036–038, REQ-043–044, REQ-050; DEC-011–012, DEC-015, DEC-017; BR-023–025; BDD-020–022, BDD-024–025, BDD-028 (parte T19); ENG-011, ENG-017.

## Handoff

- Entrega de empacotamento; **não** fecha sozinha o MVP.
- Handoff para **T21** (compose e2e estável) e para `docs-cicd-e2e-release` (consumo dos 3 composes).
- Rollback: não publicar/usar a tag; volumes locais descartáveis.
