# Task T01 — ci-pr-unit-bdd

| Campo | Valor |
|---|---|
| Task ID | `T01-ci-pr-unit-bdd` |
| Feature | `docs-cicd-e2e-release` |
| Estado | `PENDING_PO_REVIEW` |
| Onda | W0 |

## Objetivo

Criar o workflow de CI de PR que executa testes unitários e BDD em `ubuntu-latest`, sem publicar imagem nem alterar versão, estabelecendo os jobs/checks estáveis do gate.

## Escopo

- Workflow `.github/workflows/ci-pr.yml` disparado em `pull_request` contra `main`.
- Jobs (nomes estáveis, ENG-011): pelo menos `unit` e `bdd` (ou equivalentes documentados).
- Instalar deps de teste (venv/pip conforme projeto) e rodar a suíte existente com cobertura (fail_under 95% do projeto).
- Garantir que o workflow de PR **não** faz push GHCR nem edita `pyproject.toml` version.
- Documentar no handoff os nomes exatos dos checks para branch protection (completo após T05).

## Fora de escopo

- Job e2e / Podman / Robot (T05).
- Workflow de release (T06).
- Alterar código de domínio ou `spec/` (exceto artefatos desta feature).
- Ownership dos composes T19.

## Dependências

- Nenhuma task desta feature.
- Pré-existente: suíte unit/BDD do repositório executável localmente.

## Critérios de aceite

- PR contra `main` dispara CI com unitários e BDD.
- Falha em unit ou BDD falha o check correspondente (base de BDD-001).
- Sucesso do workflow de PR não publica GHCR nem altera versão (BDD-002).
- Cobertura mínima do projeto permanece configurada (≥ 95%).

## Arquivos prováveis

- `.github/workflows/ci-pr.yml`
- Ajustes mínimos em `pyproject.toml` optional-deps / cache de CI se necessário (sem bump de versão de produto)

## Rastreabilidade

- REQ-002, REQ-012 (parcial), REQ-014; BR-001–002; ENG-001, ENG-007, ENG-011; BDD-001 (parcial), BDD-002.

## Handoff

- Contratos: `PrQualityGate` (fase unit/BDD).
- Próximas: T05 adiciona e2e; T07 referencia comandos de teste.
- Rollback: remover/reverter o workflow.
