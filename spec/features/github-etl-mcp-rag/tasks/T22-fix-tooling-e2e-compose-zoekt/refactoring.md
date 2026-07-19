# Refactoring Blue — T22-fix-tooling-e2e-compose-zoekt

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T22-fix-tooling-e2e-compose-zoekt` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Branch | `feature/github-etl-mcp-rag-T22-fix-tooling-e2e-compose-zoekt` |
| Superfície | manifesto/docs (+ helper só em `tests/support`) |

## 1. Baseline (pré-Blue)

| Métrica | Valor | Evidência |
|---|---|---|
| Subset T22 | **35 passed**, 16 subtests, **0.04s** | comando abaixo |
| Complexidade Python produção | Nenhuma (`src/` inalterado) | working tree T22 = composes + docs |
| Helper de teste | `tests/support/compose_manifest.py` (~207 LOC pré-Blue) | I-T22-007 |
| Gargalo de performance | Nenhum aplicável | asserts de texto/YAML; sem I/O runtime |

### Comando baseline

```bash
.venv/bin/python -m pytest \
  tests/bdd/test_e2e_compose_zoekt_fix.py \
  tests/unit/delivery/test_zoekt_compose_manifest.py \
  tests/unit/delivery/test_manifest.py \
  -q --tb=line --no-cov
# → 35 passed, 16 subtests passed in 0.04s
```

## 2. Metas Blue

| Meta | Critério | Resultado |
|---|---|---|
| Sem mudança de comportamento / contratos | BDD EZ-* + UT-Z* + `test_manifest` verdes | OK |
| Sem alterar composes/docs de produção | Diff Blue só em helper de teste (se houver) | OK |
| Simplificação | Só complexidade desnecessária com evidência | **Blue mínima** (código morto) |
| Performance | Só com baseline reproduzível antes/depois | **N/A** — sem hot path |

## 3. Análise de simplificação

| Candidato | Decisão | Evidência |
|---|---|---|
| Simplificação estrutural dos 3 composes / docs | **N/A** | YAML/markdown já mínimos (D-T22-001/002/004); alterar seria cosmético ou risco de contrato |
| Unificar parsers BDD ↔ unit helper | Rejeitado | BDD mantém asserts independentes; unificar alteraria superfície sem ganho de contrato |
| Fundir `service_block` / `zoekt_command_blob` / `parse_command_argv` | Rejeitado | Separação I-T22-007 (responsabilidade + motivo) |
| `canonical_argv_present` não usado | **Removido** | só definição; nenhum import/assert; SUGGESTION residual da review unitária |

### Mudança Blue aplicada

- Arquivo: `tests/support/compose_manifest.py`
- Remoção de `canonical_argv_present` + import `typing.Sequence` (mortos)
- Asserts / contratos / composes / docs: **inalterados**

## 4. Baseline pós-Blue

```text
.venv/bin/python -m pytest \
  tests/bdd/test_e2e_compose_zoekt_fix.py \
  tests/unit/delivery/test_zoekt_compose_manifest.py \
  tests/unit/delivery/test_manifest.py \
  -q --tb=line --no-cov
# → 35 passed, 16 subtests passed in 0.04s
```

Comparação performance before/after: **N/A** (mesma contagem; sem meta de latência).

## 5. Decisão

`BLUE_APPROVED_BY_ARCHITECT` — simplificação estrutural de produção **N/A**; Blue mínima no helper de teste (remoção de API morta); subset T22 estável em **35 passed / 16 subtests / 0.04s**.

## 6. Evidência de cobertura (gate pós-Blue / docs)

| Métrica | Valor | Critério |
|---|---|---|
| Suite completa | **1215 passed**, **2 skipped** | regressão |
| Cobertura TOTAL | **96.53%** | ≥95% (obrigatório) |

Evidência registrada no gate `ARCHITECT_DOCS` (`approvals.md` / `reviews.md`), 2026-07-19.
