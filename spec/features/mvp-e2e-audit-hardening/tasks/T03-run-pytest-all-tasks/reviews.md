# Reviews — T03-run-pytest-all-tasks

## Review Design — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Versão revisada | `0.1.0` → `0.1.1` |
| Data | 2026-07-18 |
| Branch | `feature/mvp-e2e-audit-hardening-T03-run-pytest-all-tasks` |
| Base | `main` @ `086f3b3` |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| Alinhamento `ParentPytestRun` / ENG-003 / BDD-004 | OK — executar `tests/`, registrar, não corrigir produto |
| Soft-dep T01 não bloqueia | OK — §1, §3.3 item 7, §7 |
| Artefato em `runs/` sem secrets (ENG-002 / BR-004) | OK — §3.3, §6, §8 |
| Sem mudança `src/**` / `e2e/robot/**` / `pyproject.toml` | OK — D-T03-001, §14 |
| Superfícies ENG-006 para handoff T05 | OK — heurística §3.3 |
| Run-first (não expandir suíte / não fix produto) | OK — §2, §15 |
| Fora de escopo T04/T05/T06 | OK — §15 |

### Achados

| ID | Severidade | Evidência | Achado | Correção esperada | Status |
|---|---|---|---|---|---|
| M-01 | `MAJOR` | `design.md` v0.1.0 §3.5/§14 vs handoff T05 | Testes de contrato da feature filha em `tests/bdd/test_mvp_e2e_audit_pytest_run.py` poderiam ser tratados como falhas do pai na lista para T05 | D-T03-002: excluir nodeids da filha da lista T05; contrato só valida estrutura/sanitização do resumo; ordem run → artefato → asserts | Corrigido em `0.1.1` §3.4.1, §5, §7, §13 |
| M-02 | `MAJOR` | `design.md` v0.1.0 §3.4/§7; `pyproject.toml` `fail_under = 95` | Exit ≠ 0 só por gate de cobertura sem nodeids falhos poderia ser mapeado como falha de produto | Registrar `coverage_gate`; lista de falhas do pai vazia nesse caso | Corrigido em `0.1.1` §3.3 item 4, §3.4, §5, §7 |
| S-01 | `SUGGESTION` | `design.md` v0.1.0 §3.3 item 2 vs §3.4 | Comando canônico citado de duas formas | Unificar no comando de §3.4 | Corrigido em `0.1.1` |

### Bloqueios abertos

Nenhum `BLOCKING` / `MAJOR` aberto após `0.1.1`.

### Decisão

`APPROVED_BY_ARCHITECT` — design `0.1.1` apto para BDD/interfaces (contrato documental `ParentPytestRun`). Gate humano intermediário substituído pela aprovação Architect (modo autonomous-implementation-orchestrator).

---

## Review BDD — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `tests/bdd/test_mvp_e2e_audit_pytest_run.py` |
| Versão revisada | `0.1.0` → `0.1.1` |
| Data | 2026-07-18 |
| Branch | `feature/mvp-e2e-audit-hardening-T03-run-pytest-all-tasks` |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| PYTEST-01 path canônico `runs/pytest-all-tasks.md` | OK |
| PYTEST-02 metadados + comando canônico §3.4 | OK |
| PYTEST-03 exit + contagens | OK |
| PYTEST-04 cobertura / `coverage_gate` (D-T03 / M-02) | OK — campo sempre no contrato |
| PYTEST-05 falhas pai: nodeid, tipo, mensagem, superfície ENG-006 | OK após M-01 |
| PYTEST-06 soft-dep T01 | OK |
| PYTEST-07 sem secrets (BR-004) | OK |
| PYTEST-08 D-T03-002 exclui `mvp_e2e_audit_*` | OK |
| PYTEST-09 D-T03-001 sem mudança produto/src/robot | OK |
| Sem exigir fix de produto | OK |
| RED pré-artefato | OK — 9 failed / 0 passed (`artefato ausente`) |

### Achados

| ID | Severidade | Evidência | Achado | Correção esperada | Status |
|---|---|---|---|---|---|
| M-01 | `MAJOR` | `test_mvp_e2e_audit_pytest_run.py` PYTEST-05; `bdd.md` PYTEST-05 | BDD exige mensagem sanitizada nas entradas; teste não assertava | Assert `mensagem`/`message`/`msg` quando há entradas | Corrigido no teste |
| S-01 | `SUGGESTION` | `bdd.md` PYTEST-04 vs teste | “quando aplicável” vs campo sempre exigido no teste | Alinhar BDD: `coverage_gate` sempre `true\|false\|N/A` | Corrigido em `bdd.md` 0.1.1 |

### Bloqueios abertos

Nenhum.

### Evidência RED (Architect)

```text
9 failed in 0.06s — artefato ausente (razão esperada)
comando: python -m pytest tests/bdd/test_mvp_e2e_audit_pytest_run.py -q --no-cov
```

### Decisão

`APPROVED_BY_ARCHITECT` — BDD v0.1.1 apto para gate de interfaces (contrato documental `ParentPytestRun`). Gate humano intermediário substituído pela aprovação Architect (modo autonomous).
