# CoverageInventory — inventário de cobertura MVP e2e

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T01-coverage-inventory` |
| Data | 2026-07-18 |
| Critério | texto **integral** dos BDD-001–024 do pai `github-etl-mcp-rag` (BR-001 / DEC-002) |
| Exclusão | **BDD-015** fora do inventário automatizado (REQ-010 / DEC-019) |
| Método | **inspeção estática** (sem run de pytest/Robot nesta task) |
| Fontes | `requirements.md` do pai; design T21 §3.5; `e2e/robot/**` (leitura); `tests/**` relevantes |
| SoT para | T06 `ParentGapFillBacklog` |

> **BDD-015 — Apoiar Discovery no Cursor:** fora do inventário automatizado (REQ-010 / DEC-019). Validação humana; não gera linha de status nesta matriz.

> Este inventário é SoT de lacunas para T06; green path T21 parcial **não** basta para fechar a auditoria nem o MVP. T06 consome as linhas `lacuna`.

## Matriz

| bdd_id | superficie | status | evidencia_robot | evidencia_pytest | evidencia_browser | nota_parcial_t21 | motivo_lacuna |
|---|---|---|---|---|---|---|---|
| BDD-001 | ui | lacuna | e2e/robot/catalog_indexing.robot — BDD-001 Github Reference Repo Appears In Catalog (bdd001) | tests/bdd/test_github_discovery.py; tests/bdd/test_catalog_sync.py | nao | T21 §3.5: UI `GET /api/repos` (API-smoke); critério integral exige listagem UI com wildcards | UI só RequestsLibrary; sem browser nem assert visual de wildcards de inclusão |
| BDD-002 | ui | lacuna | e2e/robot/catalog_indexing.robot — BDD-002 Index Reference Repo Until Updated (bdd002) | tests/bdd/test_indexing_orchestrator.py; tests/bdd/test_worker_limiter.py | nao | T21 §3.5: POST index + poll estados; sem checkbox UI nem assert de limite de workers no Robot | Sem seleção por checkbox na UI; paralelismo de workers não observado no e2e |
| BDD-003 | catalog_indexing | lacuna | e2e/robot/catalog_indexing.robot — BDD-003 Scheduler Cron Get And Put (bdd003) | tests/bdd/test_daily_scheduler.py | n/a | T21 §3.5 Sim (parcial): GET/PUT cron ativo; **não** espera ciclo 24h | Critério integral exige disparo no horário diário e indexação dos desatualizados |
| BDD-004 | catalog_indexing | coberto-integral | e2e/robot/catalog_indexing.robot — BDD-004 Reindex When Already Updated Stays Updated (bdd004) | tests/bdd/test_indexing_orchestrator.py; tests/bdd/test_catalog_persistence.py | n/a | — | — |
| BDD-005 | catalog_indexing | lacuna | e2e/robot/catalog_indexing.robot — BDD-002 Index Reference Repo Until Updated (tags bdd005) | tests/bdd/test_main_snapshot.py; tests/bdd/test_indexing_orchestrator.py | n/a | T21 §3.5 agrupa 004–005; Robot só poll `atualizado` sem assert de mudança de commit | Sem evidência e2e de que commit novo vira último processado após snapshot distinto |
| BDD-006 | catalog_indexing | lacuna | e2e/robot/catalog_indexing.robot — BDD-006 Exact Search Finds Python Or Markdown (bdd006) | tests/bdd/test_file_eligibility.py | n/a | T21 §3.5 Sim (parcial): hits Markdown/Python; exclusão CSV/binários/gitignore não integral | Sem assert e2e de exclusão CSV, imagens e caminhos `.gitignore` |
| BDD-007 | ui | lacuna | e2e/robot/catalog_indexing.robot — BDD-002 Index Reference Repo Until Updated (tags bdd007) | tests/bdd/test_indexing_orchestrator.py; tests/bdd/test_treesitter_chunker.py | nao | T21 §3.5: detalhe `progress`/flags; suíte só asserta estado `atualizado` | Sem percentual/etapa por arquivo nem passagem Zoekt/Tree-sitter/metadados na UI |
| BDD-008 | negative | lacuna | e2e/robot/catalog_indexing.robot — BDD-008 Invalid Index Request; negative.robot — Unknown Repository Id (bdd008) | tests/bdd/test_indexing_orchestrator.py | nao | T21 §3.5: induz `erro` API; não cobre falha parcial pós-arquivos + histórico + reindex total | Assert de payload inválido ≠ falha parcial de pipeline com histórico na UI |
| BDD-009 | ui | lacuna | e2e/robot/ui.robot — BDD-009 Exact Search Via Ui (bdd009); catalog_indexing.robot tag bdd009 | tests/bdd/test_query_services.py; tests/bdd/test_zoekt_adapter.py | nao | T21 §3.5: `POST /api/search/exact` via RequestsLibrary | Busca exata só API; critério exige apresentação na UI (browser) |
| BDD-010 | ui | lacuna | e2e/robot/ui.robot — BDD-010 Semantic Search Via Ui (bdd010) | tests/bdd/test_query_services.py; tests/bdd/test_qdrant_vector_store.py | nao | T21 §3.5: `POST /api/search/semantic` via RequestsLibrary | Busca semântica só API; critério exige UI no browser |
| BDD-011 | mcp | coberto-integral | e2e/robot/mcp.robot — BDD-011 Approved Mcp Tools / List Repos Via Mcp (bdd011) | tests/bdd/test_mcp_evidence_server.py | n/a | — | — |
| BDD-012 | mcp | coberto-integral | e2e/robot/mcp.robot — BDD-012 Optional Details Omitted/When Requested (bdd012) | tests/bdd/test_mcp_evidence_server.py | n/a | — | — |
| BDD-013 | mcp | lacuna | e2e/robot/mcp.robot — BDD-013 Parallel Mcp Tool Calls Succeed (bdd013) | tests/bdd/test_mcp_evidence_server.py; tests/bdd/test_worker_limiter.py | n/a | T21 §3.5 Sim (parcial): paralelo sob limite; sem assert de SLO/fila de excedentes | Duas calls sequenciais com sucesso ≠ paralelismo + fila até limite configurado |
| BDD-014 | mcp | coberto-integral | e2e/robot/mcp.robot — BDD-014 Mcp Responses Never Echo Token (bdd014); common.resource Response Must Not Contain Token | tests/bdd/test_mcp_evidence_server.py; tests/unit/e2e/test_errors.py | n/a | — | — |
| BDD-016 | ui | lacuna | e2e/robot/catalog_indexing.robot — BDD-016 Local Fixture Repo Appears As Local (bdd016) | tests/bdd/test_local_discovery.py; tests/bdd/test_local_discovery_git_sdk.py | nao | T21 §3.5: listagem origem local via API | Identificação `local` só em JSON API; critério exige aparição na UI |
| BDD-017 | catalog_indexing | lacuna | e2e/robot/catalog_indexing.robot — BDD-017 Local Repo Can Be Indexed (bdd017) | tests/bdd/test_main_snapshot.py; tests/bdd/test_local_discovery.py | n/a | T21 §3.5: index local observável; sem assert “somente main” | Indexa até `atualizado`; não prova exclusão de outras branches/uncommitted |
| BDD-018 | negative | lacuna | e2e/robot/negative.robot — BDD-018 Catalog Listing Remains Well Formed (bdd018) | tests/bdd/test_local_discovery.py | nao | T21 §3.5: volume/fixture; caso Robot só valida listagem bem formada | Sem volume ausente/inacessível nem erro correspondente na UI |
| BDD-019 | catalog_indexing | lacuna | e2e/robot/catalog_indexing.robot — BDD-001 tags bdd019; resources/auth.resource Require E2e Credential Present | tests/bdd/test_config_loader.py; tests/bdd/test_github_discovery.py | nao | T21 §3.5: sync GitHub só com env | Token via env coberto na suíte; UI não solicitar/persistir token não provado sem browser |
| BDD-020 | health | coberto-integral | e2e/robot/health.robot — BDD-020 Healthz Reports Ui And Mcp Ready (bdd020) | tests/bdd/test_container_delivery.py; tests/unit/delivery/test_manifest.py | n/a | — | — |
| BDD-021 | catalog_indexing | coberto-integral | e2e/robot/catalog_indexing.robot — BDD-001/016 tags bdd021 (`origin`/`connection_name`) | tests/bdd/test_config_loader.py; tests/bdd/test_catalog_sync.py | n/a | — | — |
| BDD-022 | negative | lacuna | e2e/robot/negative.robot — BDD-022 Empty Index Payload / Unknown Repository Id (bdd022) | tests/bdd/test_config_loader.py | n/a | T21 §3.5: fail-fast config; casos Robot rejeitam payload de index, não `CONFIG_PATH` inválido | Sem assert de CONFIG_PATH ausente/malformado sem aplicação parcial nem leak de segredos |
| BDD-023 | ui | lacuna | e2e/robot/ui.robot — BDD-023 Connections Crud Not Available (bdd023) | tests/bdd/test_management_ui.py | nao | T21 §3.5: POST/PUT `/api/connections` → 404 | CRUD bloqueado via API; fluxo UI (estados/seleção/pesquisa) sem browser |
| BDD-024 | sdk | lacuna | e2e/robot/mcp.robot — BDD-011 tags bdd024 (smoke tools); health + sync implícitos | tests/bdd/test_local_discovery_git_sdk.py; tests/bdd/test_treesitter_chunker.py; tests/bdd/test_qdrant_vector_store.py; tests/bdd/test_zoekt_adapter.py; tests/bdd/test_container_delivery.py | n/a | T21 §3.5 Sim (smoke): imagem sobe; pin DEC-015 permanece gate unitário | Smoke Robot ≠ conformidade integral DEC-015/BR-024 em todas as integrações |

## Handoff T06

- Toda linha `status=lacuna` é candidata a task `gap-*` no pai (agrupamento por `superficie` / ENG-006).
- Priorizar denylist T21 parcial/smoke (003, 006, 013, 024) e superfície `ui` com `evidencia_browser=nao`.
- BDD-015 não gera task a partir desta matriz.
