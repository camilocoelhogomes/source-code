# Task T06 — release-semver-ghcr

| Campo | Valor |
|---|---|
| Task ID | `T06-release-semver-ghcr` |
| Feature | `docs-cicd-e2e-release` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W1 |
| Plano | v0.2.0 |

## Objetivo

Após merge na `main`, versionar automaticamente via Conventional Commits (fallback patch), atualizar `pyproject.toml` e publicar a imagem no GHCR com tags `latest` e a versão semver.

## Escopo

- Workflow `.github/workflows/release.yml` em `push` para `main` (ENG-001); **não** dispara em PR.
- `SemverBumper` (ENG-003–004):
  - intervalo desde última tag (ou baseline documentada);
  - `fix` → patch; `feat` → minor; `BREAKING CHANGE` / `!` → major; sem prefixo aplicável → patch (BDD-008);
  - escrever versão em `pyproject.toml` (SoT);
  - commit bot + tag git `vX.Y.Z`.
- `GhcrPublisher`: build via Dockerfile T19; push `ghcr.io/<owner>/<repo>` com `latest` e `X.Y.Z` (BR-005).
- Permissões: `contents: write`, `packages: write`.
- Falha de build/push = falha observável; não reportar sucesso com tag parcial enganosa.
- Garantir que `docker-compose.yml` (T19) permanece utilizável apontando para a imagem pública (BDD-006) — ajuste mínimo só se o compose ainda não referenciar GHCR corretamente (justificar; ownership continua T19).
- Não alterar código de domínio; não criar suíte Robot.

## Fora de escopo

- Gate de PR / invocação Robot (T01/T04/T05).
- Assinatura de imagem, SBOM, provenance avançada.
- Self-hosted runners.
- Declaração de MVP entregue (gate T19+T21 em `github-etl-mcp-rag`).

## Dependências

- **Dura:** `github-etl-mcp-rag` / `T19-container-delivery` (Dockerfile + compose de usuário apontando para imagem pública).
- Independente de T04/T05 no DAG (paralelo em W1 após T19); em operação, merges na `main` devem já passar pelo gate quando T05 estiver ativo (que por sua vez exige T21).

## Critérios de aceite

- Merge elegível bumpa `pyproject.toml` conforme Conventional Commits (BDD-005).
- Sem Conventional Commits aplicáveis → patch (BDD-008).
- Imagem publicada com `latest` + versão (BDD-005).
- Compose de usuário consome a imagem pública de forma documentada (BDD-006).
- Workflow de PR (T01/T05) permanece sem publish.

## Arquivos prováveis

- `.github/workflows/release.yml`
- Script auxiliar de bump (ex.: `scripts/bump_version.py`) se necessário
- `pyproject.toml` (apenas via automação de release em runtime; não bump manual na task de implementação além do necessário para tooling)

## Rastreabilidade

- REQ-003, REQ-015–017; BR-003–005; ENG-001, ENG-003, ENG-004, ENG-009; BDD-005, BDD-006, BDD-008.

## Handoff

- Contratos: `SemverBumper`, `GhcrPublisher`.
- Configurar visibilidade pública do pacote GHCR se necessário (HITL).
- Rollback: reverter commit de bump; não promover `latest` falho.
