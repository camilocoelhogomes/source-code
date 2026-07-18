---
name: autonomous-implementation-orchestrator
description: Orquestra a implementação autônoma e paralela de várias tasks aprovadas, cada uma em seu próprio subagent e branch, com aprovação apenas do Architect e único gate humano no merge via PR no GitHub. Use após o plano da feature ser aprovado para executar as tasks sem aprovações humanas intermediárias.
---

# Orquestrador de implementação autônoma e paralela

O agente principal apenas orquestra: lê o plano aprovado, monta ondas de dependência, dispara um subagent `implementation-task-runner` por task, monitora a execução em paralelo, coleta os PRs e entrega ao humano. Não implementa, não escreve testes e não aprova artefatos.

## Diferença para o `implementation-pipeline` padrão

- Não há gates de aprovação humana intermediários (design, BDD, interfaces, testes unitários, implementação, docs).
- A aprovação do `tech-lead-architect` substitui cada gate intermediário.
- O único gate humano é a revisão e o merge do PR no GitHub.
- Cada pipeline de task roda dentro do seu próprio subagent; tasks paralelizáveis rodam ao mesmo tempo, cada uma em sua branch.

## Quando usar

- O `requirements.md` e o `implementation-plan.md` da feature já foram aprovados pelo humano.
- As tasks estão marcadas como prontas para implementação.
- O humano solicitou execução autônoma das tasks.

## Pré-condições (bloqueie e reporte se faltar)

1. `requirements.md` e `implementation-plan.md` aprovados em `spec/features/<feature-id>/approvals.md`.
2. Todas as tasks a executar estão em estado `READY_FOR_IMPLEMENTATION`.
3. Repositório Git com remote do GitHub configurado (`git remote -v`).
4. `gh` instalado e autenticado (`gh auth status`).
5. `main` atualizada.

Se qualquer pré-condição faltar, pare antes de disparar qualquer runner e reporte o bloqueio ao humano.

## Papéis

- **Agente principal (orquestrador)**: monta o grafo de dependências, define ondas, dispara e monitora os runners, coleta status/branch/PR/cobertura, apresenta ao humano. Nunca implementa nem aprova.
- **`implementation-task-runner` (subagent)**: executa o pipeline completo de UMA task, em branch própria, com gate do Architect, e abre o PR. Um subagent por task.

## Ondas de dependência e paralelismo

- Construa o grafo de dependências a partir do `implementation-plan.md`.
- Uma **onda** é o conjunto de tasks cujas dependências já têm branch disponível.
- Dispare em paralelo (background) um runner por task da onda, em uma única mensagem com múltiplas chamadas.
- Nomeie a branch de cada task como `feature/<feature-id>-<task-id>`.
- Regra de base da branch:
  - Task sem dependências pendentes: branch a partir da `main` atualizada; PR com `--base main`.
  - Task que depende de outra ainda não mesclada: branch a partir da branch do pré-requisito e PR empilhado (`--base <branch-do-pré-requisito>`). Documente a ordem de merge para o humano.
- Nunca dispare uma task antes de a branch do seu pré-requisito existir.

## Fluxo

1. Verifique todas as pré-condições. Bloqueie e reporte se faltar.
2. Carregue o plano e as tasks; valide `READY_FOR_IMPLEMENTATION`.
3. Atualize a `main`. Monte as ondas de dependência.
4. Para cada onda, dispare em paralelo (background) um `implementation-task-runner` por task, passando o handoff completo. Se o tipo de subagent dedicado não estiver disponível, use `generalPurpose` instruindo-o a seguir este contrato.
5. Monitore os runners até a onda terminar. Colete `status`, `branch`, `pr_url`, `coverage` e resumo de cada task.
6. Uma task que falha não bloqueia as independentes: reporte a falha e siga com as demais. Não avance ondas que dependem de uma task falha.
7. Ao final, apresente ao humano: lista de PRs abertos, ordem de merge, cobertura e resumo por task. Este é o ÚNICO gate humano.
8. Não faça merge. O humano revisa e mescla no GitHub. Só execute `gh pr merge` se o humano autorizar explicitamente, sempre sem force push.

## Contrato exigido de cada runner

- Seguir a disciplina e a ordem: design → BDD → interfaces comentadas → testes unitários (extremos e corner cases) → implementação TDD → refatoração Blue → cobertura ≥ 95% → docs/changelog.
- Aprovação do `tech-lead-architect` em cada etapa; sem gate humano intermediário.
- Commit por etapa na branch; artefatos em `spec/features/<feature-id>/tasks/<task-id>/`.
- Push da branch e abertura de PR via `gh` com corpo detalhado (resumo do porquê, escopo, cenários BDD cobertos, resultados de teste e cobertura, riscos, dependências e ordem de merge).
- Nunca mesclar na `main`; nunca force push.
- Retornar `status`, `branch`, `base`, `pr_url`, `coverage`, `test_results`, `open_risks`, `merge_order_notes` e `summary_for_human`.

## Handoff para o runner

Inclua: `feature-id`, `task-id`, branch base, arquivos de contexto (`requirements.md`, `implementation-plan.md`, `tasks/<task-id>.md`, interfaces esperadas, artefatos de dependências), critérios de aceite, definição de pronto e limites de escopo.

## Restrições

- Neste pipeline não há gate HITL intermediário; a aprovação do Architect substitui as aprovações humanas intermediárias.
- Mudança de escopo pausa a task e retorna ao pipeline de descoberta.
- Nunca force push; nunca mescla sem revisão humana no PR.
- Respeite dependências e grupos paralelos definidos no plano aprovado.
- Se `gh` ou o remote do GitHub estiverem ausentes, pare e reporte antes de disparar qualquer runner.
- Nenhum subagent aprova o próprio merge; o merge é decisão humana no GitHub.
