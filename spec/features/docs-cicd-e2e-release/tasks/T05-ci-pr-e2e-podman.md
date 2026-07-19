# Task T05 — ci-pr-e2e-podman

| Campo | Valor |
|---|---|
| Task ID | `T05-ci-pr-e2e-podman` |
| Feature | `docs-cicd-e2e-release` |
| Estado | `PENDING_PO_REVIEW` |
| Onda | W2 |

## Objetivo

Integrar no gate de PR a subida da stack e2e com Podman e a execução da suíte Robot, tornando o check e2e obrigatório para merge na `main`, sem publish nem bump.

## Escopo

- Estender `.github/workflows/ci-pr.yml`: após unit/BDD verdes (ENG-007), job `e2e`:
  1. preparar Podman em `ubuntu-latest` (ENG-008);
  2. subir stack com `docker-compose.e2e.yml` (T19);
  3. injetar `E2E_GITHUB_TOKEN` e env necessários sem echo do segredo;
  4. executar Robot (`T04`);
  5. teardown da stack (sempre que possível).
- Nomes de checks estáveis para branch protection: `unit`, `bdd`, `e2e` (ENG-011).
- Documentar checklist de required checks + secret `E2E_GITHUB_TOKEN` para o mantenedor (HITL no GitHub).
- PR continua sem GHCR publish e sem alteração de versão (BDD-002).

## Fora de escopo

- Workflow de release (T06).
- Ownership/reescrita dos composes T19 (ajustes mínimos só se inevitáveis e justificados).
- Habilitar branch protection na UI do GitHub (handoff humano; artefato documenta o que marcar).

## Dependências

- `T01-ci-pr-unit-bdd`
- `T04-robot-e2e-suite`
- **Dura:** `github-etl-mcp-rag` / `T19-container-delivery`

## Critérios de aceite

- Falha em unit, BDD ou e2e falha o required check e bloqueia merge (BDD-001).
- Stack e2e sobe com Podman e Robot alcança serviços (BDD-003).
- PR bem-sucedido não publica release nem altera `pyproject.toml` (BDD-002).
- Secret ausente → e2e falha de forma explícita.

## Arquivos prováveis

- `.github/workflows/ci-pr.yml`
- `.github/SECRETS.md` ou seção em `docs/contributing` (pode ficar em T07; no mínimo checklist no handoff)

## Rastreabilidade

- REQ-002, REQ-007, REQ-012–014, REQ-017; BR-001–002, BR-006; ENG-001, ENG-007, ENG-008, ENG-011; BDD-001, BDD-002, BDD-003.

## Handoff

- Contrato: `PrQualityGate` completo + `E2eStackLauncher` no CI.
- Mantenedor: marcar required checks `unit`/`bdd`/`e2e` e configurar `E2E_GITHUB_TOKEN`.
- Rollback: remover job e2e (quebra BR-001 até restaurar).
