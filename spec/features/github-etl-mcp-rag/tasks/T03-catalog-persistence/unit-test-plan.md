# Plano de testes unitários — T03-catalog-persistence

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T03-catalog-persistence` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` (review independente — modo autônomo; ver `reviews.md`) |
| Versão | `0.1.0` |
| Interfaces base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Escopo | Testes unitários dos contratos do catálogo (domínio puro + porta via fake in-memory). Sem implementação de produção além dos stubs já congelados. |

## 1. Objetivo

Verificar, **antes da implementação**, o comportamento congelado nas interfaces
(`interfaces.md` §5/§6/§7): a máquina de estados pura (`transitions.py`), a forma
dos read models (`models.py`) e o contrato de comportamento da porta
`CatalogRepository` exercido contra o fake `InMemoryCatalogRepository`. A suíte
deve falhar (RED) pela ausência de implementação:

- `transitions.is_transition_allowed` / `ensure_transition_allowed` / `is_up_to_date`
  permanecem stub (`...` ⇒ retornam `None`);
- `github_rag.catalog.memory.InMemoryCatalogRepository` **ainda não existe**.

## 2. Decisões fixadas neste gate (reviews SUGGESTION I-1 / I-2 / I-3)

| ID | Decisão fixada nos testes |
|---|---|
| I-1 | `mark_updated` / `mark_error` **sem execução corrente aberta** = **no-op de fechamento**: a transição de estado e o carimbo de commit ocorrem mesmo assim; nenhuma execução é criada nem alterada (`test_mark_updated_without_open_execution_is_noop_closure`, `test_mark_error_without_open_execution_is_noop_closure`). |
| I-2 | `mark_indexing` **não abre execução implícita**: após `mark_indexing`, o histórico permanece vazio até `start_execution` (`test_mark_indexing_does_not_open_execution_implicitly`). |
| I-3 | `execution_id` inexistente reutiliza `RepositoryNotFoundError` em `record_file_stage` / `list_file_progress` (I-3 documentado; `ExecutionNotFoundError` fica para gate futuro). |

## 3. Superfície sob teste

| Símbolo | Módulo | Tipo de verificação |
|---|---|---|
| `ALLOWED_TRANSITIONS` / `IDEMPOTENT_SELF_STATES` | `github_rag.catalog.transitions` | Contrato declarativo (dados) |
| `is_transition_allowed` / `ensure_transition_allowed` / `is_up_to_date` | `github_rag.catalog.transitions` | Comportamento (RED até implementação) |
| `RepoState` / `RepoOrigin` / `FileStage` / `ExecutionStatus` | `github_rag.catalog.models` | Enums fechados |
| `Progress` / `CatalogEntry` / `IndexingExecution` / `FileProgress` | `github_rag.catalog.models` | Read models imutáveis (`frozen`) |
| `CatalogRepository` (via `InMemoryCatalogRepository`) | `github_rag.catalog.memory` | Comportamento da porta (RED — módulo ausente) |
| `RepositoryNotFoundError` / `InvalidStateTransitionError` / `ConcurrencyConflictError` | `github_rag.catalog.errors` | Erros de domínio |

**Fora de escopo:** adaptador PG (`PostgresCatalogRepository`), migrations Alembic,
`CatalogPersistenceError` (exclusivo do adaptador; testado no gate de impl com
testcontainers), UI/MCP.

## 4. Casos — `test_transitions.py` (18 métodos)

| ID | Caso | Expectativa | Contrato |
|---|---|---|---|
| TR-01 | `ALLOWED_TRANSITIONS` == spec congelada | igualdade exata | §5.1 |
| TR-02 | Toda `RepoState` é chave de origem | domínio completo | §5.1 |
| TR-03 | `IDEMPOTENT_SELF_STATES` == {not_indexed, queued} | igualdade | §5.2 |
| TR-04 | indexing/up_to_date/error sem auto-idempotência | ausentes do set | §5.2 |
| TR-05 | Todos os pares válidos ⇒ `True` | `assertIs(..., True)` | §5.1 |
| TR-06 | Auto-transições idempotentes ⇒ `True` | `assertIs(..., True)` | §5.2 |
| TR-07 | Auto-transições ilegais ⇒ `False` | `assertIs(..., False)` | §5.2 |
| TR-08 | Todo par não listado ⇒ `False` (varredura exaustiva 5×5) | `assertIs(..., False)` | §5.1 |
| TR-09 | Pulos ilegais representativos ⇒ `False` (CP-10) | `assertIs(..., False)` | §5.1 |
| TR-10 | `ensure_transition_allowed` válido ⇒ não levanta / `None` | no-op | §5.1 |
| TR-11 | `ensure_transition_allowed` ilegal ⇒ `InvalidStateTransitionError` | raise | §5.1/CP-10 |
| TR-12..18 | `is_up_to_date`: iguais⇒True; diferentes⇒False; `None` (proc/tip/ambos)⇒False; case-sensitive⇒False; SHA-40 igual⇒True | `assertIs` estrito | §5.3/BR-002/004 |

