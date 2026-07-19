# Design — T24-gap-catalog-indexing-integral

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T24-gap-catalog-indexing-integral` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T24-gap-catalog-indexing-integral` |
| Base | `origin/feature/github-etl-mcp-rag-T22-fix-tooling-e2e-compose-zoekt` |
| Rastreabilidade | BDD-003, BDD-005, BDD-006, BDD-017; REQ-013–017, REQ-015; BR-002–004; T14/T15/T18/T21; inventário filha `mvp-e2e-audit-hardening` (linhas lacuna) |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Fortalecer asserts e2e integrais em `catalog_indexing`; preferência absoluta a Robot/keywords + fixture + MCP; sem endpoints novos no plano primário. Modo autônomo. |

## 1. Contexto

A suíte T21 em `e2e/robot/catalog_indexing.robot` cobre fatias parciais (DEC-019 / T21 §3.5) dos BDD de catálogo/indexação. A auditoria filha (`coverage-inventory.md`) classifica:

| BDD | Classificação | Lacuna atual no Robot |
|---|---|---|
| BDD-003 | `assert-fraco` | Só `GET`/`PUT /api/scheduler/cron` — não observa disparo do tick diário nem indexação dos desatualizados |
| BDD-005 | `gap-teste` | Tag em BDD-002; poll `up_to_date` sem assert de commit/snapshot distinto → último processado |
| BDD-006 | `assert-fraco` | Hits MD/Python; sem exclusão e2e de CSV, imagens e caminhos `.gitignore` |
| BDD-017 | `gap-teste` | Indexa local até `up_to_date`; sem prova “somente `main`” / uncommitted excluído |

Contratos de produto já existentes e reutilizáveis (sem redesenhar domínio):

| Superfície | Capacidade relevante |
|---|---|
| T15 `DailyScheduler` | Job APScheduler → `run_tick_once()` = `StartupIndexReconcile` + `run_until_idle` |
| T18 UI | `GET/PUT /api/scheduler/cron`, `POST /api/repos/index`, `GET /api/repos/{id}` (+ `files[]`), `GET …/executions`, `POST /api/search/exact` |
| T17 MCP | `list_repos` já expõe `last_processed_commit` e `current_main_commit` |
| T09 eligibility | Denylist CSV/imagens + pathspec `.gitignore` |
| T08 snapshot | Tip da `main` apenas; uncommitted ignorado (unitário `test_u_l05_uncommitted_ignored`) |
| T21 fixture | `e2e/fixtures/repos/sample-local` + `ensure_local_git_fixture` no launcher |

## 2. Problema

Fechar o texto integral dos BDD-003/005/006/017 na superfície e2e `catalog_indexing`, sem:

- browser UI (T23);
- fix tooling compose/zoekt (T22);
- alteração de domínio `src/github_rag/**` salvo observabilidade e2e absolutamente necessária.

A UI **não** serializa `last_processed_commit` em `repo_to_view`/`repo_to_detail` (só MCP). Não existe `POST /api/scheduler/tick`. O volume e2e monta `HOST_REPOS` como `:ro` no container — mutações Git do fixture devem ocorrer no **host** (bind mount refletido).

## 3. Solução proposta

### 3.1 Princípio

**Plano primário: só `e2e/robot/**` + enriquecimento do fixture local (+ ajuste mínimo de `ensure_local_git_fixture` / helper e2e se necessário).** Observar commits via MCP `list_repos` (já disponível). **Sem endpoints novos** no caminho feliz.

### 3.2 BDD-003 — agendamento diário (disparo + efeito)

Critério integral: horário configurado chega → sistema verifica repos e indexa os não atualizados.

Estratégia (sem esperar 24h; alinhada a T15):

1. Pré-condição: haver pelo menos um repo elegível **desatualizado** (tip ≠ último processado ou `not_indexed`). Preferir fixture local: indexar uma vez, mutar tip da `main` no host (novo commit), **não** chamar `POST /api/repos/index`.
2. `GET /api/scheduler/cron` → guardar expressão atual.
3. `PUT /api/scheduler/cron` com expressão de 5 campos que dispara na janela do teste (ex.: minuto corrente/próximo minuto UTC — keyword calcula; ou `*/1 * * * *` se APScheduler/aceitação do produto permitirem). Restaurar cron original no teardown.
4. Aguardar (poll) até o repo desatualizado atingir `up_to_date` **sem** enqueue manual — efeito do tick (`run_tick_once` via job).
5. Assert auxiliar: estado/label e, se útil, `last_processed_commit` (MCP) igual ao tip pós-mutação.

Isso exercita o **mesmo caminho** do job diário (D-T15-005/011), não só CRUD de cron.

