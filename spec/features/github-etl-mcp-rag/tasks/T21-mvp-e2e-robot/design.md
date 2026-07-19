# Design — T21-mvp-e2e-robot

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T21-mvp-e2e-robot` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Branch | `feature/github-etl-mcp-rag-T21-mvp-e2e-robot` |
| Base | `main` (T19 mesclado — PR #19 / `ce28209`) |
| Rastreabilidade | REQ-045–052; BR-025–030; DEC-017–021; ENG-018–020; BDD-026–028; exercita BDD-001–024 observáveis (exceto BDD-015) |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `PENDING_ARCHITECT_REVIEW` | `0.1.0` | Design inicial: `E2eStackLauncher` + `RobotMvpSuite`; layout `e2e/robot/`; Podman + compose e2e; GitHub real = este repo. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Review: MAJOR CI `E2E_GITHUB_TOKEN` + política partial/BDD-026; pin MCP SSE; fixture local no green path; REQ-049 via compose. Ver `reviews.md`. |

## 1. Contexto

T19 entregou empacotamento estável na `main`:

| Artefato T19 | Papel para T21 |
|---|---|
| `docker-compose.e2e.yml` | Stack isolada (`name: github-rag-e2e`, volumes `e2e_*`) |
| `Dockerfile` | Imagem `app` com UI `:8080` + MCP `:8001` + `/healthz` |
| Alias `GITHUB_TOKEN: ${E2E_GITHUB_TOKEN:-${GITHUB_TOKEN:-}}` | Credencial CI/local sem secret no git |
| `.env.example` / `docs/runbook-local.md` | Nomes canônicos; T21 documenta como rodar a prova |

O MVP só pode ser declarado entregue com **T19 e T21 verdes** (REQ-047, BR-026). Ownership da suíte Robot é exclusiva desta task (DEC-021, BR-030); `docs-cicd-e2e-release` apenas consome.

## 2. Problema

1. Provar BDD-001–024 **observáveis em runtime** (UI, MCP, health, indexação/busca) contra stack real.
2. Runtime obrigatório: **Podman** + `docker-compose.e2e.yml` (REQ-051, BR-029).
3. Integração GitHub **real** com repositório de referência = **este** remoto (`camilocoelhogomes/source-code`) — REQ-046, BR-027.
4. Excluir BDD-015 (narrativa Discovery no Cursor) do Robot.
5. Credenciais sem commit (REQ-048–049, BDD-027): local HITL via `.env`/export `GITHUB_TOKEN` (ou `E2E_GITHUB_TOKEN`); **CI exige** secret `E2E_GITHUB_TOKEN` mapeado → `GITHUB_TOKEN` no container — **proibido** usar o `GITHUB_TOKEN` default do Actions como substituto do token de produto (REQ-049).
6. Entregar contratos reutilizáveis `E2eStackLauncher` e `RobotMvpSuite` para a esteira consumidora.
7. Nova PR (não expandir #19) — REQ-050, BDD-028.
8. Sem novas features de domínio; sem mock da API GitHub; sem ownership dos composes.

## 3. Solução proposta

### 3.1 Duas camadas

| Camada | Onde | Responsabilidade |
|---|---|---|
| **Contratos Python** | `src/github_rag/e2e/` | Subir/derrubar stack (Podman), resolver credenciais, invocar Robot, mapear falhas explícitas |
| **Suíte Robot** | `e2e/robot/` | Keywords e cenários observáveis por superfície (health, catalog/indexing, UI, MCP) |

```text
docs-cicd / operador
  → RobotMvpSuite.run()
       1. resolve credentials (E2E_GITHUB_TOKEN | GITHUB_TOKEN)
       2. E2eStackLauncher.up()   # podman compose -f docker-compose.e2e.yml
       3. wait healthy (/healthz)
       4. robot e2e/robot/…       # BDD-001–024 observáveis
       5. E2eStackLauncher.down() # finally
```

### 3.2 Layout da suíte (ENG-019)

```text
e2e/
  README.md                 # como rodar com Podman; credenciais; timeouts; REQ-049
  fixtures/
    config.e2e.json         # connections GitHub + local; sem tokens
    repos/                  # bare/clone mínimo versionável (sem secrets) p/ BDD-016–018
  robot/
    health.robot            # BDD-020, healthz
    catalog_indexing.robot  # BDD-001–008, 016–019, 021 (efeitos)
    ui.robot                # BDD-009–010, 023 (+ partes UI de 001–008)
    mcp.robot               # BDD-011–014, 013
    negative.robot          # BDD-022 (fail-fast config inválida) — obrigatório no green path
    resources/
      common.resource       # base URLs, waits, retries rate-limit
      auth.resource         # lê env; nunca loga token
      http.resource         # GET/POST UI + health
      mcp.resource          # tools MCP via SSE (MCP_TRANSPORT=sse, porta 8001 — T19)
