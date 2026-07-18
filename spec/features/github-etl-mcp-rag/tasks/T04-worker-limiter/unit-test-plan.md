# Unit test plan — T04-worker-limiter

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T04-worker-limiter` |
| Autor | Implementation Task Runner (QA step) |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Interfaces base | `APPROVED_BY_ARCHITECT` |
| Branch | `feature/github-etl-mcp-rag-T04-worker-limiter` |

## Objetivo

Cobrir contratos, extremos e corner cases do `WorkerLimiter` antes da
implementação completa (TDD: red → green).

## Arquivo de testes

`tests/unit/concurrency/test_worker_limiter.py`

## Matriz de casos

| ID | Cenário | Tipo | Expectativa |
|---|---|---|---|
| U-01 | `capacity` válido exposto | contrato | `limiter.capacity == n` |
| U-02 | `acquire` permite até `capacity` simultâneos | contrato | pico ≤ capacity |
| U-03 |  `(capacity+1)`-ésimo bloqueia até release | fila | waiter só entra após exit |
| U-04 | `capacity == 1` serializa | extremo | intervalos sem overlap |
| U-05 | rajada N=20, capacity=2 | corner | todos concluem; pico ≤ 2 |
| U-06 | exceção no CM libera slot | falha | próximo `acquire` ok |
| U-07 | `capacity == 0` | inválido | `WorkerLimiterError` |
| U-08 | `capacity == -5` | inválido | `WorkerLimiterError` |
| U-09 | factory index usa `index_workers` | contrato | capacity do settings |
| U-10 | factory query usa `query_workers` | contrato | capacity do settings |
| U-11 | factories produzem limiters isolados | isolamento | saturar index ≠ bloquear query |
| U-12 | settings com workers `0` via factory | inválido | `WorkerLimiterError` sem fallback |
| U-13 | `isinstance(impl, WorkerLimiter)` | contrato | Protocol runtime |
| U-14 | reentrada sequencial no mesmo thread | corner | dois acquires sequenciais ok |
| U-15 | mensagem de erro cita pool e valor | contrato | substrings pool + valor |
| U-16 | WL-04 inverso: query cheio não bloqueia index | isolamento | espelha SUGGESTION BDD |

## Demonstração red

Antes da implementação completa (stubs com `...`):

```bash
python -m pytest tests/unit/concurrency/test_worker_limiter.py -q
```

Falhas esperadas: `TypeError` / instância incompleta ao construir ou ao usar
`acquire`/`capacity` (stubs).

## Fora de escopo dos unitários

- Jobs reais, MCP, UI
- Reimplementar testes de tipagem de env (já T01); apenas fronteira factory
