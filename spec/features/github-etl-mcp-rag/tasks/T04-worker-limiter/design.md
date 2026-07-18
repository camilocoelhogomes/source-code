# Design — T04-worker-limiter

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T04-worker-limiter` |
| Autor | Implementation Task Runner + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão do design | `0.1.1` |
| Branch | `feature/github-etl-mcp-rag-T04-worker-limiter` |
| Base | `main` (T01 já mesclado) |
| Rastreabilidade | REQ-004, REQ-037; BR-006; BDD-002, BDD-013; ENG-003 |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 (review design v0.1.0 → v0.1.1) |

## 1. Contexto

T01 entregou bootstrap de processo (`AppSettings`, `load_settings`) com defaults
`INDEX_WORKERS=2` e `QUERY_WORKERS=4`, conversão tipada e rejeição de não-inteiros
via `SettingsBootstrapError`. **Não** aplicou política de mínimos/máximos de
workers (I-T01-008 / design T01: política = T04).

T04 implementa a porta `WorkerLimiter` e a política de paralelismo: semáforos
isolados para indexação e consulta, fila/espera quando o limite é atingido, e
tratamento explícito de valores inválidos além do tipado em T01.

Fora de escopo: jobs reais de indexação, tools MCP, UI, orquestração (T14/T17
consomem esta porta depois).

## 2. Solução técnica

### 2.1 Estratégia geral

1. Criar pacote `github_rag.concurrency` (fronteira nova alinhada ao plano §2 —
   porta `WorkerLimiter`; não existia em T01 além do placeholder implícito).
2. Expor contrato `WorkerLimiter` (Protocol) com aquisição/liberação de slot
   que **bloqueia/aguarda** quando a capacidade está esgotada.
3. Manter **dois limiters isolados**: um para indexação (`index`) e um para
   consulta (`query`), criados a partir dos inteiros já resolvidos em
   `AppSettings` (ou valores explícitos injetáveis nos testes).
4. Aplicar política de validade de capacidade **na construção do limiter**
   (não reparsear env no limiter): rejeitar `capacity < 1` com erro tipado;
   documentar ausência de fallback silencioso.
5. Garantir liberação de slot em cancelamento/exceção (context manager /
   `try/finally`), coberta por testes de corner case.

### 2.2 Componentes

| Componente | Módulo | Responsabilidade |
|---|---|---|
| `WorkerLimiter` | `concurrency/limiter.py` | Porta: adquirir/liberar slot; nunca exceder capacidade |
| `SemaphoreWorkerLimiter` | `concurrency/limiter.py` | Implementação baseada em semáforo (threading) |
| `WorkerLimiterError` | `concurrency/limiter.py` | Erro de construção/uso inválido (capacidade inválida) |
| `create_index_limiter` / `create_query_limiter` | `concurrency/limiter.py` | Factories a partir de `AppSettings` (ou `int`) |
| Constantes de política | `concurrency/limiter.py` ou reexport | `MIN_WORKERS = 1` (sem máximo funcional no MVP) |

Decisão D-T04-001: **dois limiters** (index/query), não um único compartilhamento
de pool. Motivo: BR-006 e isolamento orquestrador × MCP/query (handoff T04);
rajadas de query não devem roubar slots de indexação e vice-versa.

Decisão D-T04-002: implementação **síncrona** com `threading.Semaphore` +
context manager. Motivo: T01/settings e futuros workers de indexação podem
rodar em threads; superfícies async (MCP/FastAPI em T16/T17) poderão adaptar
via `asyncio.to_thread` ou wrapper futuro sem mudar o contrato síncrono da
porta nesta task. Evita acoplar T04 a event loop.

Decisão D-T04-003: política de env inválido **além** do tipado T01:
- T01 já rejeita não-inteiro (`SettingsBootstrapError`).
- T04 rejeita `capacity < 1` na factory/`WorkerLimiter` com
  `WorkerLimiterError` (mensagem cita pool + valor + razão).
- **Sem** fallback silencioso para default na factory quando o inteiro já veio
  inválido do snapshot (ex.: `0` ou negativo após bootstrap). Defaults `2`/`4`
  continuam sendo responsabilidade de `load_settings` quando env ausente/blank.
- Sem máximo rígido no MVP (dúvida Dockerfile não bloqueante); capacidade
  positiva arbitrária é aceita.

Decisão D-T04-004: API pública mínima do contrato:

```text
WorkerLimiter.capacity -> int
WorkerLimiter.acquire() -> context manager (bloqueia até haver slot)
WorkerLimiter.try_acquire() -> bool  (opcional se útil a testes; preferir só acquire)
WorkerLimiter.active_count / available_permits  (somente se necessário a asserts;
  preferir observação via comportamento, não API de métricas)
