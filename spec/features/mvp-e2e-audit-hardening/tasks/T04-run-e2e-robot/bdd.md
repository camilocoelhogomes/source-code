# BDD — T04-run-e2e-robot

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T04-run-e2e-robot` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Execução | `tests/bdd/test_mvp_e2e_audit_e2e_robot_run.py` — valida artefato `RobotGreenPathRun` (não reexecuta Podman/Robot no CI unitário) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | E2E-01..E2E-10; contrato documental BDD-003 / design §3.3; RED até existir `runs/e2e-robot-green-path.md`. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Review BDD OK; cenários cobrem metadados, fases, suítes, falhas T05, soft T03, secrets, sem expansão Robot. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **Artefato (pytest BDD)** | Existência/conteúdo de `runs/e2e-robot-green-path.md` | CI unitário/BDD padrão |
| **Operacional HITL** | Execução real `python -m github_rag.e2e` (Podman + GitHub) | Runner T04; resultado no artefato |
| **Expansão Robot / produto** | Fora do escopo (BR-007 / D-T04-001) | Não alterar |

- Path canônico: `spec/features/mvp-e2e-audit-hardening/runs/e2e-robot-green-path.md`.
- Superfície: resumo Markdown only (D-T04-001); sem módulo em `src/`.
- Exit ≠ 0 é evidência válida; falhas alimentam T05.
- Soft-dep T03: evidência independente.

## Rastreabilidade

| Cenário | Feature BDD / REQ | Design |
|---|---|---|
| E2E-01 | BDD-003; REQ-015; ENG-002 | §3.3 artefato |
| E2E-02 | BDD-003; REQ-002; ENG-004 | §3.3 metadados; §3.4 comando |
| E2E-03 | BDD-003; REQ-012; T02 | §3.3 pré-condições |
| E2E-04 | BDD-003; REQ-015 | §3.3 resultado agregado / exit |
| E2E-05 | BDD-003; ENG-004 | §3.3 fases |
| E2E-06 | BDD-003; T21 green path | §3.3 suítes |
| E2E-07 | BDD-003; ENG-006; REQ-015 | §3.3 falhas T05 |
| E2E-08 | BDD-003; soft-dep T03 | §3.3 item 9 |
| E2E-09 | BDD-003; BR-004 | §3.3 proibições |
| E2E-10 | BDD-003; BR-007; D-T04-001 | §8 sem expansão / sem produto |

## Resultado RED esperado (pré-implementação)

```bash
.venv/bin/python -m pytest tests/bdd/test_mvp_e2e_audit_e2e_robot_run.py -q --no-cov
```

| Métrica | Valor esperado |
|---|---|
| passed | `0` |
| failed | `10` |
| Motivo | artefato `runs/e2e-robot-green-path.md` ausente |

---

## E2E-01 — Artefato canônico existe

**Tipo:** artefato Markdown  
**Dado** o run-first Robot documental T04  
**Quando** o resumo `RobotGreenPathRun` for publicado  
**Então** existe o arquivo `spec/features/mvp-e2e-audit-hardening/runs/e2e-robot-green-path.md`

## E2E-02 — Metadados e comando canônico

**Tipo:** artefato Markdown  
**Dado** o artefato `e2e-robot-green-path.md`  
**Quando** a seção de metadados for lida  
**Então** registra data/hora em formato ISO  
**E** registra branch e commit SHA  
**E** documenta o comando canônico exatamente `python -m github_rag.e2e`  
**E** registra versão Python, OS e Podman (resumidos)

## E2E-03 — Pré-condições T02 / HITL

**Tipo:** artefato Markdown  
**Dado** o artefato `e2e-robot-green-path.md`  
**Quando** as pré-condições forem inspecionadas  
**Então** registra gate T02 `READY` (ou status equivalente)  
**E** registra presença de token apenas como booleano (`present=true/false`)  
**E** menciona Podman e o repo `camilocoelhogomes/source-code`

## E2E-04 — Resultado agregado (exit code)

**Tipo:** artefato Markdown  
**Dado** o artefato `e2e-robot-green-path.md`  
**Quando** o resultado agregado for lido  
**Então** registra exit code do entrypoint  
**E** exit ≠ 0 é tratado como evidência válida (não exige “verde” de produto)

## E2E-05 — Fases da prova

**Tipo:** artefato Markdown  
**Dado** o artefato `e2e-robot-green-path.md`  
**Quando** as fases forem inspecionadas  
**Então** documenta credential / compose (up|stack) / healthy / robot / down  
**E** cada fase tem status observável (ok/fail/skip ou equivalente)

## E2E-06 — Suítes green path T21

**Tipo:** artefato Markdown  
**Dado** o artefato `e2e-robot-green-path.md`  
**Quando** a lista de suítes for lida  
**Então** menciona `health`, `catalog_indexing`, `ui`, `mcp`, `negative`  
**E** registra exclusão `bdd015` (ou `--exclude bdd015`)  
**E** registra resultado por suíte quando observável (pass/fail/unknown)

## E2E-07 — Falhas acionáveis para T05

**Tipo:** artefato Markdown  
**Dado** o artefato `e2e-robot-green-path.md`  
**Quando** a lista de falhas for lida  
**Então** cada entrada (se houver) inclui identificação (suíte/cenário/fase), tipo/motivo sanitizado e superfície candidata  
**E** superfícies pertencem a `{health, catalog_indexing, ui, mcp, negative, tooling-e2e}`  
**E** lista vazia é válida quando exit code = 0 sem falhas de cenário

## E2E-08 — Soft-dep T03 independente

**Tipo:** artefato Markdown  
**Dado** o artefato `e2e-robot-green-path.md`  
**Quando** a nota de dependência T03 for lida  
**Então** declara o estado da soft-dep T03 (aberta/mergeada/indisponível)  
**E** deixa explícito que a evidência T04 é **independente** (não rebase em T03)

## E2E-09 — Artefato sem padrões de token

**Tipo:** artefato Markdown  
**Dado** o artefato `e2e-robot-green-path.md`  
**Quando** o conteúdo for varrido por padrões de segredo  
**Então** não contém prefixos de token GitHub (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`)  
**E** não contém atribuições com valor longo de `GITHUB_TOKEN` / `E2E_GITHUB_TOKEN`

## E2E-10 — Sem expansão Robot / sem mudança de produto

**Tipo:** artefato Markdown  
**Dado** o escopo run-first T04 (D-T04-001 / BR-007)  
**Quando** o resumo for lido  
**Então** declara explicitamente que **não** há expansão de cobertura Robot nem browser nesta task  
**E** confirma que `src/github_rag/**` e `e2e/robot/**` permanecem sem alteração de escopo T04

---

## Comando de verificação

```bash
python -m pytest tests/bdd/test_mvp_e2e_audit_e2e_robot_run.py -q --no-cov
```

TDD: artefato ausente → falha esperada em E2E-01..10 até a implementação criar `runs/e2e-robot-green-path.md` após a execução real.
