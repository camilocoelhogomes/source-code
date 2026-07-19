# Task T04 — run-e2e-robot

| Campo | Valor |
|---|---|
| Task ID | `T04-run-e2e-robot` |
| Feature | `mvp-e2e-audit-hardening` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W2 |
| Plano | v0.1.0 |

## Objetivo

Executar o green path e2e canônico via `python -m github_rag.e2e` (Podman + `docker-compose.e2e.yml` + GitHub real) e registrar sucesso/falha por cenário/suíte **sem** expandir cobertura integral.

## Escopo

- Pré: T02 satisfeito (`.env`/token + Podman).
- Comando: `python -m github_rag.e2e` (deps `.[e2e]` conforme `e2e/README.md`).
- Registrar: exit code, suítes/cenários falhos, timeouts/rate-limit, presença de artefatos em `e2e/results/` (gitignored).
- Versionar apenas resumo sanitizado (sem token, sem dumps com segredo).
- Green path atual T21 apenas — proibido adicionar `.robot`/browser nesta fase (BR-007).

## Fora de escopo

- Expandir asserts integrais ou browser (T06 → tasks no pai).
- Corrigir produto/flakiness (só registrar para T05).
- Pytest (T03).
- CI Actions.

## Dependências

- **Dura:** T02.
- Soft: T03 (ordem preferida pytest → e2e).

## Critérios de aceite

- Prova Robot green path exercitada em stack real; resultado observável (BDD-003).
- Falha de stack/credencial/cenário registrada explicitamente (REQ-015).
- Nenhum segredo no resumo versionado (BR-004).

## Arquivos prováveis

- `spec/features/mvp-e2e-audit-hardening/runs/e2e-robot-green-path.md`
- Consumo: `docker-compose.e2e.yml`, `e2e/robot/**`, `src/github_rag/e2e/**`
- Artefatos locais: `e2e/results/` (não versionar)

## Rastreabilidade

- REQ-002, REQ-012–015; DEC-004; ENG-004; BDD-003.

## Handoff

- Achados → T05.
- Não bloqueia inventário T01; T06 espera T05.
