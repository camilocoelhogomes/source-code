# Interfaces — T26-gap-mcp-parallel-slo

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T26-gap-mcp-parallel-slo` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T26-gap-mcp-parallel-slo` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | I-T26-001..007; Protocol WorkerLimiter intacto; modo autônomo. |

## 1. Princípios de separação

| Fronteira | Responsabilidade | Motivo da separação |
|---|---|---|
| `SemaphoreWorkerLimiter` (contadores) | Observar `active`/`waiting`/`peak_active` durante `acquire` | Prova in-process de pico/fila sem mudar o Protocol T04 nem T17 |
| `parallel_slo` | Avaliar wall-clock vs ondas `ceil(N/capacity)` | Regra de aceite BDD-013 compartilhada Robot↔pytest; pura e testável |
| `McpKeywords` (paralelo) | Disparo SSE concorrente + medições | Transporte MCP fora do domínio; Robot só orquestra |
| Tools MCP / Protocol | Inalterados | Escopo = asserts + observabilidade, não novo binding de tools |

## 2. Contratos

### I-T26-001 — Contadores no `SemaphoreWorkerLimiter`

```python
class SemaphoreWorkerLimiter:
    @property
    def active(self) -> int:
        """Slots atualmente na seção crítica."""
        ...

    @property
    def waiting(self) -> int:
        """Threads bloqueadas em acquire aguardando slot."""
        ...

    @property
    def peak_active(self) -> int:
        """Máximo de active desde a construção."""
        ...
```

**Responsabilidade:** expor observação thread-safe do estado do semáforo.  
**Motivo da separação:** não poluir `WorkerLimiter` Protocol (D-T26-001); fakes T14/T17 permanecem válidos.  
**Invariantes:** `0 <= active <= capacity`; `waiting >= 0`; `peak_active <= capacity`; `active==0` e `waiting==0` quando ocioso após joins.  
**Erros:** nenhum nas propriedades.

### I-T26-002 — `min_waves`

```python
def min_waves(n_calls: int, capacity: int) -> int:
    """ceil(n_calls / capacity); exige n_calls>=1 e capacity>=1."""
    ...
```

**Responsabilidade:** onda mínima teórica sob limite.  
**Motivo da separação:** aritmética isolada do avaliador e das keywords.  
**Erros:** `ValueError` se `n_calls < 1` ou `capacity < 1`.

### I-T26-003 — `ParallelSloResult` + `evaluate_parallel_slo`

```python
@dataclass(frozen=True)
class ParallelSloResult:
    ok: bool
    reason: str  # vazio se ok; senão diagnóstico sem secrets
    min_waves: int

def evaluate_parallel_slo(
    *,
    capacity: int,
    n_calls: int,
    wall_seconds: float,
    single_seconds: float,
    tol_low: float = 0.35,
    tol_serial: float = 0.85,
) -> ParallelSloResult:
    ...
```

**Responsabilidade:** aceitar/rejeitar evidência de paralelismo sob limite + fila de excedentes.  
**Motivo da separação:** uma regra (D-T26-002) para pytest e Robot.  
**Regras:**
1. Entradas: `capacity>=1`, `n_calls>=1`, `single_seconds>0`, `wall_seconds>=0` senão `ok=False` com reason.
2. Se `n_calls > capacity`: exigir `wall >= single * (min_waves - tol_low)` (fila/ondas).
3. Se `capacity > 1` e `n_calls > capacity`: exigir `wall < single * n_calls * tol_serial` (não serial total).
4. Se `n_calls <= capacity`: exigir `wall < single * n_calls * tol_serial` quando `n_calls > 1` (paralelismo) **ou**, se `n_calls==1`, apenas `wall` finito/`single>0`.
5. `reason` nunca inclui tokens/env secrets.

### I-T26-004 — Keyword `mcp_parallel_call_tools`

```python
def mcp_parallel_call_tools(
    name: str,
    arguments_json: str,
    n_calls: int,
    base_url: str = "http://127.0.0.1:8001",
) -> dict[str, Any]:
    """Dispara n_calls sessões MCP em paralelo; retorna results/wall_seconds/n_calls."""
    ...
```

**Responsabilidade:** concorrência real no transporte SSE.  
**Motivo da separação:** protocolo MCP ≠ domínio limiter.  
**Invariantes:** `n_calls >= 1`; cada result passa por redaction BDD-014; `wall_seconds` medido no host.  
**Retorno:** `{"results": list[str], "wall_seconds": float, "n_calls": int}`.

### I-T26-005 — Keyword `mcp_measure_single_call_seconds`

```python
def mcp_measure_single_call_seconds(
    name: str,
    arguments_json: str = "{}",
    base_url: str = "http://127.0.0.1:8001",
    samples: int = 2,
) -> float:
    """Mediana de samples chamadas sequenciais (baseline single_seconds)."""
    ...
```

**Responsabilidade:** baseline estável para SLO.  
**Motivo da separação:** medição distinta do assert.  
**Erros:** falha se mediana `<= 0`.

### I-T26-006 — Keyword `mcp_assert_parallel_slo`

```python
def mcp_assert_parallel_slo(
    capacity: int,
    n_calls: int,
    wall_seconds: float,
    single_seconds: float,
) -> None:
    """Delegata evaluate_parallel_slo; levanta AssertionError se ok=False."""
    ...
```

**Responsabilidade:** ponte Robot → avaliador puro.  
**Motivo da separação:** Robot não reimplementa aritmética.

### I-T26-007 — Robot BDD-013 sem smoke sequencial

O caso `BDD-013` em `mcp.robot` **deve** usar I-T26-004..006 com `N = 2 * QUERY_WORKERS` e redaction; **não** pode ser apenas duas `Mcp Call Tool` sequenciais.

## 3. Mapa interfaces → cenários

| Interface | Cenários |
|---|---|
| I-T26-001 | PS-01, PS-02, PS-03, PS-04, PS-06 |
| I-T26-002/003 | PS-03..PS-06, Robot |
| I-T26-004..007 | Robot BDD-013; contratos unitários keywords |
| BDD-014 | PS-07; redaction em I-T26-004 |

## 4. Não-objetivos de interface

- Alterar `WorkerLimiter` Protocol.
- Alterar `/healthz` ou payload T19.
- Novas tools MCP.
