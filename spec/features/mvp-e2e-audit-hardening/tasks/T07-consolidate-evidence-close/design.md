# Design — T07-consolidate-evidence-close

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T07-consolidate-evidence-close` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/mvp-e2e-audit-hardening-T07-consolidate-evidence-close` |
| Base | `origin/feature/mvp-e2e-audit-hardening-T06-open-gap-fill-tasks-parent` |
| Rastreabilidade | Métricas de sucesso requirements; BR-005; ENG-002, ENG-010; BDD-001–008 (fechamento); contrato `AuditClosurePack` |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Pacote canônico `closure-pack.md`; métricas/BR-005/BDD-007; anti-MVP; ENG-010; sem código produto. |

## 1. Contexto

A feature filha `mvp-e2e-audit-hardening` é um pipeline de **auditoria + execução + backlog**, não incremento de domínio (ENG-010). T07 é a onda W5:

- **Dura:** T05 (`ParentFailureBacklog` / T22) + T06 (`ParentGapFillBacklog` / T23–T27).
- Consolidar evidências já produzidas (T01–T06) em um **pacote canônico** rastreável.
- Declarar a feature filha **encerrável / aguardando merge dos PRs** — **sem** declarar MVP de produto entregue.
- **Não** implementar fixes; **não** mesclar; **não** alterar `src/github_rag/**`, `e2e/robot/**` nem composes.

### Evidência consumida (já na base T06)

| Fonte | Artefato | Papel |
|---|---|---|
| T01 | `audit/coverage-inventory.md` | Inventário BDD × cobertura / lacuna |
| T02 | `audit/hitl-env-checklist.md` | Prep `.env` HITL |
| T03 | `runs/pytest-all-tasks.md` | Run pytest (todas as tasks) |
| T04 | `runs/e2e-robot-green-path.md` | Run Robot green path |
| T05 | `audit/failure-backlog-index.md` + pai T22 | Falhas → tasks |
| T06 | `audit/gap-fill-backlog-index.md` + pai T23–T27 | Lacunas → tasks |

## 2. Problema

1. Evidências estão espalhadas em `audit/` e `runs/`; falta índice único para gate de encerramento.
2. Métricas de sucesso do `requirements.md` precisam de verificação explícita no pacote.
3. Toda falha/lacuna deve apontar para task ID no pai (BR-005).
4. Ordem run-first → falha → gap-fill deve ficar demonstrada (BDD-007).
5. Estado da feature deve deixar claro: auditoria/backlog prontos; correções pendentes no pai; MVP **não** entregue.

## 3. Solução proposta

### 3.1 Decisão de abordagem

| Opção | Avaliação |
|---|---|
| A — Pacote Markdown canônico `audit/closure-pack.md` + testes BDD de contrato + status da feature | Satisfaz métricas / BR-005 / BDD-007; zero código de produto |
| B — Declarar MVP entregue no pacote | Viola fora de escopo / DEC-001 handoff |
| C — Implementar T22–T27 nesta feature | Viola ENG-010 |
| D — Só atualizar approvals sem índice | Não rastreia métricas nem ordem run-first |

**Escolha: opção A.**

### 3.2 Contrato lógico `AuditClosurePack`

| Responsabilidade | Motivo da separação |
|---|---|
| Indexar inventário, checklist HITL, runs pytest+e2e, índices T05/T06 e IDs T22–T27 | Isola W5 de abertura de backlog (T05/T06) e de implementação no pai |
| Verificar métricas de sucesso (inventário; runs; falhas/lacunas em tasks; gap-fill pós run-first) | Fecha BDD-001–008 desta feature no nível de evidência |
| Explicitar que correções ficam no pai; MVP não entregue | ENG-010; fora de escopo T07 |
| Sanitização: sem secrets nos artefatos versionados | BR-004; ENG-002 |

Forma: artefato Markdown (+ opcional status em `approvals.md` / task T07) — sem Protocol/ABC em `src/`.

### 3.3 Artefatos obrigatórios

1. **Canônico:** `spec/features/mvp-e2e-audit-hardening/audit/closure-pack.md`
2. Atualização de estado da feature: `approvals.md` e/ou cabeçalho da task T07 → status `CLOSURE_READY` / aguardando merge dos PRs (sem `MVP_DELIVERED`)
3. Testes BDD: `tests/bdd/test_mvp_e2e_audit_closure_pack.py`

Atualização leve de índices em `audit/` / `runs/` **só se necessário** para links; preferir não duplicar conteúdo.

### 3.4 Conteúdo mínimo do `closure-pack.md`

