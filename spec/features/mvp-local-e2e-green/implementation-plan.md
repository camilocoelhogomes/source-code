# Plano de implementação — mvp-local-e2e-green

| Campo | Valor |
|---|---|
| Feature ID | `mvp-local-e2e-green` |
| Versão do plano | `0.1.0` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Revisão PO | `aprovado` (2026-07-19) |
| Requisitos base | `requirements.md` v0.1.0 (`APPROVED` 2026-07-19 por `operador`) |
| Natureza | feature filha operacional: loop e2e → backlog no pai → orquestrador autônomo → imagem local → merge auto quando Robot verde |
| Feature pai / destino das tasks de bug | `github-etl-mcp-rag` (T22–T27 existentes + novas T28+) |
| Feature irmã / contexto | `mvp-e2e-audit-hardening` (inventário T22–T27 já abertas) |
| Dependências externas | T19 (composes/Dockerfile), T21 (`python -m github_rag.e2e`), skill `autonomous-implementation-orchestrator` |

## 1. Arquitetura

### 1.1 Visão

Pipeline de **entrega do MVP local verde**, complementar à auditoria (`mvp-e2e-audit-hardening`):

```text
                    ┌─────────────────────────────────────┐
                    │  Pré-reqs (HITL): .env, Podman,     │
                    │  pip -e ".[e2e]", rfbrowser init    │
                    └──────────────────┬──────────────────┘
                                       │
W1  T01-run-e2e-local ────────────────┤  python -m github_rag.e2e
         │                             │  (Podman + docker-compose.e2e.yml)
         ▼                             │
W2  T02-open-bug-tasks-parent ────────┤  falhas → tasks pai (T28+)
         │                             │  dedup T22–T27 (BR-005)
         ▼                             │
W3  T03-orchestrate-bugfix-loop ──────┤  autonomous-implementation-orchestrator
         │                             │  (Architect gate; PRs por task)
         │         ┌──────────────────┘
         │         │  loop REQ-005 até Robot verde
         ▼         ▼
W4  T04-build-local-image ────────────┤  docker build → github-rag:local
         │                             │  compose end-user: image: (delta T19/pai)
         ▼                             │
W5  T05-verify-and-auto-merge ────────┘  re-run e2e + gh pr merge (sem force)
```

**Critério de entrega (BR-001):** Robot green path 100% verde + `docker compose up -d` (sem `--build`) com `github-rag:local` + `/healthz` OK.

### 1.2 Superfícies e ownership

| Superfície | Run e2e (T21) | Backlog existente | Novas tasks (T28+) |
|---|---|---|---|
| `tooling-e2e` | compose/boot/launcher | **T22** | runtime failures não cobertas |
| `ui` / browser | `ui`, `ui_browser` | **T23** | falhas de cenário UI |
| `catalog_indexing` | `catalog_indexing` | **T24** | falhas de cenário catálogo |
| `negative` | `negative` | **T25** | falhas negativas |
| `mcp` | `mcp` | **T26** (`PR_OPENED`) | falhas MCP / SLO |
| `sdk` / delivery | smoke BDD-024 | **T27** | conformidade integral |
| `health` | `health` | — | falhas `/healthz` |
| `container-delivery` | — | — | **T28+** compose `image:` + imagem local |

Esta feature **orquestra**; correções de produto/composes permanecem no pipeline do pai (`github-etl-mcp-rag`).

### 1.3 Estratégia imagem local `github-rag:local`

| Aspecto | Decisão | Referência |
|---|---|---|
| Tag canônica | `github-rag:local` | REQ-006, DEC-006 |
| Plataforma | `linux/amd64` | ENG-006, REQ-021 |
| Build | Explícito, nunca implícito no `compose up` | DEC-007, REQ-022 |
| Comando | `docker build --platform linux/amd64 -t github-rag:local .` (Podman equivalente) | REQ-022 |
| Entrypoint | `python -m github_rag.delivery` (via Dockerfile) | BDD-005 |
| Rebuild | Após cada merge que altere código containerizado | BR-007 |
| Escopo compose | **`docker-compose.yml`** end-user: `image: github-rag:local`; remover/evitar `build:` padrão | REQ-007, DEC-006 |
| E2e canônico | Continua **`docker-compose.e2e.yml`** + Podman (T19/T21); não substituir | REQ-025, BR-008 |
| Dev | `docker-compose.dev.yml` inalterado (infra-only + app host) | REQ-025 |

