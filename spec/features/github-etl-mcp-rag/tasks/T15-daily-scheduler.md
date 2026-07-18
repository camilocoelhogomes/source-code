# Task T15 — daily-scheduler

| Campo | Valor |
|---|---|
| Task ID | `T15-daily-scheduler` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W6 |

## Objetivo

Agendar indexação periódica uma vez ao dia, com horário configurável por variável de ambiente e pela UI (persistido), verificando repositórios que não estejam `atualizado` com o commit atual da `main`.

## Escopo

- `DailyScheduler` que dispara o orquestrador no horário configurado.
- Precedência ENG-004: env = default no boot; preferência de horário definida na UI e persistida em PostgreSQL prevalece em runtime.
- Persistência da preferência de horário **não** é CRUD de conexões/repositórios (BR-017).
- No disparo: indexar elegíveis (`não indexado` ou `erro`, ou qualquer repo cujo tip `main` ≠ último processado — T14 aplica a transição para `não indexado`); não reprocessar `atualizado` com commit igual.

## Fora de escopo

- Telas da UI (T18 implementa o controle de horário); delivery; edição de `CONFIG_PATH`.

## Dependências

- `T14-indexing-orchestrator`

## Critérios de aceite

- BDD-003: horário diário configurável pela UI **ou** por variável de ambiente; ao chegar o horário, verifica repositórios e indexa os que não estiverem atualizados.
- API/contrato de preferência de horário legível/gravável pela UI (T18), sem permitir criar/editar/remover conexões ou definições de repositórios.
- Não reprocessa repos `atualizado` com mesmo commit.
- Mudança de horário via preferência persistida passa a valer sem editar o JSON de conexões.

## Arquivos prováveis

- `src/.../schedule/daily.py`
- `src/.../schedule/preferences.py`
- `tests/unit/schedule/...`
- `tests/bdd/...`

## Rastreabilidade

- REQ-017; BR-017; BDD-003; ENG-004.

## Handoff

- Interface: `DailyScheduler` + preferência de horário.
- T18: controle de horário diário na UI (BDD-003); zero CRUD de conexões.
