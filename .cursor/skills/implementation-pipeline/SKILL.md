---
name: implementation-pipeline
description: Orquestra uma task aprovada entre Architect, QA, Developer e humano, com BDD, interfaces, TDD, reviews, cobertura e documentação. Use para implementar cada task de uma feature refinada.
---

# Pipeline de implementação

Execute uma task por instância. O agente principal apenas coordena e solicita aprovações.

## Artefatos

Toda documentação gerada pela spec deve ser salva na pasta raiz do projeto chamada `spec/`.

Em `spec/features/<feature-id>/tasks/<task-id>/` mantenha:

- `design.md`
- `bdd.md`
- `interfaces.md`
- `unit-test-plan.md`
- `refactoring.md`
- `reviews.md`
- `approvals.md`

## Fluxo obrigatório

1. Valide que requisitos, plano e task possuem aprovação humana registrada.
2. Atualize a `main` e crie a branch exclusiva `feature/<feature-id>-<task-id>` a partir dela. Todo o trabalho da task, incluindo specs, testes, implementação, refatoração e documentação, deve ocorrer nessa branch.
3. Invoque `tech-lead-architect` para descrever solução, impacto, interfaces e compatibilidade.
4. Faça commit candidato, solicite aprovação humana do design e, após aprovação, registre-a e faça outro commit.
5. Invoque `qa-engineer` para escrever primeiro os testes BDD executáveis.
6. Invoque `tech-lead-architect` para revisar os testes contra design e requisitos; devolva ao QA até ambos concordarem.
7. Faça commit candidato e solicite aprovação humana dos testes BDD. Registre a aprovação e faça outro commit.
8. Invoque `tech-lead-architect` para definir interfaces com comentários explicando responsabilidade e motivo da separação.
9. Faça commit candidato e solicite aprovação humana das interfaces. Registre a aprovação e faça outro commit.
10. Invoque `qa-engineer` para escrever testes unitários de contratos, extremos e corner cases, sem implementar produção.
11. Invoque `tech-lead-architect` para revisar suficiência e aderência; repita até concordarem.
12. Faça commit candidato e solicite aprovação humana dos testes unitários. Registre a aprovação e faça outro commit.
13. Invoque `developer` para implementar estritamente o necessário, guiado pelos testes e preservando comportamento existente.
14. Invoque `tech-lead-architect` para revisar a implementação; devolva ao Developer até não haver bloqueios.
15. Após a aprovação técnica do Architect, inicie a etapa Blue de refatoração entre `tech-lead-architect` e `developer`.
16. O Architect identifica complexidade desnecessária e gargalos de performance comprovados, define metas e registra baseline em `refactoring.md`.
17. O Developer simplifica e otimiza sem alterar comportamento, executando testes e benchmarks após cada mudança.
18. O Architect revisa os resultados; devolva ao Developer até as metas serem atendidas sem regressões e registre a aprovação Blue.
19. Invoque `qa-engineer` para executar suites, regressão, benchmarks aplicáveis e cobertura. Exija no mínimo 95%; configure cobertura se ausente.
20. Faça commit candidato e solicite aprovação humana da implementação com a refatoração Blue. Registre a aprovação e faça outro commit.
21. Invoque `tech-lead-architect` para atualizar documentação e changelog.
22. Faça commit candidato e solicite aprovação humana da documentação. Registre a aprovação e faça o commit final na branch.
23. Confirme que não há alterações pendentes e que todos os testes, benchmarks aplicáveis e cobertura estão aprovados.
24. Mescle a branch da task na `main`, sem force push. Se houver conflito, resolva na branch com review Architect–Developer e repita toda a validação antes do merge.

## Commits nos gates

- Todo artefato da spec vive em `spec/` e é versionado.
- Todos os commits do pipeline são feitos na branch exclusiva da task; nunca desenvolva diretamente na `main`.
- Antes de cada pedido de aprovação humana, faça um commit dos arquivos da spec.
- Depois de obter a aprovação humana, faça outro commit registrando a decisão.
- Não faça commit se não houver repositório Git ou se o humano não autorizou o workflow; reporte o bloqueio.

## Restrições

- Pare em cada gate `HITL`; aprovação de persona não substitui aprovação humana.
- Nenhum subagent pode aprovar o próprio trabalho.
- QA cria testes antes da implementação; Developer não reduz, ignora ou reescreve testes para obter verde.
- A etapa Blue não pode alterar comportamento, contratos ou escopo; otimizações exigem baseline e comparação reproduzível.
- Mudança de escopo retorna ao pipeline de descoberta.
- Falha preexistente deve ser evidenciada e separada de regressão introduzida.
- Reviews devem registrar achados, resposta, resolução e arquivos/linhas afetados.
- A branch só pode ser mesclada na `main` após todas as aprovações humanas e validações obrigatórias.
