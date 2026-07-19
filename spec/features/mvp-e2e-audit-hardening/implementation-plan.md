# Plano de implementação — mvp-e2e-audit-hardening

| Campo | Valor |
|---|---|
| Feature ID | `mvp-e2e-audit-hardening` |
| Versão do plano | `0.1.0` |
| Estado | `PENDING_PO_REVIEW` |
| Requisitos base | `requirements.md` v0.1.0 (aprovado 2026-07-18, commits `c460bd5` / `5e07020`) |
| Natureza | feature filha operacional: audita cobertura MVP integral, executa provas (pytest + Robot), abre backlog no pai — **não** corrige produto |
| Feature pai / destino das tasks de correção | `github-etl-mcp-rag` (IDs novos após T21, ex. T22+) |
| Dependências externas | T19 (`docker-compose.e2e.yml`) + T21 (`e2e/robot/**`, `python -m github_rag.e2e`) entregues no pai |

## 1. Arquitetura do trabalho

### 1.1 Visão

Esta feature é um **pipeline de auditoria e backlog**, não um incremento de domínio:

```text
W0  inventário BDD integral × suíte atual     prep .env HITL (doc + checklist)
         │                                         │
         ▼                                         ▼
W1  pytest (todas as tasks do pai)  ───────────────┘
         │
         ▼
W2  python -m github_rag.e2e  (Podman + green path T21)
         │
         ▼
W3  tasks de FALHA no pai (por superfície + classificação)
         │
         ▼
W4  tasks de LACUNA / gap-fill no pai (browser UI + asserts integrais)
         │
         ▼
W5  consolidação de evidências + encerramento desta feature
```

**Regra dura (BR-007 / DEC-008):** run-first (W1–W3) **antes** de gap-fill (W4). Não expandir a suíte Robot para “passar” o green path atual.

### 1.2 Ownership

| Artefato | Dono | Esta feature |
|---|---|---|
| Producto ETL/RAG/MCP, composes T19, suíte Robot T21 | `github-etl-mcp-rag` | **não altera código**; só consome e abre tasks |
| Inventário, logs de run, evidências, plano/tasks desta feature | `mvp-e2e-audit-hardening` | **dona** |
| Tasks de falha / lacuna resultantes | `github-etl-mcp-rag/tasks/` | **cria** artefatos de task; implementação fica no pipeline do pai |
| CI/docs/release | `docs-cicd-e2e-release` | fora de escopo (BR-009) |

### 1.3 Decisões de engenharia

| ID | Decisão | Motivo |
|---|---|---|
| ENG-001 | Critério de auditoria = texto integral BDD-001–024 do pai (exceto 015); fatias DEC-019/T21 parcial = lacuna se o critério integral exigir mais | REQ-001, BR-001, DEC-002 |
| ENG-002 | Evidências versionáveis em `spec/features/mvp-e2e-audit-hardening/audit/` e `runs/`; artefatos Robot em `e2e/results/` (já gitignored) — resumo do run é versionado, não o log bruto com risco de segredo | REQ-015, BR-004 |
| ENG-003 | Comando pytest canônico: `pytest` em `tests/` (todas as tasks do pai já cobertas pela árvore); registrar exit code + falhas por nó | REQ-003, BDD-004 |
| ENG-004 | Entrypoint e2e canônico: `python -m github_rag.e2e` com Podman + `docker-compose.e2e.yml`; repo ref `camilocoelhogomes/source-code` | REQ-002, 012–013 |
| ENG-005 | `.env` local: checklist HITL + verificação de existência/gitignore; **operador** gera o token — plano/tasks nunca inventam nem colocam PAT | REQ-004, 011; DEC-005 |
| ENG-006 | Agrupamento de tasks no pai por superfície: `health`, `catalog_indexing`, `ui`, `mcp`, `negative`, `tooling-e2e` — não 1:1 por BDD | REQ-016, BR-006, DEC-007 |
| ENG-007 | Cada task no pai declara classificação: `produto` \| `flakiness` \| `gap-teste` \| `assert-fraco` (combinação documentada se necessário) | REQ-017, DEC-006 |
| ENG-008 | Gap-fill UI obriga browser (Browser Library / Playwright / equivalente); API HTTP sozinha não fecha lacuna UI | REQ-007, BR-008, BDD-006 |
| ENG-009 | IDs sugeridos no pai: sequência após T21 (`T22+`), nome espelhando superfície + tipo (`T22-fix-health-…`, `T23-gap-ui-browser-…`) | rastreabilidade; evita colidir com T01–T21 |
| ENG-010 | Esta feature **para** após abrir backlog + consolidar evidências; correções só via pipeline das tasks do pai | Fora de escopo; DEC-001 |

### 1.4 Fronteiras e contratos lógicos

| Contrato | Responsabilidade | Não faz |
|---|---|---|
| `CoverageInventory` | Matriz BDD-001–024 (exc. 015) × evidência Robot/pytest/browser/lacuna | Implementar asserts novos |
| `HitlEnvPrep` | Checklist `.env` a partir de `.env.example`; gate “token presente, arquivo não trackeado” | Gerar/commitar token |
| `ParentPytestRun` | Executar e registrar pytest de todas as tasks | Corrigir falhas de produto |
| `RobotGreenPathRun` | Executar green path T21 e registrar resultado | Expandir cobertura integral antes do run |
| `ParentFailureBacklog` | Abrir tasks de falha no pai por superfície | Implementar fixes |
| `ParentGapFillBacklog` | Abrir tasks de lacuna (browser + asserts integrais) após W3 | Implementar keywords/browser |
| `AuditClosurePack` | Pacote de evidências + índice de tasks abertas para gate de encerramento | Declarar MVP entregue |

