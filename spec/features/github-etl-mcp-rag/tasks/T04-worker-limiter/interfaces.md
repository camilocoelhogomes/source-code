# Interfaces — T04-worker-limiter

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T04-worker-limiter` |
| Autor | Implementation Task Runner + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `APPROVED_BY_ARCHITECT` |
| Branch | `feature/github-etl-mcp-rag-T04-worker-limiter` |
| Escopo desta etapa | Contratos de comunicação T04 **somente** |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `WorkerLimiter` | `concurrency/limiter.py` | Porta de aquisição/liberação de slot |
| `WorkerLimiterError` | `concurrency/limiter.py` | Erro de capacidade inválida |
| `SemaphoreWorkerLimiter` | `concurrency/limiter.py` | Implementação (stub nesta etapa) |
| `create_index_limiter` | `concurrency/limiter.py` | Factory do pool de indexação |
| `create_query_limiter` | `concurrency/limiter.py` | Factory do pool de consulta |
| `MIN_WORKERS` | `concurrency/limiter.py` | Literal de política `1` |

### Fora de escopo

| Item | Dono |
|---|---|
| Reparse de env / `load_settings` | T01 (já entregue) |
| Jobs de indexação | T14 |
| Tools MCP / query handlers | T16 / T17 |
| UI | T18 |
| Wrapper asyncio nativo | futuro consumidor, se necessário |
| `try_acquire` / métricas públicas | omitidos (SUGGESTION design) |

## 2. Decisões de contrato

| ID | Decisão | Motivo |
|---|---|---|
| I-T04-001 | Porta `WorkerLimiter` (Protocol) com `capacity` e `acquire()` context manager | D-T04-004; API mínima aprovada no design |
| I-T04-002 | Dois factories: `create_index_limiter` / `create_query_limiter` | Isolamento BR-006; D-T04-001 |
| I-T04-003 | Capacidade vem de `AppSettings` ou `int` explícito; limiter **não** lê env | Fronteira T01; evita dual parsing |
| I-T04-004 | `capacity < MIN_WORKERS` (1) → `WorkerLimiterError`; sem fallback silencioso | D-T04-003; aceite task |
| I-T04-005 | Implementação síncrona (`threading.Semaphore`) | D-T04-002 |
| I-T04-006 | Nome do pool (`"index"` \| `"query"`) só para mensagem de erro | Observabilidade mínima sem API de métricas |
| I-T04-007 | Sem `try_acquire` / `active_count` na porta pública | SUGGESTION Architect no design |

## 3. Contratos detalhados

### 3.1 `WorkerLimiterError`

```python
class WorkerLimiterError(Exception):
    """Capacidade inválida ou uso inválido do limiter."""
```

- **Responsabilidade:** sinalizar rejeição explícita de `capacity < 1` (e falhas de construção).
- **Motivo da separação:** distinto de `SettingsBootstrapError` (tipagem de env em T01).
- **Invariantes:** mensagem cita pool (se conhecido), valor e razão; sem segredos.
- **Erros:** esta classe **é** o tipo.

### 3.2 `WorkerLimiter` (Protocol)

```python
@runtime_checkable
class WorkerLimiter(Protocol):
    @property
    def capacity(self) -> int: ...

    def acquire(self) -> AbstractContextManager[None]: ...
```

- **Responsabilidade:** limitar concorrência a `capacity` slots; `acquire()` bloqueia até haver slot e libera no exit do context manager (mesmo com exceção).
- **Motivo da separação:** porta estável para T14 (index) e T17 (query) sem acoplar a semáforo concreto ou a settings.
- **Invariantes:** `capacity >= 1` em instância válida; pico de entradas no CM ≤ `capacity`; pools distintos não compartilham slots.
- **Erros:** construção inválida via `WorkerLimiterError`; o Protocol não levanta em `capacity`/`acquire` após construção ok.

### 3.3 `SemaphoreWorkerLimiter`

- **Responsabilidade:** implementação concreta do Protocol com `threading.Semaphore`.
- **Motivo da separação:** permite testar/substituir a porta sem mudar consumidores.
- **Construtor:** `SemaphoreWorkerLimiter(*, capacity: int, pool: str)`.
- **Erros:** `capacity < 1` → `WorkerLimiterError`.

### 3.4 Factories

```python
def create_index_limiter(settings: AppSettings) -> WorkerLimiter: ...
def create_query_limiter(settings: AppSettings) -> WorkerLimiter: ...
```

- **Responsabilidade:** materializar limiters isolados a partir de `index_workers` / `query_workers`.
- **Motivo da separação:** callers não escolhem pool string nem acoplam a classe concreta; garante isolamento index×query.
- **Invariantes:** capacities = atributos do snapshot; rejeição se `< 1`.
- **Erros:** `WorkerLimiterError` se capacity inválida no snapshot.

### 3.5 Constante

- `MIN_WORKERS = 1` — menor capacidade aceita (política T04).

## 4. Mapa AppSettings → limiter

| Fonte | Factory | Pool label |
|---|---|---|
| `settings.index_workers` | `create_index_limiter` | `"index"` |
| `settings.query_workers` | `create_query_limiter` | `"query"` |

Defaults `2`/`4` continuam em T01 (`load_settings`); T04 só aplica `>= 1`.

## 5. Código nesta etapa

| Arquivo | Conteúdo |
|---|---|
| `src/github_rag/concurrency/__init__.py` | Reexports públicos |
| `src/github_rag/concurrency/limiter.py` | Protocol + erro + stub/`...` ou esqueleto que ainda falha nos BDD de comportamento até a implementação |

Gate interfaces: contratos e comentários de responsabilidade/separação presentes; comportamento completo fica para TDD após unit-test-plan aprovado.

## 6. Compatibilidade

OS-agnostic; Windows/macOS/Linux first-class; utilizável em venv e T19 sem event loop.