| Seção | Obrigatório |
|---|---|
| Metadados (feature, task T07, data, contrato `AuditClosurePack`) | sim |
| Índice de evidências com links: inventário T01, checklist T02, runs T03/T04, índices T05/T06 | sim |
| Lista de IDs de tasks abertas no pai: T22 + T23–T27 | sim |
| Verificação das métricas de sucesso (cada métrica → evidência / status) | sim |
| Demonstração ordem: inventário → HITL → pytest → e2e → falhas (T22) → gap-fill (T23–T27) | sim |
| BR-005: toda falha/lacuna aponta para task ID | sim |
| Declaração: feature filha **encerrável** / aguardando merge dos PRs | sim |
| Declaração explícita: **MVP de produto NÃO entregue**; green path integral pendente no pai | sim |
| Declaração ENG-010: sem fix/implementação nesta feature; trabalho restante T22+ no pai | sim |
| Sanitização / sem secrets | sim |
| PRs desta feature (T03–T07 abertos; T01/T02 mergeados) — referência operacional | sim (quando conhecidos) |

### 3.5 Métricas de sucesso → mapeamento

| Métrica (requirements) | Evidência no pacote |
|---|---|
| Inventário BDD-001–024 (exc. 015) completo | Link T01 `coverage-inventory.md` |
| Pytest + e2e executados e registrados | Links T03 + T04 runs |
| Toda falha/lacuna em task(s) no pai por superfície | Índice T05 (T22) + T06 (T23–T27) |
| Gap-fill documentado após run-first | Ordem explícita + refs T05 antes T06 |

### 3.6 Decisões

| ID | Decisão | Motivo |
|---|---|---|
| D-T07-001 | Artefato canônico = `audit/closure-pack.md` | ENG-002; plano §1.4 / arquivos prováveis da task |
| D-T07-002 | Não declarar MVP entregue | Fora de escopo; critério pai T19+T21 integrais |
| D-T07-003 | Status feature = encerrável / aguardando merge PRs | Gate humano = merge + aprovação do pacote |
| D-T07-004 | Não implementar nem mesclar T22–T27 | ENG-010 |
| D-T07-005 | Não alterar `src/github_rag/**`, `e2e/robot/**`, composes | ENG-010; natureza documental |
| D-T07-006 | Pacote só referencia artefatos existentes; não reexecuta runs | Runs já em T03/T04 |
| D-T07-007 | Sanitização final no pacote + asserts BDD | BR-004 |
| D-T07-008 | BDD-015 permanece fora; não claim de cobertura | REQ-010 |

## 4. Fluxo

```text
T01 inventory ─┐
T02 hitl ──────┤
T03 pytest ────┼──► AuditClosurePack ──► audit/closure-pack.md
T04 e2e ───────┤         │
T05 T22 ───────┤         ├── status feature: CLOSURE_READY
T06 T23–T27 ───┘         └── handoff: merge PRs + pipeline pai T22+
```

## 5. Dados

- Entrada: Markdown T01–T06 já versionados na base.
- Saída: `closure-pack.md` + status + asserts BDD.
- Sem secrets; sem logs brutos Robot.

## 6. Erros e bordas

| Caso | Tratamento |
|---|---|
| Link quebrado / artefato ausente | BDD falha; pacote incompleto → não encerrável |
| Claim “MVP entregue” | Proibido (D-T07-002); BDD rejeita |
| Task pai faltando (T22–T27) | BDD falha (BR-005) |
| Secrets em artefatos | BDD sanitização falha |
| Tentativa de patch produto | Fora de escopo; diff só spec/tests |

## 7. Segurança

- Não copiar PAT/`.env`/Authorization.
- Referenciar paths e exit codes já sanitizados nos runs.

## 8. Compatibilidade

- Não altera runtime T19/T21.
- PR empilhado: `--base feature/mvp-e2e-audit-hardening-T06-open-gap-fill-tasks-parent`.
- Merge order: … → T05 → T06 → **T07**.

## 9. Observabilidade

- Pacote lista contagens: tasks pai abertas (6: T22–T27), métricas ok/pendente produto.
- BDD valida presença, links, IDs, ordem, anti-MVP-entregue, ENG-010, secrets.

## 10. Riscos e rollback

| Risco | Mitigação |
|---|---|
| Declarar MVP entregue por engano | D-T07-002 + assert BDD |
| Pacote incompleto sem T05/T06 | Base = branch T06; BDD exige artefatos |
| Merge T07 antes de T06 | merge_order_notes no PR |

Rollback: remover `closure-pack.md` + testes BDD T07 + reverter status.

## 11. Fora de escopo

- Implementar ou mesclar correções do pai (T22–T27).
- Automatizar BDD-015.
- Esteira `docs-cicd-e2e-release`.
- Declarar MVP entregue.
- Re-executar pytest/e2e nesta task (já evidenciado em T03/T04).
