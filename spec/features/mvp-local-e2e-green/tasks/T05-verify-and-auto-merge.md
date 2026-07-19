# Task T05 — verify-and-auto-merge

| Campo | Valor |
|---|---|
| Task ID | `T05-verify-and-auto-merge` |
| Feature | `mvp-local-e2e-green` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W5 |
| Plano | v0.1.0 |

## Objetivo

Reexecutar validação e2e canônica; se Robot verde, executar merge automático dos PRs do ciclo na `main` (sem force push) e confirmar critério BR-001 de MVP local entregue.

## Escopo

### Validação final e2e (REQ-005, REQ-027, BDD-004)

- Pré: T04 concluído (imagem + compose end-user).
- Re-run: `python -m github_rag.e2e` — mesmo contrato T01.
- Critério verde: exit 0 + suítes REQ-002 passando (`--exclude bdd015`).
- Registrar em `spec/features/mvp-local-e2e-green/runs/e2e-final-YYYYMMDD.md`.
- Se falhar: **não** merge auto; retornar loop → T02 (evidência nova) → T03 → T04 rebuild → T05.

### Validação end-user BR-001

- `docker compose up -d` sem `--build` com `github-rag:local`.
- `GET /healthz` sucesso após healthy.

### Merge automático (REQ-008, REQ-026, DEC-005, BDD-007)

- PRs elegíveis: tasks do ciclo T22–T27 + T28+ com pipeline autônomo concluído.
- Ordem: dependências documentadas em T03 (`merge_order_notes`); T22 antes de cenários produto; T26 respeitar base empilhada se aplicável.
- Comando: `gh pr merge` (merge commit ou squash conforme repo); **proibido** `--force` na `main`.
- Gate humano de revisão **dispensado** quando Robot verde local nesta execução (operador 2026-07-19).
- pytest ≥ 95% nas branches mergeadas (gate pipeline autônomo herdado).

### Falhas de merge (REQ-028)

- Conflito, CI remota, regressão pós-merge: pausar merge auto; registrar bloqueio; abrir/atualizar task `tooling-e2e` T28+; **não** declarar MVP entregue.

## Fora de escopo

- Abrir backlog inicial (T02).
- Disparar orquestrador (T03).
- Build inicial de imagem (T04 — salvo rebuild pós-merge parcial no loop).
- BDD-015 / gate HITL Discovery.

## Dependências

- **Dura:** T04.
- **Dura:** PRs do ciclo prontos (T03).
- Consumo: resumos T01, handoff T03, build T04.

## Critérios de aceite

- Robot verde local documentado (BDD-004, BDD-007).
- PRs elegíveis mergeados sem force push OU bloqueio documentado com task tooling.
- BR-001 satisfeito para declarar MVP local entregue.
- Nenhum segredo em logs versionados (BDD-008).

## Arquivos prováveis

- `spec/features/mvp-local-e2e-green/runs/e2e-final-YYYYMMDD.md`
- `spec/features/mvp-local-e2e-green/runs/merge-auto-YYYYMMDD.md`
- `spec/features/mvp-local-e2e-green/runs/mvp-local-delivered.md` (encerramento)

## Rastreabilidade

- REQ-005, REQ-008, REQ-026–028; BR-001, BR-006; DEC-005; BDD-004, BDD-007, BDD-008.

## Handoff

- Sucesso: encerrar feature `mvp-local-e2e-green`; MVP local operacional.
- Falha residual: retorno T02→T03→T04→T05 até verde ou bloqueio explícito.