```

### 3.3 Contratos Python

| Contrato | Responsabilidade | Motivo da separação |
|---|---|---|
| `E2eStackLauncher` | `up` / `down` / `wait_healthy` via Podman + compose e2e; falha explícita se stack não sobe; exporta `HOST_CONFIG`/`HOST_REPOS` | Runtime ≠ asserções Robot; reutilizável pela esteira |
| `RobotMvpSuite` | Orquestra credenciais → launcher → `robot` CLI → exit code; declara exclusão BDD-015 | Suíte canônica consumível sem ownership transferida (handoff plano) |
| `E2eCredentialResolver` | Resolve credencial conforme ambiente (HITL vs CI); falha se ausente/inválida; redaction | Isola política DEC-020 / REQ-049; não é handoff externo |
| Helpers | paths canônicos (`COMPOSE_E2E`, `ROBOT_ROOT`), timeouts/retry GitHub | Constantes testáveis sem I/O |

Pacote: `github_rag.e2e` (novo). Fora do domínio de produto; opcional-deps `e2e` no `pyproject.toml`.

Handoff público para `docs-cicd-e2e-release`: apenas `E2eStackLauncher` + `RobotMvpSuite` (e defaults concretos). Demais tipos são internos ao pacote.

### 3.4 Config e2e de referência

`e2e/fixtures/config.e2e.json` (sem secrets), schema Sourcebot-like:

- Conexão GitHub nomeada com `orgs`/`repos` apontando **este** remoto (`camilocoelhogomes/source-code` ou glob mínimo que o inclua).
- Token no JSON: `{ "token": { "env": "GITHUB_TOKEN" } }` (REQ-041); valor injetado pelo compose alias.
- Conexão local `type: "git"`, `url: "file:///repos/*"` (ou path do fixture) para BDD-016–018.
- Fixture `e2e/fixtures/repos/` com bare/clone mínimo **versionável** (sem secrets) montado via `HOST_REPOS` no green path MVP.

Launcher ao `up`:

- `HOST_CONFIG=<repo>/e2e/fixtures/config.e2e.json`
- `HOST_REPOS=<repo>/e2e/fixtures/repos`
- Demais vars REQ-049 (`DATABASE_URL`, `ZOEKT_URL`, `QDRANT_URL`, `OPENAI_BASE_URL`, workers/cron/superfície) vêm do **compose e2e T19**; README documenta que o operador só precisa fornecer token (+ Podman). `CONFIG_PATH` no container permanece `/config/config.json`.

### 3.5 Mapeamento BDD → superfície observável

| BDD | No Robot green path? | Como (fatia observável obrigatória) |
|---|---|---|
| 001 | Sim | UI `GET /api/repos` contém este repo após sync |
| 002 | Sim | `POST /api/repos/index` → poll até `atualizado` / labels PT |
| 003 | Sim (parcial) | `GET/PUT /api/scheduler/cron` + evidência de cron ativo (**não** espera 24h) |
| 004–005 | Sim | Reindex após `atualizado` permanece/atualiza commit; poll estado |
| 006 | Sim (parcial) | Indexação deste repo: hits Markdown/Python; ausência típica de binários via busca |
| 007 | Sim | Detalhe repo com `progress` / files flags durante/após index |
| 008 | Sim | Induz estado `erro` (repo/config controlada ou keyword dedicada) e asserta UI/histórico |
| 009–010 | Sim | `POST /api/search/exact` e `/semantic` com hits |
| 011–012 | Sim | Tools MCP via **SSE** `:8001` — `list_repos`, `search_code`, … + omit details |
| 013 | Sim (parcial) | Disparo paralelo de tools MCP (sucesso sob limite; sem assert de SLO rígido) |
| 014 | Sim | Respostas/logs keywords sem substring do token |
| 015 | **Não** | Excluído (`--exclude` tag `bdd015` / sem arquivo Discovery); única exclusão do Robot |
| 016–018 | Sim | Fixture local montada; listagem origem local + index/busca observáveis |
| 019 | Sim | Sync GitHub só com env (sem UI de token) |
| 020 | Sim | `/healthz` + UI `:8080` + MCP SSE `:8001` up |
| 021 | Sim | Repos com `connection_name` / `origin` |
| 022 | Sim | `negative.robot`: config inválida / override → falha explícita, sem parcial |
| 023 | Sim | `POST /api/connections` → 404; UI sem CRUD |
| 024 | Sim (smoke) | Imagem sobe (health + sync GitHub); pin DEC-015 permanece gate unitário T19/T20 |

**Política BDD-026 / BR-026 (obrigatória):** tag `manual_or_partial` só documenta *como* a fatia observável é verificada (ex.: cron sem esperar 24h). **Não** autoriza skip que deixe o green path passar sem a asserção. Falha de qualquer cenário incluído na suíte MVP → exit ≠ 0 → MVP não entregue. Única exclusão do Robot: BDD-015.

Núcleo D-T21-010 = mínimo documentado para operadores; a suíte canônica `RobotMvpSuite.run()` executa **todos** os `.robot` do green path acima (incl. local + negative).

### 3.6 Credenciais e segurança (DEC-020 / REQ-049)

| Ambiente | Detecção | Fonte obrigatória | Mapeamento no container |
|---|---|---|---|
| Local HITL | `GITHUB_ACTIONS` ausente/`false` | `GITHUB_TOKEN` **ou** `E2E_GITHUB_TOKEN` (preferir este se ambos) | Compose: `GITHUB_TOKEN: ${E2E_GITHUB_TOKEN:-${GITHUB_TOKEN:-}}` |
| CI | `GITHUB_ACTIONS=true` (ou flag explícita `E2E_REQUIRE_E2E_TOKEN=1`) | **Somente** `E2E_GITHUB_TOKEN` não vazio | Mesmo alias compose; resolver **rejeita** confiar só no `GITHUB_TOKEN` default do Actions |
| Proibido | — | Commit de `.env` com valor; logar token em keyword/stdout/artefato Robot | Assert unitário + keyword redaction |

Token ausente/vazio (ou CI sem `E2E_GITHUB_TOKEN`) → `E2eCredentialError` / falha explícita **antes** de `up` / declarar MVP.

### 3.7 Timeouts e retry (rate-limit GitHub)

| Fase | Timeout default | Retry |
|---|---|---|
| `compose up --build` + healthy | 600s | healthcheck compose (já em T19) |
| Indexação repo referência | 900s | poll 5s |
| Busca UI/MCP | 60s | 3× com backoff se HTTP 429 |
| Keyword GitHub 429 | — | wait 30–60s, max 3 |

Constantes em `github_rag.e2e.timeouts` e espelhadas em `common.resource`.

### 3.8 Consumo por `docs-cicd-e2e-release`

Contrato estável (sem ownership transferida):

```python
from github_rag.e2e import DefaultRobotMvpSuite, PodmanE2eStackLauncher

