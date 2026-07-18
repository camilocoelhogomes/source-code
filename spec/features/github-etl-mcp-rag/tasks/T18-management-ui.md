# Task T18 — management-ui

| Campo | Valor |
|---|---|
| Task ID | `T18-management-ui` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W7 |

## Objetivo

Entregar UI simples de gestão e busca: listar repos (origem/conexão/estado REQ-020), checkbox e disparo de indexação, progresso por etapa, falhas com mensagem/horário/histórico, configuração do horário diário, busca exata e semântica; sem editar config ou token.

## Escopo

- API HTTP + frontend leve consumindo catálogo, orquestrador, scheduler (horário) e `QueryService`.
- Estados conforme REQ-020 apenas.
- Progresso conforme REQ-021–022 (percentual, arquivos, etapa; flags Zoekt/Tree-sitter/metadados).
- Em falhas (REQ-023): exibir **mensagem**, **horário** e **histórico de execuções** — **não** “logs” genéricos.
- Controle explícito na UI para **configurar o horário diário** de indexação (REQ-017, BDD-003), persistido via T15; sem CRUD de conexões/repos.
- Origem GitHub vs local visível (REQ-035).
- Sem formulários de conexões/repos/token (BR-012, BR-017, BDD-023).
- Apoio opcional do modelo local na UX de busca semântica (REQ-027), sem substituir Qdrant.

## Fora de escopo

- CRUD de `CONFIG_PATH`; MCP; build de imagem final (T19); stream de logs genéricos.

## Dependências

- `T07`, `T14`, `T15`, `T16`

## Critérios de aceite

- BDD-002, BDD-003, BDD-007, BDD-009, BDD-010, BDD-016, BDD-023 (perspectiva UI).
- BDD-003: usuário consegue configurar o horário diário na UI; o agendamento usa esse horário (ou o env, conforme ENG-004); não há CRUD de conexões.
- Em `erro`: UI mostra mensagem, horário e histórico (REQ-023 / BDD-008 na superfície UI).
- Token nunca solicitado/persistido pela UI.
- Usuário não consegue criar/editar/remover conexões ou definições de repos.

## Arquivos prováveis

- `src/.../api/...`
- `web/` ou `src/.../ui/...`
- `tests/bdd/ui/...`
- `tests/unit/api/...`

## Rastreabilidade

- REQ-006,012,017,020–027,035; BR-012,017; BDD-002,003,007,009–010,016,023.

## Handoff

- Interface: `ManagementUiApi` (+ app web).
- Empacotamento em T19.