**`image:` vs `build:`:** o fluxo end-user padrão (`docker compose up -d`) **não** deve disparar rebuild silencioso. O delta de manifesto (`docker-compose.yml`) é entregue via task pai de `container-delivery` (ex. **T28**), acionada por T04; ownership permanece T19 no pai.

### 1.4 Handoff `autonomous-implementation-orchestrator`

Payload mínimo (REQ-018):

```yaml
feature_id: github-etl-mcp-rag
stop_criterion: python -m github_rag.e2e exit 0 (suítes REQ-002, --exclude bdd015)
tasks:
  - id: T22-fix-tooling-e2e-compose-zoekt
    state: READY_FOR_IMPLEMENTATION
  - id: T23-gap-ui-browser
  - id: T24-gap-catalog-indexing-integral
  - id: T25-gap-negative-integral
  - id: T26-gap-mcp-parallel-slo  # PR_OPENED — incluir no merge order
  - id: T27-gap-sdk-dec015-conformity
  - id: T28+  # runtime failures de T02
waves: conforme DAG do pai + dependências T22→demais
architect_gate: substitui HITL intermediário (DEC-004, REQ-020)
human_gate: dispensado para merge pós-Robot verde (DEC-005, REQ-008)
```

Regras:

- Consumir **T22–T27** antes de duplicar (BR-005, DEC-008).
- Branch por task: `feature/github-etl-mcp-rag-<task-id>`.
- Cobertura ≥ 95% herdada do pipeline autônomo.
- Falha de uma task não bloqueia independentes; ondas dependentes aguardam.
- Após onda aplicável: rebuild imagem (BR-007) → T01/T05 re-run.

### 1.5 Merge automático pós-Robot verde

| Condição | Ação |
|---|---|
| `python -m github_rag.e2e` exit 0 + suítes REQ-002 verdes | Elegível para merge auto (DEC-005) |
| PRs do ciclo (T22–T27 + T28+) | `gh pr merge` na ordem de dependências, **sem force push** (REQ-026) |
| Conflito / CI remota / regressão | Pausar merge; task `tooling-e2e` T28+; não declarar entregue (REQ-028) |
| BDD-015 | Fora do critério (BR-003, DEC-009) |
| Segredos | Nunca commit; redaction em evidências (BR-004) |

T05 executa validação final **e** merge auto autorizado pelo operador (gate HITL de merge dispensado em requisitos 0.1.0).

### 1.6 Decisões de engenharia

| ID | Decisão | Motivo |
|---|---|---|
| ENG-001 | Entrypoint e2e = `python -m github_rag.e2e`; suítes green path REQ-002 com `--exclude bdd015` | DEC-002, REQ-002 |
| ENG-002 | Evidências versionáveis em `spec/features/mvp-local-e2e-green/runs/`; `e2e/results/` gitignored | REQ-013, BR-004 |
| ENG-003 | Dedup obrigatório com T22–T27 antes de criar T28+ | BR-005, DEC-008 |
| ENG-004 | T03 invoca orquestrador autônomo sem HITL intermediário | DEC-004, REQ-004 |
| ENG-005 | Imagem local separada do fluxo e2e (compose.e2e.yml); validada em T04/T05 | REQ-025 |
| ENG-006 | Loop REQ-005: T01→T02→T03→(rebuild T04)→T05 até verde ou bloqueio documentado | BDD-004 |
| ENG-007 | Merge auto só após Robot verde **local** na validação final T05 | BR-006 |
| ENG-008 | Delta `docker-compose.yml` via task pai T28+ (ownership T19); T04 orquestra build + handoff | REQ-007, BR-008 |

## 2. Ordem e dependências (DAG)

```text
T01-run-e2e-local
        │
        ▼
T02-open-bug-tasks-parent
        │
        ▼
T03-orchestrate-bugfix-loop  ◄── inclui T22–T27 + T28+
        │
        ▼
T04-build-local-image        ◄── rebuild pós-merge (BR-007); delta compose → T28+
        │
        ▼
T05-verify-and-auto-merge
```

| Task | Depende de | Produz |
|---|---|---|
| T01 | Pré-reqs HITL (`.env`, Podman, deps e2e) | `runs/e2e-*.md` |
| T02 | **Dura** T01 | tasks pai T28+ ou updates T22–T27 |
| T03 | **Dura** T02 | PRs no pai; branches mergeáveis |
| T04 | **Dura** T03 (merges aplicáveis); soft rebuild inicial se imagem ausente | `github-rag:local`; handoff T28 compose |
| T05 | **Dura** T04 + Robot verde candidato | MVP local entregue ou bloqueio |