```

Preferência: context manager `with limiter.acquire(): ...` que libera no
`__exit__` mesmo com exceção/cancelamento cooperativo. Método `acquire`/
`release` explícitos permitidos se o context manager os usar internamente.

### 2.3 Fluxo

```text
load_settings() → AppSettings(index_workers, query_workers)
        │
        ├─► create_index_limiter(settings) → WorkerLimiter (cap = index_workers)
        └─► create_query_limiter(settings) → WorkerLimiter (cap = query_workers)

Caller (futuro T14/T17):
  with index_limiter.acquire():
      # no máximo `capacity` entradas simultâneas neste bloco
      run_index_job(...)
```

Quando N > capacity tentam adquirir: as primeiras `capacity` entram; as
excedentes **esperam** até um slot ser liberado; depois executam. Nunca há
mais de `capacity` seções críticas ativas no mesmo limiter.

Isolamento: slots do index limiter não afetam o query limiter.

### 2.4 Dados

| Dado | Origem | Persistência |
|---|---|---|
| Capacidade index | `AppSettings.index_workers` | Somente memória do processo |
| Capacidade query | `AppSettings.query_workers` | Somente memória do processo |
| Estado do semáforo | Runtime | Ephemeral; sem PostgreSQL |

Sem schema, sem I/O de arquivo, sem rede.

### 2.5 Erros

| Situação | Tipo | Comportamento |
|---|---|---|
| `capacity < 1` na construção | `WorkerLimiterError` | Rejeitar; mensagem com pool/valor/razão |
| Env não-inteiro | (já T01) `SettingsBootstrapError` | Fora do escopo de reimplementar; testes T04 podem referenciar a fronteira |
| Exceção dentro do `with acquire` | — | Slot liberado no `__exit__` |
| Thread interrompida / cancelamento cooperativo | — | Liberação garantida pelo context manager |

### 2.6 Segurança

- Não lê tokens nem paths de config.
- Não loga valores sensíveis (não há segredos neste módulo).
- Mensagens de erro só com nome do pool e capacidade numérica.

### 2.7 Compatibilidade

- OS-agnostic (threading padrão da stdlib).
- Windows / macOS / Linux first-class (herdado de T01).
- Sem dependência de event loop; utilizável em venv e container T19.

### 2.8 Observabilidade

- Sem métricas obrigatórias no MVP.
- Comportamento observável via testes: contagem de concorrência máxima,
  espera de excedentes, liberação após erro.

### 2.9 Riscos e rollback

| Risco | Mitigação |
|---|---|
| Deadlock se caller nunca liberar | Context manager obrigatório no contrato documentado |
| Capacidade alta esgota CPU/memória | Defaults baixos (ENG-003); sem máximo no MVP |
| Confusão sync vs async em T17 | Documentar adaptação futura; contrato sync estável |

Rollback: remover pacote `concurrency` e factories; T14/T17 ainda não
dependem desta branch até merge.

## 3. Critérios de aceite mapeados

| Aceite da task | Design |
|---|---|
| Paralelismo nunca excede o limite | Semáforo com `capacity`; testes de rajada |
| Excedentes aguardam e depois executam | `acquire` bloqueante; teste de fila |
| Env inválido explícito | `capacity < 1` → `WorkerLimiterError`; sem fallback silencioso |
| Corner: limite 1, rajadas, cancel/release | Cenários BDD + unit dedicados |
| Isolamento index × query | Dois limiters; teste de não-interferência |

## 4. Arquivos previstos

- `src/github_rag/concurrency/__init__.py`
- `src/github_rag/concurrency/limiter.py`
- `tests/unit/concurrency/test_worker_limiter.py`
- `tests/bdd/test_worker_limiter.py`
- Artefatos em `spec/.../tasks/T04-worker-limiter/`

## 5. Fora de escopo (confirmação)

- Indexação real, MCP tools, UI, scheduler.
- Reparse de env dentro do limiter (usa `AppSettings` / `int`).
- Máximo absoluto de workers no Dockerfile (T19).
- Wrapper asyncio nativo (pode vir em task consumidora se necessário).
