# Task T22 — fix-tooling-e2e-compose-zoekt

| Campo | Valor |
|---|---|
| Task ID | `T22-fix-tooling-e2e-compose-zoekt` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` (candidata; aberta por auditoria filha) |
| Superfície | `tooling-e2e` |
| Origem | feature filha `mvp-e2e-audit-hardening` / T05 (`ParentFailureBacklog`) |
| Evidência | `spec/features/mvp-e2e-audit-hardening/runs/e2e-robot-green-path.md` |

## Classificação (REQ-017) — combinação documentada

| ID evidência | Classificação | Motivo |
|---|---|---|
| F-T04-001 | `flakiness` | Compose provider ausente no host (`podman-compose`/`docker-compose` not in PATH); pré-req de runtime local / ambiente, não defeito de domínio |
| F-T04-002 | `produto` | Serviço `zoekt` (`sourcegraph/zoekt:latest`) exit 1 — entrypoint/`tini` inválido no compose e2e; bloqueia `depends_on` do app |
| F-T04-003 | consequência de F-T04-002 | Fases `healthy`/`robot` skip; green path não exercitado — sem task extra |

## Objetivo

Corrigir a stack e2e (tooling) para que `python -m github_rag.e2e` consiga subir o compose (incl. zoekt saudável), alcançar wait healthy e executar o green path Robot — **sem** expandir cobertura integral nesta task (lacunas → auditoria T06).

## Evidência do run (sanitizada)

- Attempt A: `looking up compose provider failed` → F-T04-001 (`flakiness`).
- Attempt B: `podman compose up -d --build` hang; container zoekt `Exited (1)`; log `tini` help → F-T04-002 (`produto`).
- App ficou `Created`; `/healthz` não alcançado; Robot não rodou → F-T04-003 (consequência).
- Exit code agregado T04: `3`.

## Escopo

- Documentar/garantir pré-req de compose provider (Podman + `podman-compose` ou equivalente) em `e2e/README.md` / runbook (mitiga F-T04-001).
- Corrigir definição do serviço `zoekt` em `docker-compose.e2e.yml` (e alinhar `docker-compose.yml` se compartilhado) — command/entrypoint/imagem compatível (mitiga F-T04-002).
- Validar que stack e2e fica healthy e Robot green path inicia (fecha F-T04-003 como consequência).
- Testes de manifesto/delivery conforme padrão T19 quando aplicável.

## Fora de escopo

- Expandir suíte Robot / browser (T06 da feature filha).
- Declarar MVP entregue.
- Alterações de domínio ETL/RAG/MCP não relacionadas ao bootstrap e2e.

## Critérios de aceite

- Com pré-reqs documentados, `podman compose` (ou provider suportado) resolve sem F-T04-001.
- Serviço zoekt sobe sem exit 1 por entrypoint/`tini` inválido.
- `python -m github_rag.e2e` passa da fase compose/healthy; Robot green path **executa** (pass/fail de cenário de produto passa a ser evidência nova — não bloqueada por tooling).
- Nenhum segredo versionado.
- Esta task é implementada no **pipeline do pai**; a feature filha `mvp-e2e-audit-hardening` **não implementa** o fix (ENG-010).

## Arquivos prováveis

- `docker-compose.e2e.yml` (serviço `zoekt`)
- `docker-compose.yml` (se entrypoint compartilhado)
- `e2e/README.md` / `docs/runbook-local.md`
- testes de manifesto/delivery sob `tests/` (T19)

## Dependências

- T19 (`docker-compose.e2e.yml`), T21 (`python -m github_rag.e2e`)
- Evidência auditoria: T04 run + índice T05

## Handoff

- Ownership da correção: `github-etl-mcp-rag` (esta task).
- Feature filha apenas abriu o backlog; **sem implementação** de fix em `mvp-e2e-audit-hardening` — sem alteração de `src/github_rag/**`, `e2e/robot/**` nem composes **nessa** feature.
- Após verde tooling: re-rodar e2e; falhas de cenário de produto (se houver) abrem tasks novas por superfície.
