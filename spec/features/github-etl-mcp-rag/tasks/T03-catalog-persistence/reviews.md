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