**Loop externo:** se T05 falhar e2e, retornar a T02 (novas evidências) → T03 → T04 rebuild → T05.

## 3. Ondas paralelas

| Onda | Tasks | Gate |
|---|---|---|
| W0 | Pré-reqs HITL (checklist `mvp-e2e-audit-hardening`) | `.env` válido, Podman, `rfbrowser init` |
| W1 | `T01` | Primeiro run e2e registrado |
| W2 | `T02` | Backlog runtime deduplicado com T22–T27 |
| W3 | `T03` | Orquestrador autônomo concluiu onda aplicável |
| W4 | `T04` | Imagem `github-rag:local` + compose end-user |
| W5 | `T05` | Robot verde + merge auto + BR-001 |

**Critical path:**  
`T01 → T02 → T03 → T04 → T05`  
(com sub-loop T02–T05 até exit 0).

## 4. Reutilização T22–T27

| Task pai | Incluir em T03 | Observação |
|---|---|---|
| T22 | Sim (prioridade W3) | Pré-req stack zoekt/compose — bloqueia green path |
| T23 | Sim | Browser UI; depende stack saudável |
| T24 | Sim | Asserts catálogo integral |
| T25 | Sim | Cenários negativos |
| T26 | Sim | PR já aberto — merge order após deps |
| T27 | Sim | Conformidade SDK/BDD-024 |
| T28+ | Criadas por T02 | Falhas runtime novas pós-auditoria |

T02 **atualiza** task existente com nova evidência quando o achado for o mesmo (BR-005); **não** duplica.

## 5. Rastreabilidade requisito → task

| Task | REQs / BRs / DECs | BDDs |
|---|---|---|
| T01 | REQ-001, 011–014; DEC-002 | BDD-001 |
| T02 | REQ-003, 015–017; BR-002, BR-005; DEC-003, DEC-008 | BDD-002 |
| T03 | REQ-004, 018–020; DEC-004 | BDD-003 |
| T04 | REQ-006, 007, 021–025; DEC-006, DEC-007; BR-007 | BDD-005, BDD-006 |
| T05 | REQ-005, 008, 026–028; BR-001, BR-006; DEC-005 | BDD-004, BDD-007, BDD-008 |

## 6. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Flakiness GitHub real | Classificar `flakiness`; task tooling; reexecução no loop |
| Imagem desatualizada pós-merge parcial | BR-007: T04 rebuild explícito antes de T05 |
| Merge auto sem revisão humana | Robot verde local obrigatório + pytest ≥ 95% no pipeline autônomo |
| Conflitos na `main` | Pausar merge auto; task tooling T28+; rebase documentado |
| Duplicar backlog T22–T27 | ENG-003 dedup em T02 |
| T26 PR empilhado / ordem merge | T05 documenta `merge_order_notes` do orquestrador |

## 7. Migração / rollback

- **Compose end-user:** migrar `build:` → `image: github-rag:local` via task pai T28; rollback = reverter commit da task T28 na `main`.
- **Imagem local:** tag local apenas; rollback = rebuild explícito de commit anterior.
- **Loop autônomo:** reverter merges individuais no GitHub; reexecutar T01.
- Esta feature não faz force push na `main`.

## 8. Handoff orquestrador principal

1. Implementar tasks W1→W5 desta feature (`implementation-pipeline` padrão ou coordenação direta).
2. Em T03, carregar `.cursor/skills/autonomous-implementation-orchestrator/SKILL.md` com handoff §1.4.
3. Monitorar PRs até T05; executar merge auto quando Robot verde (autorização DEC-005).
4. Declarar MVP local entregue somente se BR-001 satisfeito.

## 9. Arquivos alterados / criados (escopo do plano)

| Caminho | Papel |
|---|---|
| `spec/features/mvp-local-e2e-green/implementation-plan.md` | este plano |
| `spec/features/mvp-local-e2e-green/tasks/T01-*.md` … `T05-*.md` | tasks desta feature |
| `spec/features/mvp-local-e2e-green/runs/*.md` | evidências de execução e2e (T01, T05) |
| `spec/features/mvp-local-e2e-green/runs/orchestrator-handoff-*.md` | payload T03 |
| `spec/features/mvp-local-e2e-green/runs/merge-auto-*.md` | log T05 merge |
| `spec/features/github-etl-mcp-rag/tasks/T28+*.md` | novas tasks runtime (T02) |
| `docker-compose.yml` | delta `image:` (via task pai T28, T04 handoff) |
| `Dockerfile` | consumido no build; sem alteração obrigatória nesta feature |
