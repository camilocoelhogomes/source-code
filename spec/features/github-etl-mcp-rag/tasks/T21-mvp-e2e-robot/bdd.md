# BDD — T21-mvp-e2e-robot

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T21-mvp-e2e-robot` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Execução (contratos / CI padrão) | `tests/bdd/test_mvp_e2e_robot.py` — doubles de launcher/robot runner; **sem** `podman compose up` real |
| Execução (prova real) | Robot Framework em `e2e/robot/` via `RobotMvpSuite.run()` (operador/CI e2e; fora do gate pytest) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | E2E-01..E2E-10 (contratos) + documentação Robot green path; BDD-015 excluído; mapeamento BDD-001–024. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Review: corrigidos falsos verdes E2E-01/02; exclude bdd015 explícito; redaction E2E-10 via `E2eStackError` + argv. Ver `reviews.md`. |

## Convenções

| Camada | O que prova | Gate |
|---|---|---|
| **Contrato (pytest BDD)** | `E2eCredentialResolver`, `E2eStackLauncher`, `RobotMvpSuite` / `DefaultRobotMvpSuite` com doubles; manifests sem secrets; exclusão `bdd015` | CI unitário/BDD padrão — **proibido** `compose up` / Podman real |
| **Robot (stack real)** | Superfícies observáveis BDD-001–024 (exceto 015) contra Podman + `docker-compose.e2e.yml` + GitHub real | Operador HITL / job e2e dedicado — **não** no gate pytest |

- Doubles representam fronteiras: compose/Podman, CLI `robot`, health HTTP.
- Credencial CI: somente `E2E_GITHUB_TOKEN` (rejeitar fallback ao `GITHUB_TOKEN` default do Actions).
- HITL: `E2E_GITHUB_TOKEN` **ou** `GITHUB_TOKEN` (preferir o primeiro se ambos).
- Falha de qualquer cenário incluído no green path → exit ≠ 0 → MVP não entregue (BDD-026).
- Única exclusão Robot: tag `bdd015` / BDD-015.

---

## Camada A — Contratos Python (executável em pytest)

### E2E-01 — Credencial ausente → falha explícita antes de `up` (BDD-027 / DEC-020)

**Tipo:** contrato (doubles)  
**Dado** ambiente HITL sem `GITHUB_TOKEN` nem `E2E_GITHUB_TOKEN` (vazios/ausentes)  
**Quando** `DefaultRobotMvpSuite(...).run()` (ou `E2eCredentialResolver.resolve`) executa  
**Então** levanta `E2eCredentialError` (ou exit ≠ 0 com mensagem explícita)  
**E** `E2eStackLauncher.up` **não** é chamado  
**E** a mensagem observável não contém valor de token

### E2E-02 — CI exige `E2E_GITHUB_TOKEN` (BDD-027 / REQ-049 / D-T21-006)

**Tipo:** contrato (doubles)  
**Dado** `GITHUB_ACTIONS=true` (ou `E2E_REQUIRE_E2E_TOKEN=1`)  
**E** apenas `GITHUB_TOKEN` preenchido (simula default Actions), sem `E2E_GITHUB_TOKEN`  
**Quando** o resolver / `suite.run()` resolve credenciais  
**Então** falha com `E2eCredentialError` (exit ≠ 0)  
**E** `launcher.up` **não** é chamado  
**E** com `E2E_GITHUB_TOKEN` não vazio a resolução sucede e o fluxo pode seguir

### E2E-03 — Stack que não sobe → falha explícita (BDD-026)

**Tipo:** contrato (doubles)  
**Dado** credencial válida e double de `E2eStackLauncher.up` que levanta `E2eStackError` (compose/Podman falhou)  
**Quando** `DefaultRobotMvpSuite.run()` orquestra  
**Então** o resultado é exit ≠ 0  
**E** o CLI `robot` **não** é invocado  
**E** `launcher.down()` é chamado no `finally` (cleanup mesmo em falha)  
**E** mensagem/stderr truncado não contém o token

### E2E-04 — Health timeout → falha; MVP não entregue (BDD-026 / BDD-020 smoke)

**Tipo:** contrato (doubles)  
**Dado** `up` ok e `wait_healthy` que falha com `E2eStackError` (timeout `/healthz`)  
**Quando** `suite.run()` continua após `up`  
**Então** exit ≠ 0  
**E** `robot` não roda  
**E** `down()` ocorre no `finally`

### E2E-05 — Green path orquestra credencial → up → healthy → robot → down (BDD-026)

**Tipo:** contrato (doubles)  
**Dado** credencial válida, launcher double com `up`/`wait_healthy` ok, robot runner double retornando `0`  
**Quando** `DefaultRobotMvpSuite(launcher=..., robot_runner=...).run()`  
**Então** exit code `0`  
**E** ordem: resolve → `up` → `wait_healthy` → `robot` → `down`  
**E** `up` recebe env com `HOST_CONFIG` apontando fixture `e2e/fixtures/config.e2e.json` e `HOST_REPOS` → `e2e/fixtures/repos`  
**E** compose alvo é `docker-compose.e2e.yml` (constante/path canônico do launcher)

### E2E-06 — Robot do green path falha → exit ≠ 0 (BDD-026)

**Tipo:** contrato (doubles)  
**Dado** stack saudável e robot runner retornando exit `1`  
**Quando** `suite.run()`  
**Então** exit ≠ 0 (MVP não entregue)  
**E** `down()` ainda é chamado

### E2E-07 — Tag `bdd015` excluída da invocação Robot (BDD-015 / D-T21-005)

**Tipo:** contrato (doubles)  
**Dado** green path com robot runner que registra argv/kwargs  
**Quando** `suite.run()` invoca o CLI Robot  
**Então** a invocação inclui exclusão **explícita** da tag `bdd015` (`--exclude bdd015` / `exclude=` / lista `excludes` — mera substring `bdd015` **não** basta)  
**E** a suíte **não** referencia arquivo/cenário Discovery Cursor como obrigatório  
**E** os suites green path incluem ao menos: `health`, `catalog_indexing`, `ui`, `mcp`, `negative`

### E2E-08 — Sem secrets no git (BDD-027)

**Tipo:** contrato (manifesto; sem Podman)  
**Dado** raiz do repositório  
**Quando** inspecionar `.gitignore`, `.env.example`, e paths canônicos e2e (`e2e/fixtures/**` se existirem)  
**Então** `.env` está no `.gitignore`  
**E** `e2e/results/` (e/ou `*.secret`) está ignorado ou documentado para ignore  
**E** `.env.example` e fixtures JSON **não** contêm tokens reais (`ghp_`, PAT longo)  
**E** token no config fixture (quando presente) usa `{ "token": { "env": "GITHUB_TOKEN" } }` sem valor literal

### E2E-09 — Ownership: contratos `E2eStackLauncher` / `RobotMvpSuite` consumíveis (BDD-028 / BR-030)

**Tipo:** contrato (import surface)  
**Dado** o pacote `github_rag.e2e`  
**Quando** o consumidor (`docs-cicd-e2e-release`) importa a superfície pública  
**Então** exporta `E2eStackLauncher`, `RobotMvpSuite`, `PodmanE2eStackLauncher`, `DefaultRobotMvpSuite`  
**E** o padrão estável é:

```python
from github_rag.e2e import DefaultRobotMvpSuite, PodmanE2eStackLauncher

suite = DefaultRobotMvpSuite(launcher=PodmanE2eStackLauncher())
raise SystemExit(suite.run())  # 0 = MVP proof green
```

**E** a suíte Robot permanece ownership T21 (paths sob `e2e/robot/`); T19 ownership de composes não é alterada por este pacote

### E2E-10 — Falha de credencial não vaza secret; redaction (BDD-014 smoke / BDD-027)

**Tipo:** contrato (doubles)  
**Dado** token `ghp_should_never_appear_in_e2e_9f3a2` no env de teste  
**Quando** (1) CI resolve credencial só com `GITHUB_TOKEN` Actions e falha; (2) `E2eStackError` é construído a partir de stderr bruto contendo o token; (3) green path invoca robot  
**Então** mensagem de `E2eCredentialError` **não** contém o token  
**E** `str(E2eStackError(...))` **não** contém o token (redaction no tipo / `from_stderr` se existir)  
**E** argv/kwargs do robot runner **não** recebem o token

---

## Camada B — Suíte Robot (prova real; documentada; `.robot` nesta etapa ainda podem não existir)

> Estes cenários são a prova MVP em stack real. **Não** fazem parte do gate pytest. Serão implementados em `e2e/robot/*.robot` + resources. Invocação canônica: `RobotMvpSuite.run()`.

### ROBOT-01 — `health.robot` (BDD-020, smoke BDD-024)

**Arquivo previsto:** `e2e/robot/health.robot`  
**Tags:** `bdd020`, `bdd024`  
**Dado** stack e2e up via Podman + compose e2e  
**Quando** keywords HTTP verificam superfícies  
**Então** `GET http://127.0.0.1:8080/healthz` = 200 `{status:ok,…}` com UI+MCP ready  
**E** UI `:8080` e MCP SSE `:8001` respondem

### ROBOT-02 — `catalog_indexing.robot` (BDD-001–008, 016–019, 021)

**Arquivo previsto:** `e2e/robot/catalog_indexing.robot`  
**Tags:** `bdd001`…`bdd008`, `bdd016`…`bdd019`, `bdd021` (+ `manual_or_partial` só onde documenta fatia, **sem skip**)  
**Dado** GitHub real deste remoto + fixture local montada (`HOST_REPOS`)  
**Quando** sync/index/poll via UI APIs  
**Então** efeitos observáveis de descoberta, indexação, progresso, erro induzido, origem/conexão e sync só-via-env passam (ver mapeamento § abaixo)

### ROBOT-03 — `ui.robot` (BDD-009–010, 023 + fatias UI de 001–008)

**Arquivo previsto:** `e2e/robot/ui.robot`  
**Tags:** `bdd009`, `bdd010`, `bdd023`  
**Dado** repos indexados / stack saudável  
**Quando** busca exact/semantic e tentativa de CRUD de connections  
**Então** hits nas buscas; `POST /api/connections` → 404 / UI sem CRUD

### ROBOT-04 — `mcp.robot` (BDD-011–014, 013)

**Arquivo previsto:** `e2e/robot/mcp.robot`  
**Tags:** `bdd011`, `bdd012`, `bdd013`, `bdd014`  
**Dado** MCP SSE em `:8001`  
**Quando** tools `list_repos`, `search_code`, … e disparos paralelos  
**Então** evidências corretas; omit details; paralelismo sob limite; respostas/logs sem substring do token

### ROBOT-05 — `negative.robot` (BDD-022) — obrigatório no green path

**Arquivo previsto:** `e2e/robot/negative.robot`  
**Tags:** `bdd022`  
**Dado** config inválida / override controlado  
**Quando** a superfície sob teste é exercitada  
**Então** falha explícita, sem sucesso parcial  
**E** falha deste arquivo → exit ≠ 0 da suíte MVP

### ROBOT-06 — Exclusão Discovery (BDD-015)

**Arquivo:** nenhum / tag `bdd015` nunca incluída  
**Quando** `robot … --exclude bdd015`  
**Então** narrativa Discovery no Cursor **não** é automatizada

---

## Mapeamento BDD-00x → Robot / contrato

| BDD | No green path Robot? | Cenário Robot (prova real) | Teste contrato pytest |
|---|---|---|---|
| 001 | Sim | ROBOT-02 — `GET /api/repos` contém este repo após sync | E2E-05 (orquestra green path) |
| 002 | Sim | ROBOT-02 — `POST /api/repos/index` → poll `atualizado` / labels PT | E2E-05 |
| 003 | Sim (parcial) | ROBOT-02 — `GET/PUT /api/scheduler/cron` + evidência cron ativo (não espera 24h) | E2E-05 |
| 004–005 | Sim | ROBOT-02 — reindex / commit após `atualizado` | E2E-05 |
| 006 | Sim (parcial) | ROBOT-02 — hits MD/Python; ausência típica binários | E2E-05 |
| 007 | Sim | ROBOT-02 — detalhe `progress` / files flags | E2E-05 |
| 008 | Sim | ROBOT-02 — estado `erro` induzido + UI/histórico | E2E-05 |
| 009–010 | Sim | ROBOT-03 — `POST /api/search/exact` e `/semantic` | E2E-05 |
| 011–012 | Sim | ROBOT-04 — tools MCP SSE + omit details | E2E-05 |
| 013 | Sim (parcial) | ROBOT-04 — tools em paralelo sob limite | E2E-05 |
| 014 | Sim | ROBOT-04 — sem token em corpo/logs | E2E-10 |
| 015 | **Não** | ROBOT-06 — excluído | E2E-07 |
| 016–018 | Sim | ROBOT-02 — fixture local listagem/index/busca | E2E-05 (`HOST_REPOS`) |
| 019 | Sim | ROBOT-02 — sync GitHub só com env | E2E-01/02/05 |
| 020 | Sim | ROBOT-01 — `/healthz` + UI + MCP | E2E-04/05 |
| 021 | Sim | ROBOT-02 — `connection_name` / `origin` | E2E-05 |
| 022 | Sim | ROBOT-05 — `negative.robot` | E2E-05/06 |
| 023 | Sim | ROBOT-03 — sem CRUD connections | E2E-05 |
| 024 | Sim (smoke) | ROBOT-01 — imagem sobe + sync GitHub | E2E-05 |
| 026 | — (meta) | Toda a suíte Robot green path | E2E-01..07 |
| 027 | — (meta) | Keywords auth + fixtures | E2E-01/02/08/10 |
| 028 | — (meta) | Consumo docs-cicd da suíte T21 | E2E-09 |

---

## Critérios de aceite da task × cenários

| Aceite | Cenários |
|---|---|
| Robot passa BDD-001–024 observáveis com Podman/compose/credenciais | ROBOT-01..05; E2E-05 |
| Token ausente/inválido → falha explícita | E2E-01, E2E-02 |
| Stack que não sobe → falha explícita | E2E-03, E2E-04 |
| Regressão observável → Robot falha; MVP não entregue | E2E-06; ROBOT-* |
| BDD-015 não automatizado | E2E-07; ROBOT-06 |
| Nenhum segredo versionado | E2E-08, E2E-10 |
| Ownership Robot T21; docs-cicd só consome | E2E-09 |
| T19+T21 verdes = MVP | Documentado; prova = E2E-05 exit 0 + ROBOT green |

---

## Comando

```bash
# Gate CI padrão (contratos / doubles — sem Podman real)
python -m pytest tests/bdd/test_mvp_e2e_robot.py -q

# Prova real (fora do gate pytest; requer Podman + E2E_GITHUB_TOKEN|GITHUB_TOKEN)
python -c "from github_rag.e2e import DefaultRobotMvpSuite, PodmanE2eStackLauncher; raise SystemExit(DefaultRobotMvpSuite(launcher=PodmanE2eStackLauncher()).run())"
```

## Notas TDD

- Até existir `src/github_rag/e2e/`, os testes de contrato devem falhar por `ImportError` (razão esperada).
- E2E-08 pode parcialmente passar via manifesto (`.gitignore` / `.env.example`) antes do pacote existir; asserts de fixture e2e ficam red até os artefatos serem criados na implementação.
- Arquivos `.robot` podem ser criados na fase de implementação Developer; esta etapa BDD documenta o contrato comportamental.
