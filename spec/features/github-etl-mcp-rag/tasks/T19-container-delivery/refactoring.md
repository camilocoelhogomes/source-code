# Refactoring Blue — T19-container-delivery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T19-container-delivery` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Baseline commit / working tree | pós-correção Architect (binds produção) |

## 1. Baseline

| Métrica | Valor | Evidência |
|---|---|---|
| Suites | unit `delivery` + BDD CD + regressão global | `pytest -q` → **1010 passed**, 1 skipped |
| Cobertura global | **96.38%** (≥95%) | `pytest --cov=github_rag` |
| Complexidade observada | Composition root fino (`runtime` orquestra; `wiring` factories; `health` probe) | layout I-T19 / D-T19-001 |
| Gargalo de performance | Nenhum comprovado no path de entrega (I/O real é Docker/infra) | sem benchmark aplicável além de asserts de manifesto |

### Comando baseline

```bash
cd /private/tmp/github_rag_T19
PYTHONPATH=src python -m pytest -q --cov=github_rag --cov-report=term-missing:skip-covered
```

## 2. Metas Blue

| Meta | Critério | Resultado |
|---|---|---|
| Sem mudança de comportamento / contratos | BDD CD-01..10 + unit UT-* verdes | OK |
| Simplificação | Remover só complexidade desnecessária com evidência | **N/A** — estrutura já mínima |
| Performance | Só com baseline reproduzível antes/depois | **N/A** — sem gargalo medido |

## 3. Análise de simplificação

| Candidato | Decisão | Evidência |
|---|---|---|
| Fundir `wiring.py` em `runtime.py` | Rejeitado | Viola I-T19-008 (helpers isolados do orquestrador) |
| Remover `ports.py` | Rejeitado | Protocol `ContainerRuntime` exigido CD-10 / I-T19-002 |
| Unificar binds UI/MCP num único helper | Rejeitado | D-T19-007 (SSE vs stdio) e injeção CD-04 |
| Path produção (thread MCP + drain) | Mantido | Correção BLOCKING da review de implementação; necessário para uvicorn/mcp bloqueantes |

**Conclusão:** nenhuma refatoração Blue adicional — o pacote já é composition root sem domínio; a única mudança pós-implementação foi correção funcional (não cosméticas).

## 4. Gate Blue (0.1.x — código delivery)

| Decisão | Autor | Data |
|---|---|---|
| `BLUE_APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 |

## 5. Baseline pós-delta 0.2.0 (três composes)

| Campo | Valor |
|---|---|
| Escopo Blue | Manifestos `docker-compose.yml` / `.e2e.yml` / `.dev.yml` + `.env.example` / docs |
| Código Python `delivery` | Inalterado neste delta |
| Suites | **1021 passed**, 2 skipped |
| Cobertura global | **96.59%** (≥95%) |
| Gargalo / complexidade | Nenhum comprovado — YAML declarativo; papéis D-T19-020 já mínimos |
| Refatoração aplicada | **N/A** — nada a simplificar sem alterar contratos de manifesto |

### Comando baseline (pós-delta)

```bash
cd /private/tmp/github_rag_T19
PYTHONPATH=src python -m pytest -q --cov=github_rag --cov-report=term-missing:skip-covered
# → 1021 passed, 2 skipped; Total coverage: 96.59%
```

### Metas Blue 0.2.0

| Meta | Critério | Resultado |
|---|---|---|
| Sem mudança de comportamento / contratos | CD-11 + UT-M07/08/09 + regressão | OK |
| Simplificação manifesto | Só com evidência de complexidade desnecessária | **N/A** |
| Performance | Só com baseline reproduzível | **N/A** — sem I/O runtime no gate T19 |

### Gate Blue 0.2.0

| Decisão | Autor | Data |
|---|---|---|
| `BLUE_APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 |
