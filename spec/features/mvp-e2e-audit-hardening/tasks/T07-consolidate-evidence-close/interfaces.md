# Interfaces — T07-consolidate-evidence-close

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T07-consolidate-evidence-close` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `DRAFT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` |
| Branch | `feature/mvp-e2e-audit-hardening-T07-consolidate-evidence-close` |
| Natureza | **100% documental / operacional** (D-T07-005) |
| Escopo desta etapa | Contrato lógico `AuditClosurePack` — pacote + status; **sem** Protocol/ABC Python novo, **sem** código de produção |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| — | — | pendente | `0.1.0` | Aguarda review Architect. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Forma | Papel |
|---|---|---|
| `AuditClosurePack` | Markdown canônico + status da feature | Consolidar evidências T01–T06 e declarar feature encerrável |

Path canônico:

```text
spec/features/mvp-e2e-audit-hardening/audit/closure-pack.md
```

Status: atualização em `approvals.md` e/ou `tasks/T07-consolidate-evidence-close.md` → `CLOSURE_READY` (aguardando merge dos PRs).

### Explicitamente fora de escopo — sem interfaces Python novas de runtime

| Item | Motivo |
|---|---|
| `typing.Protocol` / ABC / classes novas em `src/` | D-T07-005; pacote documental |
| Alteração de `src/github_rag/**`, `e2e/robot/**`, `docker-compose*.yml` / Dockerfile | CLOSE-12; ENG-010 |
| Implementação de T22–T27 | Pipeline do pai |
| Declaração de MVP entregue | D-T07-002 |

**Não serão criados** arquivos `.py` de interface de produção nesta task.

## 2. Interface lógica: `AuditClosurePack`

```text
# AuditClosurePack — interface lógica (documental / operacional)
#
# Responsabilidade:
#   Consumir artefatos T01–T06 (inventário, HITL, runs pytest+e2e, índices
#   de falha e gap-fill) e materializar um pacote canônico de evidências
#   com verificação das métricas de sucesso, lista de tasks abertas no pai
#   (T22–T27), demonstração da ordem run-first → falha → gap-fill, status
#   da feature filha como encerrável (CLOSURE_READY / aguardando merge),
#   sem declarar MVP de produto entregue e sem implementar correções.
#
# Motivo da separação:
#   - Isola a onda W5 (consolidação / gate de encerramento) da abertura de
#     backlog (T05/T06) e da implementação no pai, evitando misturar
#     evidência com fix de produto.
#   - Congela um contrato auditável (métricas; BR-005; BDD-001–008 fechamento;
#     ENG-002/010) sem código de domínio novo (D-T07-005).
#   - Impõe D-T07-001..008: pacote canônico; anti-MVP; sanitização; sem re-run.
#
# Forma:
#   1) Pacote: audit/closure-pack.md
#   2) Status feature: CLOSURE_READY (approvals / task T07)
#   Sem Protocol/ABC novos em src/.
```

### Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T07-001 | Única interface lógica: `AuditClosurePack` | Contrato da task | design §3.2 |
| I-T07-002 | Materialização = `closure-pack.md` + status | SoT versionável | CLOSE-01/10 |
| I-T07-003 | Sem Protocol/ABC/classes novas em `src/` | D-T07-005 | design §3.1 |
| I-T07-004 | Links obrigatórios T01–T06 | Métricas / rastreabilidade | CLOSE-02..07 |
| I-T07-005 | Lista T22–T27 com slugs completos | SUGGESTION S-01 Architect; BR-005 | CLOSE-06/07/09 |
| I-T07-006 | Ordem run-first → falha → gap-fill explícita | BDD-007 | CLOSE-08 |
| I-T07-007 | Anti-MVP-entregue + CLOSURE_READY | D-T07-002/003 | CLOSE-10 |
| I-T07-008 | Sem secrets | BR-004 | CLOSE-11 |
| I-T07-009 | Sem fix; sem alterar src/robot/composes | ENG-010 | CLOSE-12 |
| I-T07-010 | Não reexecuta runs nesta task | D-T07-006 | design §3.6 |
| I-T07-011 | Consumidor = gate humano (merge PRs + aprovação pacote) | Handoff task | design §8 |

## 3. Estrutura obrigatória do pacote

| Campo / seção | Obrigatório |
|---|---|
| Metadados (feature, T07, `AuditClosurePack`, data) | sim |
| Índice de evidências com links T01–T06 | sim |
| Tabela/lista tasks pai T22–T27 (paths/slugs) | sim |
| Verificação métricas de sucesso | sim |
| Ordem run-first → falhas → gap-fill | sim |
| Status `CLOSURE_READY` / encerrável / aguardando merge | sim |
| MVP **não** entregue | sim |
| ENG-010 / trabalho restante no pai | sim |
| Sem secrets | sim |

## 4. Relação com outros contratos

| Contrato | Relação |
|---|---|
| `CoverageInventory` (T01) | Entrada — inventário |
| `HitlEnvPrep` (T02) | Entrada — checklist |
| `ParentPytestRun` (T03) | Entrada — run |
| `RobotGreenPathRun` (T04) | Entrada — run |
| `ParentFailureBacklog` (T05) | Entrada — T22 |
| `ParentGapFillBacklog` (T06) | Entrada — T23–T27 |
| Pipeline pai T22+ | Sucessor — implementação de correções/lacunas |

## 5. Fora de escopo desta interface

- Qualquer API Python de runtime / `typing.Protocol` / ABC.
- Alteração de `src/github_rag/**`, `e2e/robot/**`, composes/Dockerfile.
- Declaração de MVP entregue.
- Merge de PRs.
