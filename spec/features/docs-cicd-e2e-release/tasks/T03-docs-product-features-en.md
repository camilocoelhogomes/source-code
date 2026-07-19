# Task T03 — docs-product-features-en

| Campo | Valor |
|---|---|
| Task ID | `T03-docs-product-features-en` |
| Feature | `docs-cicd-e2e-release` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W0 |
| Plano | v0.2.0 |

## Objetivo

Criar documentação em inglês em `docs/` cobrindo as features do produto (MVP), com índice navegável a partir do README.

## Escopo

- Criar `docs/` em inglês documentando capacidades do produto alinhadas ao MVP (`github-etl-mcp-rag`): discovery, indexação, UI, MCP, config, containers de usuário.
- Incluir índice (`docs/README.md` ou equivalente) linkado pelo README de usuário.
- Linguagem de usuário/operador; não copiar `spec/` nem mover artefatos de spec.
- Não alterar `spec/`.

## Fora de escopo

- Seção completa de contribuidores / Podman / e2e T21 (T07).
- CI/CD e criação de suíte Robot.
- Alterar código de domínio.

## Dependências

- Soft: T02 (links mútuos README ↔ docs); pode paralelizar com T02.

## Critérios de aceite

- Existe `docs/` em inglês com features do produto (BDD-007 / REQ-020 parcial).
- README (T02) pode apontar para essa área sem depender de conteúdo de desenvolvimento.
- `spec/` intocado.

## Arquivos prováveis

- `docs/README.md`
- `docs/*.md` (features do produto)

## Rastreabilidade

- REQ-004, REQ-020; BR-010; ENG-012; BDD-007.

## Handoff

- T07 adiciona contributing (incl. e2e T21).
- Rollback: reverter `docs/` de produto.
