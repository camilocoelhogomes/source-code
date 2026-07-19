# Design — T04-run-e2e-robot

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T04-run-e2e-robot` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/mvp-e2e-audit-hardening-T04-run-e2e-robot` |
| Base | `main` @ `935e91b` |
| Rastreabilidade | REQ-002, REQ-012–015; DEC-004; ENG-004; BDD-003; contrato `RobotGreenPathRun` |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Superfície mínima: execução canônica T21 + resumo sanitizado em `runs/`; sem expandir Robot; sem fix de produto; soft-dep T03 independente. |

## 1. Contexto

A feature filha `mvp-e2e-audit-hardening` audita o MVP sem corrigir domínio. T04 é a onda W2 (run-first Robot):

- Pré dura: T02 (`HitlEnvPrep` gate T04 = `READY`) — Podman + `.env` com token presente, não versionado.
- Soft-dep T03: ordem preferida pytest → e2e (REQ-014); **não** bloqueia; evidência T04 é independente (não rebase em T03).
- Executar green path canônico via `python -m github_rag.e2e` (Podman + `docker-compose.e2e.yml` + GitHub real) — ENG-004 / T21.
- Registrar sucesso/falha observável e versionável (REQ-015 / ENG-002), sem secrets (BR-004).
- Green path atual T21 apenas — **proibido** adicionar `.robot`/browser (BR-007).

T04 **não** altera produto, compose, keywords Robot nem pytest (T03).

## 2. Problema

1. Precisa-se de evidência reproduzível de que o green path Robot foi exercitado em stack real (BDD-003).
2. Falha de stack/credencial/cenário deve ficar explícita para T05 (REQ-015) — exit ≠ 0 é resultado válido.
3. Fase run-first: **não** corrigir flakiness/produto nem expandir suíte para “passar”.
4. Soft-dep T03: registrar nota de independência se T03 ainda aberto.
5. Menor superfície: evitar código de domínio novo (plano §1.2).

## 3. Solução proposta

### 3.1 Decisão de superfície (D-T04-001)

| Opção | Avaliação |
|---|---|
| A — Resumo Markdown versionado em `runs/` + testes BDD de contrato do artefato | Satisfaz BDD-003 / REQ-015 / ENG-002/004; zero mudança de produto; alinhado ao ownership da feature filha |
| B — Runner Python novo em `src/github_rag/**` | Desnecessário: `python -m github_rag.e2e` já é o entrypoint T21; viola “não altera código” do plano §1.2 |
| C — Commitar `e2e/results/` (log/XML/HTML Robot bruto) | Risco de secrets/ruído; ENG-002: `e2e/results/` gitignored; versionar só resumo sanitizado |

**Escolha: opção A** — artefato `runs/e2e-robot-green-path.md` + asserts pytest de contrato documental. **Nenhum** módulo novo em `src/github_rag/**`. **Nenhuma** alteração em `e2e/robot/**` / compose / produto.

### 3.2 Contrato lógico `RobotGreenPathRun`

| Responsabilidade | Motivo da separação |
|---|---|
| Executar `python -m github_rag.e2e` com Podman + compose e2e + credencial HITL | ENG-004 / REQ-002, 012–013 / BDD-003 |
| Registrar exit code, fases (credencial/stack/robot), suítes/cenários falhos, timeouts/rate-limit, presença de artefatos locais | REQ-015; handoff T05 |
| Mapear falhas a superfícies candidatas sem abrir tasks | Alimenta T05; ENG-006 |
| Não expandir Robot nem corrigir produto | run-first / BR-007 / DEC-008 |

Implementação do contrato = **execução + estrutura do resumo Markdown**, não classe Python de produto.

### 3.3 Artefato principal

`spec/features/mvp-e2e-audit-hardening/runs/e2e-robot-green-path.md`

Conteúdo obrigatório (sem segredos):

1. **Metadados do run** — data/hora ISO, branch, commit SHA, Python, OS, Podman version resumida.
2. **Comando canônico** — exatamente `python -m github_rag.e2e`.
3. **Pré-condições** — gate T02 (`READY`); token `present=true/false` (nunca valor); Podman ok; repo ref `camilocoelhogomes/source-code`.
4. **Resultado agregado** — exit code do entrypoint T21 (`0` ok; `2` credencial; `3` stack; demais ≠0 robot/erro).
5. **Fases** — credential resolve; compose up/build; wait_healthy; robot; compose down (status ok/fail/skip + nota sanitizada).
6. **Suítes green path** — `health`, `catalog_indexing`, `ui`, `mcp`, `negative` (T21; `--exclude bdd015`); resultado por suíte quando observável (pass/fail/unknown).
7. **Falhas acionáveis para T05** — por suíte/cenário ou fase (stack/credencial/timeout/rate-limit); superfície candidata ENG-006; lista vazia válida se exit 0.
8. **Artefatos locais** — presença de `e2e/results/` (output.xml / log.html / report.html) como boolean; **não** versionar conteúdo.
9. **Soft-dep T03** — declarar se evidência pytest T03 estava mergeada; run é **independente** (não rebase).
10. **Proibições** — nunca PAT, `.env`, Authorization, dumps de env.

