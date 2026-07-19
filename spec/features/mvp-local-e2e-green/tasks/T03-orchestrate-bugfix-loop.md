# Task T03 — orchestrate-bugfix-loop

| Campo | Valor |
|---|---|
| Task ID | `T03-orchestrate-bugfix-loop` |
| Feature | `mvp-local-e2e-green` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W3 |
| Plano | v0.1.0 |

## Objetivo

Disparar e monitorar o skill `autonomous-implementation-orchestrator` para implementar tasks `READY_FOR_IMPLEMENTATION` no pai (`T22–T27` + `T28+` de T02) até estabilizar correções mergeáveis, preparando re-run e2e.

## Escopo

- Carregar `.cursor/skills/autonomous-implementation-orchestrator/SKILL.md`.
- Handoff mínimo (REQ-018) documentado em `spec/features/mvp-local-e2e-green/runs/orchestrator-handoff-*.md`:

```yaml
feature_id: github-etl-mcp-rag
stop_criterion: python -m github_rag.e2e exit 0 (REQ-002, exclude BDD-015)
tasks: [lista T02 — T22..T27 + T28+]
dependency_waves: conforme DAG pai (T22 tooling antes de cenários produto)
architect_gate: true
human_intermediate_gate: false  # DEC-004
```

- Pré-condições do skill: `gh` autenticado, remote GitHub, `main` atualizada.
- Cada task: branch `feature/github-etl-mcp-rag-<task-id>`, pipeline autônomo, cobertura ≥ 95%, PR aberto.
- Ordem sugerida de ondas pai:
  1. **T22** (tooling/stack) — desbloqueia Robot
  2. **T26** (se PR_OPENED — retomar/merge order)
  3. **T23, T24, T25, T27** — paralelo conforme deps
  4. **T28+** runtime — por superfície
- Task falha no pipeline: registrar; não bloquear independentes; não avançar ondas dependentes.
- Ao concluir onda aplicável: registrar `branch`, `pr_url`, `coverage`, `merge_order_notes`.
- **Não** executar merge auto nesta task (T05); **não** declarar Robot verde sem re-run T01/T05.

## Fora de escopo

- Merge na `main` (T05, exceto merges já feitos pelo operador durante loop longo — documentar).
- Build imagem end-user (T04).
- Re-run e2e final de validação (T05).
- Implementar código diretamente nesta feature.

## Dependências

- **Dura:** T02 (lista de tasks + dedup).
- Soft: pré-reqs skill (`gh`, remote).

## Critérios de aceite

- Orquestrador invocado automaticamente após T02 (BDD-003, REQ-004).
- T22–T27 incluídas quando pendentes (DEC-008).
- PRs abertos com cobertura ≥ 95% por task concluída.
- Handoff T04/T05 com ordem de merge e estado dos PRs.

## Arquivos prováveis

- `spec/features/mvp-local-e2e-green/runs/orchestrator-handoff-YYYYMMDD.md`
- `spec/features/mvp-local-e2e-green/runs/orchestrator-status-YYYYMMDD.md`
- Artefatos por task: `spec/features/github-etl-mcp-rag/tasks/<task-id>/` (pipeline autônomo)

## Rastreabilidade

- REQ-004, REQ-018–020; DEC-004; BDD-003.

## Handoff

- PRs + merge order → T04 (rebuild pós-merge) → T05 (validação + merge auto remanescente).