## 2. Ordem e dependências (DAG)

```text
T01-coverage-inventory ──────────────────────────────┐
T02-hitl-env-prep ──┐                                │
                    ▼                                │
                 T03-run-pytest-all-tasks            │
                    │                                │
                    ▼                                │
                 T04-run-e2e-robot ◄── T02           │
                    │                                │
                    ▼                                │
                 T05-open-failure-tasks-parent       │
                    │                                │
                    ▼                                │
                 T06-open-gap-fill-tasks-parent ◄────┘ (T01 + T05)
                    │
                    ▼
                 T07-consolidate-evidence-close
```

| Task | Depende de |
|---|---|
| T01 | — (pré: requisitos pai + árvore `e2e/` T21) |
| T02 | — (HITL humano para token) |
| T03 | Soft T01 (contexto); não bloqueia em T02 |
| T04 | **Dura** T02; Soft T03 (ordem preferida pytest → e2e, REQ-014) |
| T05 | **Dura** T03 + T04 |
| T06 | **Dura** T01 + T05 (BR-007) |
| T07 | **Dura** T05 + T06 |

## 3. Ondas paralelas

| Onda | Tasks | Gate |
|---|---|---|
| W0 | `T01`, `T02` | Inventário + prep env (HITL) em paralelo |
| W1 | `T03` | Pytest todas as tasks registrado |
| W2 | `T04` | Robot green path executado (Podman) |
| W3 | `T05` | Tasks de falha abertas no pai |
| W4 | `T06` | Tasks de lacuna/gap-fill abertas no pai |
| W5 | `T07` | Evidências consolidadas; feature encerrável |

**Critical path:**  
`T02 → T04 → T05 → T06 → T07`  
(com `T01` alimentando T06; `T03` alimentando T05 em paralelo ao eixo e2e após T02).

## 4. Estratégia anti-retrabalho

1. **Inventário antes do gap-fill** — lacunas documentadas em T01; T06 só materializa tasks a partir do inventário + resultado do run.
2. **Não expandir Robot em W1–W2** — mede o green path atual; evita mascarar bugs com asserts novos.
3. **Agrupar por superfície** — uma task por superfície/tipo dominante, não explosão 1:1 BDD.
4. **Classificação obrigatória** — evita misturar flakiness com bug de produto no mesmo backlog sem rótulo.
5. **Segredos só HITL** — T02 documenta; never commit `.env`.
6. **Ownership estável** — correções e keywords novas só no pai; esta feature só abre a porta.
7. **IDs T22+ no pai** — não reabre T21; tasks delta explícitas.
8. **Browser só em gap-fill** — custo de Browser Library fica em W4 via tasks do pai, não no run-first.

## 5. Rastreabilidade requisito → task

| Task | REQs / BRs / DECs | BDDs desta feature |
|---|---|---|
| T01 | REQ-001, 008–010; BR-001–002; DEC-002; ENG-001–002 | BDD-001, BDD-008 (parcial) |
| T02 | REQ-004, 011–012; BR-004; DEC-005; ENG-005 | BDD-002 |
| T03 | REQ-003, 014–015; DEC-004; ENG-003 | BDD-004 |
| T04 | REQ-002, 012–015; DEC-004; ENG-004 | BDD-003 |
| T05 | REQ-005, 016–017; BR-005–007; DEC-006–008; ENG-006–007, 009 | BDD-005, BDD-007 (parcial) |
| T06 | REQ-005–007, 018–019; BR-007–008; DEC-003, 008; ENG-008–009 | BDD-006, BDD-007, BDD-008 |
| T07 | Métricas de sucesso; BR-005; ENG-002, 010 | BDD-001–008 (fechamento) |

## 6. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Token HITL ausente | T02 bloqueia T04; falha explícita vira achado `tooling-e2e` se comportamento ≠ contrato T21 |
| Rate limit / flakiness GitHub | Classificar `flakiness`; task `tooling-e2e`; não ignorar (BR-005) |
| Muitas lacunas vs T21 parcial | Agrupamento ENG-006; inventário T01 como SoT |
| Tentativa de “corrigir” na feature filha | ENG-010; critérios de aceite proíbem mudança de domínio |
| Segredo em artefato Robot | ENG-002: versionar só resumo sanitizado; `e2e/results/` gitignored |
| Declarar MVP entregue cedo | Fora de escopo; T07 só encerra auditoria/backlog |

## 7. Migração / rollback

- Sem migração de dados ou API.
- Rollback: reverter commits de `spec/features/mvp-e2e-audit-hardening/**` e tasks abertas no pai que ainda não entraram em implementação.
- Tasks do pai já em pipeline: tratadas individualmente no pai; esta feature não faz force-merge nem implementa.

## 8. Handoff

- Estado do plano: `PENDING_PO_REVIEW`.
- Próximo gate: revisão PO (rastreabilidade/valor) → aprovação humana do plano → implementação task a task nesta feature (W0→W5).
- Tasks de correção/lacuna no pai entram no `implementation-pipeline` / orquestrador autônomo **depois** de abertas (T05/T06), sob ownership de `github-etl-mcp-rag`.
