# Interfaces — T05-open-failure-tasks-parent

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T05-open-failure-tasks-parent` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/mvp-e2e-audit-hardening-T05-open-failure-tasks-parent` |
| Natureza | **100% documental / operacional** (D-T05-005) |
| Escopo desta etapa | Contrato lógico `ParentFailureBacklog` — índice + task pai; **sem** Protocol/ABC Python novo, **sem** código de produção |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` (draft) | `0.1.0` | Interface lógica única alinhada design §3 e BDD FAIL-01..10; sem src/. |
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` → corrigido | `0.1.0` | M-01: Estado T22; M-02: escopo FAIL-10 `src/github_rag/**` / `e2e/robot/**` / composes. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Contrato documental `ParentFailureBacklog` alinhado design/BDD 0.1.1. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Forma | Papel |
|---|---|---|
| `ParentFailureBacklog` | Índice Markdown + task(s) Markdown no pai | Converter falhas run-first em backlog acionável |

Paths canônicos:

```text
spec/features/mvp-e2e-audit-hardening/audit/failure-backlog-index.md
spec/features/github-etl-mcp-rag/tasks/T22-fix-tooling-e2e-compose-zoekt.md
```

### Explicitamente fora de escopo — sem interfaces Python novas de runtime

| Item | Motivo |
|---|---|
| `typing.Protocol` / ABC / classes novas em `src/` | D-T05-005; backlog documental |
| Alteração de `src/github_rag/**`, `e2e/robot/**`, `docker-compose*.yml` / Dockerfile como entrega T05 | FAIL-10; ENG-010; D-T05-005 |
| Alteração de keywords Robot / produto | ENG-010; ownership pai T19/T21/T22 |
| Gap-fill / browser | T06 |
| Implementação do fix T22 | Pipeline do pai após abertura |

**Não serão criados** arquivos `.py` de interface de produção nesta task.

## 2. Interface lógica: `ParentFailureBacklog`

```text
# ParentFailureBacklog — interface lógica (documental / operacional)
#
# Responsabilidade:
#   Consumir as evidências run-first ParentPytestRun (T03) e RobotGreenPathRun
#   (T04) e materializar (1) um índice local auditável e (2) task(s) de
#   correção/falha no feature pai github-etl-mcp-rag, agrupadas por superfície
#   ENG-006 e classificadas REQ-017, sem implementar o fix nesta feature filha.
#
# Motivo da separação:
#   - Isola a onda W3 (abertura de backlog de FALHA) dos runs (T03/T04) e do
#     gap-fill (T06), evitando misturar lacunas documentais com falhas runtime.
#   - Congela um contrato auditável (BDD-005 / REQ-016–017 / ENG-006–007/009–010)
#     sem código de domínio novo (D-T05-005).
#   - Impõe D-T05-001/002: não inventar falhas pytest nem superfícies Robot
#     unknown/skip; uma task dominante tooling-e2e (T22) para F-T04-001..003.
#
# Forma:
#   1) Índice: failure-backlog-index.md
#   2) Task pai: T22-fix-tooling-e2e-compose-zoekt.md
#   Sem Protocol/ABC novos em src/.
```

### Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T05-001 | Única interface lógica: `ParentFailureBacklog` | Contrato da task | design §3.2 |
| I-T05-002 | Materialização = índice + T22 Markdown | SoT versionável | FAIL-01/02 |
| I-T05-003 | Sem Protocol/ABC/classes novas em `src/` | D-T05-005 | design §3.1 |
| I-T05-004 | Superfície dominante `tooling-e2e` | ENG-006; run T04 | FAIL-03 |
| I-T05-005 | Classificação combinada REQ-017 em T22 | D-T05-003 | FAIL-04 |
| I-T05-006 | Cobrir F-T04-001..003 | BR-005 | FAIL-05 |
| I-T05-007 | Zero falhas pytest explícito | D-T05-001 | FAIL-06 |
| I-T05-008 | Sem task health/catalog/ui/mcp/negative de falha; sem T23 | D-T05-001/002 | FAIL-07/08 |
| I-T05-009 | Sem secrets | BR-004 | FAIL-09 |
| I-T05-010 | Sem fix nesta feature; não altera `src/github_rag/**`, `e2e/robot/**`, composes | ENG-010; D-T05-005 | FAIL-10 |
| I-T05-011 | Consumidor do fix = pipeline do pai (T22) | Handoff | design §8 |
| I-T05-012 | Consumidor de lacunas = T06 | BR-007 | design §3.6 |
| I-T05-013 | T22 Estado `READY_FOR_IMPLEMENTATION` (candidata) | design §3.5 | design §3.5 |

## 3. Estrutura obrigatória do índice

| Campo / seção | Obrigatório |
|---|---|
| Metadados (feature, task T05, data, refs T03/T04) | sim |
| Resumo pytest: zero falhas | sim |
| Resumo e2e: exit 3; F-T04-001..003 | sim |
| Superfície afetada: `tooling-e2e` → T22 | sim |
| Superfícies sem falha observável: `health` (sem falha independente), `catalog_indexing`, `ui`, `mcp`, `negative` | sim |
| Ponteiro lacunas → T06 | sim |
| Declaração ENG-010 (sem fix aqui; sem alterar `src/github_rag/**` / `e2e/robot/**` / composes nesta feature) | sim |
| Sem secrets | sim |

## 4. Estrutura obrigatória da task T22 (pai)

| Campo | Obrigatório |
|---|---|
| Task ID `T22-fix-tooling-e2e-compose-zoekt` | sim |
| Feature `github-etl-mcp-rag` | sim |
| Estado `READY_FOR_IMPLEMENTATION` (candidata) | sim |
| Superfície `tooling-e2e` | sim |
| Classificação combinada (F-T04-001=`flakiness`; F-T04-002=`produto`; F-T04-003=consequência de F-T04-002) | sim |
| Evidência runs T04 + IDs | sim |
| Objetivo / critérios de aceite: (a) provider docs compose; (b) zoekt entrypoint/`tini` desbloqueando `healthy`/`robot` | sim |
| Arquivos prováveis (compose e2e, e2e README, etc.) | sim |
| Dependências (T19/T21; evidência audit filha) | sim |
| Handoff: implementação no pipeline do pai; filha não corrige | sim |

## 5. Relação com outros contratos

| Contrato | Relação |
|---|---|
| `ParentPytestRun` (T03) | Entrada — lista de falhas (vazia) |
| `RobotGreenPathRun` (T04) | Entrada — F-T04-001..003 |
| `CoverageInventory` (T01) | Não misturar; lacunas → T06 |
| `ParentGapFillBacklog` (T06) | Sucessor para gaps sem falha runtime |

## 6. Fora de escopo desta interface

- Qualquer API Python de runtime / `typing.Protocol` / ABC.
- Alteração de `src/github_rag/**`, `e2e/robot/**`, `docker-compose*.yml`, Dockerfile como entrega desta task.
- Declaração de MVP entregue.
