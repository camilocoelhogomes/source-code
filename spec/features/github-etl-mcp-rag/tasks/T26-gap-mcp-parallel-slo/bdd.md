# BDD — T26-gap-mcp-parallel-slo

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T26-gap-mcp-parallel-slo` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Execução (contratos) | `tests/bdd/test_mcp_parallel_slo.py` (+ extensão MCP-04 em `tests/bdd/test_mcp_evidence_server.py`) |
| Execução (Robot / stack) | `e2e/robot/mcp.robot` tag `bdd013` via `McpKeywords` — operador/CI e2e (T21/T22) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Cenários PS-01..PS-07 + Robot BDD-013 integral. |
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Alinhado a D-T26-001..006; remove smoke sequencial. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **pytest BDD** | Limiter observável; SLO puro; MCP-04 wall-clock + peak/wait | CI padrão |
| **Robot** | N calls MCP concorrentes reais + SLO sob `QUERY_WORKERS` + sem token | Stack e2e (não no gate pytest compose-up) |

---

## PS-01 — Contadores: peak nunca excede capacity

**Rastreabilidade:** BDD-013; D-T26-001; T04

**Dado** `SemaphoreWorkerLimiter(capacity=2, pool="query")`  
**E** seção crítica que bloqueia até release  
**Quando** 4 threads entram em `acquire()` concorrentemente  
**Então** `peak_active <= 2` em todo o intervalo  
**E** após release e join, todas as threads completam  
**E** `active == 0` ao final

**Critérios de verificação**
- `assert limiter.peak_active <= 2`
- `assert limiter.active == 0` pós-join

---

## PS-02 — Excedentes aguardam (waiting observável)

**Rastreabilidade:** BDD-013; BR-006

**Dado** limiter `capacity=1`  
**Quando** a primeira thread segura o slot  
**E** a segunda tenta `acquire()`  
**Então** a segunda permanece bloqueada (`entered_second` falso)  
**E** `waiting >= 1` enquanto a primeira não libera  
**Quando** a primeira libera  
**Então** a segunda entra e completa

---

## PS-03 — SLO wall-clock com capacity=1 (ondas = N)

**Rastreabilidade:** BDD-013; D-T26-002; D-T26-003

**Dado** work com duração controlada `T ≈ 0.15s` dentro do slot  
**E** `capacity=1`, `N=3` threads  
**Quando** as N invocações correm em paralelo sob o limiter  
**Então** `peak_active == 1`  
**E** `evaluate_parallel_slo` aceita `wall_seconds` com `single_seconds≈T`  
**E** `wall_seconds >= T * (3 - tol)` (excedentes enfileirados)

---

## PS-04 — SLO com capacity=2 e N=4 (duas ondas + paralelismo)

**Rastreabilidade:** BDD-013; REQ-029

**Dado** work `T ≈ 0.15s`, `capacity=2`, `N=4`  
**Quando** 4 threads adquirem concorrentemente  
**Então** `peak_active <= 2` e `peak_active >= 1`  
**E** SLO passa: wall coerente com `min_waves=2` e estritamente menor que serial total `4*T` (folga)

---

## PS-05 — Avaliador puro rejeita smoke sequencial disfarçado

**Rastreabilidade:** D-T26-004

**Dado** `capacity=4`, `n_calls=8`, `single_seconds=1.0`  
**Quando** `wall_seconds ≈ 8.0` (serial total)  
**Então** `evaluate_parallel_slo` **falha** (não houve paralelismo sob limite)  
**Quando** `wall_seconds ≈ 1.0` com `n_calls=8` (ilimitado)  
**Então** falha por ausência de fila/ondas (`n > capacity`)  
**Quando** `wall_seconds ≈ 2.0`  
**Então** aceita

---

## PS-06 — MCP-04 SLO na superfície de tools (search_code)

**Rastreabilidade:** BDD-013; MCP-04; I-T17-006

**Dado** server MCP com `query_limiter` capacity=1 e spy que dorme `T` em `search_exact`  
**Quando** 3 `search_code` concorrentes via app  
**Então** `peak_active <= 1`  
**E** wall satisfaz `evaluate_parallel_slo`  
**E** as 3 completam com sucesso

---

## PS-07 — BDD-014 no caminho paralelo (sem eco de token)

**Rastreabilidade:** BDD-014; D-T26-006

**Dado** token sentinela no ambiente de teste  
**Quando** N calls paralelas de `list_repos` (ou search) sucedem  
**Então** nenhum payload/`str` de erro contém o token

---

## Robot — BDD-013 integral (documental; prova em stack)

**Arquivo:** `e2e/robot/mcp.robot`  
**Tags:** `bdd013`  
**Keywords:** `Mcp Measure Single Call Seconds`, `Mcp Parallel Call Tools`, `Mcp Assert Parallel Slo`

**Dado** `${QUERY_WORKERS}` (default `4`, alinhado a `docker-compose.e2e.yml`)  
**E** baseline `single` via `search_code` `{"pattern":"def","max_matches":3}`  
**Quando** `N=${QUERY_WORKERS}*2` calls concorrentes do mesmo tool  
**Então** todos os resultados contêm `hits` (ou estrutura válida)  
**E** `Mcp Assert Parallel Slo` passa  
**E** `Response Must Not Contain Token` em cada resultado  
**E** o caso **não** usa duas calls sequenciais como único assert

**Nota gate pytest:** contratos das keywords / `parallel_slo` / limiter são cobertos por PS-*; Robot real depende de T22 stack.

---

## Mapa de rastreabilidade

| Cenário | BDD produto | Design |
|---|---|---|
| PS-01 | BDD-013 | D-T26-001 |
| PS-02 | BDD-013 | D-T26-001 |
| PS-03 | BDD-013 | D-T26-002/003 |
| PS-04 | BDD-013 | D-T26-002/003 |
| PS-05 | BDD-013 | D-T26-004 |
| PS-06 | BDD-013 | MCP-04 |
| PS-07 | BDD-014 | D-T26-006 |
| Robot bdd013 | BDD-013/014 | D-T26-003/004/006 |

## Execução

```bash
python -m pytest tests/bdd/test_mcp_parallel_slo.py tests/bdd/test_mcp_evidence_server.py -q --tb=short
```
