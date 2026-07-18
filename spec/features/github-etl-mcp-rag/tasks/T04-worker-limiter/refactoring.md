# Refatoração Blue — T04-worker-limiter

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T04-worker-limiter` |
| Data | 2026-07-18 |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Branch | `feature/github-etl-mcp-rag-T04-worker-limiter` |
| Implementação base | `APPROVED_BY_ARCHITECT` |

## Baseline (pré-Blue)

| Métrica | Valor |
|---|---|
| Suite | `python -m pytest -q` → 64 passed, 36 subtests |
| Cobertura | 100% (TOTAL 84 stmts) |
| Arquivo alvo | `src/github_rag/concurrency/limiter.py` |

## Objetivos Blue (sem mudança de comportamento)

1. Eliminar closure `@contextmanager` recriada a cada `acquire()` (SUGGESTION Architect).
2. Remover atributo `self._pool` não lido após construção (SUGGESTION Architect).
3. Não alterar contratos públicos nem testes.

## Mudanças aplicadas

| Mudança | Antes | Depois |
|---|---|---|
| `acquire` | nested `@contextmanager` dentro do método | método decorado com `@contextmanager` |
| `self._pool` | armazenado e nunca lido | removido; `pool` só em validação |

## Resultados (pós-Blue)

| Métrica | Valor |
|---|---|
| Suite | `python -m pytest -q` → 64 passed, 36 subtests |
| Cobertura | 100% (TOTAL 81 stmts; `limiter.py` 35 stmts) |
| Comportamento | idêntico (mesmos testes verdes) |
| Simplificação | -3 stmts no módulo (`limiter.py` 38→35) |

## Fora de escopo Blue

- Wrapper asyncio
- Máximos de workers / Dockerfile
- Consumidores T14/T17
