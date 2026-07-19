# Refactoring Blue — T17-mcp-evidence-server

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T17-mcp-evidence-server` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Pipeline | autonomous |
| Natureza | **no-op Blue** |

## 1. Baseline

| Métrica | Valor |
|---|---|
| Suíte T17 | `66 passed` (BDD + unit `tests/unit/mcp/`) |
| Cobertura `github_rag.mcp` | **98.87%** (branch; ≥95%) |
| Comando | `.venv/bin/python -m pytest tests/bdd/test_mcp_evidence_server.py tests/unit/mcp/ -q --override-ini='addopts=--import-mode=importlib' --cov=github_rag.mcp --cov-branch --cov-fail-under=95` |
| Data baseline | 2026-07-18 |

Detalhe por módulo (baseline):

| Módulo | Cover |
|---|---|
| `__init__` / `errors` / `fake` / `ports` / `server` / `tools` | 100% |
| `serialize` | 95% (ramo dict aninhado parcial) |
| **TOTAL** | **98.87%** |

## 2. Metas Blue

| Meta | Critério de aceite |
|---|---|
| Preservar contratos I-T17-* | Sem mudança de assinaturas/tools/JSON |
| Preservar comportamento | 66 passed idêntico |
| Cobertura | `github_rag.mcp` ≥95% |
| Performance | Só alterar se houver gargalo com comparação before/after reproduzível |

## 3. Análise Blue

| Item | Achado | Ação |
|---|---|---|
| Complexidade desnecessária | Não — superfície fina: serialize / errors / register_tools / `_EvidenceFastMCP` (necessário para I-T17-012) | Nenhuma |
| Alias `query_svc = query` | Necessário: parâmetro `query` de `semantic_search` sombrearia o `QueryService` injetado | Manter |
| Gargalo de performance | Nenhum mensurável — I/O/CPU está nas portas injetadas (T16/T07/T04), não no envelope MCP | Sem otimização especulativa |
| DRY speculative (factory de handlers) | Aumentaria indireção sem evidência de custo/bug | Rejeitado |

## 4. Mudanças aplicadas

Nenhuma (no-op Blue). Developer dispensado.

## 5. Comparação antes/depois

| | Antes | Depois |
|---|---|---|
| Testes | 66 passed | 66 passed |
| Cov `github_rag.mcp` | 98.87% | 98.87% |
| Contratos | I-T17-* | preservados |
| Diff produção | — | vazio |
| Performance | N/A (sem gargalo) | N/A |

## 6. Decisão Architect

| Decisão | Status | Autor | Data |
|---|---|---|---|
| `BLUE_APPROVED_BY_ARCHITECT` | aprovado | tech-lead-architect | 2026-07-18 |

Motivo: código já alinhado a design/interfaces; sem complexidade desnecessária nem gargalo comprovável; refatoração especulativa rejeitada.
