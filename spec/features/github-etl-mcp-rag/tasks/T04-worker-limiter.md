# Task T04 — worker-limiter

| Campo | Valor |
|---|---|
| Task ID | `T04-worker-limiter` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W1 |

## Objetivo

Implementar limitação de paralelismo de indexação e de consulta via variáveis de ambiente.

## Escopo

- `WorkerLimiter` (ou dois limiters: index/query) lendo env.
- Defaults de engenharia: `INDEX_WORKERS=2`, `QUERY_WORKERS=4`.
- Fila/espera quando o limite é atingido (excedentes aguardam capacidade).
- Isolamento para uso por orquestrador e por MCP/query.

## Fora de escopo

- Jobs de indexação reais; tools MCP; UI.

## Dependências

- `T01-project-foundation`

## Critérios de aceite

- Paralelismo nunca excede o limite configurado.
- Tarefas excedentes aguardam e depois executam.
- Valores inválidos de env tratados de forma explícita (rejeitar ou fallback documentado nos testes).
- Cobertura de corner cases: limite 1, rajadas, cancelamento/liberação de slot.

## Arquivos prováveis

- `src/.../concurrency/limiter.py`
- `src/.../concurrency/settings.py`
- `tests/unit/concurrency/...`

## Rastreabilidade

- REQ-004, REQ-037; BR-006; BDD-002, BDD-013.

## Handoff

- Interface: `WorkerLimiter`.
- Consumidores: `T14`, `T17` (e query se aplicável).
