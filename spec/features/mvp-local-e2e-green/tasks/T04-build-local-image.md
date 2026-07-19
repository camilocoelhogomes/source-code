# Task T04 — build-local-image

| Campo | Valor |
|---|---|
| Task ID | `T04-build-local-image` |
| Feature | `mvp-local-e2e-green` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W4 |
| Plano | v0.1.0 |

## Objetivo

Produzir imagem local pré-buildada `github-rag:local` (`linux/amd64`) e garantir que `docker-compose.yml` end-user referencia `image:` em vez de `build:` como caminho padrão de subida.

## Escopo

### Build explícito (REQ-006, REQ-021–022, BDD-005)

```bash
docker build --platform linux/amd64 -t github-rag:local .
# equivalente Podman: podman build --platform linux/amd64 -t github-rag:local .
```

- Verificar tag local presente e entrypoint `python -m github_rag.delivery`.
- Rebuild após merges de T03 que alterem código containerizado (BR-007).
- Documentar comando em runbook/`e2e/README.md` ou `docs/runbook-local.md` se ausente.

### Delta compose end-user (REQ-007, REQ-023–024, BDD-006)

- Ownership manifesto: **T19** no pai — entregar via task pai **`T28-container-delivery-compose-local-image`** (criar em T02 se inexistente) ou implementação no pipeline autônomo acionada por T03.
- Alteração alvo `docker-compose.yml` serviço `app`:
  - `image: github-rag:local`
  - Remover `build:` do fluxo padrão ou restringir a override opcional documentado
  - Manter `platform: linux/amd64`, healthcheck, volumes (ENG-009: sem `.venv` host)
- **Não** alterar `docker-compose.e2e.yml` (e2e canônico Podman) nem `docker-compose.dev.yml`.
- Validar: `docker compose up -d` **sem** `--build` sobe `app` e `GET /healthz` OK quando imagem existe.

## Fora de escopo

- Corrigir falhas Robot de produto (tasks pai T22–T28+).
- Merge automático de PRs (T05).
- Publicação GHCR / CI release.
- Hot-reload dev compose.

## Dependências

- **Dura:** T03 (código mergeável ou PRs prontos para merge antes de rebuild final).
- Consumo: T19 (`Dockerfile`, composes), task pai T28 (delta compose).

## Critérios de aceite

- Imagem `github-rag:local` existe localmente `linux/amd64` (BDD-005).
- `docker-compose.yml` referencia `image: github-rag:local`; `compose up -d` sem rebuild funciona (BDD-006, REQ-024).
- Compatível com `docker-compose.e2e.yml` e `docker-compose.dev.yml` (REQ-025).
- Rebuild documentado como explícito apenas (DEC-007).

## Arquivos prováveis

- `Dockerfile` (consumo)
- `docker-compose.yml` (delta via T28 pai)
- `docs/runbook-local.md` ou `e2e/README.md` (comando build)
- `spec/features/github-etl-mcp-rag/tasks/T28-container-delivery-compose-local-image.md`
- `spec/features/mvp-local-e2e-green/runs/local-image-build-YYYYMMDD.md`

## Rastreabilidade

- REQ-006, REQ-007, REQ-021–025; DEC-006, DEC-007; BR-007; BDD-005, BDD-006.

## Handoff

- Imagem + compose validados → T05 (`verify-and-auto-merge`).
