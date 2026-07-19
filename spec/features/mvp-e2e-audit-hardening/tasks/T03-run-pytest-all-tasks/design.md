# Design — T03-run-pytest-all-tasks

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T03-run-pytest-all-tasks` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Branch | `feature/mvp-e2e-audit-hardening-T03-run-pytest-all-tasks` |
| Base | `main` @ `086f3b3` |
| Rastreabilidade | REQ-003, REQ-014–015; DEC-004; ENG-003; BDD-004; contrato `ParentPytestRun` |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `PENDING_ARCHITECT_REVIEW` | `0.1.0` | Draft inicial: run-first pytest + resumo versionável sem secrets; sem fix de produto. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Correções M-01/M-02: handoff T05 (falhas do pai vs contrato da filha; exit coverage-gate); comando canônico unificado. |

## 1. Contexto

A feature filha `mvp-e2e-audit-hardening` audita o MVP sem corrigir domínio. T03 é a onda W1 (run-first pytest):

- Executar a suíte canônica `pytest` sobre `tests/` (ENG-003) — unitários + BDD de contrato de **todas as tasks** do pai `github-etl-mcp-rag`.
- Registrar resultado observável e versionável (REQ-015 / ENG-002).
- Mapear falhas a superfícies candidatas (`health`, `catalog_indexing`, `ui`, `mcp`, `negative`, `tooling-e2e`) para handoff T05 — **sem** abrir tasks no pai.
- Soft-dep T01: inventário é contexto opcional; se T01 não estiver mergeado, o run **não** depende do artefato de inventário.

T03 **não** roda Robot/`python -m github_rag.e2e` (T04), **não** altera produto nem `e2e/robot/**`.

## 2. Problema

1. Precisa-se de evidência reproduzível de que pytest de todas as tasks do pai foi executado (BDD-004).
2. Falhas devem ficar acionáveis para T05 (nó de teste + superfície candidata) sem secrets.
3. Fase run-first: **não** corrigir falhas de produto nem expandir testes para “passar”.
4. Menor superfície: evitar código de domínio novo (plano §1.2).

## 3. Solução proposta

### 3.1 Decisão de superfície (D-T03-001)

| Opção | Avaliação |
|---|---|
| A — Resumo Markdown versionado em `runs/` + testes BDD de contrato do artefato | Satisfaz BDD-004 / REQ-015 / ENG-002–003; zero mudança de produto; alinhado ao ownership da feature filha |
| B — Runner Python em `src/github_rag/**` | Desnecessário: `pytest` já é o entrypoint canônico; viola “não altera código” do plano §1.2 |
| C — Commitar XML/JUnit bruto + HTML coverage | Risco de ruído/segredos; ENG-002 prefere resumo sanitizado |

**Escolha: opção A** — artefato `runs/pytest-all-tasks.md` + asserts pytest de contrato documental. **Nenhum** módulo novo em `src/github_rag/**`. **Nenhuma** alteração em código de produto ou `e2e/robot/**`.

### 3.2 Contrato lógico `ParentPytestRun`

| Responsabilidade | Motivo da separação |
|---|---|
| Executar pytest canônico sobre `tests/` (todas as tasks do pai) | ENG-003 / REQ-003 / BDD-004 |
| Registrar exit code, contagens, lista de falhas, data/ambiente, cobertura se disponível | REQ-015; handoff T05 |
| Mapear cada falha a superfície candidata sem abrir tasks | Alimenta T05; ENG-006 |
| Não corrigir produto nem expandir suíte | run-first / DEC-008 |

Implementação do contrato = **execução + estrutura do resumo Markdown**, não classe Python de produto.

### 3.3 Artefato principal

`spec/features/mvp-e2e-audit-hardening/runs/pytest-all-tasks.md`

Conteúdo obrigatório (sem segredos):

1. **Metadados do run** — data/hora (ISO), branch/commit SHA, comando, Python version, OS resumido.
2. **Comando canônico** — exatamente o de §3.4 (documentar no resumo; `addopts` de cobertura do `pyproject.toml` aplicam-se).
3. **Resultado agregado** — exit code; passed / failed / skipped / errors / total (quando disponível).
4. **Cobertura** — percentual reportado pelo `pytest-cov` se o run o emitir; senão `N/A` com motivo. Se `fail_under` fizer exit ≠ 0 **sem** nodeids falhos, registrar `coverage_gate: true` (ou equivalente) e **não** inventar falhas de produto para T05.
5. **Lista de falhas (pai)** — para cada nó falho **do domínio pai** (excluir nodeids de contrato desta feature filha — ver D-T03-002): `nodeid` pytest, tipo (`failed`/`error`), mensagem sanitizada (sem tokens/env dumps), superfície candidata.
6. **Mapa de superfícies** — heurística estável por path/nodeid (independente de T01):

| Superfície | Heurística (path / marcadores) |
|---|---|
| `health` | `delivery`, `health`, `runtime_boot`, `wiring`, `manifest` |
| `catalog_indexing` | `catalog`, `indexing`, `index/`, `snapshot`, `eligibility`, `schedule`, `sources`, `concurrency` |
| `ui` | `ui/`, `management_ui` |
| `mcp` | `mcp/` |
| `negative` | cenários negativos explícitos / markers se presentes; senão N/A nesta task |
| `tooling-e2e` | `e2e/`, `config`, `settings`, infra de teste, coleta/import errors de ambiente |

7. **Nota soft-dep T01** — declarar se inventário T01 estava disponível no commit base; se não, registrar run sem depender dele.
8. **Proibições** — nunca colar PAT, conteúdo de `.env`, headers Authorization, dumps de env.

### 3.4 Comando de execução

Comando canônico único (ENG-003):

```bash
python -m pytest tests/ -q --tb=line
```

Notas:

- `testpaths = ["tests"]` e cobertura já em `pyproject.toml` (`--cov=github_rag`, `fail_under = 95`).
- Integração (`pytest -m integration`) **não** é obrigatória nesta task; o run padrão do projeto (sem exigir Docker/testcontainers) é o canônico ENG-003. Se o runner local pular integration por indisponibilidade, registrar skipped.
- Exit code ≠ 0 **é resultado válido** desta task (evidência), não motivo para “corrigir até verde” o produto.
- Distinguir no resumo: (a) falhas/erros de nodeid; (b) exit ≠ 0 só por gate de cobertura — (b) não gera linha na lista de falhas do pai para T05.

### 3.4.1 Decisão D-T03-002 — contrato da filha vs falhas do pai

| Item | Regra |
|---|---|
| Testes BDD/unitários de contrato T03 (`tests/bdd/test_mvp_e2e_audit_pytest_run.py` e afins) | Validam **estrutura/sanitização** do artefato `runs/pytest-all-tasks.md`; **não** são achados de produto do pai |
| Lista de falhas no resumo para T05 | Só nodeids de suíte do domínio pai; **excluir** nodeids cujo path/nome seja claramente desta feature filha (`mvp_e2e_audit_*` / paths da task T03) |
| Ordem de implementação | (1) executar comando canônico e capturar saída; (2) escrever `runs/pytest-all-tasks.md`; (3) testes de contrato passam ao validar o artefato já versionável — sem exigir reexecução do pai “até verde” |

### 3.5 Alinhamento com artefatos existentes

| Artefato | Ação T03 |
|---|---|
| `tests/**` | **Consumir** via pytest; não adicionar testes de produto do pai |
| `src/github_rag/**` | **Sem mudanças** |
| `e2e/robot/**` | **Sem mudanças** |
| `pyproject.toml` | **Sem mudanças** (cobertura já configurada) |
| Inventário T01 | Soft; não bloqueia |
| `runs/pytest-all-tasks.md` | **Criar** (resumo sanitizado) |
| Testes BDD desta feature | Contrato do artefato `ParentPytestRun` |

## 4. Componentes

| Componente | Tipo | Papel |
|---|---|---|
| `pytest` + `tests/` | ferramenta + suíte pai | Execução canônica |
| `runs/pytest-all-tasks.md` | doc versionada | SoT do resultado do run |
| Testes BDD de contrato | pytest (feature filha) | Congelam presença/campos do resumo sem secrets |
| T05 | consumidor | Lê falhas + superfícies; abre tasks no pai |

## 5. Fluxo

```text
Operador / pipeline T03
  1. Garantir deps de teste (venv + pytest/pytest-cov)
  2. python -m pytest tests/ -q --tb=line
  3. Capturar exit code, contagens, nodeids falhos, coverage term
  4. Sanitizar saída (remover secrets)
  5. Filtrar nodeids da feature filha (D-T03-002); mapear falhas do pai → superfície
  6. Se exit ≠ 0 só por fail_under e sem nodeids do pai: registrar coverage_gate
  7. Escrever runs/pytest-all-tasks.md
       │
       ▼
T05 consome lista de falhas do pai (não nesta task)
```

## 6. Dados

| Dado | Versionado? | Notas |
|---|---|---|
| Exit code, contagens, nodeids | Sim | Resumo |
| Mensagens de assert (sanitizadas) | Sim, truncadas | Sem env/token |
| Coverage % | Sim se disponível | Do term report |
| XML/HTML coverage bruto | Não obrigatório | Local ok |
| PAT / `.env` / Authorization | **Nunca** | BR-004 |

## 7. Erros e estados

| Situação | Comportamento T03 |
|---|---|
| Pytest exit 0 | Registrar verde; lista de falhas vazia |
| Pytest exit ≠ 0 com nodeids falhos do pai | Registrar falhas + superfícies; **não** corrigir produto |
| Pytest exit ≠ 0 só por `fail_under` (sem nodeids do pai) | Registrar cobertura + `coverage_gate`; lista de falhas do pai vazia |
| Coverage < 95% no run | Registrar valor; não é escopo T03 “subir cobertura” do pai |
| Coleta falha (import error) | Registrar como error; superfície `tooling-e2e` se ambiente; senão path |
| Falha só em teste de contrato T03 | Não entra na lista T05 do pai (D-T03-002); corrigir artefato/contrato nesta feature |
| Segredo em saída bruta | Sanitizar antes de versionar; rejeitar padrões `ghp_`/`gho_`/… |
| T01 ausente | Nota no resumo; run prossegue |

## 8. Segurança

- Resumo sem prefixos de token GitHub e sem atribuições longas a `GITHUB_TOKEN` / `E2E_GITHUB_TOKEN`.
- Não versionar dumps de `os.environ`.
- Truncar mensagens de falha se contiverem paths sensíveis além do necessário.

## 9. Compatibilidade

- Não altera API, schema, compose nem comportamento de produto.
- Alinhado a DEC-004 / ENG-003.
- Soft-dep T01 não empilha PR; base = `main`.

## 10. Observabilidade

- Artefato único versionável com exit code + falhas + superfícies.
- Sem telemetria nova.

## 11. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Tentativa de “corrigir” falhas na feature filha | D-T03-001 + critérios de aceite proíbem mudança de domínio |
| Segredo no log de pytest | Sanitização + teste HITL-like de padrões de token no artefato |
| Heurística de superfície imprecisa | Suficiente para T05; T05 pode reclassificar |
| Dependência dura de T01 | Soft; nota no resumo |
| Suíte longa / flaky | Registrar como está; classificação fina em T05 |

## 12. Rollback

- Reverter commits de `runs/pytest-all-tasks.md`, artefatos T03 e testes de contrato desta feature.
- Sem impacto em runtime de produto.

## 13. Critérios de aceite técnicos (BDD-004)

| Critério | Como T03 cobre |
|---|---|
| Pytest de todas as tasks executado | Comando canônico §3.4 + metadados no resumo |
| Resultado registrado | `runs/pytest-all-tasks.md` |
| Falhas acionáveis para T05 | nodeid do pai + superfície candidata (D-T03-002) |
| Sem alteração de produto / robot | D-T03-001 |

## 14. Arquivos a criar / alterar

| Path | Ação |
|---|---|
| `spec/.../runs/pytest-all-tasks.md` | **Criar** |
| `spec/.../tasks/T03-run-pytest-all-tasks/*` | design, bdd, interfaces, unit-test-plan, reviews, refactoring, approvals |
| `tests/bdd/test_mvp_e2e_audit_pytest_run.py` | Contrato documental do resumo |
| `src/**`, `e2e/robot/**`, `pyproject.toml` | **Não alterar** |

## 15. Fora de escopo

- `python -m github_rag.e2e` / Robot (T04).
- Abrir tasks no pai (T05).
- Fixes de produto ou novos testes de domínio.
- Gap-fill / browser (T06).
- Runner Python em `src/`.

## 16. Handoff

- Próximo: BDD (QA) cobrindo BDD-004 e estrutura do resumo.
- Interfaces: contrato documental `ParentPytestRun`.
- T05 consome `runs/pytest-all-tasks.md`.
- Aprovação humana: único gate no merge do PR.