suite = DefaultRobotMvpSuite(launcher=PodmanE2eStackLauncher())
raise SystemExit(suite.run())  # 0 = MVP proof green
```

CLI opcional: `python -m github_rag.e2e` (entrypoint fino).

## 4. Componentes

| ID | Componente | Tipo |
|---|---|---|
| C-T21-01 | `E2eStackLauncher` Protocol | Porta |
| C-T21-02 | `PodmanE2eStackLauncher` | Adaptador Podman compose |
| C-T21-03 | `RobotMvpSuite` Protocol | Porta |
| C-T21-04 | `DefaultRobotMvpSuite` | Orquestração |
| C-T21-05 | `E2eCredentialResolver` | Política credencial |
| C-T21-06 | Suítes `.robot` + resources (incl. `negative.robot`) | Asserções runtime |
| C-T21-07 | `e2e/fixtures/config.e2e.json` + `repos/` | Config + fixture local |
| C-T21-08 | optional-deps `e2e` | `robotframework`, `robotframework-requests` |

## 5. Fluxo

### 5.1 Happy path (BDD-026)

1. Operador exporta `GITHUB_TOKEN` **ou** CI define secret `E2E_GITHUB_TOKEN`.
2. `RobotMvpSuite.run()` → `E2eCredentialResolver` (CI exige `E2E_GITHUB_TOKEN`; falha se inválido).
3. `launcher.up(env)` → `podman compose -f docker-compose.e2e.yml` com `HOST_CONFIG`/`HOST_REPOS` dos fixtures → `up -d --build`.
4. `wait_healthy` → `GET http://127.0.0.1:8080/healthz` = 200 `{status:ok,…}` (UI+MCP ready).
5. `robot` executa suítes do green path (exclui tag `bdd015` / Discovery).
6. Exit 0 → MVP proof green; `finally: launcher.down()` (também em falha).

### 5.2 Falhas explícitas

| Condição | Resultado |
|---|---|
| Token ausente / CI sem `E2E_GITHUB_TOKEN` | exit ≠ 0; mensagem sem secret |
| Podman/compose falha | exit ≠ 0; MVP não entregue |
| Health timeout | exit ≠ 0 |
| Qualquer cenário Robot do green path falha | exit ≠ 0; MVP não entregue (BDD-026) |
| BDD-015 | nunca executado |

