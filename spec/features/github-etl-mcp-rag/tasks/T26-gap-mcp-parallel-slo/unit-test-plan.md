# Unit test plan — T26-gap-mcp-parallel-slo

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T26-gap-mcp-parallel-slo` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Arquivos | `tests/unit/concurrency/test_parallel_slo.py`; extensão `tests/unit/concurrency/test_worker_limiter.py`; `tests/unit/e2e/test_mcp_parallel_keywords.py` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | UT-S*/UT-L*/UT-K*; RED esperado pré-impl. |

## Contratos / extremos

| ID | Caso | Entrada | Esperado | Interface |
|---|---|---|---|---|
| UT-S01 | min_waves básico | n=8,c=4 | 2 | I-T26-002 |
| UT-S02 | min_waves resto | n=5,c=2 | 3 | I-T26-002 |
| UT-S03 | min_waves inválido | n=0 ou c=0 | ValueError | I-T26-002 |
| UT-S04 | SLO aceita 2 ondas | wall=2,single=1,n=8,c=4 | ok | I-T26-003 |
| UT-S05 | SLO rejeita serial | wall=8,single=1,n=8,c=4 | not ok | I-T26-003 |
| UT-S06 | SLO rejeita ilimitado | wall=1,single=1,n=8,c=4 | not ok | I-T26-003 |
| UT-S07 | single<=0 | single=0 | not ok | I-T26-003 |
| UT-S08 | capacity inválida | c=0 | not ok | I-T26-003 |
| UT-S09 | n_calls==capacity>1 paralelismo | n=c=2,wall≈single | ok se wall < 2*single*tol | I-T26-003 |
| UT-L01 | peak_active sob saturação | c=2,N=4 block | peak<=2 | I-T26-001 |
| UT-L02 | waiting sob saturação | c=1 + waiter | waiting>=1 | I-T26-001 |
| UT-L03 | active zero após release | pós-join | active=0,waiting=0 | I-T26-001 |
| UT-L04 | exceção libera slot + contadores | raise no with | active=0; próximo acquire ok | I-T26-001 |
| UT-K01 | parallel keyword shape | mock call | keys results/wall/n_calls | I-T26-004 |
| UT-K02 | assert_parallel_slo falha | serial wall | AssertionError | I-T26-006 |
| UT-K03 | measure_single samples | mock times | mediana | I-T26-005 |
| UT-K04 | robot mcp.robot sem smoke sequencial | AST/texto | usa Parallel + Assert Slo | I-T26-007 |

## Corner / concorrência

- UT-L01/L02 sob ThreadPool.
- UT-S05 garante denylist anti-falso-verde.

## RED pré-implementação

```bash
python -m pytest tests/bdd/test_mcp_parallel_slo.py tests/unit/concurrency/test_parallel_slo.py tests/unit/e2e/test_mcp_parallel_keywords.py -q --tb=line
```

Esperado: ImportError/`AttributeError`/`peak_active` ausente / robot ainda sequencial.
