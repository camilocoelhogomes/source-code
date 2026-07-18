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