## 6. Dados

- Config fixture JSON (sem secrets) + fixture local `e2e/fixtures/repos/`.
- Env operador: token (`GITHUB_TOKEN` HITL / `E2E_GITHUB_TOKEN` CI). Demais REQ-049 injetadas pelo compose e2e.
- Repo referência GitHub: `camilocoelhogomes/source-code` (remoto deste projeto).
- Artefatos Robot (`output.xml`, `log.html`) em `e2e/results/` (gitignored).

## 7. Erros

| Erro | Tipo | Observabilidade |
|---|---|---|
| Credencial ausente/inválida | `E2eCredentialError` | mensagem genérica |
| Stack down / timeout | `E2eStackError` | stderr compose truncado, sem token |
| Robot failed | exit code do `robot` | reports em `e2e/results/` |
| Rate limit | retry keyword; depois fail | log “rate limited” sem token |

## 8. Segurança

- `.env` já no `.gitignore`; reforçar `e2e/results/` e qualquer `*.secret`.
- Keywords de auth mascaram token em logs Robot (`Log` level + replace).
- Nunca passar token em argv visível além de env do processo compose.
- Asserções BDD-014: corpo HTTP/MCP não contém valor do token.

## 9. Compatibilidade

- Consome T19 sem alterar Dockerfile/composes (exceto se bug bloqueante → `SCOPE_CHANGE_REQUIRED`).
- Python ≥3.12; Podman + `podman compose` (ou `podman-compose`) no PATH.
- Plataforma primária `linux/amd64` (ENG-006); Apple Silicon via emulação (risco documentado).

## 10. Observabilidade

- Logs launcher: comandos (sem env secret), duração up/down.
- Robot: tags por BDD-id (`bdd001`, …).
- Exit codes estáveis para CI.

## 11. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Flakiness GitHub/rate-limit | retry + timeouts documentados |
| Indexação longa (SLM/Zoekt) | timeout 900s; poll; fixture repo único |
| Podman ausente no dev unitário | unit tests com doubles; Robot real = gate e2e |
| BDD-008/022 difíceis | indução controlada + `negative.robot` no green path (sem soft-pass) |
| Conflito de portas host | um stack por vez (risco residual T19) |
| CI usa `GITHUB_TOKEN` do Actions por engano | resolver exige `E2E_GITHUB_TOKEN` quando `GITHUB_ACTIONS=true` |

## 12. Rollback

Reverter PR da suíte/contratos; MVP deixa de estar “entregue”; `docs-cicd` falha ao invocar até restaurar. Composes T19 permanecem.

## 13. Decisões de design

| ID | Decisão |
|---|---|
| D-T21-001 | Pacote Python `github_rag.e2e` separado de `delivery` (T19) |
| D-T21-002 | Runtime Podman obrigatório no launcher (não Docker CLI como path primário) |
| D-T21-003 | Compose file fixo: `docker-compose.e2e.yml` na raiz do repo |
| D-T21-004 | Repo GitHub de referência = este remoto; fixture sem token |
| D-T21-005 | BDD-015 excluído por tag/`--exclude`; única exclusão do Robot |
| D-T21-006 | HITL: `E2E_GITHUB_TOKEN` \| `GITHUB_TOKEN`; CI (`GITHUB_ACTIONS`): **exige** `E2E_GITHUB_TOKEN` (não usar default Actions `GITHUB_TOKEN`) |
| D-T21-007 | optional-deps `e2e` + `requirements-e2e.txt` espelho |
| D-T21-008 | Gate unitário = doubles; prova real = Robot (operador/CI) |
| D-T21-009 | Nova PR; não tocar ownership T19 |
| D-T21-010 | Green path = todos BDD-001–024 observáveis (exceto 015); `manual_or_partial` ≠ skip |
| D-T21-011 | MCP e2e = SSE `:8001` (compose T19); não stdio Cursor na suíte Robot |
| D-T21-012 | Fixture local versionada em `e2e/fixtures/repos` montada no `up` do green path |

## 14. Fora de escopo

- Esteira GitHub Actions, docs EN, release GHCR.
- Mock GitHub API.
- Automatizar BDD-015.
- Alterar 3 composes/Dockerfile (consumo apenas).
- Novas features de domínio.

## 15. Critério de pronto (DoD)

- Artefatos design/BDD/interfaces/unit-plan/reviews/refactoring aprovados pelo Architect.
- Suíte em `e2e/robot/` + README; contratos Python testados (cov ≥95% no código novo).
- Unitários verdes; documentação/changelog atualizados.
- PR aberta contra `main` com instruções HITL de `.env` / `E2E_GITHUB_TOKEN`.
