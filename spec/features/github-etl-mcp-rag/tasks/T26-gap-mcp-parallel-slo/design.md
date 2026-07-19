# Design — T26-gap-mcp-parallel-slo

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T26-gap-mcp-parallel-slo` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T26-gap-mcp-parallel-slo` |
| Base | `origin/feature/github-etl-mcp-rag-T22-fix-tooling-e2e-compose-zoekt` |
| Rastreabilidade | BDD-013 (integral), BDD-014 (regressão), REQ-029, BR-006; ENG-010; inventário T01 (lacuna assert-fraco); T04, T17, T21, T22 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Gap-fill BDD-013: paralelismo real + fila/excedentes + SLO; Robot deixa de ser smoke sequencial; modo autônomo. |

## 1. Contexto

BDD-013 exige: múltiplas consultas MCP **simultâneas** processadas em paralelo **até o limite** (`QUERY_WORKERS` / pool query) e **excedentes aguardam capacidade**.

Estado atual (auditoria filha / coverage-inventory):

| Evidência | Problema |
|---|---|
| `e2e/robot/mcp.robot` «BDD-013 Parallel Mcp Tool Calls Succeed» | Duas `Mcp Call Tool` **sequenciais** — smoke de sucesso, não prova concorrência |
| T21 §3.5 | Marcado parcial: «sucesso sob limite; sem assert de SLO/fila de excedentes» |
| `tests/bdd/test_mcp_evidence_server.py` MCP-04 | Já cobre peak ≤ capacity e wait com capacity=1, **sem** SLO de parede (wall-clock) explícito |

Ownership: pai `github-etl-mcp-rag` (ENG-010). Filha não implementa.

## 2. Problema

Classificação REQ-017: `assert-fraco`.

Critério integral BDD-013 **não** é satisfeito por «duas calls com sucesso». Falta:

1. Disparo **concorrente** real (N > 1 ao mesmo tempo).
2. Observação de **pico ≤ limite** e de **fila/excedentes**.
3. Assert de **SLO** (tempo de parede coerente com `ceil(N/capacity)` ondas).
4. Manter BDD-014 (sem eco de token) nas respostas do cenário paralelo.

## 3. Solução proposta

### 3.1 Observabilidade mínima no `SemaphoreWorkerLimiter` (T04 extensão compatível)

Acrescentar contadores thread-safe na implementação concreta (não obrigar o `Protocol`):

| Campo | Semântica |
|---|---|
| `active` | Slots em seção crítica agora |
| `waiting` | Threads bloqueadas em `acquire` (ainda sem slot) |
| `peak_active` | Máximo de `active` desde a construção |

Atualização em `acquire()`: incrementar `waiting` antes do `Semaphore.acquire`; ao obter slot, decrementar `waiting`, incrementar `active`/`peak_active`; no `finally`, decrementar `active`.

**Compatibilidade:** Protocol `WorkerLimiter` inalterado; fakes/doubles existentes seguem válidos. Callers T14/T17 não precisam mudar.

### 3.2 Avaliador puro de SLO (`parallel_slo`)

Módulo `github_rag.concurrency.parallel_slo` com funções puras:

- `min_waves(n_calls, capacity) -> int` = `ceil(n_calls / capacity)`
- `evaluate_parallel_slo(...)` — dados: `capacity`, `n_calls`, `wall_seconds`, `single_seconds`, tolerâncias → resultado tipado (ok / razões de falha)

Regras (D-T26-003):

| Assert | Condição (com folga configurável) |
|---|---|
| Fila / excedentes | Se `n_calls > capacity`: `wall >= single * (min_waves - tol_low)` |
| Paralelismo (não serial total) | Se `capacity > 1` e `n_calls > capacity`: `wall < single * n_calls * tol_serial` |
| Pico (quando medido) | `peak_active <= capacity` e, se saturação forçada, `peak_active >= min(capacity, n_calls)` |

Motivo da separação: Robot e pytest compartilham a mesma regra de aceite SLO sem duplicar aritmética.

### 3.3 Keywords Robot / `McpKeywords.py`

Novas keywords (nomes estáveis para `mcp.robot`):

1. `Mcp Parallel Call Tools` — dispara N invocações MCP **em paralelo** (thread pool; cada thread uma sessão SSE), retorna lista de payloads JSON-string + metadados (`wall_seconds`, `n_calls`).
2. `Mcp Measure Single Call Seconds` — baseline `single_seconds` para o mesmo tool/args.
3. `Mcp Assert Parallel Slo` — delega a `evaluate_parallel_slo`; falha com mensagem sem secrets.
4. Manter `Response Must Not Contain Token` / `_assert_no_token` em cada payload (BDD-014).

### 3.4 Cenário Robot BDD-013 (substitui smoke sequencial)

