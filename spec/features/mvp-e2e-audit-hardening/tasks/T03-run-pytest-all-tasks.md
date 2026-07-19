# Task T03 — run-pytest-all-tasks

| Campo | Valor |
|---|---|
| Task ID | `T03-run-pytest-all-tasks` |
| Feature | `mvp-e2e-audit-hardening` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W1 |
| Plano | v0.1.0 |

## Objetivo

Executar a suíte pytest do projeto cobrindo **todas as tasks** de `github-etl-mcp-rag` (unitários + BDD de contrato) e registrar resultado observável para abertura de backlog.

## Escopo

- Rodar pytest canônico sobre `tests/` (ENG-003; cobertura do projeto já configurada em `pyproject.toml`).
- Registrar: exit code, lista de falhas (nó de teste), data/ambiente, cobertura reportada se disponível.
- Mapear cada falha a superfície candidata (`health`, `catalog_indexing`, `ui`, `mcp`, `negative`, `tooling-e2e`) para T05 — sem abrir tasks ainda.
- Fase run-first: **não** expandir testes nem corrigir produto nesta task.

## Fora de escopo

- `python -m github_rag.e2e` (T04).
- Abrir tasks no pai (T05).
- Implementar fixes ou novos testes de produto.
- Gap-fill / browser (T06).

## Dependências

- Soft: T01 (contexto de superfícies).
- Não depende de T02 (pytest local sem PAT GitHub real, em regra).

## Critérios de aceite

- Pytest de todas as tasks do pai executado e resultado registrado (BDD-004).
- Falhas listadas de forma acionável para T05 (REQ-015).
- Nenhuma alteração de código de produto nem de `e2e/robot/**` nesta task.

## Arquivos prováveis

- `spec/features/mvp-e2e-audit-hardening/runs/pytest-all-tasks.md` (resumo sanitizado)
- Saída local de cobertura/term (não obrigatório versionar XML bruto)

## Rastreabilidade

- REQ-003, REQ-014–015; DEC-004; ENG-003; BDD-004.

## Handoff

- Alimenta T05 (achados pytest).
- Ordem preferida: concluir antes de T04 (REQ-014); T04 pode seguir se T02 pronto.