**Contingência (não primária):** se flakiness de relógio/cron for evidenciada no pipeline, avaliar `POST /api/scheduler/tick` fino que só chama `DailyScheduler.run_tick_once()` — alteração mínima de UI wiring. Só ativar com evidência; ver D-T24-008.

### 3.3 BDD-005 — novo snapshot → último processado

1. Indexar fixture local (ou referência) até `up_to_date`.
2. Capturar `last_processed_commit` via MCP `list_repos` (e opcionalmente último `commit_target` em `GET /api/repos/{id}/executions`).
3. No host: novo commit na `main` do fixture (arquivo distinto / mensagem única).
4. `POST /api/repos/index` para o repo (critério BDD-005: “quando a indexação for executada” — sob demanda é válido).
5. Poll `up_to_date`.
6. Assert: novo `last_processed_commit` ≠ valor anterior **e** igual a `current_main_commit` (MCP); opcionalmente hits de busca com `commit` = novo SHA.

Não depender de push no GitHub de referência (flaky / sem escrita).

### 3.4 BDD-006 — elegibilidade (include + exclude)

Enriquecer fixture `sample-local` (seed no launcher e/ou keyword de preparação idempotente) com árvore mínima:

| Path | Papel |
|---|---|
| `src/Hello.java` ou `src/app.py` | include textual |
| `docs/notes.md` | include Markdown |
| `data/report.csv` | exclude denylist CSV |
| `img/photo.png` (bytes mínimos + marker único em sidecar não indexável, ou marker só no CSV) | exclude imagem |
| `.gitignore` com `ignored_dir/` (e/ou `node_modules/`) | exclude pathspec |
| `ignored_dir/secret_marker.txt` (ou `node_modules/pkg/x.js`) com token único | não deve aparecer em hits nem em `files[]` |

Após indexação:

- `POST /api/search/exact` com tokens únicos dos includes → hits não vazios; paths coerentes.
- Busca pelos tokens únicos dos excludes → **zero** hits (ou nenhum path excluído).
- `GET /api/repos/{id}` → `files[].path` contém includes e **não** contém paths excluídos.

Manter smoke de hits MD/Python do BDD-006 atual como complemento, não como único assert.

### 3.5 BDD-017 — somente `main` / sem uncommitted

Sobre o mesmo fixture local (preparação idempotente):

1. Branch `main` com marker `MAIN_ONLY_MARKER` commitado.
2. Branch `other` (ou `feature/x`) com marker `OTHER_BRANCH_MARKER` commitado **somente** nessa branch.
3. Working tree: arquivo uncommitted com marker `UNCOMMITTED_MARKER` (não `git add` / não commit).
4. Indexar via `POST /api/repos/index` → `up_to_date`.
5. Assert:
   - busca exact `MAIN_ONLY_MARKER` → hits; `commit` = tip `main` (MCP).
   - busca `OTHER_BRANCH_MARKER` e `UNCOMMITTED_MARKER` → zero hits.
   - opcional: MCP `list_tree` / `read_file` no tip processado não lista o arquivo uncommitted nem paths só da outra branch.

### 3.6 Organização Robot

| Artefato | Mudança |
|---|---|
| `e2e/robot/catalog_indexing.robot` | Substituir/estender casos BDD-003, BDD-005 (caso próprio), BDD-006, BDD-017 |
| `e2e/robot/resources/common.resource` | Timeouts/poll scheduler se necessário |
| `e2e/robot/resources/catalog_indexing.resource` (novo, preferível) | Keywords: cron soon + restore; wait tick effect; MCP parse commits; prepare fixture markers; assert search absence |
| `e2e/robot/libraries/` | Helper Python leve se parsing JSON MCP / cálculo cron UTC for verboso demais em Robot puro |
| `src/github_rag/e2e/launcher.py` `ensure_local_git_fixture` | Seed idempotente da árvore BDD-006/017 (ainda superfície e2e, não domínio ETL) |

Tags: manter `bdd003`, `bdd005`, `bdd006`, `bdd017`; não misturar asserts fracos como único gate.

## 4. Componentes

| ID | Componente | Responsabilidade | Motivo da separação |
|---|---|---|---|
| C-T24-01 | `catalog_indexing.robot` | Cenários BDD-003/005/006/017 integrais | Superfície inventário `catalog_indexing` |
| C-T24-02 | `resources/catalog_indexing.resource` | Keywords de cron-tick, fixture host, asserts de ausência | Evita inchamento do `.robot` e reuso entre casos |
| C-T24-03 | Fixture `sample-local` (+ `ensure_local_git_fixture`) | Árvore controlada include/exclude/branches/uncommitted | Única origem mutável sem depender do remoto GitHub |
| C-T24-04 | MCP `list_repos` (existente) | Observar `last_processed_commit` / `current_main_commit` | Evita endpoint UI novo (D-T24-002) |
| C-T24-05 | UI search/repos/cron (existente) | Disparo sob demanda, cron, hits, `files[]` | Contratos T18 já suficientes |
| C-T24-06 | T15 job / `run_tick_once` (existente) | Efeito do agendamento diário | BDD-003 alinha ao critério, não só CRUD |

