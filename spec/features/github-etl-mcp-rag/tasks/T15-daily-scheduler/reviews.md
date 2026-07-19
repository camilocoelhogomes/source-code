# Reviews — T15-daily-scheduler

## Revisão 1 — Tech Lead Architect — `design.md` v0.1.0 → v0.2.0

- **Revisor:** Tech Lead Architect
- **Artefato:** `spec/features/github-etl-mcp-rag/tasks/T15-daily-scheduler/design.md`
- **Data:** 2026-07-18

### Achados

| ID | Severidade | Evidência | Descrição | Correção esperada |
|---|---|---|---|---|
| M-T15-01 | MAJOR | `design.md` v0.1.0 §3.3 (`on_tick(): StartupIndexReconcile.run() + run_until_idle()`) | `StartupIndexReconcile.run()` (T14, `spec/.../T14-indexing-orchestrator/design.md` §3.2) reclassifica `indexing`/`queued` órfãos assumindo perda da fila em memória por reinício de processo (ENG-011). Reutilizar esse método em **todo tick periódico**, sem guarda de concorrência, é seguro apenas enquanto nada mais chamar o orquestrador em paralelo. T18 (UI, disparo sob demanda) depende de T14/T15/T16/T07 e deve compartilhar a mesma instância de `IndexingOrchestrator`; sem serialização explícita, um disparo sob demanda concorrente a um tick teria sua execução `indexing` legítima incorretamente marcada como órfã, reenfileirada e reprocessada em duplicidade. | Introduzir guarda de execução única (`run_tick_once` com lock de instância) e registrar handoff de contrato obrigatório para T18 reutilizar o mesmo guard antes de chamar o orquestrador. |
| M-T15-02 | MAJOR | `design.md` v0.1.0 §4.2 ("não obrigatório estender `AppSettings` em T01... factory lê env/`os.environ`") | Contradiz o próprio design de T01 (`spec/.../T01-project-foundation/design.md` §2.5, tabela de variáveis: `INDEX_CRON` já reservada com "dono futuro: T15") e o padrão estabelecido por T04 (`spec/.../T04-worker-limiter/design.md` §2.1 item 4: "não reparsear env no limiter"; consome `AppSettings.index_workers`/`query_workers`). Ler `os.environ` ad-hoc no pacote `schedule` duplica a fonte de verdade de configuração e quebra a convenção de settings centralizados. | Estender `AppSettings`/`load_settings` (T01) com `index_cron: str`; pacote `schedule` consome `AppSettings`, nunca `os.environ` diretamente. |

### Verificação dos demais critérios (sem achados)

- ENG-004 (env default; preferência UI PG prevalece): D-T15-001/002 conformes.
- ENG-010 (só cron, sem segundo modelo de config): §1/§2 conformes.
- DEC-015/BDD-024 (APScheduler; SDK confinado ao adaptador): D-T15-003/004/010 conformes.
- Persistência de preferência sem CRUD de conexões (BR-017) e via SQLAlchemy (BR-024): D-T15-006, tabela `scheduler_preference` isolada de `CatalogRepository`, adaptador `SqlAlchemyCronPreferenceStore`.
- Expressão inválida → erro tipado, sem aplicação parcial: D-T15-003/008, §3.5.
- Escopo: sem UI, sem compose — §11 conforme.
- Ambiguidade menor identificada e corrigida no mesmo ciclo: §3.4 citava dois métodos alternativos (`notify_preference_changed` | `set_cron`) para o mesmo efeito; unificado em `set_cron` como único ponto de escrita.

### Resultado

`CHANGES_REQUIRED` na v0.1.0 (M-T15-01, M-T15-02) → correções aplicadas pelo próprio Architect no `design.md` (§3.1 D-T15-011/012, §3.6, §4.2, §5, §10, §12) → **`APPROVED_BY_ARCHITECT`** na v0.2.0. Sem achados BLOCKING ou MAJOR abertos.
