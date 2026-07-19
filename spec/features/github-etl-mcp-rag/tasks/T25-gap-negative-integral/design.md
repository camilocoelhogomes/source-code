# Design — T25-gap-negative-integral

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T25-gap-negative-integral` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T25-gap-negative-integral` |
| Base | `origin/feature/github-etl-mcp-rag-T22-fix-tooling-e2e-compose-zoekt` (PR empilhado) |
| Rastreabilidade | BDD-008, BDD-018, BDD-022; BR-005, BR-008; REQ-023; inventário filha T01; backlog T06 → T25; T21 negative suite |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Fecha lacunas integrais negative via API + probes Robot; UI browser residual documentado (T23). |

## 1. Contexto

A auditoria filha (`mvp-e2e-audit-hardening` / T01) classificou:

| BDD | Motivo da lacuna |
|---|---|
| BDD-008 | Robot só rejeita payload/unknown id; não cobre falha parcial pós-arquivos + histórico + reindex total |
| BDD-018 | Robot só valida listagem bem formada; sem volume ausente/inacessível nem erro na superfície UI |
| BDD-022 | Robot rejeita payload de index; não exercita `CONFIG_PATH` ausente/malformado fail-fast sem leak |

Ownership: pai `github-etl-mcp-rag`. Esta task fortalece asserts negativos integrais na suíte T21 e superfícies associadas (config loader, indexing orchestrator, delivery, UI API).

## 2. Problema

1. Assert fraco BDD-008 ≠ texto integral (estado `erro` + mensagem + horário + histórico + restart total).
2. Issues locais de discovery (T06/T07) existem em `CatalogSyncResult.local_issues` mas **não** são expostas à UI/API — BDD-018 não é observável.
3. Fail-fast `CONFIG_PATH` (T02/T19) está coberto em pytest unit/BDD delivery, mas **não** no green path Robot (`negative.robot`).

## 3. Solução proposta

### 3.1 Superfície API para issues locais (BDD-018)

Introduzir store mutável de issues do último sync, injetado na Management UI:

- Porta `CatalogIssueStore` com `replace(issues)` / `list_issues()`.
- Implementação default in-memory `InMemoryCatalogIssueStore`.
- Rota `GET /api/catalog/issues` → `{ "issues": [ { "connection_name", "path", "message" } ] }`.
- `DefaultContainerRuntime.boot`: após `run_catalog_sync`, `store.replace(result.local_issues)` (issues não abortam sync — T07).
- Wire: criar store cedo; passar a `wire_ui_app` / `DefaultManagementUiApi` / `create_app` (UI lê store a cada request — resolve ordem wire-antes-de-sync).

**Browser (T23):** fora do escopo obrigatório desta task. Asserts API autocontidos; risco residual de apresentação visual documentado.

### 3.2 Fixture e2e com volume ausente (BDD-018 live)

Em `e2e/fixtures/config.e2e.json`, adicionar conexão git apontando para path inexistente sob `/repos/` (ex. `file:///repos/__missing_e2e_volume__/*`), sem secrets. Sync permanece não-fatal; Robot asserta:

- `GET /api/catalog/issues` contém issue da conexão missing (mensagem tipada, sem token);
- nenhum repo do volume ausente aparece em `GET /api/repos`.

### 3.3 Falha parcial + histórico + reindex (BDD-008)

Camada A (obrigatória, pytest/BDD): stack in-process UI TestClient + orquestrador real com porta vetorial falhando após progresso parcial (padrão IO-07), depois retry:

1. `GET /api/repos/{id}` → `state=error`, `state_label=erro`;
2. `GET /api/repos/{id}/executions` → execução `failed` com `error_message` + `error_at`; histórico retém falha;
3. nova indexação após remoção da falha → `up_to_date` e evidência de restart total (`delete_repository` / wipe vetorial).

Camada B (Robot green path): keyword/Process invoca `python -m github_rag.e2e.negative_probes bdd008` (mesma indução controlada, exit 0/1, stdout sem secrets). Não depende de fault injection no stack Podman ao vivo.

### 3.4 CONFIG_PATH fail-fast (BDD-022)

