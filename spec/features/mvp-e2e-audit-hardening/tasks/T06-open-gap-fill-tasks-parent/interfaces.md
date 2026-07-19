# Interfaces — T06-open-gap-fill-tasks-parent

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T06-open-gap-fill-tasks-parent` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/mvp-e2e-audit-hardening-T06-open-gap-fill-tasks-parent` |
| Natureza | **100% documental / operacional** (D-T06-006) |
| Escopo desta etapa | Contrato lógico `ParentGapFillBacklog` — índice + tasks pai; **sem** Protocol/ABC Python novo, **sem** código de produção |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Interface lógica única alinhada design §3 e BDD GAP-01..12; sem src/; browser obrigatório em T23. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Forma | Papel |
|---|---|---|
| `ParentGapFillBacklog` | Índice Markdown + tasks Markdown no pai | Converter lacunas T01 em backlog acionável de gap-fill |

Paths canônicos:

```text
spec/features/mvp-e2e-audit-hardening/audit/gap-fill-backlog-index.md
spec/features/github-etl-mcp-rag/tasks/T23-gap-ui-browser.md
spec/features/github-etl-mcp-rag/tasks/T24-gap-catalog-indexing-integral.md
spec/features/github-etl-mcp-rag/tasks/T25-gap-negative-integral.md
spec/features/github-etl-mcp-rag/tasks/T26-gap-mcp-parallel-slo.md
spec/features/github-etl-mcp-rag/tasks/T27-gap-sdk-dec015-conformity.md
```

### Explicitamente fora de escopo — sem interfaces Python novas de runtime

| Item | Motivo |
|---|---|
| `typing.Protocol` / ABC / classes novas em `src/` | D-T06-006; backlog documental |
| Alteração de `src/github_rag/**`, `e2e/robot/**`, `docker-compose*.yml` / Dockerfile como entrega T06 | GAP-12; ENG-010; D-T06-006 |
| Implementação de keywords Robot / browser / produto | ENG-010; ownership pai T21 |
| Tasks de falha runtime | T05 / T22 |
| Implementação das tasks T23–T27 | Pipeline do pai após abertura |

**Não serão criados** arquivos `.py` de interface de produção nesta task.

## 2. Interface lógica: `ParentGapFillBacklog`

```text
# ParentGapFillBacklog — interface lógica (documental / operacional)
#
# Responsabilidade:
#   Consumir CoverageInventory (T01) e o índice ParentFailureBacklog (T05),
#   e materializar (1) um índice local auditável de gap-fill e (2) tasks de
#   lacuna no feature pai github-etl-mcp-rag, agrupadas por superfície,
#   classificadas gap-teste/assert-fraco (REQ-017), com UI exigindo browser
#   (ENG-008), sem implementar keywords/browser nesta feature filha.
#
# Motivo da separação:
#   - Isola a onda W4 (abertura de backlog de LACUNA) das falhas (T05/T22)
#     e da consolidação (T07), evitando misturar falha runtime com gap-teste.
#   - Congela um contrato auditável (BDD-006/008 / REQ-018–019 / ENG-008–010)
#     sem código de domínio novo (D-T06-006).
#   - Impõe D-T06-001..009: toda lacuna vira task; browser em UI; IDs T23+;
#     sem BDD-015; sem duplicar T22; superfície sdk do inventário preservada.
#
# Forma:
#   1) Índice: gap-fill-backlog-index.md
#   2) Tasks pai: T23..T27 gap-*.md
#   Sem Protocol/ABC novos em src/.
```

### Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T06-001 | Única interface lógica: `ParentGapFillBacklog` | Contrato da task | design §3.2 |
| I-T06-002 | Materialização = índice + T23–T27 Markdown | SoT versionável | GAP-01/02 |
| I-T06-003 | Sem Protocol/ABC/classes novas em `src/` | D-T06-006 | design §3.1 |
| I-T06-004 | Cinco superfícies: ui, catalog_indexing, negative, mcp, sdk | D-T06-002/007 | GAP-03 |
| I-T06-005 | Classificação `gap-teste` / `assert-fraco` | REQ-017 | GAP-04 |
| I-T06-006 | T23 exige browser; API insuficiente | ENG-008; D-T06-003 | GAP-05 |
| I-T06-007 | Cobrir todas as lacunas T01 (exc. 015) | BDD-008; D-T06-001 | GAP-06 |
| I-T06-008 | Denylist 003/006/013/024 coberta | INV-07 | GAP-07 |
| I-T06-009 | Sem BDD-015 | D-T06-008 | GAP-08 |
| I-T06-010 | Sem duplicar T22 / sem gap-tooling | D-T06-005 | GAP-09 |
| I-T06-011 | Referência a T05/ordem falhas→lacunas | REQ-019; D-T06-009 | GAP-10 |
| I-T06-012 | Sem secrets | BR-004 | GAP-11 |
| I-T06-013 | Sem keywords nesta feature; não altera `src/github_rag/**` / `e2e/robot/**` / composes | ENG-010; D-T06-006 | GAP-12 |
| I-T06-014 | Consumidor da implementação = pipeline do pai (T23–T27) | Handoff | design §8 |
| I-T06-015 | Consumidor do fechamento = T07 | Plano W5 | design §4 |
| I-T06-016 | Estado tasks pai `READY_FOR_IMPLEMENTATION` (candidata) | design §3.5 | design §3.5 |

## 3. Estrutura obrigatória do índice

| Campo / seção | Obrigatório |
|---|---|
| Metadados (feature, task T06, data, refs T01/T05) | sim |
| Declaração: falhas (T05/T22) antes de lacunas | sim |
| Cross-ref: não duplicar T22 | sim |
| Tabela tasks T23–T27 × superfície × BDD × classificação | sim |
| Lista / cobertura de todas as lacunas do inventário | sim |
| Declaração ENG-010 (sem keywords aqui; sem alterar `src/github_rag/**` / `e2e/robot/**` / composes) | sim |
| Exclusão BDD-015 | sim |
| Sem secrets | sim |

## 4. Estrutura obrigatória das tasks pai (T23–T27)

| Campo | Obrigatório |
|---|---|
| Task ID (`T23-gap-ui-browser` … `T27-gap-sdk-dec015-conformity`) | sim |
| Feature `github-etl-mcp-rag` | sim |
| Estado `READY_FOR_IMPLEMENTATION` (candidata) | sim |
| Superfície | sim |
| Classificação REQ-017 | sim |
| BDD lacunas (lista) | sim |
| Evidência inventário T01 | sim |
| Objetivo / critérios de aceite (fortalecer T21; **não** implementar nesta feature filha) | sim |
| T23: browser obrigatório + API insuficiente | sim |
| Arquivos prováveis | sim |
| Dependências (T21; T22 para re-run stack; auditoria filha) | sim |
| Handoff: implementação no pipeline do pai | sim |

## 5. Relação com outros contratos

| Contrato | Relação |
|---|---|
| `CoverageInventory` (T01) | Entrada — linhas `lacuna` |
| `ParentFailureBacklog` (T05) | Pré-requisito; não duplicar T22 |
| `AuditClosurePack` (T07) | Sucessor — consolida índice de tasks abertas |

## 6. Fora de escopo desta interface

- Qualquer API Python de runtime / `typing.Protocol` / ABC.
- Alteração de `src/github_rag/**`, `e2e/robot/**`, `docker-compose*.yml`, Dockerfile como entrega desta task.
- Declaração de MVP entregue.
