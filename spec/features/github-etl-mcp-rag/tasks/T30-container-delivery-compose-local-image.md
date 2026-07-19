# Task T30 — container-delivery-compose-local-image

| Campo | Valor |
|---|---|
| Task ID | `T30-container-delivery-compose-local-image` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Superfície | `container-delivery` |
| Origem | `mvp-local-e2e-green` REQ-006/007, T04 |
| Evidência | `spec/features/mvp-local-e2e-green/requirements.md` BDD-005/006 |

## Classificação

| ID | Classificação | Motivo |
|---|---|---|
| REQ-006/007 | `produto` | Compose end-user rebuild implícito; falta imagem local taggeada |

## Objetivo

Entregar imagem local `github-rag:local` (`linux/amd64`) e alterar `docker-compose.yml` para `image:` sem `build:` padrão.

## Escopo

- Tag canônica `github-rag:local`; build explícito documentado.
- `docker-compose.yml` serviço `app`: `image: github-rag:local`; remover/evitar rebuild silencioso.
- Manter compatibilidade com `docker-compose.e2e.yml` e `docker-compose.dev.yml`.
- Script ou doc de rebuild pós-merge (BR-007).

## Critérios de aceite

- `docker build --platform linux/amd64 -t github-rag:local .` produz imagem com entrypoint delivery.
- `docker compose up -d` (sem `--build`) sobe app com imagem local; `/healthz` OK.
- Testes delivery/manifesto conforme T19.

## Dependências

- **Soft:** Robot verde (T28/T29 + gaps) antes de declarar MVP local entregue; implementação pode paralelizar após T29.
