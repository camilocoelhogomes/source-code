# RobotGreenPathRun — e2e Robot green path (T04)

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T04-run-e2e-robot` |
| Contrato | `RobotGreenPathRun` |
| Data/hora (UTC) | `2026-07-19T02:36:12Z` (attempt B; attempt A `2026-07-19T02:35:52Z`) |
| Branch | `feature/mvp-e2e-audit-hardening-T04-run-e2e-robot` |
| Commit SHA | `94c99d27d06e844c136f06eec58d2b6daea038c7` |
| Python | `Python 3.14.6` |
| OS | `Darwin 24.6.0 arm64` |
| Podman | `podman version 6.0.1` (+ `podman-compose version 1.6.0` no attempt B) |
| Comando canônico | `python -m github_rag.e2e` |
| Repo ref | `camilocoelhogomes/source-code` |

## Escopo (D-T04-001 / BR-007)

Declaração: **não** há expansão de cobertura Robot nem browser nesta task. **Não** há mudança de produto exigida — `src/github_rag/**` e `e2e/robot/**` permanecem sem alteração de escopo T04. Falhas alimentam T05; exit ≠ 0 é evidência válida.

## Soft-dep T03

Soft-dep T03 (PR #24 / `feature/mvp-e2e-audit-hardening-T03-run-pytest-all-tasks`) permanece **aberta** no momento deste run. Evidência T04 é **independente** — **sem rebase** em T03; run-first e2e executado mesmo assim (REQ-014 soft).

## Pré-condições (T02 / HITL)

| Check | Status | Evidência permitida |
|---|---|---|
| Gate T02 | `READY` | checklist `audit/hitl-env-checklist.md` (mergeado) |
| `.env` local | ok | `test -f .env` exit 0 (não versionado; `git check-ignore` ok) |
| Token | `present=true` | chave observada `E2E_GITHUB_TOKEN` (valor **não** registrado) |
| Podman | ok | `/opt/homebrew/bin/podman`; `podman info` ok; machine `Currently running` |
| Repo ref | ok | `camilocoelhogomes/source-code` |

## Resultado agregado

| Métrica | Valor |
|---|---|
| exit code | `3` (stack failure — contrato T21 `E2eStackError`) |
| interpretação | exit ≠ 0 é evidência válida (não exige produto “verde”) |
| robot executado? | **não** (falha antes da fase robot) |
| duração attempt B | ~7m25s até falha/interrupção do compose hang |

### Attempt A (pré-compose-provider)

| Campo | Valor |
|---|---|
| UTC | `2026-07-19T02:35:52Z` |
| exit code | `3` |
| Motivo | `looking up compose provider failed` — `docker-compose` / `podman-compose` ausentes no PATH |
| Superfície | `tooling-e2e` |
| Mitigação operacional | instalado `podman-compose` 1.6.0 via Homebrew (**não** é fix de produto; pré-req de runtime local) |

### Attempt B (canônico pós-provider)

| Campo | Valor |
|---|---|
| UTC | `2026-07-19T02:36:12Z` → ~`02:43:37Z` |
| exit code | `3` |
| Motivo | falha/hang em `podman compose … up -d --build`; stack não ficou healthy; Robot não iniciou |
| Observação runtime | `sourcegraph/zoekt:latest` container `github-rag-e2e_zoekt_1` → `Exited (1)`; log mostra help do `tini` (entrypoint inválido). `postgres` healthy; `qdrant`/`slm` Up; `app` ficou `Created` aguardando deps. Compose ficou em `podman wait --condition=running` incluindo zoekt. |

## Fases da prova

| Fase | Status | Nota sanitizada |
|---|---|---|
| credential | ok | `E2eCredentialResolver` resolveu; `present=true` (`E2E_GITHUB_TOKEN`) |
| compose (up/build) | fail | Attempt A: provider ausente. Attempt B: build app ok; pull deps; zoekt exit 1; hang no wait → stack failure exit `3` |
| healthy | skip | `/healthz` não alcançado (app não iniciou) |
| robot | skip | green path não exercitado (suítes não rodaram) |
| down | ok | teardown best-effort após falha (`podman compose down`) |

## Suítes green path T21

Exclude: `bdd015` (`--exclude bdd015`).

| Suíte | Resultado | Nota |
|---|---|---|
| health | unknown | não executada (robot skip) |
| catalog_indexing | unknown | não executada (robot skip) |
| ui | unknown | não executada (robot skip) |
| mcp | unknown | não executada (robot skip) |
| negative | unknown | não executada (robot skip) |

## Artefatos locais

| Campo | Valor |
|---|---|
| `e2e/results/` presente | `true` (dir existe) |
| `output.xml` / `log.html` / `report.html` | `false` (ausentes — robot não rodou) |
| Conteúdo versionado? | **não** (`e2e/results/` gitignored; só este resumo) |
| Log bruto local | `/tmp/t04-e2e-run/*.log` (não versionado; redacted) |

## Lista de falhas acionáveis para T05

| ID | Identificação (fase/suíte/cenário) | Tipo / motivo sanitizado | Superfície candidata |
|---|---|---|---|
| F-T04-001 | fase `compose` / attempt A | compose provider ausente (`podman-compose`/`docker-compose` not in PATH) | `tooling-e2e` |
| F-T04-002 | fase `compose` / serviço `zoekt` | container exit 1; imagem `sourcegraph/zoekt:latest` entrypoint/`tini` usage; bloqueia `depends_on` do app | `tooling-e2e` (infra e2e; impacto em indexação) |
| F-T04-003 | fase `healthy` / `robot` | não alcançadas — consequência de F-T04-002; green path Robot não exercitado | `tooling-e2e` |

Lista **não** inclui falhas de contrato BDD da feature filha (`mvp_e2e_audit_*`) — D-T04-002.

## Proibições / sanitização

- Nenhum PAT, conteúdo de `.env`, header Authorization ou dump de env neste artefato.
- Sem prefixos `ghp_` / `gho_` / `ghu_` / `ghs_` / `ghr_`.
- Token apenas como `present=true`.
- Log bruto em `/tmp` (não versionado).

## Handoff T05

- Achados deste run: F-T04-001..003 (`tooling-e2e`); green path Robot **não** chegou a cenários de produto.
- T05 deve abrir tasks no pai por superfície/classificação; esta feature **não** corrige zoekt/compose.
- Soft-dep T03 independente; consolidar com falhas pytest quando T03 mergear.