**Dado** stack e2e com `QUERY_WORKERS` conhecido (compose e2e: `4`; variável Robot `${QUERY_WORKERS}`)  
**E** baseline `single_seconds` de uma `search_code` (ou `list_repos` se search indisponível — preferir `search_code` com `max_matches` baixo)  
**Quando** `N = QUERY_WORKERS + QUERY_WORKERS` (2× capacidade) calls concorrentes do mesmo tool  
**Então** todas sucedem (payload válido)  
**E** SLO de fila/ondas passa (`evaluate_parallel_slo`)  
**E** nenhum payload contém token (BDD-014)

O smoke sequencial antigo **é removido** do caso BDD-013 (não coexistir como falso verde).

### 3.5 Fortalecer BDD/unitário in-process (MCP-04 + limiter)

Em `tests/bdd/test_mcp_evidence_server.py`:

- Manter peak ≤ capacity e excess wait.
- Acrescentar cenário SLO: work com duração controlada `T`, `capacity=1`, `N=3` → `wall >= ~3T` (folga) e `peak_active == 1`; `waiting` observado > 0 enquanto saturado.
- Com `capacity=2`, `N=4`, delay `T`: `peak_active <= 2` e wall coerente com 2 ondas.

Unitário `tests/unit/concurrency/`: contadores `active`/`waiting`/`peak_active`; `parallel_slo` extremos (capacity=1, N=capacity, N>>capacity, single=0 inválido).

## 4. Componentes

| Componente | Papel |
|---|---|
| `SemaphoreWorkerLimiter` | Contadores de observabilidade para prova de pico/fila |
| `parallel_slo` | Contrato puro SLO ondas/excedentes |
| `McpKeywords` | Disparo paralelo SSE + assert SLO + redaction |
| `mcp.robot` | Cenário integral BDD-013 |
| BDD MCP-04 / unit limiter | Prova in-process peak/wait/SLO |

## 5. Fluxo

```text
Robot BDD-013:
  single = measure(search_code)
  results, wall = parallel_call(N=2*QUERY_WORKERS, search_code)
  assert all ok + no token
  evaluate_parallel_slo(capacity=QUERY_WORKERS, n=N, wall, single)

In-process MCP-04:
  spy blocks T seconds inside acquire window
  N threads → observe peak/waiting + wall SLO
```

## 6. Dados

- `QUERY_WORKERS` (env/compose) — capacidade do pool query.
- Nenhuma persistência nova; sem alteração de schema.

## 7. Erros

- SLO falhou → AssertionError/Robot Fail com capacidade, N, wall, single, min_waves (sem token).
- Tool MCP falhou → falha do cenário (não mascarar).
- `single_seconds <= 0` → erro de medição explícito.

## 8. Segurança

- BDD-014 obrigatório em todos os payloads do cenário paralelo.
- Contadores do limiter não expõem segredos.
- Não logar `Authorization` / tokens nas keywords.

## 9. Compatibilidade

- Protocol `WorkerLimiter` estável.
- Tools MCP e wiring T17 inalterados funcionalmente (só observabilidade no limiter concreto).
- `/healthz` **não** muda (evita acoplar T19).
- BDD-011/012/014 Robot preservados.

## 10. Observabilidade

- Contadores in-process para testes.
- Robot observa indiretamente via wall-clock SLO + sucesso concorrente.
- Sem novo endpoint HTTP nesta task.

## 11. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Flake de timing no e2e (rede/Zoekt) | Folgas generosas (`tol_low`/`tol_serial`); preferir `search_code` com carga estável; N=2×capacity |
| Baseline `single` ruidoso | Mediana de 2–3 samples no keyword de measure |
| Contadores race em waiting | Aceitável para asserts «waiting > 0 sob saturação»; peak sob lock |
| Inventário filha ainda marca lacuna | Fora de escopo T26 (T07/auditoria); prova passa a existir no pai |

## 12. Rollback

Reverter branch/PR: robot volta ao smoke sequencial; remover contadores/`parallel_slo`. Sem migração de dados.

## 13. Decisões

| ID | Decisão | Motivo |
|---|---|---|
| D-T26-001 | Contadores só na implementação concreta | Não quebrar Protocol/fakes T04/T17 |
| D-T26-002 | SLO puro compartilhado Robot+pytest | Uma regra de aceite BDD-013 |
| D-T26-003 | Robot: N=2×`QUERY_WORKERS` + wall SLO | Prova fila sem endpoint novo |
| D-T26-004 | Remover smoke sequencial do caso BDD-013 | Eliminar falso verde da denylist |
| D-T26-005 | Não alterar `/healthz` | Isolar de contratos T19 |
| D-T26-006 | Manter redaction BDD-014 no paralelo | Critério de aceite explícito |

## 14. Fora de escopo

- Atualizar `coverage-inventory.md` da filha / fechar denylist documental (T07).
- BDD-011/012 mudanças; DEC-015; browser UI.
- Alterar defaults `QUERY_WORKERS` nos composes.
- Endpoint métricas HTTP.

## 15. Definição de pronto

- Artefatos design→BDD→interfaces→unit→impl→Blue→cov≥95%→docs com gate Architect.
- Robot BDD-013 concorrente + SLO; MCP-04 com SLO; limiter observável.
- PR empilhado sobre T22; não mergeado.
