# Task T02 — config-loader

| Campo | Valor |
|---|---|
| Task ID | `T02-config-loader` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W1 |

## Objetivo

Carregar e validar integralmente o JSON apontado por `CONFIG_PATH` no padrão Sourcebot (`connections`), sem aplicar configuração parcial.

## Escopo

- `ConfigLoader` + schema de conexões `github` e `git`.
- Resolução de token via `{ "env": "VAR" }` sem embutir segredo no JSON.
- Wildcards de inclusão no campo `repos` (somente inclusão).
- URLs `file://` com glob em conexões locais.
- Erros explícitos: path ausente, JSON inválido, tipo desconhecido, `env` inexistente — sem cadastro parcial.
- Garantir que valores de segredo não vazem em mensagens de erro.

## Fora de escopo

- Chamadas GitHub; varredura de disco; persistência PostgreSQL; UI.

## Dependências

- `T01-project-foundation`

## Critérios de aceite

- BDD-021 e BDD-022 cobertos por testes BDD da task.
- Config válida produz modelo tipado de conexões.
- Config inválida rejeita 100% e não retorna conexões parciais.
- Token nunca aparece em exceções/logs gerados pelo loader.

## Arquivos prováveis

- `src/.../config/loader.py`
- `src/.../config/schema.py`
- `src/.../config/secrets.py`
- `tests/bdd/...`
- `tests/unit/config/...`
- Exemplos em `examples/config.json` (opcional)

## Rastreabilidade

- REQ-009, REQ-039–042; BR-016–021; DEC-012; BDD-021, BDD-022; BDD-014 (parcial).

## Handoff

- Interfaces: `ConfigLoader`, `SecretResolver`.
- Consumidores: `T05`, `T06`.
- Risco: schema deve permanecer estável — mudanças quebram descoberta.