**RED esperado:** TR-05..09 e TR-11..18 falham (stub retorna `None`, não `True/False`
nem levanta). Passam: TR-01..04 (dados congelados) e TR-10 (no-op coincide com stub).

## 5. Casos — `test_models.py` (14 métodos)

Blindam a forma congelada contra regressão durante a implementação: enums fechados
(REQ-020 exatamente 5; `ExecutionStatus` disjunto de `RepoState`), herança de `str`,
lookup por valor, `ValueError` em valor desconhecido, imutabilidade `frozen`
(`FrozenInstanceError` em `setattr`) e defaults `None` dos campos opcionais de
`CatalogEntry`/`IndexingExecution`/`FileProgress`/`Progress`.

**Nota:** os modelos são contratos de dados já congelados no gate de interfaces
(sem `...`); portanto **estes 14 casos passam desde já** — não são o alvo do RED,
mas guardam a superfície de leitura consumida por T07/T14/T17/T18.

## 6. Casos — `test_memory_repository.py` (56 métodos)

Contrato de comportamento da porta `CatalogRepository` (interfaces §6/§7) contra o
fake in-memory. Grupos:

| Grupo | Cobertura |
|---|---|
| `upsert` / `get` / soft-delete / `list_active_catalog` | criação em `not_indexed`/`active`; origem local; preservação de estado/commit no re-upsert; reativação de soft-deleted mesma identidade; `get` not found; lista vazia; exclusão de desativados; exposição de estado + `last_processed_commit`; `deactivate` seta flags; not found |
| `transition_state` (ordem congelada existência → versão → validade) | transição válida + bump de versão; auto-idempotente no-op; **not found antes** de versão/validade; **versão stale ⇒ conflito mesmo com alvo válido** (CP-12); **versão antes de validade** (stale + ilegal ⇒ conflito); ilegal com versão correta ⇒ erro + estado preservado (CP-10); reuso de versão consumida ⇒ conflito |
| atalhos `mark_*` (efeitos §7) | `mark_queued` de not_indexed/error/queued(no-op)/ilegal de up_to_date/not found; `mark_indexing` de queued/**não abre execução (I-2)**/ilegal/not found; `mark_updated` carimba commits + fecha execução SUCCEEDED/**no-op sem execução (I-1)**/ilegal; `mark_error` seta error + FAILED com msg+horário (CP-06)/**no-op sem execução (I-1)**/ilegal |
| `update_main_commit` / `reconcile_repository` | tip sem mudar estado; not found; reconcile mantém up_to_date se igual (CP-01); reverte a not_indexed preservando base se difere (CP-02); mantém se tip ausente; no-op fora de up_to_date; not found |
| `update_progress` (REQ-021) | armazenado e legível via `progress`; extremos 0 e 100; not found |
| `start_execution` / `list_executions` (REQ-023) | cria RUNNING e vincula corrente; not found; histórico vazio; not found; **histórico retém falha entre tentativas** (CP-07/BR-005); histórico retido após soft-delete |
| `record_file_stage` / `list_file_progress` (REQ-022) | 3 etapas setam 3 timestamps; **re-registro idempotente sem duplicar** (CP-05); arquivos distintos ⇒ linhas distintas; execução inexistente ⇒ not found (I-3); lista vazia; execução inexistente ⇒ not found |

**RED esperado:** o módulo `github_rag.catalog.memory` não existe ⇒ o import de topo
falha na **coleta** com `ModuleNotFoundError` — RED estrutural documentado. Quando o
Developer criar o fake, os 56 casos passam a coletar e devem ficar verdes (paridade
com o adaptador PG).

## 7. Estratégia RED

- Domínio puro (`transitions`): asserções estritas (`assertIs(..., True/False)` e
  `assertRaises`) forçam falha enquanto os stubs retornam `None`.
