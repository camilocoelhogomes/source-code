# Unit Test Plan — T21-mvp-e2e-robot

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T21-mvp-e2e-robot` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Design / BDD / Interfaces | `0.1.1` / `0.1.1` / `0.1.0` (todos `APPROVED_BY_ARCHITECT`) |
| Cobertura alvo | ≥95% em `github_rag.e2e` e gate global |
| Branch | `feature/github-etl-mcp-rag-T21-mvp-e2e-robot` |
| Suíte | `tests/unit/e2e/` |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Plano + unitários TDD RED; `ImportError` esperado até `src/github_rag/e2e/`. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Review: MAJOR CI blank token, redaction tautologia, run_mvp_e2e/main sem Robot real, L05/L06 frágeis — corrigidos na suíte. |

## 1. Estratégia

| Camada | Arquivo | Doubles / fronteira |
|---|---|---|
| Credenciais HITL/CI | `test_credentials.py` | `environ` Mapping injetado |
| Erros / redaction | `test_errors.py` | stderr bruto + secrets conhecidos |
| Paths / timeouts | `test_paths_timeouts.py` | `tmp_path` / repo_root sintético |
| Launcher Podman | `test_launcher.py` | `run_command` + health HTTP fake |
| Suite orquestração | `test_suite.py` | `RecordingLauncher` / `RecordingRobotRunner` |
| Superfície pública | `test_exports.py` | imports / `__all__` / Protocols |
| Helpers | `helpers.py` | doubles + token canônico + markers |

- Sem Podman real, sem `compose up`, sem Robot CLI real (D-T21-008).
- BDD (`tests/bdd/test_mvp_e2e_robot.py` E2E-01..10) permanece superfície; unitários isolam contratos e corners.
- Pré-implementação: falha por `ImportError: github_rag.e2e` — **RED esperado**.

## 2. Matriz unitária

### 2.1 Credenciais — `E2eCredentialResolver` (I-T21-006/007)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-C01 | HITL sem token → `E2eCredentialError` | raise tipado | E2E-01 |
| UT-C02 | HITL só `GITHUB_TOKEN` não vazio → resolve; `source=GITHUB_TOKEN` | `.token` correto | I-T21-006 |
| UT-C03 | HITL só `E2E_GITHUB_TOKEN` → resolve; `source=E2E_GITHUB_TOKEN` | ok | I-T21-006 |
| UT-C04 | HITL ambos presentes → preferir `E2E_GITHUB_TOKEN` | source + token do E2E | I-T21-006 |
| UT-C05 | HITL token só whitespace / vazio → `E2eCredentialError` | rejeita blank | corner |
| UT-C05b | HITL `E2E_GITHUB_TOKEN` blank + `GITHUB_TOKEN` válido → fallback GITHUB | blank ≠ presente | corner |
| UT-C06 | CI (`GITHUB_ACTIONS=true`) só `GITHUB_TOKEN` → falha | sem fallback Actions | E2E-02; D-T21-006 |
| UT-C07 | CI com `E2E_GITHUB_TOKEN` → resolve mesmo com `GITHUB_TOKEN` presente | usa E2E | E2E-02 |
| UT-C08 | `E2E_REQUIRE_E2E_TOKEN=1` (sem ACTIONS) só `GITHUB_TOKEN` → falha | flag força CI | I-T21-006 |
| UT-C08b | CI `E2E_GITHUB_TOKEN` blank/whitespace + `GITHUB_TOKEN` → falha; sem token em str | empty CI | corner; E2E-10 |
| UT-C09 | `GITHUB_ACTIONS=false` + flag ausente = HITL | aceita `GITHUB_TOKEN` | corner |
| UT-C10 | `str(E2eCredentialError)` nunca contém valor do token (CI + token no env) | redaction | E2E-10 |

### 2.2 Erros — `E2eStackError` / redaction (I-T21-008)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-E01 | `from_stderr` com token em `secrets=` redige substring | `str(err)` sem token | E2E-10 |
| UT-E02 | `from_stderr` com padrão `ghp_…` sem lista secrets | redige `ghp_` | E2E-10 |
| UT-E03 | `from_stderr` raw vazio / só whitespace | erro tipado; msg segura | estado vazio |
| UT-E04 | `from_stderr` sem secrets e sem `ghp_` | preserva gist truncável; sem crash | feliz |
| UT-E05 | `E2eStackError` ≠ `E2eCredentialError` (hierarquia) | tipos distintos | I-T21-007/008 |

### 2.3 Paths e timeouts (I-T21-004/016)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-P01 | `COMPOSE_E2E_NAME == "docker-compose.e2e.yml"` | constante | E2E-05 |
| UT-P02 | `COMPOSE_E2E` / `ROBOT_ROOT` / fixtures paths terminam nos canônicos | `e2e/robot`, `config.e2e.json`, `repos` | E2E-05/09 |
| UT-P03 | `resolve_repo_root` encontra raiz com compose+pyproject | Path válido | I-T21-004 |
| UT-P04 | `resolve_repo_root` sem âncora → erro tipado / explícito | não retorna cwd arbitrário silencioso | inválido |
| UT-P05 | Timeouts defaults: compose+healthy 600; index 900/poll 5; search 60; 429 ≤3; wait 30–60 | constantes exatas | design §3.7 |
| UT-P06 | `E2E_RESULTS_DIRNAME == "e2e/results"` | path results | BDD-027 |

### 2.4 Launcher — `PodmanE2eStackLauncher` (I-T21-003/005)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-L01 | `up` invoca `podman compose -f <COMPOSE_E2E> up -d --build` via `run_command` | argv contém podman/compose/file | D-T21-002/003 |
| UT-L02 | `up` sem HOST_* no env → injeta abs `HOST_CONFIG` + `HOST_REPOS` fixtures | paths absolutos | E2E-05; D-T21-012 |
| UT-L03 | `up` com HOST_CONFIG/HOST_REPOS já setados → não sobrescreve | preserva caller | corner |
| UT-L04 | `run_command` exit ≠ 0 → `E2eStackError` (via `from_stderr`) | sem token em str | E2E-03 |
| UT-L05 | `wait_healthy` timeout → `E2eStackError`; HTTP mock (urllib+httpx); timeout curto | sem robot/compose | E2E-04 |
| UT-L06 | `wait_healthy` sucesso quando health fake 200 ready (urllib+httpx mock) | retorna sem erro | feliz |
| UT-L07 | `down` duas vezes (idempotente) → não propaga falha fatal / não crasha | 2ª chamada ok | concorrência/idempotência |
| UT-L08 | `down` com `run_command` falhando → best-effort (não mascara com secret) | sem token | E2E-03 finally |
| UT-L09 | `isinstance(PodmanE2eStackLauncher(...), E2eStackLauncher)` | Protocol | I-T21-002 |
| UT-L10 | compose_file default aponta `docker-compose.e2e.yml` sob repo_root | path | I-T21-004 |

### 2.5 Suite — `DefaultRobotMvpSuite` (I-T21-009..015)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-S01 | Green path: ordem resolve→up→wait_healthy→robot→down; exit 0 | ordem estrita | E2E-05 |
| UT-S02 | Credencial ausente → exit ≠ 0; `up` não chamado | fail-fast | E2E-01 |
| UT-S03 | CI só Actions token → exit ≠ 0; `up` não chamado | CI policy | E2E-02 |
| UT-S04 | `up` levanta `E2eStackError` → exit ≠ 0; robot não roda; `down` 1× | finally | E2E-03 |
| UT-S05 | `wait_healthy` falha → exit ≠ 0; robot não; `down` 1× | finally | E2E-04 |
| UT-S06 | robot exit 1 → suite ≠ 0; `down` ainda 1× | MVP bloqueado | E2E-06 |
| UT-S07 | robot invocação: exclude explícito `bdd015` (`--exclude` / `exclude=` / `excludes`) | regex explícita; substring só não basta | E2E-07; I-T21-010 |
| UT-S08 | green path markers: `health`, `catalog_indexing`, `ui`, `mcp`, `negative` | presentes em argv/kwargs | E2E-07; I-T21-011 |
| UT-S09 | token **nunca** em argv/kwargs do `robot_runner` | redaction | E2E-10; I-T21-015 |
| UT-S10 | `up` env inclui HOST_CONFIG/HOST_REPOS canônicos | fixtures | E2E-05 |
| UT-S11 | `isinstance(DefaultRobotMvpSuite(...), RobotMvpSuite)` | Protocol | I-T21-002 |
| UT-S12 | keyword-only + `TypeError` posicional; `run_mvp_e2e` com mock suite (sem Robot real) | I-T21-013/018 | E2E-09 |
| UT-S13 | Falha credencial: suite captura → ≠0 (não propaga exceção ao caller estável) | I-T21-012 | E2E-01 |
| UT-S14 | `down` chamado mesmo se robot levanta exceção inesperada | finally robusto | corner |
| UT-S15 | Duas chamadas `run()` green path: cada uma faz down (não compartilha estado quebrado) | idempotência observacional | concorrência |

### 2.6 Exports / entry (I-T21-017/018)

| ID | Cenário | Esperado | Contrato / BDD |
|---|---|---|---|
| UT-X01 | Exporta `E2eStackLauncher`, `RobotMvpSuite`, `PodmanE2eStackLauncher`, `DefaultRobotMvpSuite` | handoff | E2E-09 |
| UT-X02 | Exporta erros, resolver, `COMPOSE_E2E`, `ROBOT_ROOT`, fixtures, `timeouts` | pacote testável | I-T21-017 |
| UT-X03 | `__main__` / `main` → `SystemExit` com código de `run_mvp_e2e` (mock; sem Robot) | entry fino | I-T21-018 |
| UT-X04 | Pacote `e2e` não importa adapters de domínio catalog/index/query | AST / imports | interfaces §14 |

## 3. Sobreposição com BDD

| Área | BDD | Unit |
|---|---|---|
| Credencial ausente / CI | E2E-01/02 | UT-C* (blank, preferência, flag `E2E_REQUIRE_*`, CI blank) |
| Stack / health fail | E2E-03/04 | UT-L04/L05 + UT-S04/S05 |
| Green path + HOST_* | E2E-05 | UT-S01/S10 + UT-L02/L03 |
| Robot fail / exclude / markers | E2E-06/07 | UT-S06..S08 |
| Redaction | E2E-10 | UT-C08b/C10, UT-E*, UT-S09 |
| Handoff exports | E2E-09 | UT-X* |
| Manifesto git secrets | E2E-08 | fora do unit (permanece BDD) |

Unitários **não** duplicam E2E-08 (manifesto `.gitignore`); focam contratos Python isolados.

## 4. Demonstração RED (TDD)

```bash
cd /Users/camilocoelhogomes/projects/github_rag && .venv/bin/pytest tests/unit/e2e/ -q --tb=line 2>&1 | tail -40
```

Falhas esperadas pré-implementação:

| Área | Razão |
|---|---|
| Todos os testes que importam `github_rag.e2e` | `ImportError` — pacote ainda não existe em `src/` |

Após implementação Developer: verde + cobertura ≥95% em `github_rag.e2e`.

## 5. Fora de escopo unitário

- Podman / compose / Robot reais (gate e2e / ROBOT-01..06)
- Alterar Dockerfile / composes T19
- Mock da API GitHub
- Automatizar BDD-015
- Implementação de produção em `src/` (Developer)

## 6. Architect Review

| Decisão | Status | Autor | Data |
|---|---|---|---|
| Unit plan + suíte `0.1.1` | `APPROVED_BY_ARCHITECT` | Tech Lead Architect | 2026-07-18 |
