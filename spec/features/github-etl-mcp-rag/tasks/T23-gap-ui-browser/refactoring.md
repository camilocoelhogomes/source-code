# Refactoring Blue — T23-gap-ui-browser

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T23-gap-ui-browser` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Branch | `feature/github-etl-mcp-rag-T23-gap-ui-browser` |
| Superfície | Robot e2e (`browser.resource`, `ui_browser.robot`) |

## 1. Baseline (pré-Blue)

| Métrica | Valor | Evidência |
|---|---|---|
| Subset T23 (Camada A) | **35 passed**, 8 subtests, **0.04s** | comando abaixo |
| Suite global | **1250 passed**, 2 skipped | `pytest tests/` |
| Cobertura TOTAL | **96.53%** | ≥95% |
| Gargalo de performance | Nenhum aplicável | manifesto texto/fs; Robot browser fora do gate pytest |

### Comando baseline

```bash
.venv/bin/python -m pytest \
  tests/bdd/test_ui_browser_gap.py \
  tests/unit/e2e/test_ui_browser_manifest.py \
  -q --tb=line --no-cov
# → 35 passed, 8 subtests passed in 0.04s
```

## 2. Metas Blue

| Meta | Critério | Resultado |
|---|---|---|
| Sem mudança de comportamento / contratos | UB-01..09/18 + UT-UB + green path | OK |
| Sem alterar `GREEN_PATH_SUITES` / deps / fixture | Diff Blue só Robot helpers/cases | OK |
| Simplificação | Só complexidade/código morto com evidência | OK |
| Performance | Só com baseline reproduzível antes/depois | **N/A** — nenhuma otimização necessária |

## 3. Análise de simplificação

| Candidato | Decisão | Evidência |
|---|---|---|
| `Library Collections` sem uso | **Removido** | nenhum keyword Collections no resource |
| Asserts duplicados case×keyword (019/007/009/010) | **Removidos** | keywords já cobrem; seletores canônicos UB-18 preservados na suite |
| Assert BDD-007 só `Detalhe` + flags | **Reforçado** | regexp de `state_label` PT (`app.js` emite etapa em `#repo-detail`) |
| Unificar `${GITHUB_INCLUSION_PATTERN}` com loader de fixture | Rejeitado | risco de acoplamento; espelho documentado (SUGGESTION residual) |
| Fundir `ui_browser.robot` em `ui.robot` | Rejeitado | D-T23-003 / I-T23-002 |
| Otimização Playwright / poll timings | **N/A** | sem medição de hot path; fora do gate unitário |

### Mudança Blue aplicada

- `e2e/robot/resources/browser.resource`: remove `Collections`; `Assert Repo Detail Progress And Flags` exige etapa PT.
- `e2e/robot/ui_browser.robot`: remove redundâncias 019/007/009/010 mantendo seletores canônicos.
- Contratos manifesto / deps / `suite.py` / fixture: **inalterados**.

## 4. Baseline pós-Blue

```text
.venv/bin/python -m pytest \
  tests/bdd/test_ui_browser_gap.py \
  tests/unit/e2e/test_ui_browser_manifest.py \
  -q --tb=line --no-cov
# → 35 passed, 8 subtests passed in 0.04s
```

Comparação performance before/after: **N/A** (mesma contagem; nenhuma otimização necessária).

## 5. Decisão

`BLUE_APPROVED_BY_ARCHITECT` — Blue mínima em artefatos Robot; performance N/A; subset T23 estável em **35 passed / 8 subtests / 0.04s**; suite global **1250 passed**, cobertura **96.53%**.

## 6. Evidência de cobertura (gate pós-Blue)

| Métrica | Valor | Critério |
|---|---|---|
| Suite completa | **1250 passed**, **2 skipped** | regressão |
| Cobertura TOTAL | **96.53%** | ≥95% (obrigatório) |