- Porta (`memory`): import de topo do módulo inexistente ⇒ falha de coleta
  (`ModuleNotFoundError`) — a razão esperada e reproduzível.
- Modelos (`models`): já congelados; verdes por design (não são alvo do RED).

## 8. Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Plano | `spec/features/github-etl-mcp-rag/tasks/T03-catalog-persistence/unit-test-plan.md` |
| Domínio puro | `tests/unit/catalog/test_transitions.py` |
| Read models | `tests/unit/catalog/test_models.py` |
| Contrato da porta | `tests/unit/catalog/test_memory_repository.py` |

## 9. Comandos

```bash
# venv do workspace canônico + PYTHONPATH=src (workspace T03 sem .venv próprio)
PYTHONPATH=src /Users/camilocoelhogomes/projects/github_rag/.venv/bin/python \
  -m pytest tests/unit/catalog -p no:cacheprovider --no-cov -q
```

`--no-cov` é usado nesta etapa para isolar o sinal RED do gate de cobertura
(`fail_under=95`), que só se aplica **após** a implementação.

## 10. Evidência RED (pré-implementação, 2026-07-18)

Execução completa da pasta `tests/unit/catalog` (a coleta é interrompida pelo
módulo `memory` ausente):

```
ERROR collecting tests/unit/catalog/test_memory_repository.py
E   ModuleNotFoundError: No module named 'github_rag.catalog.memory'
!!! Interrupted: 1 error during collection !!!
1 error in 0.10s
```

Execução por arquivo (isolando os grupos coletáveis):

```
tests/unit/catalog/test_transitions.py .......... 54 failed, 11 passed, 9 subtests passed in 0.13s
tests/unit/catalog/test_models.py ............... 14 passed in 0.01s
tests/unit/catalog/test_memory_repository.py .... 1 error (ModuleNotFoundError: github_rag.catalog.memory)
```

Interpretação:

- `test_transitions.py` — **54 falhas** pela razão esperada: `is_transition_allowed`
  / `is_up_to_date` retornam `None` (stub) em vez de `True/False`, e
  `ensure_transition_allowed` não levanta `InvalidStateTransitionError` nos casos
  ilegais. **11 passam** (contrato declarativo `ALLOWED_TRANSITIONS`/
  `IDEMPOTENT_SELF_STATES` + `ensure` válido no-op). Sem erro de coleta.
- `test_models.py` — **14 passam**: read models/enums já congelados (não são alvo
  do RED; blindagem contra regressão).
- `test_memory_repository.py` — **erro de coleta** `ModuleNotFoundError:
  github_rag.catalog.memory`: o fake ainda não foi implementado (trabalho do
  Developer) — RED estrutural esperado.

## 11. Bloqueios preexistentes de execução

| ID | Bloqueio | Evidência (2026-07-18) | Impacto |
|---|---|---|---|
| BLK-01 | Workspace T03 sem `.venv` próprio | `ls .venv` → ausente | Execução usa `../github_rag/.venv` com `PYTHONPATH=src` |
| BLK-02 | Launcher `python` ausente no host (macOS); `python3` disponível | comando canônico pós-venv permanece `python -m pytest` | Checks QA no greenfield usam o interpretador do venv canônico |

**Não são bloqueios:** as 54 falhas de `transitions` e o `ModuleNotFoundError` de
`memory` — RED esperado até a implementação (domínio + fake).

## 12. Cobertura

Gate de cobertura ≥95% aplica-se **após** a implementação (domínio + fake +
adaptador PG). Nesta etapa o objetivo é o RED comportamental/estrutural documentado,
não o threshold de coverage. `pyproject.toml` já define `--cov=github_rag`,
`branch=true` e `fail_under=95`.

## 13. Critérios de pronto (unit tests)

- [ ] Contratos, extremos, corner cases, entradas inválidas, estados vazios, falhas
      e idempotência cobertos.
- [ ] Máquina de estados: transições válidas e inválidas (incluindo auto-transições).
- [ ] Repo/execução inexistente ⇒ `RepositoryNotFoundError`.
- [ ] Update concorrente (versão stale) ⇒ `ConcurrencyConflictError` na ordem
      existência → versão → validade.
- [ ] `is_up_to_date` / `reconcile_repository` cobertos.
- [ ] File stages idempotentes; histórico de execução retido.
- [ ] Soft-delete filtra `list_active_catalog`.
- [ ] I-1/I-2/I-3 fixados nos testes.
- [ ] Evidência RED reproduzida e registrada.
- [ ] Review do Architect.
