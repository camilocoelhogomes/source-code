---
name: e2e-robot-autonomous-loop
description: Executa o ciclo determinístico python -m github_rag.e2e → descoberta de falhas → tasks de bug → orquestrador autônomo até Robot verde. Substitui gates HITL por commits; único gate humano é aprovação de mudanças em e2e/robot/**. Use ao rodar e2e Robot, fechar MVP local verde, ou corrigir falhas e2e de forma autônoma.
---

# Loop autônomo e2e Robot

O agente principal **apenas orquestra**. Não implementa correções nem altera suítes Robot sem gate humano.

## Princípios

1. **Critério de parada determinístico:** `python -m github_rag.e2e` exit `0` (green path: `health`, `catalog_indexing`, `ui`, `ui_browser`, `mcp`, `negative`; `--exclude bdd015`).
2. **Commit substitui HITL:** em cada etapa que `feature-discovery` ou `implementation-pipeline` pediriam aprovação humana, faça **commit** com artefato candidato e registre decisão automática (`APPROVED_BY_ARCHITECT` ou `APPROVED_BY_PO`) em `approvals.md`. **Não** aguarde humano, exceto no gate Robot (abaixo).
3. **Suítes Robot congeladas:** arquivos em `e2e/robot/**` e `e2e/fixtures/**` são **imutáveis** neste loop. Qualquer proposta de alteração → pare, commit candidato, solicite aprovação humana explícita. Sem aprovação, trate como `gap-teste` ou `produto` — nunca mude o Robot.
4. **Correções no pai:** tasks de bug vivem em `spec/features/github-etl-mcp-rag/tasks/` (T22–T27 existentes + T28+ novas).
5. **Orquestração filha (opcional):** runs e índices em `spec/features/mvp-local-e2e-green/runs/` ou `spec/features/<loop-feature-id>/runs/`.

## Pré-condições (bloqueie e reporte)

| Item | Verificação |
|------|-------------|
| `.env` local | Token GitHub válido; **nunca** commitar |
| Podman + compose | `podman-compose` ou `podman compose` no PATH |
| Deps e2e | `pip install -e ".[e2e]"` |
| Browser | `rfbrowser init` |
| GitHub | `git remote -v` + `gh auth status` |
| `main` | Atualizada antes de cada onda |

Referência operacional: `e2e/README.md`, checklist `spec/features/mvp-e2e-audit-hardening/audit/hitl-env-checklist.md`.

## Ciclo principal

```text
┌─────────────────────────────────────────────────────────────┐
│  W1  RUN E2E  →  resumo sanitizado em spec/.../runs/       │
└────────────────────────────┬────────────────────────────────┘
                             │ exit ≠ 0 ou falhas residuais
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  W2  DISCOVERY (variante)  →  tasks bug no pai + dedup     │
│       commit por gate que seria HITL                        │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  W3  autonomous-implementation-orchestrator               │
│       PRs por task; merge conforme política do loop         │
└────────────────────────────┬────────────────────────────────┘
                             ▼
                    re-run W1 até exit 0
```

Repita W1→W2→W3 até exit `0`. Exit `0` na primeira W1 encerra (registrar verde; W2 dedup confirma zero falhas novas).

## W1 — Executar e2e

```bash
python -m github_rag.e2e
```

Registrar em `spec/features/<loop-feature-id>/runs/e2e-run-YYYYMMDD.md`:

- exit code, fase falha (compose / healthy / robot)
- suítes e cenários falhos (nome Robot, tag BDD se houver)
- classificação: `produto` | `flakiness` | `gap-teste` | `tooling-e2e`
- superfície (tabela abaixo)
- paths gitignored: `e2e/results/` — **sem segredos** no artefato versionado

**Commit:** `chore(e2e): registro run Robot YYYYMMDD`

## W2 — Descoberta de falhas (variante de `feature-discovery`)

Carregue `.cursor/skills/feature-discovery/SKILL.md` e aplique **com estas substituições**:

| Gate original | Neste loop |
|---------------|------------|
| HUMAN_REQUIREMENTS_APPROVAL | PO produz `requirements.md` da falha → commit → `approvals.md` com `APPROVED_BY_PO` + data |
| HUMAN_PLAN_APPROVAL | Principal Engineer produz/atualiza tasks → PO revisa rastreabilidade → commit → `APPROVED_BY_PO` |
| Perguntas ao humano | PO infere de logs Robot; se ambíguo, classifique conservador e documente em `requirements.md` |
| Entrega ao `implementation-pipeline` | **Não.** Handoff direto para W3 |

### Dedup (BR-005)

Antes de criar T28+, verificar tasks existentes:

| Superfície | Task existente |
|------------|----------------|
| compose / boot / launcher e2e | **T22** |
| UI browser / fluxos visuais | **T23** |
| catálogo / indexação | **T24** |
| cenários negativos | **T25** |
| MCP / SLO | **T26** |
| SDK / BDD-024 | **T27** |
| container / compose end-user | **T28+** |

Achado já coberto → **atualizar evidência** na task existente; não duplicar.

Cada task nova/atualizada:

- estado `READY_FOR_IMPLEMENTATION`
- evidência sanitizada (comando, cenário, log)
- critério de aceite ligado ao cenário BDD do pai
- **fora de escopo:** alterar `e2e/robot/**`

Índice: `spec/features/<loop-feature-id>/runs/failure-backlog-index.md`

**Commits por etapa:**

1. `docs(spec): requisitos falha e2e <superfície>` — após PO
2. `docs(spec): tasks bug e2e <IDs>` — após PE + revisão PO
3. `docs(spec): aprovação automática discovery e2e` — registro em `approvals.md`

## W3 — Orquestrador autônomo

Carregue `.cursor/skills/autonomous-implementation-orchestrator/SKILL.md`.

Handoff mínimo em `spec/features/<loop-feature-id>/runs/orchestrator-handoff-YYYYMMDD.md`:

```yaml
feature_id: github-etl-mcp-rag
stop_criterion: python -m github_rag.e2e exit 0
tasks: [T22..T27 pendentes + T28+ de W2]
dependency_waves: conforme implementation-plan.md do pai
architect_gate: true
human_intermediate_gate: false
robot_files_frozen: true
```

Ordem sugerida de ondas:

1. **T22** (tooling/stack)
2. **T26** (se PR aberto — retomar)
3. **T23, T24, T25, T27** — paralelo conforme deps
4. **T28+** — por superfície

Após cada onda: status em `orchestrator-status-YYYYMMDD.md`. **Commit:** `chore(e2e): status orquestrador onda N`.

### Política de merge

- **Padrão deste loop:** após exit `0`, merge automático dos PRs do ciclo na ordem de dependências (`gh pr merge`, sem force push), conforme `mvp-local-e2e-green` REQ-008/REQ-026.
- Se o operador pedir só PRs abertos: pare em W3 e entregue URLs + ordem de merge.

Task falha no pipeline: registrar; não bloquear independentes; não avançar ondas dependentes.

## Gate humano único — Robot congelado

Dispare **somente** se uma task exigir mudança em:

- `e2e/robot/**`
- `e2e/fixtures/**`
- contrato de suíte (`GREEN_PATH_SUITES`, tags `--exclude`)

Fluxo:

1. Commit candidato com proposta isolada
2. Pare o loop
3. Aguarde aprovação humana explícita
4. Após aprovação: commit de registro em `approvals.md` e retome W1

## Classificação por superfície

| Superfície | Suites / sintoma |
|------------|------------------|
| `health` | `health.robot`, `/healthz` |
| `catalog_indexing` | `catalog_indexing.robot` |
| `ui` | `ui.robot` |
| `ui` (browser) | `ui_browser.robot` → task **T23** |
| `mcp` | `mcp.robot` |
| `negative` | `negative.robot` |
| `tooling-e2e` | compose, boot, launcher, credencial, timeout |
| `container-delivery` | imagem, `docker-compose.yml` end-user |

## Restrições

- Agente principal **nunca** implementa código de produto nem altera Robot sem gate.
- Cobertura ≥ 95% herdada do orquestrador autônomo por task.
- Nunca force push; nunca commitar `.env` ou `e2e/results/`.
- Falha de token/stack/timeout vira achado registrado — não abortar sem evidência.
- Mudança de escopo fora do achado e2e → pausar e devolver ao discovery completo.

## Referências

- Feature operacional: `spec/features/mvp-local-e2e-green/`
- Plano e tasks W1–W3: `implementation-plan.md`, `tasks/T01`–`T03`
- Parent backlog: `spec/features/github-etl-mcp-rag/tasks/`