### 3.4 Comando de execução

```bash
set -a; source .env; set +a
python -m github_rag.e2e
```

Notas:

- Deps: `pip install -e ".[e2e]"` (ou `requirements-e2e.txt`) conforme `e2e/README.md`.
- Runtime: Podman + `docker-compose.e2e.yml` (T19/T21).
- Exit ≠ 0 **é resultado válido** (evidência); não corrigir produto até verde.
- Redaction: qualquer saída capturada deve passar por sanitização antes do resumo (substituir valores de token por `[REDACTED]`).

### 3.5 Decisão D-T04-002 — contrato da filha vs falhas do pai

| Item | Regra |
|---|---|
| Testes BDD de contrato T04 (`tests/bdd/test_mvp_e2e_audit_e2e_robot_run.py`) | Validam estrutura/sanitização do artefato; **não** são achados de produto |
| Lista de falhas no resumo para T05 | Só falhas da prova Robot/stack/credencial do green path; **não** incluir falhas dos testes de contrato da filha |
| Ordem de implementação | (1) executar comando canônico e capturar saída sanitizada; (2) escrever `runs/e2e-robot-green-path.md`; (3) testes de contrato passam ao validar o artefato |

### 3.6 Mapa de superfícies (ENG-006)

| Superfície | Origem na prova Robot / stack |
|---|---|
| `health` | suíte `health.robot` / `/healthz` |
| `catalog_indexing` | suíte `catalog_indexing.robot` |
| `ui` | suíte `ui.robot` (API HTTP — lacuna browser fica para T06) |
| `mcp` | suíte `mcp.robot` |
| `negative` | suíte `negative.robot` |
| `tooling-e2e` | falha de credencial, compose/Podman, timeout de stack, rate-limit infra, entrypoint |

## 4. Fluxo

```text
T02 gate READY (.env + Podman)
        │
        ▼
python -m github_rag.e2e
  resolve credential → podman compose up --build
  → wait /healthz → robot (5 suítes, exclude bdd015)
  → compose down (finally)
        │
        ▼
runs/e2e-robot-green-path.md  (sanitizado)
        │
        ▼
T05  (falhas → tasks no pai)
```

## 5. Dados / erros / segurança

| Aspecto | Contrato |
|---|---|
| Secrets | Nunca versionar; evidência token = `present=true/false` |
| `e2e/results/` | Local, gitignored; só boolean de presença no resumo |
| Exit codes T21 | `0` sucesso; `2` credencial; `3` stack; ≠0 robot/erro genérico |
| Rate-limit / timeout | Registrar em falhas com superfície `tooling-e2e` ou da suíte afetada; classificar depois em T05 |
| Soft-dep T03 | Nota explícita; evidência independente |

## 6. Observabilidade

- Resumo versionável é a evidência SoT desta task.
- Logs brutos ficam em `/tmp` ou `e2e/results/` local — não commitados.
- Handoff T05: lista de falhas + superfícies; ausência de falha não encerra lacunas (T01/T06).

## 7. Compatibilidade / riscos / rollback

| Risco | Mitigação |
|---|---|
| Token inválido / rate-limit GitHub | Registrar falha explícita; não inventar PAT |
| Build Podman longo / flaky | Timeout documentado; classificar em T05 |
| Tentativa de expandir Robot | BR-007 / D-T04-001 proíbe |
| Segredo em log | Sanitização obrigatória no resumo |
| T03 ainda aberto | Soft-dep; evidência independente |

Rollback: reverter commits de `spec/.../T04-*/**`, `runs/e2e-robot-green-path.md` e testes de contrato; sem impacto em produto.

## 8. Fora de escopo

- Expandir asserts integrais ou browser (T06 / pai).
- Corrigir produto/flakiness.
- Pytest all-tasks (T03).
- Abrir tasks no pai (T05).
- CI Actions (BR-009).
- Qualquer mudança em `src/github_rag/**`, `e2e/robot/**`, `docker-compose*.yml`.

## 9. DoD do design

- [x] Contrato `RobotGreenPathRun` e artefato `runs/e2e-robot-green-path.md` definidos.
- [x] Comando canônico `python -m github_rag.e2e` congelado.
- [x] Soft-dep T03 e proibição de expansão Robot explícitas.
- [x] Superfície zero de produto (D-T04-001).
- [x] `APPROVED_BY_ARCHITECT`.
