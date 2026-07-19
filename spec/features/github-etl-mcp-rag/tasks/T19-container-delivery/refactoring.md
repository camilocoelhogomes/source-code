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

## 4. Gate Blue

| Decisão | Autor | Data |
|---|---|---|
| `BLUE_APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 |
