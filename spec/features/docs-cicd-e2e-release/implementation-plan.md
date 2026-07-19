# Plano de implementação — docs-cicd-e2e-release

| Campo | Valor |
|---|---|
| Feature ID | `docs-cicd-e2e-release` |
| Versão do plano | `0.2.0` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Requisitos base | `requirements.md` v0.2.0 (aprovado 2026-07-18, commit candidato `37f7def`) |
| Natureza | delta sobre v0.1.1 — remove ownership da suíte Robot (passa a `github-etl-mcp-rag` / T21); T04 vira consumo/integração; mantém CI, docs EN, release GHCR |
| Dependência externa | `github-etl-mcp-rag` / `T19-container-delivery` **e** `T21-mvp-e2e-robot` |
| Revisão humana (plano 0.1.1) | `aprovado` em 2026-07-18 por `camilocoelhogomes` (`HUMAN_PLAN_APPROVAL` v0.1.1 / `8d0f84b`); **obsoleto** para implementação sob 0.2.0 |
| Revisão PO (plano 0.2.0) | `PO_PLAN_REVIEW` aprovado em 2026-07-18 por `product-owner` |
| Revisão humana (plano 0.2.0) | `aprovo` em 2026-07-18 por `camilocoelhogomes` (commit candidato `bbf46d608ea75930577eae5362a82719a9b8cf6d`) |

## 1. Arquitetura

### 1.1 Visão

Camada de **qualidade e entrega** sobre o MVP empacotado (T19) e **provado** (T21):

1. **Gate de PR** — GitHub Actions em `ubuntu-latest`, ordem **obrigatória** (REQ-012): **testes unitários do projeto** → BDD → só então stack e2e (Podman + `docker-compose.e2e.yml` de T19) → **invocar** suíte Robot de **T21**. Unitários e BDD são **pré-condição** do e2e; required checks bloqueiam merge; **sem** publish nem bump.
2. **Consumo e2e** — esta feature **não** cria suíte Robot; invoca a suíte canônica de T21 contra stack real e GitHub real.
3. **Release pós-merge** — Conventional Commits → bump em `pyproject.toml` → build/push GHCR (`latest` + versão).
4. **Docs em inglês** — README (usuário final), CHANGELOG, `docs/` (produto + contribuidores apontando e2e T21).

```text
PR → main                         main (após merge)
┌────────────────────────────┐    ┌────────────────────────────┐
│ ci-pr                      │    │ release                    │
│  1. unitários (obrigatório)│    │  1. bump semver (pyproject)│
│  2. BDD (obrigatório)      │    │  2. build imagem (T19)     │
│  ── gate: 1 e 2 verdes ──  │    │  3. push GHCR latest+ver   │
│  3. podman up e2e compose  │    │                            │
│  4. invocar Robot T21      │    │                            │
│  (não publica / não bump)  │    │                            │
└────────────────────────────┘    └────────────────────────────┘
         │                                    │
         ▼                                    ▼
   docker-compose.e2e.yml (T19)         docker-compose.yml (T19)
   + suíte Robot (T21)                  → ghcr.io/<owner>/<repo>
```

**Pré-condição explícita do e2e:** o job/fase e2e **só** inicia depois que os **testes unitários do projeto** e os testes BDD estiverem verdes no mesmo workflow de PR. Falha em unitários ou BDD falha o required check correspondente e **impede** a execução do e2e (short-circuit) e o merge.

### 1.2 Ownership (DEC-007 / DEC-009)

| Artefato | Dono | Esta feature |
|---|---|---|
| Dockerfile, `docker-compose.yml`, `docker-compose.e2e.yml`, `docker-compose.dev.yml` | T19 | **consome** |
| Suíte Robot Framework e2e (prova MVP) | **T21** | **consome / invoca** — **não** cria |
| Workflows Actions, README/CHANGELOG/`docs/`, release semver+GHCR | esta feature | **dona** |
| Código de domínio / `spec/` (exceto artefatos desta feature) | MVP / outras features | **não altera** |

**Pré-gate:** W1+ desta feature exige T19 **e** T21 DONE (REQ-006). Sem T21, T04–T05/T07 e2e ficam bloqueadas.

### 1.3 Decisões de engenharia

