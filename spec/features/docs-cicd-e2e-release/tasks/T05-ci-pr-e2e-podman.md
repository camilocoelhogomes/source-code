# Task T05 — ci-pr-e2e-podman

| Campo | Valor |
|---|---|
| Task ID | `T05-ci-pr-e2e-podman` |
| Feature | `docs-cicd-e2e-release` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W2 |
| Plano | v0.2.0 |

## Objetivo

Integrar no gate de PR a subida da stack e2e com Podman e a **invocação da suíte Robot de T21**, **somente após** os testes unitários do projeto e os BDD estarem verdes, tornando o check e2e obrigatório para merge na `main`, sem publish nem bump.

## Escopo

- Estender `.github/workflows/ci-pr.yml`: o job `e2e` **depende** dos jobs `unit` e `bdd` verdes (ENG-007 / REQ-012); **não** inicia e2e se unitários ou BDD falharam ou foram skipped por falha anterior.
- Após unit/BDD verdes, job `e2e`:
  1. preparar Podman em `ubuntu-latest` (ENG-008);
  2. subir stack com `docker-compose.e2e.yml` (T19);
  3. injetar `E2E_GITHUB_TOKEN` e env necessários sem echo do segredo (contrato T21 / REQ-049);
  4. **invocar** a suíte Robot de T21 via contrato T04 (`T21SuiteInvoker`) — sem suíte duplicada;
  5. teardown da stack (sempre que possível).
- Nomes de checks estáveis para branch protection: `unit`, `bdd`, `e2e` (ENG-011); os três são required.
- Documentar checklist de required checks + secret `E2E_GITHUB_TOKEN` para o mantenedor (HITL no GitHub).
- PR continua sem GHCR publish e sem alteração de versão (BDD-002).

## Fora de escopo

- Criar suíte Robot (ownership = T21).
- Workflow de release (T06).
- Ownership/reescrita dos composes T19 (ajustes mínimos só se inevitáveis e justificados).
- Habilitar branch protection na UI do GitHub (handoff humano).

## Dependências

- `T01-ci-pr-unit-bdd`
- `T04-consume-t21-e2e`
- **Dura:** `github-etl-mcp-rag` / `T19-container-delivery`
- **Dura:** `github-etl-mcp-rag` / `T21-mvp-e2e-robot`

## Critérios de aceite

- **Pré-condição obrigatória:** o job e2e só executa depois que os **testes unitários do projeto** e os testes BDD passaram no mesmo workflow de PR (REQ-012, ENG-007).
- Com unitários ou BDD vermelhos, e2e **não** sobe stack / não invoca Robot (short-circuit), e o merge permanece bloqueado.
- Falha em unit, BDD ou e2e (suíte T21) falha o required check correspondente e bloqueia merge (BDD-001, BDD-004).
- Stack e2e sobe com Podman e a esteira executa a suíte T21 (BDD-003).
- PR bem-sucedido não publica release nem altera `pyproject.toml` (BDD-002).
- Secret ausente → e2e falha de forma explícita.
- Nenhuma segunda suíte Robot sob esta feature (BDD-009).

## Arquivos prováveis

- `.github/workflows/ci-pr.yml`
- `.github/SECRETS.md` ou seção em `docs/contributing` (pode ficar em T07; no mínimo checklist no handoff)

## Rastreabilidade

- REQ-001–002, REQ-007, REQ-012–014, REQ-017; BR-001–002, BR-006, BR-009; ENG-001, ENG-007, ENG-008, ENG-011; BDD-001–004, BDD-009.

## Handoff

- Contrato: `PrQualityGate` completo + `E2eStackLauncher` + `T21SuiteInvoker` no CI.
- Mantenedor: marcar required checks `unit`/`bdd`/`e2e` e configurar `E2E_GITHUB_TOKEN`.
- Rollback: remover job e2e (quebra BR-001 até restaurar).
