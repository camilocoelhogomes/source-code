# Unit Test Plan — T04-run-e2e-robot

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T04-run-e2e-robot` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design / BDD / Interfaces | `0.1.0` / `0.1.0` / `0.1.0` |
| Natureza | Documental/operacional — sem `src/` novo; contrato `RobotGreenPathRun` |
| Suíte de aceite | `tests/bdd/test_mvp_e2e_audit_e2e_robot_run.py` (E2E-01..10) |
| Branch | `feature/mvp-e2e-audit-hardening-T04-run-e2e-robot` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Corners cobertos pelo BDD; unitários em `src/` desnecessários (D-T04-001); RED pré-artefato obrigatório. |

## 1. Estratégia

| Camada | Onde | Fronteira |
|---|---|---|
| Contrato documental (aceitação) | `tests/bdd/test_mvp_e2e_audit_e2e_robot_run.py` | Path real do resumo + guards de sanitização |
| Runtime Python em `src/` | **não aplicável** (sem mudança) | D-T04-001; T21 já testado no pai |
| Prova operacional Podman/Robot | Execução HITL do runner | Resultado materializado no artefato; **não** reexecutada nos asserts BDD |

Decisão (I-T04-003 / D-T04-001):

- Não há implementação nova em `src/github_rag/**` ⇒ **não** há testes unitários de produto a escrever.
- Unitários adicionais em `src/` são **explicitamente desnecessários**.
- BDD de contrato **não** sobe stack Podman (evita flakiness/CI pesado); a prova real é evidência operacional versionada.

## 2. Mapeamento corner cases → BDD

| ID | Corner case | Camada BDD | Como é coberto | Unitário `src/`? |
|---|---|---|---|---|
| C-01 | Artefato ausente | E2E-01 (+02..10 via `_read_artifact`) | `artefato ausente` | Não |
| C-02 | Metadados/comando incompletos | E2E-02 | ISO, branch, SHA, comando, Python, OS, Podman | Não |
| C-03 | Pré-condições HITL incompletas / token em claro | E2E-03 + E2E-09 | READY, `present=`, repo; `TOKEN_*_RE` | Não |
| C-04 | Exit code ausente | E2E-04 | Regex exit code numérico | Não |
| C-05 | Fases incompletas | E2E-05 | credential/compose/healthy/robot/down | Não |
| C-06 | Suítes green path / bdd015 ausentes | E2E-06 | 5 suítes + exclude | Não |
| C-07 | Falhas sem superfície / lista malformada | E2E-07 | ENG-006; lista vazia ok | Não |
| C-08 | Soft-dep T03 omitida / rebase implícito | E2E-08 | T03 + independente | Não |
| C-09 | Secrets no markdown | E2E-09 | prefix/assign regex | Não |
| C-10 | Expansão Robot / mudança produto implícita | E2E-10 | declarações de escopo | Não |
| C-11 | Exit ≠ 0 (stack/credencial/robot) | E2E-04/07 + run real | Evidência válida; alimenta T05 | Não |
| C-12 | `e2e/results/` não versionado | design §3.3 + gitignore | Resumo só boolean; não commitar results | Não |

**Pré-implementação:** C-01..C-10 em RED (artefato ausente).

## 3. Decisão sobre unitários auxiliares

| Opção | Avaliação | Escolha |
|---|---|---|
| A — Só BDD E2E-01..10 | Suficiente para contrato documental | **Escolhida** |
| B — `tests/unit/` parser markdown sintético | Pouco ganho além dos asserts no path real | Descartada |
| C — Testes novos em `src/` | Violaria D-T04-001 | Proibida |
| D — Reexecutar Robot nos pytest BDD | Flaky/lento; prova já é operacional HITL | Proibida |

## 4. Demonstração RED (pré-implementação)

```bash
.venv/bin/python -m pytest tests/bdd/test_mvp_e2e_audit_e2e_robot_run.py -q --no-cov
```

Estado esperado: **10 failed, 0 passed** (artefato ausente).

## 5. Fora de escopo

- Qualquer teste unitário novo sob `src/github_rag/**`.
- Corrigir falhas de produto/flakiness para “ficar verde”.
- Expandir `.robot` / browser.
- Abrir tasks no pai (T05).
- Reexecutar Podman dentro dos asserts BDD de contrato.