| ID | Decisão | Motivo |
|---|---|---|
| ENG-001 | Dois workflows: `.github/workflows/ci-pr.yml` (`pull_request` → `main`) e `.github/workflows/release.yml` (`push` → `main`) | Separa gate (BR-001–002) de publish (BR-003); evita publish acidental em PR |
| ENG-002 | Secret dedicado `E2E_GITHUB_TOKEN` (PAT com escopos mínimos de leitura); nunca logar; `GITHUB_TOKEN` do Actions **não** substitui o token de integração e2e do produto; mapeamento alinhado a T21 / REQ-049 | REQ-009; BR-007; DEC-020 do MVP |
| ENG-003 | Release: calcula bump → atualiza `version` em `pyproject.toml` → commit bot na `main` + tag git `vX.Y.Z` → build/push GHCR com tags `latest` e `X.Y.Z` | Mantém `pyproject.toml` como SoT (BR-004); tag-only deixaria SoT desatualizado |
| ENG-004 | Bump: `fix:*` → patch; `feat:*` → minor; `BREAKING CHANGE` / `type!:` → major; sem prefixo aplicável no intervalo desde a última tag → **patch** | REQ-016; BDD-008 |
| ENG-005 | **Removido ownership de criação Robot.** T04 define apenas contrato de **consumo/invocação** da suíte T21 (entrypoint, paths, env); nenhum `*.robot` novo sob esta feature | REQ-008; BR-011; DEC-009; BDD-009 |
| ENG-006 | BDD-015 permanece fora do Robot (definido em T21); esta feature não tenta automatizá-lo | Premissa MVP |
| ENG-007 | Job e2e no PR **só** roda se os **testes unitários do projeto** e os testes BDD passaram (pré-condição obrigatória + short-circuit); unitários e BDD são required checks do gate (REQ-012) | Clarificação v0.1.1 preservada |
| ENG-008 | Runner `ubuntu-latest` + Podman; compose via `podman compose` ou compatível com YAML T19 | DEC-005; BR-006 |
| ENG-009 | Imagem GHCR: `ghcr.io/<owner>/<repo>`; `docker-compose.yml` (T19) referencia imagem pública — release garante tags | REQ-015; BDD-006 |
| ENG-010 | Timeout e2e alinhado ao contrato T21; retry limitado só em rate-limit GitHub | Mitiga flakiness sem mascarar regressão |
| ENG-011 | Nomes estáveis de checks: `unit`, `bdd`, `e2e` (ou equivalentes documentados em T05) | BDD-001 operacional |
| ENG-012 | Docs: README = usuário final; setup de dev/testes/e2e → `docs/contributing.md` apontando **suíte T21**; produto em `docs/` | REQ-018–021; BDD-007 |
| ENG-013 | Nenhuma alteração em `src/github_rag/**` de domínio; deps de CI apenas tooling; **proibido** segunda árvore Robot | BR-008; BR-011; DEC-008 |

### 1.4 Fronteiras

| Módulo / área | Responsabilidade | Não faz |
|---|---|---|
| `.github/workflows/ci-pr.yml` | Gate PR: unit, BDD, e2e (invoca T21) | Publish GHCR; bump versão; criar suíte Robot |
| `.github/workflows/release.yml` | Bump + tag + GHCR pós-merge | Rodar em PR; alterar domínio |
| Consumo T21 (T04) | Contrato de invocação / wiring local da suíte existente | Criar ou duplicar `e2e/robot/` |
| Consumo T19 | Subir stack / build imagem | Reescrever Dockerfile/composes |
| `docs/` + README/CHANGELOG EN | Onboarding usuário/contribuidor | Spec interna; ownership Robot/composes |

## 2. Contratos de esteira (interfaces lógicas)

| Contrato | Responsabilidade | Separação |
|---|---|---|
| `PrQualityGate` | Orquestrar **unitários do projeto** → BDD → e2e **somente se** unit e BDD verdes; falhar o check sem side-effects de release | Isola validação de publicação; e2e nunca roda sem unitários |
| `E2eStackLauncher` | Subir/derrubar stack via Podman + `docker-compose.e2e.yml` (T19); expor base URLs | Runtime ≠ suíte |
| `T21SuiteInvoker` | Invocar a suíte Robot canônica de T21 (`E2E_GITHUB_TOKEN`, repo = este) | Não cria keywords/suítes paralelas |
| `SemverBumper` | Ler commits desde última tag; aplicar ENG-004; escrever `pyproject.toml` | SoT de versão fora do Docker |
| `GhcrPublisher` | Build (Dockerfile T19) + push `latest` + versão | Publish ≠ gate de PR |
| `DocsSurface` | README usuário; `docs/` produto + contributing (e2e → T21) | Não é dona dos YAML T19 nem do Robot |

Variáveis/secrets mínimos:

| Nome | Onde | Uso |
|---|---|---|
| `E2E_GITHUB_TOKEN` | secret Actions | Token produto para e2e (contrato T21) |
| `GITHUB_TOKEN` / `packages: write` | permissões workflow release | Push GHCR + commit bump |
| Env da stack e2e | compose T19 + job | `CONFIG_PATH`, DB, etc. (sem commit de segredos) |

## 3. Ordem e dependências

### Pré-gate externo

```text
github-etl-mcp-rag/T19-container-delivery  (DONE: Dockerfile + 3 composes)
github-etl-mcp-rag/T21-mvp-e2e-robot       (DONE: suíte Robot verde na prova MVP)
        │
        ▼
   ondas W1+ desta feature (e2e / release / contributing e2e)
```

W0 (docs usuário/produto + CI unit/BDD) **pode** iniciar em paralelo ao fechamento de T19/T21; W1+ **bloqueia** em T19 **e** T21.

### DAG (task → depende de)

