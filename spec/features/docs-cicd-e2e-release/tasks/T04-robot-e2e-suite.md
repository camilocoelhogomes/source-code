# Task T04 — robot-e2e-suite

| Campo | Valor |
|---|---|
| Task ID | `T04-robot-e2e-suite` |
| Feature | `docs-cicd-e2e-release` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W1 |

## Objetivo

Introduzir suíte Robot Framework que trava fluxos observáveis do MVP sobre a stack e2e (Podman + `docker-compose.e2e.yml`), com GitHub real e este repositório como referência.

## Escopo

- Layout `e2e/robot/` com suítes por superfície (ENG-005): health, catalog/indexing, ui, mcp.
- Resources compartilhados: base URLs da stack, auth via env (`E2E_GITHUB_TOKEN`), repo de referência = este.
- Cobrir BDD-001–024 do MVP **na medida automatizável** via UI, MCP, healthchecks e efeitos de indexação/busca.
- **Excluir** validação narrativa BDD-015 (Cursor Discovery) — ENG-006.
- Dependências de Robot em tooling (optional-deps / requirements e2e), sem alterar domínio.
- Política de timeout/retry alinhada a ENG-010 (documentada na suíte/README e2e).
- Não logar o token em keywords, logs ou artefatos.
- Consumir `docker-compose.e2e.yml` de T19; não reivindicar ownership.

## Fora de escopo

- Workflow GitHub Actions (T05).
- Release/GHCR (T06).
- Mock da API GitHub.
- Reescrita dos composes/Dockerfile.

## Dependências

- **Dura:** `github-etl-mcp-rag` / `T19-container-delivery` (compose e2e + imagem/build + testes passando; REQ-006).

## Critérios de aceite

- Com stack e2e no ar (Podman + compose T19) e token válido, a suíte Robot valida fluxos MVP observáveis (BDD-003, BDD-004).
- Regressão nesses fluxos falha a suíte.
- Token ausente/inválido → falha explícita.
- BDD-015 não é critério automatizado da suíte.
- Sem alteração de código de domínio nem de `spec/` (exceto artefatos desta feature).

## Arquivos prováveis

- `e2e/robot/**/*.robot`
- `e2e/robot/resources/*.resource`
- `e2e/README.md` (como rodar localmente)
- `pyproject.toml` (optional-deps e2e) ou `requirements-e2e.txt`

## Rastreabilidade

- REQ-001, REQ-006–011; BR-006–007, BR-009; ENG-005, ENG-006, ENG-010; BDD-003, BDD-004.

## Handoff

- Contrato: `RobotE2eSuite` + uso de `E2eStackLauncher` (T05 no CI).
- T05 integra na esteira; T07 documenta execução local.
- Rollback: remover suíte; CI e2e deixa de existir até T05.
