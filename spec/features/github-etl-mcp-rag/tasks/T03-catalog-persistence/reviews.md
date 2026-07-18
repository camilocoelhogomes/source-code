# Reviews — T03-catalog-persistence

> Registro de reviews do Architect por artefato (design, BDD, interfaces, unit tests, implementação, Blue).
> Achados classificados como `BLOCKING`, `MAJOR` ou `SUGGESTION`, com evidência (arquivo/linha) e correção esperada.
> Resultado por review: `CHANGES_REQUIRED` | `APPROVED_BY_ARCHITECT` (ou `BLUE_CHANGES_REQUIRED` | `BLUE_APPROVED_BY_ARCHITECT` na etapa Blue).

## Review Design — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | tech-lead-architect (modo REVIEW; não autor do design) |
| Artefato | `design.md` `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Data | 2026-07-18 |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios verificados

| # | Critério | Veredito | Evidência |
|---|---|---|---|
| 1 | Escopo estrito (sem discovery, UI, Qdrant, Zoekt, indexing pipeline) | OK | design §1 (linha 28), §14 (linhas 302–307); alinhado ao `T03-catalog-persistence.md` "Fora de escopo" |
| 2 | Estados APENAS os 5 de REQ-020, sem extras | OK | §4.1 (linhas 103–115), §4.2, §13 D-T03-004; proíbe `desatualizado`/`indisponível`; `indexing_execution.status` é status de execução distinto de `RepoState` (§5.1 linha 187) |
| 3 | Schema versionado + `last_processed_commit` + `list_active_catalog` p/ reconcile | OK | Alembic §5.3 (linhas 212–216); `last_processed_commit` §5.1 (linha 166); `list_active_catalog()` §5.2 (linhas 208–210), §6 (linha 226); atende ENG-011 |
| 4 | Histórico com mensagem/horário de erro | OK | tabela `indexing_execution` §5.1 (linhas 191–192: `error_message`, `error_at`); `list_execution_history` §6 (linha 233); REQ-023/BDD-008 |
| 5 | File stages `zoekt \| tree_sitter \| metadata_persisted` | OK | `FileStage` §4.1 (linhas 117–123); tabela `file_processing` §5.1 (linhas 194–205); REQ-022 |
| 6 | Testabilidade e riscos aceitáveis | OK | hexagonal + fake in-memory §3.1/§3.3; testcontainers p/ semântica PG §3.2; matriz de riscos §11; estratégia de cobertura ≥95% §3.3 |

### Achados

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| S-1 | SUGGESTION | §4.2 (linhas 129–140) | Máquina de estados não lista explicitamente transições de saída de `queued`/`indexing` para `not_indexed` (dequeue/cancel no reconcile) nem a política de reentrância idempotente; hoje está apenas descrita em prosa (linha 140). | Formalizar no gate `interfaces.md`/unit tests o conjunto fechado completo de transições e a política idempotente (no-op × erro). Não bloqueia o design. |
| S-2 | SUGGESTION | §5.1 (linha 187) | Tipo de `indexing_execution.status` deixado como `text/enum` ("running/succeeded/failed") indefinido. | Decidir (enum nativo × text + CHECK) no gate `interfaces.md`/schema, mantendo separação explícita de `RepoState`. Não bloqueia. |
| S-3 | SUGGESTION | §3.2 (linha 76), §9 (linha 261) | `DATABASE_URL` é uma adição operacional fora de REQ-037; a decisão de não reabrir o contrato T01 congelado é sólida, mas convém deixar rastreável para futura consolidação em `AppSettings`. | Registrar como decisão explícita (D-T03-006 já cobre) e reavaliar em task futura. Não bloqueia. |

### Conclusão

Design íntegro, dentro do escopo aprovado, rastreável a BR-001/BR-004, REQ-020/021/022/023, DEC-005 e ENG-011, e coerente com `implementation-plan §1.3` (porta `CatalogRepository`, PostgreSQL como SoT). Nenhum achado `BLOCKING` ou `MAJOR`. Apenas 3 `SUGGESTION` endereçáveis nos próximos gates (`interfaces.md`/schema). Resultado: `APPROVED_BY_ARCHITECT`.

## Review BDD — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | tech-lead-architect (modo REVIEW; não autor do BDD) |
| Artefato | `bdd.md` `0.1.0` + `tests/bdd/test_catalog_persistence.py` + `tests/bdd/features/catalog_persistence.feature` |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Data | 2026-07-18 |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios de aceite verificados

| # | Critério / requisito | Cenário(s) | Veredito | Evidência |
|---|---|---|---|---|
| 1 | BDD-004: tip main == `last_processed_commit` ⇒ permanece `up_to_date` | CP-01 | OK | `test_catalog_persistence.py` L156–170; feature L11–17; design §4.2 (linha 140) |
| 2 | BDD-005 / ENG-011: novo commit ⇒ volta a `not_indexed`, base preservada | CP-02 | OK | L173–191 (asserta `last_processed_commit`=="C1" mantido); design §4.2 (linha 137) |
| 3 | BDD-004/005: concluir indexação grava `last_processed_commit`==`current_main_commit` | CP-03 | OK | L194–207; design §4.2 (linha 133), §6 (`mark_updated`) |
| 4 | BDD-007 / REQ-021: progresso (percentual, arquivos, etapa) persistido e legível | CP-04 | OK | L210–234; leitura via `list_active_catalog`; design §5.1/§6 |
| 5 | BDD-007 / REQ-022: etapas por arquivo idempotentes (`zoekt`,`tree_sitter`,`metadata_persisted`) | CP-05 | OK | L237–277 (re-registro não duplica; 3 timestamps setados); design §5.1 (linha 206), D-T03-009 |
| 6 | BDD-008 / REQ-023: estado `error` com mensagem + horário | CP-06 | OK | L280–305; design §5.1 (linhas 191–192) |
| 7 | BDD-008 / REQ-023: histórico retém falha entre tentativas (BR-005) | CP-07 | OK | L308–329 (error→queued→indexing; falha "boom" retida); design §4.2 (linha 135) |
| 8 | ENG-011: `list_active_catalog` só ativos, com estado + `last_processed_commit` | CP-08 | OK | L332–356 (soft-delete excluído); design §5.2 |
| 9 | REQ-020: exatamente 5 estados; sem `desatualizado`/`indisponível` | CP-09 | OK | L359–367; design §4.1, D-T03-004 |
| 10 | REQ-020: transição ilegal rejeitada e estado preservado | CP-10 | OK | L370–385 (`not_indexed`→`up_to_date` bloqueado); design §4.2, D-T03-007 |
| 11 | Corner: repositório inexistente ⇒ `RepositoryNotFoundError` | CP-11 | OK | L388–393; design §7 |
| 12 | Corner: update concorrente ⇒ `ConcurrencyConflictError` (não mascarado por transição) | CP-12 | OK | L396–412 (alvo `queued`→`indexing` válido; falha só por `expected_version` stale); design §7, D-T03-008 |
| 13 | Escopo estrito: só persistência via fake in-memory; sem PG/discovery/UI/Qdrant/Zoekt/interfaces/impl | — | OK | usa `InMemoryCatalogRepository`; sem I/O; `catalog/__init__.py` só docstring; sem produção nesta etapa |
| 14 | Evidência RED pré-implementação | — | OK | reproduzido: `Ran 12 tests ... FAILED (failures=12)`, todas por API ausente; sem erro de coleta |

### Achados

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| B-1 | SUGGESTION | `catalog_persistence.feature` (todo o arquivo); `pyproject.toml` L14–17 (sem `pytest-bdd`) | O Gherkin não está vinculado a steps executáveis (não há `pytest-bdd`/`@scenario`); o `.feature` é documentação e a execução real é via `unittest`. A rastreabilidade cenário↔teste é mantida por convenção de nome/comentário, não por binding. | Opcional em gate futuro: adotar `pytest-bdd` para vincular o `.feature` aos steps, ou manter o `.feature` explicitamente como espelho documental. Não bloqueia: comportamento é executável e RED comprovado. |
| B-2 | SUGGESTION | `test_catalog_persistence.py` L80–95 (`_invoke`) e L130–137 | O helper `_invoke` aceita listas de verbos candidatos (`mark_updated`/`mark_up_to_date`, `get`/`find`, etc.), tolerando nomenclatura ainda não fixada. Adequado antes do gate de interfaces, mas afrouxa a asserção do verbo exato. | Congelar os nomes canônicos em `interfaces.md` e, na fase de unitários/impl, reduzir os candidatos ao nome oficial. Não bloqueia nesta etapa. |
| B-3 | SUGGESTION | `test_catalog_persistence.py` L139–153 (`_read_progress`) | Leitura de progresso aceita tanto `entry.progress` (objeto) quanto campos planos (`entry.progress_percent`...). Flexibiliza a forma do `CatalogEntry`/`Progress`. | Fixar a forma de exposição do progresso em `interfaces.md` (design §4.3) e alinhar os testes ao contrato escolhido. Não bloqueia. |

### Conclusão

BDD cobre integralmente os critérios de aceite da persistência (BDD-004/005/007/008, ENG-011, REQ-020/021/022/023) e os corner cases exigidos (repo inexistente, update concorrente), estritamente no escopo de persistência via fake in-memory, sem PG, sem interfaces/implementação. Evidência RED reproduzida (12 falhas pela razão esperada, sem erro de coleta). Nenhum achado `BLOCKING` ou `MAJOR`; 3 `SUGGESTION` para os gates de `interfaces.md`/unitários. Resultado: `APPROVED_BY_ARCHITECT` (gate BDD).

## Review Interfaces — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | tech-lead-architect (modo REVIEW; não autor das interfaces) |
| Artefato | `interfaces.md` `0.1.0` + `src/github_rag/catalog/{__init__,models,errors,transitions,repository}.py` (stubs) |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Data | 2026-07-18 |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios de aceite verificados

| # | Critério | Veredito | Evidência |
|---|---|---|---|
| 1 | Estados fechados REQ-020 (exatamente 5; sem `desatualizado`/`indisponível`) | OK | `models.py` L66–70 (`RepoState`); interfaces §2.2; alinhado a design §4.1/D-T03-004 e BDD CP-09 |
| 2 | `ExecutionStatus` distinto de `RepoState` (resolve S-2) | OK | `models.py` L90–105; interfaces §2.4; não colide com REQ-020 |
| 3 | `list_active_catalog` (só ativos, estado + `last_processed_commit`) | OK | `repository.py` L103–113; interfaces §6; ENG-011/BDD CP-08 |
| 4 | `last_processed_commit` no modelo de leitura | OK | `models.py` L172 (`CatalogEntry`); interfaces §3.2; BR-004 |
| 5 | File stages (`zoekt`/`tree_sitter`/`metadata_persisted`) + registro idempotente | OK | `models.py` L73–87 (`FileStage`), L211–235 (`FileProgress`); `repository.py` L280–306; interfaces §2.3/§3.4/§6; REQ-022/BDD CP-05 |
| 6 | Histórico de erro (mensagem + horário) | OK | `models.py` L182–208 (`IndexingExecution.error_message/error_at`); `repository.py` L184–198/L267–276; interfaces §3.3/§6; REQ-023/BDD CP-06/07 |
| 7 | Comentários de responsabilidade + motivo em cada interface | OK | Docstrings em todos os módulos/enums/dataclasses/erros/métodos (`models.py`, `errors.py`, `transitions.py`, `repository.py`) |
| 8 | Sem implementação (só stubs `...`) | OK | Funções `transitions.py` L94/L110/L134 e métodos do Protocol terminam em `...`; enums/dataclasses são contratos de dados, sem lógica; fake/adaptador não exportados (`__init__.py` L14–17) |
| 9 | Nomes canônicos dentro dos candidatos do BDD | OK | interfaces §1; cada nome (`get_repository`, `reconcile_repository`, `start_execution`, `list_executions`, `mark_updated`, `deactivate_repository`, `transition_state`, `list_file_progress`...) é o 1º candidato de `_invoke` em `test_catalog_persistence.py` L122/L136/L167/L184/L202/L268/L300/L347/L379 — nenhum cenário quebra |
| 10 | Máquina de estados + idempotência (resolve S-1) | OK | `transitions.py` L33–75 (`ALLOWED_TRANSITIONS`/`IDEMPOTENT_SELF_STATES`) cobre `up_to_date→not_indexed`, `error→{queued,not_indexed}`; ordem congelada existência→versão→validade em `transition_state` garante CP-12 (`repository.py` L143–144; interfaces §6) |
| 11 | Erros com responsabilidade e motivo da separação | OK | `errors.py` L24–98; hierarquia raiz `CatalogError`; infra (`CatalogPersistenceError`) separada de domínio; invariante de segurança de credenciais (§8) |
| 12 | Forma do progresso congelada (resolve B-3) | OK | `CatalogEntry.progress: Progress \| None` (`models.py` L174); interfaces §1/§3.1; BDD `_read_progress` lê `entry.progress.*` primeiro |

### Achados

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| I-1 | SUGGESTION | `test_catalog_persistence.py` L130–137 (`_drive_to_up_to_date`); interfaces §7 (linhas 272–273) | Os fluxos CP-01/02/08 chegam a `up_to_date` via `mark_queued→mark_indexing→mark_updated` **sem** `start_execution`, ou seja, `mark_updated`/`mark_error` podem ser chamados sem execução corrente aberta. O contrato descreve "fecha a execução corrente → SUCCEEDED/FAILED", mas não fixa o comportamento quando **não há** execução corrente. | Fixar no gate de unit tests/impl que o fechamento da execução é no-op quando não há execução corrente (a transição de estado + carimbo de commit ocorrem mesmo assim), garantindo CP-01/02/08. Não bloqueia: o contrato é satisfazível sem quebrar BDD. |
| I-2 | SUGGESTION | `repository.py` L162–169; interfaces §7 (linha 271: "par de `start_execution`") | A expressão "par de `start_execution`" para `mark_indexing` é ambígua quanto a abrir (ou não) uma execução implicitamente. O BDD abre a execução **explicitamente** após `mark_indexing`. | Explicitar no gate de unit tests que `mark_indexing` **não** abre execução implícita (evita execução duplicada em CP-05/07). Não bloqueia. |
| I-3 | SUGGESTION | `errors.py` L38–49; `repository.py` L294/L304/L274 | `RepositoryNotFoundError` é reutilizado para `execution_id` inexistente (`record_file_stage`/`list_file_progress`/`list_executions`), decisão já documentada (interfaces §4). Semanticamente é um repo-not-found aplicado a execução. | Opcional em gate futuro: considerar `ExecutionNotFoundError` dedicado. Aceitável agora por estar documentado e não exercido negativamente pelo BDD. Não bloqueia. |

### Conclusão

Interfaces congelam corretamente enums fechados (REQ-020 + `ExecutionStatus` distinto), modelos de leitura imutáveis, hierarquia de erros, a máquina de estados declarativa (S-1) e a porta `CatalogRepository` com nomes canônicos 100% dentro dos candidatos do BDD (nenhum cenário quebra). Todos os stubs são `...` (sem implementação); fake/adaptador ficam fora do gate, mantendo o BDD em RED como esperado. Comentários de responsabilidade e motivo presentes em toda interface. Nenhum achado `BLOCKING` ou `MAJOR`; 3 `SUGGESTION` para o gate de unit tests/impl. Resultado: `APPROVED_BY_ARCHITECT` (gate INTERFACES).

## Review Unit Tests — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | tech-lead-architect (modo REVIEW; não autor dos unit tests) |
| Artefato | `unit-test-plan.md` `0.1.0` + `tests/unit/catalog/{test_transitions,test_models,test_memory_repository}.py` |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Data | 2026-07-18 |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios verificados

| # | Critério | Veredito | Evidência |
|---|---|---|---|
| 1 | Suficiência de extremos/corner cases | OK | `transitions`: varredura exaustiva 5×5 (`test_all_other_pairs_are_rejected` L100–107), auto-transições idempotentes×ilegais (L90–98), pulos ilegais representativos (L109–127), `is_up_to_date` com `None` em proc/tip/ambos + case-sensitive + SHA-40 (L152–172); `memory`: not found em todas as operações, sequências vazias, boundaries `0`/`100` (L409–416), idempotência de file stage (L494–500), retenção de histórico entre tentativas e após soft-delete (L449–470) |
| 2 | Aderência às interfaces `APPROVED` | OK | imports de `github_rag.catalog` ⊆ `__init__.__all__`; chamadas casam com assinaturas do Protocol: `upsert_repository(**kw)` keyword-only (repository.py L69–77), `update_progress(rid,percent,fp,ft,stage)` posicional (L230–237), `mark_error(rid,msg,at)` (L184–189), `transition_state(id,target,*,expected_version)` (L127–133), `start_execution(rid,commit_target)` (L251–255); leitura de progresso via `entry.progress.*` (B-3, models.py L174) |
| 3 | Evidência RED reproduzida | OK | `test_transitions.py` → `54 failed, 11 passed, 9 subtests passed`; `test_models.py` → `14 passed`; `test_memory_repository.py` → `ModuleNotFoundError: github_rag.catalog.memory` na coleta. Idêntico ao registrado no plano §10 |
| 4 | Sem implementação de produção nos testes | OK | helpers `_register`/`_drive_to_indexing`/`_drive_to_up_to_date` (test_memory_repository.py L53–70) apenas compõem chamadas da API pública; nenhuma lógica de domínio/persistência nos testes |
| 5 | Ordem de erros de concorrência (existência→versão→validade) | OK | `test_missing_repository_checked_before_version_and_validity` (L187–192), `test_stale_version_raises_conflict_even_when_target_valid` (L194–201, alvo válido), `test_version_checked_before_validity` (L203–211, stale+ilegal⇒conflito), `test_illegal_transition_with_correct_version_...preserves_state` (L213–221) |
| 6 | I-1/I-2/I-3 endereçados | OK | I-1: `test_mark_updated_without_open_execution_is_noop_closure` (L300–306) + `test_mark_error_without_open_execution_is_noop_closure` (L325–330); I-2: `test_mark_indexing_does_not_open_execution_implicitly` (L269–272); I-3: `test_record_file_stage_missing_execution_raises_not_found` (L509–511) + `test_list_file_progress_missing_execution_raises_not_found` (L517–519) reutilizando `RepositoryNotFoundError` |
| 7 | Contagens do plano conferem | OK | `test_transitions.py`=18, `test_models.py`=14, `test_memory_repository.py`=56 métodos — batem com plano §4/§5/§6 |
| 8 | `models` fora do alvo do RED (blindagem) | OK | enums fechados REQ-020, `ExecutionStatus` disjunto (test_models.py L80–82), imutabilidade `frozen` e defaults `None` — 14 verdes por design |

### Achados

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| U-1 | SUGGESTION | `test_memory_repository.py` L372–379 (`test_reconcile_stays_up_to_date_when_tip_absent`) | O nome/comentário do teste sugere o ramo "tip ausente" (`current_main_commit is None`) do reconcile (interfaces §5.4), mas o corpo chama `mark_updated`, que fixa `current_main_commit == "C1"`; o caso exercido é, na prática, "tip presente e igual" (redundante com `test_reconcile_keeps_up_to_date_when_commit_matches`). Via API pública do fake não há caminho para atingir `up_to_date` com tip `None`, logo o ramo pode ser inalcançável. | No gate de impl, renomear/ajustar o comentário para refletir "tip igual" ou documentar que o ramo "tip ausente" é inalcançável pela porta. Não bloqueia: cobertura efetiva do reconcile é garantida por CP-01/CP-02. |

### Conclusão

Os unit tests cobrem contratos, extremos, corner cases, entradas inválidas, estados vazios, falhas, concorrência e idempotência, aderindo integralmente às interfaces congeladas (`APPROVED_BY_ARCHITECT`), sem implementação de produção nos testes. A ordem de checagem de concorrência (existência→versão→validade) e as decisões I-1/I-2/I-3 estão fixadas. Evidência RED reproduzida e idêntica ao plano (transitions 54 falhas / memory ModuleNotFoundError; models verdes por serem blindagem, não alvo do RED). Nenhum achado `BLOCKING` ou `MAJOR`; 1 `SUGGESTION` (U-1) para o gate de implementação. Resultado: `APPROVED_BY_ARCHITECT` (gate UNIT_TESTS).

## Review Implementação — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | tech-lead-architect (modo REVIEW; não autor da implementação) |
| Artefato | `src/github_rag/catalog/{models,transitions,errors,repository,memory}.py` + `catalog/postgres/{__init__,models,factory,repository}.py` + `migrations/` + `pyproject.toml` (deps/omit) + `tests/integration/test_postgres_catalog_repository.py` |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Data | 2026-07-18 |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios de aceite verificados

| # | Critério | Veredito | Evidência |
|---|---|---|---|
| 1 | Correção funcional (BDD + unit verdes) | OK | Execução `PYTHONPATH=src ... -m pytest -q` → `137 passed, 1 skipped, 92 subtests`; sem RED remanescente |
| 2 | Arquitetura hexagonal (domínio puro × porta × fake × adaptador) | OK | `models/transitions/errors` sem I/O; `repository.py` Protocol `@runtime_checkable`; `memory.py` (fake) e `postgres/repository.py` (adaptador) implementam a MESMA porta; import do driver isolado em `catalog.postgres` |
| 3 | Estados REQ-020 exatamente 5; máquina fechada + idempotência | OK | `transitions.ALLOWED_TRANSITIONS` L34–40 == spec congelada; `IDEMPOTENT_SELF_STATES` L62–64; `test_transitions.py` (18 casos, varredura 5×5) verde |
| 4 | Ordem de concorrência existência→versão→validade | OK | `memory.transition_state` L188–196 e `postgres.transition_state` L259–270 (require→version check→`ensure_transition_allowed`); `test_version_checked_before_validity`/`test_stale_version_raises_conflict_even_when_target_valid` verdes |
| 5 | Soft-delete com retenção de histórico | OK | `deactivate_repository` seta `active=False`/`deactivated_at` (memory L167–169; pg L228–235); `upsert` reativa mesma identidade (memory L136–149; pg L203–211); `test_history_retained_after_soft_delete` verde |
| 6 | `last_processed_commit`/reconcile (ENG-011/BR-004) | OK | `mark_updated` carimba `last_processed=current_main=commit`; `reconcile_repository` rebaixa `up_to_date→not_indexed` preservando base (memory L245–255; pg L336–348); CP-01/CP-02 verdes |
| 7 | Histórico com mensagem+horário (REQ-023) | OK | `mark_error` fecha execução `FAILED` com `error_message`/`error_at` (memory L222–237; pg L304–324); `IndexingExecution` retido entre tentativas |
| 8 | File stages idempotentes (REQ-022) | OK | `record_file_stage` seta timestamp só se `None` (memory L323–327; pg L423–425); unicidade `(execution_id,file_path)` via índice `ux_file_processing_execution_path` |
| 9 | Segurança — `DATABASE_URL` sem vazar | OK | `factory.py` L42–50: ausência e falha de engine ⇒ `CatalogPersistenceError` com mensagem genérica, sem incluir a URL; `_unit_of_work` L81–85 encapsula `SQLAlchemyError` em mensagem genérica; nenhum `log`/`print` da URL; `env.py` não registra credenciais |
| 10 | Schema versionado (Alembic) + enums nativos | OK | `migrations/versions/0001_initial_catalog_schema.py` cria enums `repo_origin`/`repo_state`/`execution_status`, 3 tabelas, `CHECK` de origem, índice parcial `WHERE active`; `env.py` usa `Base.metadata` (fonte única) |
| 11 | Cobertura ≥95% + omit do adaptador PG justificado | OK | Total 98.71% (`fail_under=95`); `omit=*/catalog/postgres/*` documentado em `pyproject.toml` L39–44 (I/O só exercível com PG real; paridade validada por `tests/integration` sob marcador `integration`, pulado sem Docker) |
| 12 | Não enfraquecimento de testes | OK | Unit `assertIs(...,True/False)`/`assertRaises` estritos; BDD `_invoke` usa nomes canônicos congelados como 1º candidato (interfaces §1); nenhuma asserção afrouxada |

### Achados

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| M-1 | SUGGESTION | `postgres/models.py` L87 (`current_execution_id` Integer sem `ForeignKey`); design §5.1 (linha 173: "bigint NULL FK") | O design descreve `current_execution_id` como FK para `indexing_execution(id)`; a implementação usa `Integer` simples (ORM e migration), provavelmente para evitar FK circular (`catalog_repository`↔`indexing_execution`). Comportamento preservado e testado. | Documentar explicitamente a decisão (evitar circularidade) no design ou adicionar FK `DEFERRABLE`/`use_alter` em gate futuro. Não bloqueia. |
| M-2 | SUGGESTION | `memory.py` L251 e `test_memory_repository.py` L372–379 (U-1 remanescente) | Ramo "tip ausente" do reconcile (`current_main_commit is None`) é inalcançável pela API pública (todo caminho a `up_to_date` passa por `mark_updated`, que fixa o tip). Branch defensivo; nome do teste ainda sugere "tip ausente". Coincide com `postgres/repository.py` L341–342 (mesmo ramo, omitido da cobertura). | Renomear o teste/comentário ou marcar o ramo como defensivo documentado. Não bloqueia; reconcile efetivo coberto por CP-01/CP-02. |
| M-3 | SUGGESTION | `memory.py` L101–123 (`_close_current_execution`); `postgres/repository.py` L165–183 | Após `mark_updated`/`mark_error`, `current_execution_id` continua apontando para a execução já fechada (não é limpo). Sem impacto: novo ciclo reatribui via `start_execution`; leitura de histórico é correta. | Opcional: limpar `current_execution_id` ao fechar, para que "execução corrente" reflita "há execução em andamento". Não bloqueia. |

### Conclusão

Implementação correta, aderente às interfaces congeladas e ao design aprovado, com arquitetura hexagonal respeitada (domínio puro testável sem PG; adaptador PG isolado atrás da porta). Máquina de estados fechada, ordem de concorrência (existência→versão→validade), soft-delete com retenção de histórico, comparação de commit/reconcile, progresso e etapas por arquivo idempotentes — todos verificados por testes verdes. Segurança de `DATABASE_URL` preservada (nenhuma mensagem vaza a URL/credenciais). Cobertura 98.71% ≥ 95% com `omit` do adaptador PG justificado e paridade validada por testes `integration`. Testes não foram enfraquecidos. Nenhum achado `BLOCKING` ou `MAJOR`; 3 `SUGGESTION` (M-1/M-2/M-3) para gates futuros. Resultado: `APPROVED_BY_ARCHITECT` (gate IMPLEMENTATION).

## Review Blue (refatoração) — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | tech-lead-architect (modo REVIEW) |
| Artefato | Implementação T03 (domínio + fake + adaptador PG) + `refactoring.md` (baseline) |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Data | 2026-07-18 |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

### Análise de complexidade / gargalos (com evidência)

| Item | Observação | Veredito |
|---|---|---|
| `InMemoryCatalogRepository.upsert_repository` | Varredura linear O(n) dos repos para achar identidade (`memory.py` L136–140) | Aceitável: fake de domínio/teste; n = tamanho do catálogo (dezenas–centenas); não é caminho de produção. Sem gargalo comprovado. |
| `list_active_catalog` (memory) | Filtro linear O(n) | Aceitável: leitura de catálogo pequeno; adaptador PG usa índice. |
| Adaptador PG | Consultas por PK (`session.get`) e índices únicos (`ux_*`) | Sem gargalo comprovado; acesso indexado. |
| Duplicação fake × adaptador (`_STAGE_FIELD`, `_now`, `_close_current_execution`, lógica de reconcile) | Duplicação intencional para paridade da porta (design §3.3) | Extrair para domínio compartilhado é possível, mas borraria a fronteira hexagonal e é otimização especulativa sem ganho medido. NÃO solicitado. |

### Baseline reproduzível (antes)

`PYTHONPATH=src <venv>/bin/python -m pytest -p no:cacheprovider -q`:
`137 passed, 1 skipped, 92 subtests in 0.15s`; cobertura total **98.71%** (`fail_under=95`).

### Conclusão

Complexidade adequada ao escopo (camada de persistência); nenhum gargalo de performance comprovado por medição. As alegações de simplificação disponíveis (deduplicação fake×adaptador) são especulativas e contrariam a separação hexagonal aprovada — não devem ser exigidas na etapa Blue. Testes verdes e baseline reproduzível registrados em `refactoring.md`. **Nenhum gargalo comprovado ⇒ nenhuma meta Blue.** Resultado: `BLUE_APPROVED_BY_ARCHITECT`.
