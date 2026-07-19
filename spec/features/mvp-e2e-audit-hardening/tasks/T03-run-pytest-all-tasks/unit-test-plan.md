# Unit Test Plan — T03-run-pytest-all-tasks

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T03-run-pytest-all-tasks` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `PENDING_ARCHITECT_REVIEW` |
| Versão | `0.1.0` |
| Design / BDD / Interfaces | `0.1.1` / `0.1.1` / `0.1.0` |
| Natureza | Documental — sem `src/`; contrato `ParentPytestRun` |
| Suíte de aceite | `tests/bdd/test_mvp_e2e_audit_pytest_run.py` (PYTEST-01..09) |
| Branch | `feature/mvp-e2e-audit-hardening-T03-run-pytest-all-tasks` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `PENDING_ARCHITECT_REVIEW` | `0.1.0` | Corners cobertos pelo BDD; unitários em `src/` desnecessários (D-T03-001). |

## 1. Estratégia

| Camada | Onde | Fronteira |
|---|---|---|
| Contrato documental (aceitação) | `tests/bdd/test_mvp_e2e_audit_pytest_run.py` | Path real do resumo + guards de sanitização |
| Runtime Python em `src/` | **não aplicável** | D-T03-001: zero módulo de produto |
| Helpers `tests/unit/` de parsing puro | **não necessários nesta task** | BDD já cobre corners sem reexecutar suíte pai |

Decisão (I-T03-003 / D-T03-001):

- Não há implementação em `src/github_rag/**` ⇒ **não** há testes unitários de produto a escrever.
- Unitários adicionais em `src/` são **explicitamente desnecessários**.
- Helpers opcionais em `tests/unit/` (regex/parsing sintético) **não agregam valor** além do que PYTEST-07/`TOKEN_*_RE` e os asserts de conteúdo já exercitam; não serão criados nesta task.

## 2. Mapeamento corner cases → BDD existente

| ID | Corner case | Camada BDD | Como é coberto | Unitário `src/`? |
|---|---|---|---|---|
| C-01 | Artefato ausente | PYTEST-01 (+02..09 via `_read_artifact`) | `AssertionError: artefato ausente` | Não |
| C-02 | Metadados incompletos / comando errado | PYTEST-02 | ISO, SHA, comando canônico, python, OS | Não |
| C-03 | Agregados ausentes | PYTEST-03 | exit + passed/failed/skipped/errors/total | Não |
| C-04 | Cobertura / coverage_gate ausente | PYTEST-04 | % ou N/A + `coverage_gate` true/false | Não |
| C-05 | Falha sem superfície / superfície inválida | PYTEST-05 | SURFACES + nodeid/tipo/mensagem | Não |
| C-06 | Soft-dep T01 omitida | PYTEST-06 | nota inventário / sem depender | Não |
| C-07 | Secrets no markdown | PYTEST-07 | `TOKEN_PREFIX_RE` / `TOKEN_ASSIGN_RE` | Não |
| C-08 | Nodeid filha na lista T05 | PYTEST-08 | `CHILD_NODEID_RE` / `mvp_e2e_audit_` | Não |
| C-09 | Declaração de escopo ausente | PYTEST-09 | sem mudança produto / e2e/robot | Não |
| C-10 | Exit ≠ 0 só por coverage (sem inventar falhas) | PYTEST-04 + design | `coverage_gate: true` + lista vazia ok | Não |

**Pré-implementação:** C-01..C-09 em RED (artefato ausente) — evidência: 9 failed / 0 passed.

## 3. Decisão sobre unitários auxiliares

| Opção | Avaliação | Escolha |
|---|---|---|
| A — Só BDD PYTEST-01..09 | Suficiente para contrato documental; sem duplicação | **Escolhida** |
| B — `tests/unit/` parser de markdown sintético | Pouco ganho além dos asserts no path real | Descartada |
| C — Testes em `src/` | Violaria D-T03-001 | Proibida |

## 4. Demonstração RED (pré-implementação)

```bash
/Users/camilocoelhogomes/projects/github_rag/.venv/bin/python -m pytest tests/bdd/test_mvp_e2e_audit_pytest_run.py -q --no-cov
```

Estado esperado: **9 failed, 0 passed** (artefato ausente). Confirmado em `bdd.md` e review ARCHITECT_BDD.

## 5. Fora de escopo

- Qualquer teste unitário sob `src/github_rag/**`.
- Corrigir falhas de produto do pai para “ficar verde”.
- Executar Robot / `python -m github_rag.e2e` (T04).
- Abrir tasks no pai (T05).
