# Task T07 — docs-contributing-en

| Campo | Valor |
|---|---|
| Task ID | `T07-docs-contributing-en` |
| Feature | `docs-cicd-e2e-release` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W2 |

## Objetivo

Documentar em inglês a área de contribuidores (`docs/contributing` ou equivalente): Podman, compose de desenvolvimento, testes unitários/BDD e e2e Robot, alinhada aos comandos reais da esteira.

## Escopo

- Criar `docs/contributing.md` (ou `docs/contributing/`) em inglês.
- Incluir: setup local com Podman; `docker-compose.dev.yml` (T19); venv + unitários/BDD; como subir e2e e rodar Robot (T04); secrets locais necessários (sem valores reais); referência aos required checks do PR.
- Migrar do README o hub de desenvolvimento (REQ-021), deixando README só com link.
- Linkar a partir de `docs/` (T03) e README (T02).
- Não alterar `spec/`.

## Fora de escopo

- Implementar workflows ou suíte Robot (já T01/T04/T05).
- Ownership dos composes T19.

## Dependências

- `T01-ci-pr-unit-bdd` (comandos/checks unit/BDD)
- `T04-robot-e2e-suite` (comandos e2e reais)
- Soft: `T05-ci-pr-e2e-podman` (nomes finais dos jobs/checks)
- Soft: `T02`, `T03` (links cruzados)

## Critérios de aceite

- Contribuidor consegue seguir `docs/contributing` para Podman, testes e e2e (BDD-007 / métricas de sucesso).
- Instruções de desenvolvimento não são o foco principal do README.
- Podman documentado como runtime da stack containerizada para contribuidores (BR-006).
- `spec/` intocado.

## Arquivos prováveis

- `docs/contributing.md` ou `docs/contributing/**`
- Ajustes de links em `README.md` / `docs/README.md`

## Rastreabilidade

- REQ-011, REQ-020–022; BR-006, BR-010; ENG-008, ENG-012; BDD-007.

## Handoff

- Feature pronta para PO/humano validar docs ponta a ponta com T02/T03.
- Rollback: reverter docs de contributing.
