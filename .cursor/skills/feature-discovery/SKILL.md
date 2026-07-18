---
name: feature-discovery
description: Orquestra descoberta, refinamento e decomposição de novas features entre Product Owner, Principal Engineer e humano. Use ao receber requisitos novos ou incompletos.
---

# Pipeline de descoberta

O agente principal coordena; todo trabalho de persona ocorre em subagents.

## Estrutura

Toda documentação gerada pela spec deve ser salva na pasta raiz do projeto chamada `spec/`.

Use `spec/features/<feature-id>/`:

- `requirements.md`: problema, objetivos, fora de escopo, personas, regras, cenários BDD, restrições, riscos, dúvidas e decisões.
- `implementation-plan.md`: arquitetura, interfaces, ordem, dependências, paralelismo e estratégia para reduzir retrabalho.
- `tasks/<task-id>.md`: objetivo, escopo, dependências, critérios de aceite, arquivos prováveis e handoff.
- `approvals.md`: gate, versão/commit, decisão, autor, data e observações.

## Estados

`DRAFT_REQUIREMENTS → HUMAN_REQUIREMENTS_APPROVAL → ENGINEERING_REFINEMENT → PO_PLAN_REVIEW → HUMAN_PLAN_APPROVAL → READY_FOR_IMPLEMENTATION`

## Fluxo

1. Invoque `product-owner` com o pedido do usuário.
2. Apresente ao humano somente as perguntas produzidas pelo PO.
3. Reenvie respostas ao mesmo papel até o PO declarar requisitos completos.
4. Peça ao PO para criar/atualizar `requirements.md`, incluindo cenários BDD.
5. Faça commit da versão candidata e solicite aprovação humana dos requisitos.
6. Se aprovado, registre em `approvals.md` e faça novo commit; se rejeitado, devolva ao PO.
7. Invoque `principal-engineer` com os requisitos aprovados para criar o plano e as tasks.
8. Invoque `product-owner` para revisar rastreabilidade, valor e escopo do plano.
9. Se o PO rejeitar, devolva ao Principal Engineer e repita a revisão.
10. Após aprovação do PO, faça commit da versão candidata e solicite aprovação humana.
11. Se aprovado, registre em `approvals.md`, faça novo commit e marque as tasks prontas; se rejeitado, devolva ao papel adequado.
12. Entregue cada task separadamente ao pipeline `implementation-pipeline`, respeitando dependências e grupos paralelos.

## Gates e commits

- Todo artefato da spec vive em `spec/` e é versionado.
- Antes de cada pedido de aprovação humana, faça um commit dos arquivos da spec e mostre resumo, arquivos e o commit candidato.
- Depois de obter a aprovação humana, faça outro commit registrando a decisão.
- Nunca trate feedback como aprovação sem a palavra explícita do humano.
- Não altere specs entre o commit candidato e a decisão.
- Nunca fabrique identidade ou aprovação.
- Não faça commit se não houver repositório Git ou se o humano não autorizou o workflow; reporte o bloqueio.

## Handoff de task

Inclua: feature ID, task ID, commits aprovados, requisitos relacionados, cenários BDD, dependências, limites de escopo, interfaces esperadas, riscos e definição de pronto.
