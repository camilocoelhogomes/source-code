# Task T04 — consume-t21-e2e

| Campo | Valor |
|---|---|
| Task ID | `T04-consume-t21-e2e` |
| Feature | `docs-cicd-e2e-release` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W1 |
| Plano | v0.2.0 |
| Substitui | `T04-robot-e2e-suite` (plano 0.1.x — ownership de criação da suíte; **obsoleto**) |

## Objetivo

Estabelecer o contrato de **consumo/invocação** da suíte Robot Framework entregue por `github-etl-mcp-rag` / **T21** sobre a stack e2e (Podman + `docker-compose.e2e.yml` de T19), sem criar suíte paralela.

## Escopo

- Documentar e fixar o entrypoint de invocação da suíte T21 (path canônico, comando, env necessários).
- Wiring mínimo de tooling **somente** para invocar T21 na máquina/CI (scripts ou steps reutilizáveis) — **proibido** adicionar `*.robot` / resources novos sob ownership desta feature (BR-011, BDD-009).
- Validar que a suíte T21 é alcançável com as vars/secrets do contrato MVP (`E2E_GITHUB_TOKEN` → `GITHUB_TOKEN` no container; REQ-009).
- Alinhar timeout/retry ao contrato T21 (ENG-010).
- Consumir `docker-compose.e2e.yml` de T19; não reivindicar ownership dos composes nem da suíte.
- Smoke de consumo (quando aplicável no pipeline da task): falha explícita se suíte T21 ausente ou entrypoint inválido.

## Fora de escopo

- Criar ou ser dona da suíte Robot (ownership = T21).
- Workflow GitHub Actions completo do job e2e (T05).
- Release/GHCR (T06).
- Mock da API GitHub.
- Reescrita dos composes/Dockerfile.

## Dependências

- **Dura:** `github-etl-mcp-rag` / `T19-container-delivery` (compose e2e + imagem/build + testes passando).
- **Dura:** `github-etl-mcp-rag` / `T21-mvp-e2e-robot` (suíte Robot entregue e verde na prova MVP).

## Critérios de aceite

- Existe contrato estável `T21SuiteInvoker` + uso de stack T19 documentado para T05/T07 (BDD-003 parcial).
- Invocação aponta exclusivamente para a suíte T21; não há segunda árvore Robot nesta feature (BDD-009).
- Token ausente/inválido na invocação → falha explícita (alinhado a BDD-004 / contrato T21).
- Sem alteração de código de domínio nem de `spec/` (exceto artefatos desta feature).

## Arquivos prováveis

- Script/step de invocação (ex.: `scripts/run-e2e-robot.sh` ou documentação de comando canônico em `e2e/` **sem** novos `.robot`)
- Referência em handoff para T05/T07
- Ajustes mínimos de tooling CI se necessários para chamar T21

## Rastreabilidade

- REQ-001, REQ-005–011; BR-006–007, BR-009, BR-011; DEC-007, DEC-009; ENG-005, ENG-010; BDD-003 (parcial), BDD-004, BDD-009.

## Handoff

- T05 integra a invocação no workflow de PR; T07 documenta execução local apontando T21.
- Rollback: remover wiring de consumo; CI e2e deixa de invocar até T05 restaurar.