Camada A: manter/estender asserts delivery (CD-03) — ausente/blank/arquivo inexistente/JSON inválido → `SystemExit(1)`, sync/reconcile/bind = 0, logs sem valor de token.

Camada B (Robot): `python -m github_rag.e2e.negative_probes bdd022` exercita boot com `CONFIG_PATH` inválido + token env presente; assert exit 1, sem parcial, stdout/stderr sem token.

Casos atuais de payload index vazio/unknown id **permanecem** (regressão), mas deixam de ser a única evidência BDD-022.

### 3.5 Segurança

- Nunca logar/`Should Contain` valores de `GITHUB_TOKEN` / `E2E_GITHUB_TOKEN`.
- Probes e Robot usam `Response Must Not Contain Token` / asserts `assertNotIn(SECRET, text)`.
- Fixture JSON e artefatos sem secrets.

## 4. Componentes

| Componente | Responsabilidade |
|---|---|
| `CatalogIssueStore` / `InMemoryCatalogIssueStore` | Handoff observável issues locais pós-sync |
| `GET /api/catalog/issues` | Superfície UI API BDD-018 |
| `DefaultContainerRuntime` + wiring UI | Popular store após sync |
| `github_rag.e2e.negative_probes` | Probes Process para Robot (008/022) |
| `e2e/robot/negative.robot` | Cenários integrais green path |
| `tests/bdd/test_negative_integral.py` | BDD executável 008/018/022 |
| `tests/unit/**` | Contratos extremos/corner |

## 5. Fluxo

```
boot → load CONFIG_PATH
     → sync → CatalogSyncResult.local_issues → store.replace
     → UI GET /api/catalog/issues (BDD-018)

index → falha parcial porta → state error + execution FAILED
     → GET executions (msg/horário/histórico)
     → reindex → restart total → up_to_date (BDD-008)

boot CONFIG_PATH inválido → SystemExit(1) pré-sync/bind; sem leak (BDD-022)
```

## 6. Dados

- Issues: `connection_name`, `path`, `message` (sem token).
- Executions: campos já existentes T03/T18 (`error_message`, `error_at`, `status`).
- Fixture e2e: conexão missing adicional.

## 7. Erros

| Condição | Comportamento |
|---|---|
| Volume ausente | zero repos dessa conexão + issue no store/API |
| Falha parcial index | `error` + histórico; retry = restart total |
| CONFIG_PATH inválido | exit 1; zero parcial; mensagem tipada sem secret |

## 8. Segurança

Sem secrets em logs, Robot output, probes stdout, JSON de issues/executions.

## 9. Compatibilidade

- Extensão backward-compatible da UI API (nova rota).
- Assinaturas `create_app` / `DefaultManagementUiApi` / `wire_ui_app` ganham parâmetro opcional `issue_store` (default store vazio).
- Não depender do merge T23; browser residual documentado.

## 10. Observabilidade

- Issues e executions via API JSON.
- Probes: exit code + mensagem tipada (`error_type=`) sem token.

## 11. Riscos e rollback

| Risco | Mitigação |
|---|---|
| Browser BDD-018/008 não coberto | Assert API; residual T23 |
| Ordem wire antes de sync | Store mutável atualizado pós-sync |
| Probe Robot flaky | Indução in-process determinística; sem Podman no probe |
| Config e2e com path missing quebra sync | Issues não-fatais (T07); fixture local válida permanece |

Rollback: reverter PR; lacunas inventário reabrem.

## 12. Decisões

| ID | Decisão |
|---|---|
| D-T25-001 | `GET /api/catalog/issues` + `CatalogIssueStore` mutável (BDD-018 API) |
| D-T25-002 | BDD-008 integral via indução controlada (pytest + probe Robot), não fault injection no compose vivo |
| D-T25-003 | BDD-022 Robot via probe de boot delivery; payload-index permanece regressão |
| D-T25-004 | Asserts UI = API; browser = residual T23 |
| D-T25-005 | Conexão missing no `config.e2e.json` para assert live BDD-018 |

## 13. Fora de escopo

- Fix tooling T22; ENG-010 na filha; browser Playwright (T23); paralelismo MCP (T26); DEC-015 integral (T27).