```text
T01-ci-pr-unit-bdd
T02-docs-readme-changelog-en
T03-docs-product-features-en
T04-consume-t21-e2e              → T19 (externa), T21 (externa)
T05-ci-pr-e2e-podman             → T01, T04, T19, T21
T06-release-semver-ghcr          → T19
T07-docs-contributing-en         → T01, T04, T21   (soft T05 para nomes de jobs)
```

## 4. Ondas paralelas

| Onda | Tasks paralelas | Gate |
|---|---|---|
| W0 | `T01`, `T02`, `T03` | CI unit/BDD + docs usuário/produto (sem e2e/release) |
| W1 | `T04`, `T06` | **após T19+T21** (T04); T06 após T19; consumo T21 + release |
| W2 | `T05`, `T07` | Gate e2e no PR (invoca T21) + docs contribuidores |

**Critical path:**  
`T19 + T21 (externas) → T04 → T05`  
(com `T01` alimentando T05; `T06` paralelo após T19; docs W0/W2 fora do path crítico de merge-gate).

## 5. Estratégia anti-retrabalho

1. **Contratos de workflow e secrets antes da invocação** — nomes de jobs/checks e `E2E_GITHUB_TOKEN` fixados; branch protection não renomeia depois.
2. **Não tocar ownership T19/T21** — só consumir paths/contratos; ajustes mínimos nos composes só se inevitáveis e justificados.
3. **Uma suíte Robot** — T21; T04/T05 apenas invocam (BDD-009).
4. **Release separado do PR** — zero chance de publish em PR por share de job.
5. **Docs em camadas** — README/produto em W0; contributing após contrato de invocação T21 (T04).
6. **BDD-015 fora** — não tentar automatizar na esteira.
7. **Bump com commit na SoT** — evita divergência pyproject ↔ GHCR ↔ tags.
8. **Short-circuit unit/BDD** — e2e exige unitários + BDD verdes.

## 6. Rastreabilidade requisito → task

| Task | REQs / BRs / DECs | BDDs desta feature |
|---|---|---|
| T01 | REQ-002,012(parcial),014; BR-001–002; ENG-001,007,011 | BDD-001 (parcial), BDD-002 |
| T02 | REQ-004,018–019,021; BR-010; ENG-012 | BDD-007 (README/CHANGELOG) |
| T03 | REQ-004,020; BR-010; ENG-012 | BDD-007 (`docs/` produto) |
| T04 | REQ-001,005–011; BR-006–007,009,011; DEC-007,009; ENG-005,010 | BDD-003 (parcial), BDD-004, BDD-009 |
| T05 | REQ-001–002,007,012–014,017; BR-001–002,006,009; ENG-001,007,008,011 | BDD-001, BDD-002, BDD-003, BDD-004 |
| T06 | REQ-003,015–017; BR-003–005; ENG-001,003,004,009 | BDD-005, BDD-006, BDD-008 |
| T07 | REQ-011,020–021; BR-006,010; ENG-008,012 | BDD-007 (contributing; e2e → T21) |

## 7. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| T19 ou T21 atrasadas | Gate explícito W1; bloquear T04–T05/T07 e2e até REQ-006 |
| Flakiness GitHub real / rate limit | ENG-010; falha explícita se secret ausente; sem mock; ownership de estabilidade em T21 |
| CI longo (stack + indexação) | Short-circuit; timeouts alinhados a T21 |
| Tentativa de recriar Robot | ENG-005/013; BDD-009; review rejeita segunda suíte |
| GHCR permissions / package visibility | `packages: write` + doc no handoff T06 |
| Commit bot do bump vs proteção de branch | Documentar exceção para bot / token com contents:write no release |

## 8. Migração / rollback

- Greenfield de CI/CD/docs: sem migração de dados.
- Plano 0.1.1 / T04 “criar suíte” fica **obsoleto**; implementação sob 0.2.0.
- Rollback de workflow: reverter YAML da task/PR.
- Rollback de release: falha de push não marca sucesso; revert do commit de bump se necessário.
- Se T21 regredir: job e2e falha (BR-001) — fix na suíte T21, não duplicar aqui.

## 9. Critérios de aceite do plano (gate de PR)

- A esteira de PR documenta e implementa a ordem REQ-012: unitários → BDD → e2e (suíte T21).
- Antes do e2e, a esteira **deve** executar os **testes unitários do projeto** (e BDD); ambos verdes são pré-condição do job e2e (ENG-007; T01 + T05).
- Required checks incluem `unit`, `bdd` e `e2e`; falha em unitários bloqueia merge e impede e2e.
- Não existe segunda suíte Robot sob ownership desta feature (BDD-009).

## 10. Handoff

Plano **v0.2.0** — `READY_FOR_IMPLEMENTATION` (`HUMAN_PLAN_APPROVAL` em `bbf46d6`).

- Tasks `T01`–`T07` neste delta: `READY_FOR_IMPLEMENTATION`.
- W0 pode iniciar sem T19/T21; W1+ continua bloqueado em T19+T21 DONE (dependências externas documentadas).
