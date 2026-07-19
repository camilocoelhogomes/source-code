# Task T07 — consolidate-evidence-close

| Campo | Valor |
|---|---|
| Task ID | `T07-consolidate-evidence-close` |
| Feature | `mvp-e2e-audit-hardening` |
| Estado | `PENDING_PO_REVIEW` |
| Onda | W5 |
| Plano | v0.1.0 |

## Objetivo

Consolidar evidências (inventário, runs, índices de backlog) e declarar esta feature encerrável quando auditoria + execuções + tasks no pai estiverem registradas e aprováveis — sem declarar MVP de produto entregue.

## Escopo

- Pacote de fechamento: links para inventário T01, checklist T02, runs T03/T04, índices T05/T06, lista de IDs de tasks abertas no pai.
- Verificar métricas de sucesso dos requisitos: inventário completo; pytest+e2e executados; falhas e lacunas refletidas em tasks; gap-fill documentado após run-first.
- Sanitização final: nenhum segredo nos artefatos versionados.
- Explicitar que correções e green path integral ficam pendentes nas tasks do pai.

## Fora de escopo

- Implementar ou mesclar correções do pai.
- Automatizar BDD-015.
- Esteira `docs-cicd-e2e-release`.
- Declaração de MVP entregue (critério do pai T19+T21 integrais).

## Dependências

- **Dura:** T05, T06.

## Critérios de aceite

- Pacote de evidências completo e rastreável (métricas de sucesso do `requirements.md`).
- Toda falha e lacuna aponta para task ID no pai (BR-005).
- Ordem run-first → falha → gap-fill demonstrada no pacote (BDD-007).
- Feature filha pronta para gate de encerramento/aprovação; sem código de produto alterado por esta feature.

## Arquivos prováveis

- `spec/features/mvp-e2e-audit-hardening/audit/closure-pack.md`
- Atualização leve de índices em `audit/` / `runs/` se necessário

## Rastreabilidade

- Métricas de sucesso; BR-005; ENG-002, ENG-010; BDD-001–008 (fechamento).

## Handoff

- Orquestrador: gate humano de encerramento desta feature / aprovação do pacote.
- Trabalho restante: implementar tasks T22+ no pai.
