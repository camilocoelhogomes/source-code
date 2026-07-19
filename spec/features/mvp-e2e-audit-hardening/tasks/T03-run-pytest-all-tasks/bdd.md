# BDD — T03-run-pytest-all-tasks

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T03-run-pytest-all-tasks` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `TESTS_READY_FOR_REVIEW` |
| Versão | `0.1.0` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Execução | `tests/bdd/test_mvp_e2e_audit_pytest_run.py` — valida artefato documental `ParentPytestRun` (sem Robot/e2e; sem correção de produto) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | PYTEST-01..PYTEST-09; contrato documental BDD-004 / design §3.3 `ParentPytestRun`; RED até existir `runs/pytest-all-tasks.md`. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **Artefato (pytest BDD)** | Existência/conteúdo de `runs/pytest-all-tasks.md`; metadados, agregados, falhas do pai, sanitização | CI unitário/BDD padrão |
| **Run canônico** | `python -m pytest tests/ -q --tb=line` (implementação) | Fora destes asserts até o artefato |
| **Robot / e2e / produto** | Fora do escopo desta task (T04 / D-T03-001) | Não alterar `src/` nem `e2e/robot/**` |

- Path canônico: `spec/features/mvp-e2e-audit-hardening/runs/pytest-all-tasks.md`.
- Superfície: resumo Markdown only (D-T03-001); sem módulo em `src/`.
- Lista de falhas para T05: só domínio pai; excluir `mvp_e2e_audit_*` (D-T03-002).
- Exit ≠ 0 é evidência válida; `coverage_gate` quando exit ≠ 0 só por `fail_under`.

## Rastreabilidade

| Cenário | Feature BDD / REQ | Design |
|---|---|---|
| PYTEST-01 | BDD-004; REQ-015; ENG-002 | §3.3 artefato |
| PYTEST-02 | BDD-004; REQ-003; ENG-003 | §3.3 metadados; §3.4 comando |
| PYTEST-03 | BDD-004; REQ-015 | §3.3 resultado agregado |
| PYTEST-04 | BDD-004; REQ-015; D-T03 | §3.3 cobertura / `coverage_gate` |
| PYTEST-05 | BDD-004; ENG-006 | §3.3 lista de falhas + superfícies |
| PYTEST-06 | BDD-004; soft-dep T01 | §3.3 nota T01; §7 |
| PYTEST-07 | BDD-004; BR-004 | §8; §6 proibições |
| PYTEST-08 | BDD-004; D-T03-002 | §3.4.1 contrato filha vs pai |
| PYTEST-09 | BDD-004; D-T03-001 | §3.1; §15 sem mudança de produto |

## Resultado RED esperado (pré-implementação)

Comando:

```bash
/Users/camilocoelhogomes/projects/github_rag/.venv/bin/python -m pytest tests/bdd/test_mvp_e2e_audit_pytest_run.py -q --no-cov
```

| Métrica | Valor esperado |
|---|---|
| passed | `0` |
| failed | `9` |
| Motivo | artefato `runs/pytest-all-tasks.md` ausente — todos os cenários PYTEST-01..09 dependem dele |

### Evidência RED (execução QA)

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Comando | `/Users/camilocoelhogomes/projects/github_rag/.venv/bin/python -m pytest tests/bdd/test_mvp_e2e_audit_pytest_run.py -q --no-cov` |
| passed | `0` |
| failed | `9` |
| Status | `RED` — artefato ausente (razão esperada) |

---

## PYTEST-01 — Artefato canônico existe

**Tipo:** artefato Markdown  
**Dado** o run-first pytest documental T03  
**Quando** o resumo `ParentPytestRun` for publicado  
**Então** existe o arquivo `spec/features/mvp-e2e-audit-hardening/runs/pytest-all-tasks.md`

## PYTEST-02 — Metadados do run

**Tipo:** artefato Markdown  
**Dado** o artefato `pytest-all-tasks.md`  
**Quando** a seção de metadados for lida  
**Então** registra data/hora em formato ISO  
**E** registra branch e commit SHA  
**E** documenta o comando canônico exatamente `python -m pytest tests/ -q --tb=line`  
**E** registra versão Python e OS resumido

## PYTEST-03 — Resultado agregado

**Tipo:** artefato Markdown  
**Dado** o artefato `pytest-all-tasks.md`  
**Quando** o resultado agregado for inspecionado  
**Então** registra exit code  
**E** registra contagens `passed` / `failed` / `skipped` / `errors` / `total` (quando disponível)

## PYTEST-04 — Cobertura e coverage_gate

**Tipo:** artefato Markdown  
**Dado** o artefato `pytest-all-tasks.md`  
**Quando** a seção de cobertura for lida  
**Então** registra percentual de cobertura **ou** `N/A` com motivo  
**E** quando aplicável (exit ≠ 0 só por `fail_under` sem nodeids falhos do pai), declara `coverage_gate` (ou equivalente documentado no design)

## PYTEST-05 — Lista de falhas do pai acionável para T05

**Tipo:** artefato Markdown  
**Dado** o artefato `pytest-all-tasks.md`  
**Quando** a lista de falhas do domínio pai for lida  
**Então** cada entrada (se houver) inclui `nodeid`, tipo (`failed`/`error`), mensagem sanitizada e superfície candidata  
**E** superfícies candidatas pertencem a `{health, catalog_indexing, ui, mcp, negative, tooling-e2e}`  
**E** lista vazia é válida quando não há falhas de nodeid do pai

## PYTEST-06 — Nota soft-dep T01

**Tipo:** artefato Markdown  
**Dado** o artefato `pytest-all-tasks.md`  
**Quando** a nota de dependência T01 for lida  
**Então** declara se o inventário T01 estava disponível no commit base  
**E** deixa explícito que o run **não** depende do artefato de inventário (soft-dep)

## PYTEST-07 — Artefato sem padrões de token

**Tipo:** artefato Markdown  
**Dado** o artefato `pytest-all-tasks.md`  
**Quando** o conteúdo for varrido por padrões de segredo  
**Então** não contém prefixos de token GitHub (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`)  
**E** não contém atribuições com valor longo de `GITHUB_TOKEN` / `E2E_GITHUB_TOKEN`

## PYTEST-08 — Falhas do pai excluem contrato da filha (D-T03-002)

**Tipo:** artefato Markdown  
**Dado** a lista de falhas do pai no resumo  
**Quando** os `nodeid` forem inspecionados  
**Então** a lista **não** inclui nodeids cujo path/nome seja `mvp_e2e_audit_*` (testes de contrato desta feature filha)  
**E** falhas só de contrato T03 não alimentam T05 como achados de produto do pai

## PYTEST-09 — Sem mudança de produto exigida

**Tipo:** artefato Markdown  
**Dado** o escopo run-first T03 (D-T03-001)  
**Quando** o resumo for lido  
**Então** declara explicitamente que **não** há mudança de produto exigida nesta task  
**E** confirma que `src/github_rag/**` e `e2e/robot/**` permanecem sem alteração de escopo T03

---

## Comando de verificação

```bash
python -m pytest tests/bdd/test_mvp_e2e_audit_pytest_run.py -q --no-cov
```

TDD: artefato ausente → falha esperada em PYTEST-01..09 até a implementação documental criar `runs/pytest-all-tasks.md`.