**Não componentes desta task:** browser (T23); compose zoekt (T22); novos Protocols de domínio.

## 5. Fluxo

### 5.1 BDD-003

```text
host: commit novo na main do fixture (repo fica desatualizado no catálogo após tip mudar)
PUT /api/scheduler/cron → expressão que dispara em ≤ ~90s
     │
     ▼
APScheduler job → DailyScheduler.run_tick_once()
     → StartupIndexReconcile + run_until_idle
     │
     ▼
poll GET /api/repos/{id} state=up_to_date
MCP list_repos → last_processed_commit == tip novo
teardown: restaurar cron anterior
```

### 5.2 BDD-005

```text
index local → captura SHA_A (MCP)
host: commit → tip SHA_B
POST /api/repos/index → poll up_to_date
MCP: last_processed_commit == SHA_B ≠ SHA_A
```

### 5.3 BDD-006 / BDD-017

```text
prepare fixture (includes + excludes + other branch + uncommitted)
POST /api/repos/index → up_to_date
exact search includes → hits; excludes/other/uncommitted → empty
detail.files paths ⊆ elegíveis
```

## 6. Dados

| Dado | Origem | Notas |
|---|---|---|
| Cron ativo | PG `scheduler_preference` / env `INDEX_CRON` | PUT altera preferência; teardown restaura |
| Fixture local | `e2e/fixtures/repos/sample-local` | Sem secrets; markers sintéticos |
| Commits observados | MCP `list_repos` | Campos já no contrato T17 |
| Progresso por arquivo | UI `files[]` | Só paths processados (proxy de elegibilidade) |
| Hits exact | Zoekt via UI | Tokens únicos por arquivo |

Nenhuma migration. Nenhum segredo versionado.

## 7. Erros

| Situação | Comportamento esperado |
|---|---|
| Cron inválido no PUT de teste | 400; cenário falha explícita (não soft-pass) |
| Tick não indexa na janela | Timeout do `Wait Until Keyword Succeeds` → falha BDD-003 |
| Fixture sem `.git` / sem `main` | `ensure_local_git_fixture` / keyword falha antes dos asserts |
| Busca exclude retorna hit | Falha BDD-006/017 (lacuna real de elegibilidade ou seed) |
| Token em resposta | `Response Must Not Contain Token` permanece |

## 8. Segurança

- Markers e arquivos de fixture sem credenciais.
- Keywords não logam `E2E_GITHUB_TOKEN` / `GITHUB_TOKEN`.
- Mutação Git só no path do fixture e2e no host.
- Contingência `POST /api/scheduler/tick` (se adotada) não autentica de forma nova além da superfície UI local já exposta no compose e2e; não aceita body com secrets.

## 9. Compatibilidade

| Aspecto | Decisão |
|---|---|
| T21 green path | Cenários substituem fatias parciais; tags BDD preservadas |
| T22 tooling | Pré-requisito de stack; sem alterar composes nesta task |
| T23 UI browser | Fora |
| Domínio `src/github_rag/{catalog,indexing,schedule,eligibility,…}` | Sem mudança no plano primário |
| `github_rag.e2e.launcher` | Ajuste de seed fixture permitido (superfície e2e) |
| MCP / UI contratos | Somente consumo; sem breaking change |
| Volume `:ro` | Mutação no host; container só lê |

## 10. Observabilidade

| Sinal | Uso no e2e |
|---|---|
| `state` / `state_label` UI | Poll conclusão |
| MCP `last_processed_commit` / `current_main_commit` | BDD-005 / fecho BDD-003 |
| `files[].path` | BDD-006 elegibilidade |
| Hits exact (presença/ausência) | BDD-006 / BDD-017 |
| Cron GET após PUT | Configuração do disparo |

Logs estruturados de produto inalterados; asserts Robot são a evidência da auditoria.

## 11. Riscos

| ID | Risco | Severidade | Mitigação |
|---|---|---|---|
| R-T24-01 | Flakiness de cron “próximo minuto” / fuso | Média | Keyword UTC explícita; margem de poll ≥ 120s; teardown restaura cron; contingência D-T24-008 |
| R-T24-02 | Seed fixture não idempotente entre reruns | Média | Preparação idempotente; markers estáveis; re-init controlado se `.git` já existir |
| R-T24-03 | Repo GitHub referência sem commits novos | Baixa | BDD-005/003 usam fixture local |
| R-T24-04 | Tentação de expor endpoint tick sem evidência | Baixa | Primário = cron real; tick só com flakiness comprovada |
| R-T24-05 | Assert fraco por substring em hits parciais | Baixa | Tokens UUID-like únicos por path |

