# Task T15 — daily-scheduler

| Campo | Valor |
|---|---|
| Task ID | `T15-daily-scheduler` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W6 |

## Objetivo

Agendar indexação periódica por **expressão cron**, configurável por variável de ambiente e pela UI (persistida), verificando repositórios que não estejam `atualizado` com o commit atual da `main`.

## Escopo

- Scheduler via **APScheduler** (ou equivalente maduro de cron em Python — DEC-015); proibido cron ad-hoc reinventado.
- `DailyScheduler` (nome histórico da task) dispara o orquestrador conforme a **expressão cron** ativa.
- Configuração = expressão cron (ex.: uma vez ao dia, duas vezes ao dia, de hora em hora). O caso “uma vez ao dia” de REQ-017 / BDD-003 é um **caso especial** de cron (ex.: `0 2 * * *`), não um segundo modelo de configuração.
- Variável de ambiente (ex.: `INDEX_CRON` ou nome fixado no design) fornece o default no boot.
- Precedência **ENG-004**: env = default no boot; preferência de **cron** definida na UI e persistida em PostgreSQL prevalece em runtime.
- Expressão inválida: rejeitar com erro tipado; não aplicar parcialmente; não cair em silent no-op sem registro.
- Persistência da preferência de cron **não** é CRUD de conexões/repositórios (BR-017).
- No disparo: indexar elegíveis (`não indexado` ou `erro`, ou tip `main` ≠ último processado — T14); não reprocessar `atualizado` com commit igual.

## Fora de escopo

- Telas da UI (T18 implementa o controle de expressão cron); delivery; edição de `CONFIG_PATH`.

## Dependências

- `T14-indexing-orchestrator`

## Critérios de aceite

- BDD-003 (interpretação): agenda configurável por **expressão cron** via UI **ou** variável de ambiente; quando o próximo tick do cron ocorre, verifica repositórios e indexa os que não estiverem atualizados. “Uma vez ao dia” permanece suportado como expressão cron diária.
- Aceita expressões que disparem de hora em hora, uma vez ao dia, duas vezes ao dia, etc. (validação de sintaxe no design).
- API/contrato de preferência de **cron** legível/gravável pela UI (T18), sem CRUD de conexões/repos.
- Precedência: preferência UI persistida > default de env em runtime (ENG-004).
- Não reprocessa repos `atualizado` com mesmo commit.
- Mudança de cron via preferência persistida passa a valer sem editar o JSON de conexões.

## Arquivos prováveis

- `src/.../schedule/cron_scheduler.py`
- `src/.../schedule/preferences.py`
- `tests/unit/schedule/...`
- `tests/bdd/...`

## Rastreabilidade

- REQ-017 (diário = caso especial de cron); BR-017, BR-023; DEC-015; BDD-003 (cron UI/env); BDD-024; ENG-004; ENG-010.

## Handoff

- Interface: `DailyScheduler` + preferência de expressão cron.
- T18: controle de **cron** na UI (BDD-003); zero CRUD de conexões.
