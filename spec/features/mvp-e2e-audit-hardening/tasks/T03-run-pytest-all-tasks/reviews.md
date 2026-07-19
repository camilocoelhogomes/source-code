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
