# Task T21 — mvp-e2e-robot

| Campo | Valor |
|---|---|
| Task ID | `T21-mvp-e2e-robot` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W9 |
| Plano | v0.1.7 |

## Objetivo

Entregar a suíte **Robot Framework** que prova o MVP em stack real: **Podman** + `docker-compose.e2e.yml` (T19) + GitHub real (este repositório), validando BDD-001–024 **observáveis** em runtime. O MVP só pode ser declarado entregue com T19 **e** esta task verdes.

## Escopo

- Layout estável da suíte (sugestão ENG-019): `e2e/robot/` com suítes por superfície (`health`, `catalog_indexing`, `ui`, `mcp`) e resources compartilhados (base URLs, auth via env).
- Runtime obrigatório: **Podman** (REQ-051, BR-029); stack via `docker-compose.e2e.yml` de T19.
- Repositório de referência da integração GitHub: **este próprio repositório** (REQ-046, BR-027).
- Cobrir BDD-001–024 do MVP na medida automatizável via UI, MCP, healthchecks e efeitos de indexação/busca (DEC-019, BDD-026).
- **Excluir** BDD-015 (narrativa Discovery no Cursor) — validação humana fora do Robot.
- Credenciais (REQ-048–049, BR-028, DEC-020, BDD-027):
  - local HITL: operador exporta vars ou usa `.env` **local não versionado**;
  - CI: secret `E2E_GITHUB_TOKEN` injetado no container como `GITHUB_TOKEN` (não usar o `GITHUB_TOKEN` default do Actions como substituto);
  - proibido commit de `.env` com segredos; não logar token em keywords/artefatos.
- Dependências Robot em tooling (optional-deps / requirements e2e), sem alterar domínio de produto.
- Política de timeout/retry (rate-limit GitHub) documentada na suíte.
- Nova PR (não expandir PR #19 de T19) — REQ-050, DEC-017, BDD-028.
- Entregar contrato reutilizável para `docs-cicd-e2e-release` invocar a mesma suíte (sem ownership transferida).

## Fora de escopo

- Ownership/reescrita dos 3 composes e Dockerfile (T19), exceto consumo.
- Esteira GitHub Actions, docs EN, release GHCR (`docs-cicd-e2e-release`).
- Mock da API GitHub.
- Automatizar BDD-015.
- Novas features de domínio.

## Dependências

- **Dura:** `T19-container-delivery` (especialmente `docker-compose.e2e.yml` + imagem/build com testes de delivery passando).

## Critérios de aceite

- Com Podman, compose e2e no ar e credenciais válidas (HITL local e/ou `E2E_GITHUB_TOKEN`), a suíte Robot passa nos fluxos observáveis BDD-001–024 (BDD-026).
- Token ausente/inválido → falha explícita; MVP não entregue.
- Stack que não sobe → falha explícita; MVP não entregue.
- Regressão em fluxo observável → Robot falha; MVP não entregue.
- BDD-015 não é critério automatizado.
- Nenhum segredo versionado (BDD-027).
- Ownership Robot permanece nesta task; `docs-cicd-e2e-release` apenas consome (BDD-028, BR-030).
- T19+T21 verdes = condição necessária para declarar MVP entregue (REQ-047, BR-026).

## Arquivos prováveis

- `e2e/robot/**/*.robot`
- `e2e/robot/resources/*.resource`
- `e2e/README.md` (como rodar localmente com Podman)
- `pyproject.toml` (optional-deps e2e) ou `requirements-e2e.txt`
- fixtures/config e2e de exemplo **sem** tokens reais

## Rastreabilidade

- REQ-045–052; BR-025–030; DEC-017–021; ENG-018–020; BDD-026–028; exercita BDD-001–024 observáveis (exceto BDD-015).

## Handoff

- Contratos: `E2eStackLauncher`, `RobotMvpSuite`.
- Consumidor: `docs-cicd-e2e-release` (T04/T05) invoca a mesma suíte na esteira.
- Rollback: reverter PR/suíte; MVP deixa de estar entregue até restaurar.
