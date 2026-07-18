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
2. Invoque `tech-lead-architect` para descrever solução, impacto, interfaces e compatibilidade.
3. Faça commit candidato, solicite aprovação humana do design e, após aprovação, registre-a e faça outro commit.
4. Invoque `qa-engineer` para escrever primeiro os testes BDD executáveis.
5. Invoque `tech-lead-architect` para revisar os testes contra design e requisitos; devolva ao QA até ambos concordarem.
6. Faça commit candidato e solicite aprovação humana dos testes BDD. Registre a aprovação e faça outro commit.
7. Invoque `tech-lead-architect` para definir interfaces com comentários explicando responsabilidade e motivo da separação.
8. Faça commit candidato e solicite aprovação humana das interfaces. Registre a aprovação e faça outro commit.
9. Invoque `qa-engineer` para escrever testes unitários de contratos, extremos e corner cases, sem implementar produção.
10. Invoque `tech-lead-architect` para revisar suficiência e aderência; repita até concordarem.
11. Faça commit candidato e solicite aprovação humana dos testes unitários. Registre a aprovação e faça outro commit.
12. Invoque `developer` para implementar estritamente o necessário, guiado pelos testes e preservando comportamento existente.
13. Invoque `tech-lead-architect` para revisar a implementação; devolva ao Developer até não haver bloqueios.
14. Após a aprovação técnica do Architect, inicie a etapa Blue de refatoração entre `tech-lead-architect` e `developer`.
15. O Architect identifica complexidade desnecessária e gargalos de performance comprovados, define metas e registra baseline em `refactoring.md`.
16. O Developer simplifica e otimiza sem alterar comportamento, executando testes e benchmarks após cada mudança.
17. O Architect revisa os resultados; devolva ao Developer até as metas serem atendidas sem regressões e registre a aprovação Blue.
18. Invoque `qa-engineer` para executar suites, regressão, benchmarks aplicáveis e cobertura. Exija no mínimo 95%; configure cobertura se ausente.
19. Faça commit candidato e solicite aprovação humana da implementação com a refatoração Blue. Registre a aprovação e faça outro commit.
20. Invoque `tech-lead-architect` para atualizar documentação e changelog.
21. Faça commit candidato e solicite aprovação humana da documentação. Registre a aprovação e faça o commit final.

## Commits nos gates

- Todo artefato da spec vive em `spec/` e é versionado.
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
