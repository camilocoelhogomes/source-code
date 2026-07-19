# Task T01 — coverage-inventory

| Campo | Valor |
|---|---|
| Task ID | `T01-coverage-inventory` |
| Feature | `mvp-e2e-audit-hardening` |
| Estado | `PENDING_PO_REVIEW` |
| Onda | W0 |
| Plano | v0.1.0 |

## Objetivo

Produzir inventário BDD-001–024 (exceto BDD-015) do pai × evidência na suíte Robot/T21 e contratos pytest, marcando cobertura integral vs lacuna explícita (incl. asserts parciais/API-smoke).

## Escopo

- Ler BDD-001–024 em `spec/features/github-etl-mcp-rag/requirements.md` (pular 015).
- Inspecionar `e2e/robot/**`, design T21 (mapeamento parcial DEC-019) e testes `tests/**` relevantes.
- Para cada BDD: status `coberto-integral` | `lacuna` com evidência (arquivo/caso Robot, keyword, teste pytest ou “ausente”).
- Marcar lacuna quando o assert atual for só parcial/API e o critério integral exigir mais (ex.: exclusão de arquivos, progresso por arquivo, falha parcial+histórico, paralelismo sob limite, UI no browser).
- Documentar UI atual = RequestsLibrary (sem browser) como lacuna de superfície `ui` quando o BDD exigir fluxo UI.

## Fora de escopo

- Executar pytest/Robot (T03/T04).
- Abrir tasks no pai (T05/T06).
- Alterar `e2e/robot/**` ou código de produto.
- Automatizar BDD-015.

## Dependências

- Nenhuma task desta feature.
- Pré: artefatos T21 e requisitos 0.5.0 do pai disponíveis.

## Critérios de aceite

- Matriz completa BDD-001–024 exc. 015 com status e evidência (BDD-001 desta feature).
- Fatias parciais T21 não contam como integral sem marcar lacuna (BR-001).
- BDD-015 explicitamente fora do inventário automatizado (REQ-010).

## Arquivos prováveis

- `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md`
- Referências somente-leitura: `e2e/robot/**`, `spec/features/github-etl-mcp-rag/tasks/T21-mvp-e2e-robot/**`

## Rastreabilidade

- REQ-001, REQ-008–010; BR-001–002; DEC-002; ENG-001–002; BDD-001, BDD-008 (parcial).

## Handoff

- SoT de lacunas para T06.
- Não bloqueia T02/T03/T04.
