# BDD — T04-worker-limiter

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T04-worker-limiter` |
| Autor | Implementation Task Runner (QA step) |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão BDD | `0.1.0` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T04-worker-limiter` |
| Escopo desta etapa | Somente BDD executáveis dos critérios de aceite T04 |
| Rastreabilidade | REQ-004, REQ-037; BR-006; BDD-002, BDD-013; ENG-003 |

## Rastreabilidade

| Cenário | Aceite / requisito |
|---|---|
| WL-01 | Defaults ENG-003: index=2, query=4 via settings → limiters |
| WL-02 | Paralelismo nunca excede capacidade configurada |
| WL-03 | Excedentes aguardam e depois executam |
| WL-04 | Isolamento index × query (não compartilham slots) |
| WL-05 | Capacidade 1: serializa execução |
| WL-06 | Rajada: N > capacity; pico ≤ capacity |
| WL-07 | Liberação de slot após exceção no bloco adquirido |
| WL-08 | `capacity < 1` rejeitado com `WorkerLimiterError` (sem fallback silencioso) |
| WL-09 | Env não-inteiro permanece fronteira T01 (`SettingsBootstrapError`) |

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Steps / asserts | `tests/bdd/test_worker_limiter.py` |

## Como executar

```bash
python -m pytest tests/bdd/test_worker_limiter.py -q
```

## Cenários

### WL-01 — Defaults de engenharia nos limiters

**Dado** ambiente sem `INDEX_WORKERS` nem `QUERY_WORKERS`  
**Quando** `load_settings` carregar o snapshot e as factories criarem os limiters  
**Então** o limiter de indexação deve ter `capacity == 2`  
**E** o limiter de consulta deve ter `capacity == 4`.

### WL-02 — Paralelismo nunca excede o limite

**Dado** um `WorkerLimiter` com `capacity == 2`  
**Quando** 4 tarefas tentarem adquirir slot simultaneamente e permanecerem ativas por um intervalo  
**Então** o número máximo de tarefas dentro do bloco `acquire` ao mesmo tempo deve ser `<= 2`.

### WL-03 — Excedentes aguardam e depois executam

**Dado** um `WorkerLimiter` com `capacity == 1`  
**E** uma tarefa já ocupa o único slot  
**Quando** uma segunda tarefa tentar `acquire`  
**Então** ela deve permanecer bloqueada enquanto o primeiro slot estiver ocupado  
**E** após a liberação do primeiro, a segunda deve entrar e concluir.

### WL-04 — Isolamento index × query

**Dado** limiter de indexação com `capacity == 1` e limiter de query com `capacity == 1`  
**Quando** o slot de indexação estiver totalmente ocupado  
**Então** uma aquisição no limiter de query deve obter slot sem esperar o index  
**E** o inverso também deve valer (index não bloqueia por query cheia).

### WL-05 — Limite 1 serializa

**Dado** um `WorkerLimiter` com `capacity == 1`  
**Quando** duas tarefas com trabalho observável forem submetidas em paralelo via `acquire`  
**Então** seus intervalos de execução ativa não devem se sobrepor.

### WL-06 — Rajada respeita capacidade

**Dado** um `WorkerLimiter` com `capacity == 3`  
**Quando** 10 tarefas forem disparadas em rajada  
**Então** todas devem concluir com sucesso  
**E** o pico de concorrência observada deve ser `<= 3`.

### WL-07 — Liberação após falha no bloco

**Dado** um `WorkerLimiter` com `capacity == 1`  
**Quando** a tarefa que possui o slot levantar exceção dentro do `with acquire`  
**Então** o slot deve ser liberado  
**E** uma tarefa subsequente deve conseguir adquirir sem deadlock.

### WL-08 — Capacidade inválida rejeitada

**Dado** tentativa de criar limiter com `capacity` `0` ou negativo  
**Quando** a factory ou construtor for invocado  
**Então** deve levantar `WorkerLimiterError`  
**E** não deve aplicar fallback silencioso para o default `2` ou `4`.

### WL-09 — Não-inteiro permanece em T01

**Dado** `INDEX_WORKERS="abc"` (ou `QUERY_WORKERS` equivalente)  
**Quando** `load_settings` for chamado  
**Então** deve levantar `SettingsBootstrapError`  
**E** T04 não deve mascarar esse erro com fallback de limiter.