## 12. Rollback

1. Reverter commits que alteram `e2e/robot/**` e seed do fixture/launcher.
2. Suíte volta ao status quo T21 parcial (lacunas do inventário reaparecem).
3. Sem migration; cron persistido pode ser resetado pelo PUT de teardown ou recreação do volume PG e2e.

## 13. Decisões

| ID | Decisão | Motivo |
|---|---|---|
| D-T24-001 | Escopo = asserts e2e integrais BDD-003/005/006/017 em `catalog_indexing` (+ resources/libraries/fixture); fora browser e tooling T22 | Task gap + inventário; ENG-010 ownership no pai |
| D-T24-002 | Observar `last_processed_commit` / `current_main_commit` via MCP `list_repos` — **não** exigir novos campos na UI no plano primário | Campo já no contrato T17; evita mudança `src/github_rag/ui/**` |
| D-T24-003 | BDD-003: configurar cron que dispara na janela do teste + observar indexação de desatualizado **sem** `POST /api/repos/index` | Alinha ao “quando o horário chegar” (T15 job → `run_tick_once`), não só GET/PUT |
| D-T24-004 | BDD-005: mutar tip da `main` no fixture local no host + reindex sob demanda + assert SHA último processado | Texto integral do BDD; independente do remoto GitHub |
| D-T24-005 | BDD-006: seed include (code/MD/Java) + exclude (CSV, imagem, path gitignore) + asserts de hits e `files[]` | Fecha denylist/pathspec além do smoke MD/Python |
| D-T24-006 | BDD-017: branch não-`main` + arquivo uncommitted com markers; asserts de ausência em busca (e opcional MCP tree) | Prova snapshot só `main` |
| D-T24-007 | **Sem endpoints novos no plano primário**; reutilizar cron/repos/search UI + MCP | Preferência explícita da task; APIs existentes bastam |
| D-T24-008 | Contingência documentada: `POST /api/scheduler/tick` → `run_tick_once()` só se flakiness de cron for evidenciada | Observabilidade mínima; mesmo caminho do job; não implementar sem evidência |
| D-T24-009 | Mutações Git do fixture no host (bind `:ro` no container) | Compose e2e atual; evita alterar ownership T22 |
| D-T24-010 | Seed/prepare fixture via `ensure_local_git_fixture` e/ou keywords Robot idempotentes | Superfície e2e; domínio ETL intocado |

## 14. Endpoints novos vs keywords

| Necessidade | Plano primário | Contingência |
|---|---|---|
| Disparo diário observável | Keywords: PUT cron soon + poll estado/MCP | `POST /api/scheduler/tick` (D-T24-008) |
| Último processado | Keywords MCP `list_repos` (+ opcional `executions.commit_target`) | Expor commits no `RepoDetailView` (não necessário agora) |
| Exclusões elegibilidade | Keywords search + `files[]` + seed fixture | — |
| Somente main / uncommitted | Keywords prepare branches/WT + search/MCP | — |

**Conclusão:** implementação alvo = **somente keywords Robot + resources/libraries + fixture/e2e seed**. Endpoints novos = **não**.

## 15. Fora de escopo

- T23 browser UI / wildcards visuais.
- T22 compose/zoekt/provider.
- Alteração de produto de domínio além da contingência D-T24-008.
- Declarar MVP fechado / auditoria filha completa (só estas quatro linhas).
- Soft-pass / skip por tag `manual_or_partial`.

## 16. Critérios de aceite (design → implementação)

1. Robot cobre texto integral BDD-003/005/006/017 (não só fatia T21 parcial).
2. Nenhum segredo versionado.
3. Plano primário sem endpoints novos e sem mudança de domínio ETL/RAG.
4. Cobertura projeto ≥ 95% (testes de suporte/BDD pytest do pai se QA adicionar).
5. Stack depende de T22 para re-run; esta task não reabre tooling.

## 17. Próximos artefatos do pipeline

1. BDD (cenários Robot + pytest de suporte se necessário) — QA.
2. Interfaces (keywords/contratos de fixture; Protocols só se surgir porta e2e nova) — Architect/QA.
3. Unitários de helpers e2e / seed — QA.
4. Implementação Developer em `e2e/robot/**` (+ seed launcher).
5. Review + Blue + docs/changelog.

## 18. Estado

`APPROVED_BY_ARCHITECT` — design `0.1.0` completo, sem BLOCKING/MAJOR abertos. Contingência D-T24-008 residual documentada, não bloqueia BDD/interfaces.
