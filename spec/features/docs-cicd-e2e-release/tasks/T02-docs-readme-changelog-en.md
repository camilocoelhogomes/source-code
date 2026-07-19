# Task T02 — docs-readme-changelog-en

| Campo | Valor |
|---|---|
| Task ID | `T02-docs-readme-changelog-en` |
| Feature | `docs-cicd-e2e-release` |
| Estado | `PENDING_PO_REVIEW` |
| Onda | W0 |

## Objetivo

Entregar `README.md` e `CHANGELOG.md` em inglês, com README orientado ao usuário final (imagem GHCR, compose de usuário, variáveis essenciais, uso básico UI/MCP).

## Escopo

- Traduzir/reescrever `README.md` em inglês como página de usuário final (REQ-019).
- Traduzir/reescrever `CHANGELOG.md` em inglês.
- Migrar conteúdo de desenvolvimento (venv, pytest, etc.) para fora do foco do README — destino `docs/contributing` (T07); README pode apontar link curto.
- Descrever obtenção da imagem pública `ghcr.io/<owner>/<repo>`, uso de `docker-compose.yml` (T19) e variáveis essenciais **sem** embutir secrets.
- Não alterar `spec/`.

## Fora de escopo

- Pasta `docs/` completa de produto (T03) e contributing detalhado (T07).
- Workflows, Robot, release.
- Reescrita dos composes T19.

## Dependências

- Nenhuma task desta feature (pode usar nomes de imagem/compose já decididos nos requisitos).
- Soft: alinhamento final com tags GHCR após T06.

## Critérios de aceite

- README e CHANGELOG em inglês (BDD-007).
- README orientado a usuário final, não hub principal de setup de dev (REQ-021).
- Sem tokens/credenciais commitados.
- `spec/` intocado por esta task.

## Arquivos prováveis

- `README.md`
- `CHANGELOG.md`

## Rastreabilidade

- REQ-004, REQ-018–019, REQ-021–022; BR-010; ENG-012; BDD-007.

## Handoff

- Link para `docs/` / contributing a ser completado em T03/T07.
- Rollback: reverter arquivos de docs.
