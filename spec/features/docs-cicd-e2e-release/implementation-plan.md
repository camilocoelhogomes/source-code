# Plano de implementação — docs-cicd-e2e-release

| Campo | Valor |
|---|---|
| Feature ID | `docs-cicd-e2e-release` |
| Versão do plano | `0.1.1` |
| Estado | `PENDING_HUMAN_PLAN_APPROVAL` |
| Requisitos base | `requirements.md` v0.1.0 (aprovado 2026-07-18, commit candidato `ae1941ebd43ca97ef6d77a55004847f4af4d72db`; registro `15555f02`) |
| Natureza | qualidade, documentação e entrega contínua; não altera domínio do MVP |
| Dependência externa | `github-etl-mcp-rag` / `T19-container-delivery` (Dockerfile + 3 composes com testes passando) |
| Revisão PO | `aprovado` em 2026-07-18 por `product-owner` (`PO_PLAN_REVIEW` v0.1.1) |
| Revisão humana (plano) | `NOT_STARTED` — aguarda `HUMAN_PLAN_APPROVAL` |
| Delta v0.1.1 | Clarificação documental: unitários (e BDD) são **pré-condição obrigatória** do e2e no gate de PR (REQ-012); sem mudança de escopo |

## 1. Arquitetura

### 1.1 Visão

Camada de **qualidade e entrega** sobre o MVP já empacotado por T19:

1. **Gate de PR** — GitHub Actions em `ubuntu-latest`, ordem **obrigatória** (REQ-012): **testes unitários do projeto** → BDD → só então stack e2e (Podman + `docker-compose.e2e.yml`) → Robot Framework. Unitários e BDD são **pré-condição** do e2e (não opcionais); required checks bloqueiam merge; **sem** publish nem bump.
2. **Suíte e2e Robot** — exercita fluxos observáveis do MVP (`github-etl-mcp-rag` BDD-001–024 automatizáveis) contra stack real e GitHub real (este repositório); **nunca** substitui unitários/BDD no gate.
3. **Release pós-merge** — Conventional Commits → bump em `pyproject.toml` → build/push GHCR (`latest` + versão).
4. **Docs em inglês** — README (usuário final), CHANGELOG, `docs/` (produto + contribuidores).

```text
PR → main                         main (após merge)
┌────────────────────────────┐    ┌────────────────────────────┐
│ ci-pr                      │    │ release                    │
│  1. unitários (obrigatório)│    │  1. bump semver (pyproject)│
│  2. BDD (obrigatório)      │    │  2. build imagem (T19)     │
│  ── gate: 1 e 2 verdes ──  │    │  3. push GHCR latest+ver   │
│  3. podman up e2e compose  │    │                            │
│  4. robot e2e              │    │                            │
│  (não publica / não bump)  │    │                            │
└────────────────────────────┘    └────────────────────────────┘
         │                                    │
         ▼                                    ▼
   docker-compose.e2e.yml              docker-compose.yml
   (consumo T19)                       → ghcr.io/<owner>/<repo>
```

**Pré-condição explícita do e2e:** o job/fase e2e **só** inicia depois que os **testes unitários do projeto** e os testes BDD estiverem verdes no mesmo workflow de PR. Falha em unitários ou BDD falha o required check correspondente e **impede** a execução do e2e (short-circuit) e o merge.

### 1.2 Ownership (DEC-007)

| Artefato | Dono | Esta feature |
|---|---|---|
| Dockerfile, `docker-compose.yml`, `docker-compose.e2e.yml`, `docker-compose.dev.yml` | T19 | **consome** |
| Workflows Actions, Robot e2e, README/CHANGELOG/`docs/`, release semver+GHCR | esta feature | **dona** |
| Código de domínio / `spec/` (exceto artefatos desta feature) | MVP / outras features | **não altera** |

**Risco de pré-condição:** o arquivo de task T19 em `github-etl-mcp-rag` lista explicitamente só `docker-compose.yml`. Para esta feature, T19 **deve** entregar os **três** composes nomeados em REQ-006 antes das ondas W1+. Sem isso, T04–T06 ficam bloqueadas.

### 1.3 Decisões de engenharia

| ID | Decisão | Motivo |
|---|---|---|
| ENG-001 | Dois workflows: `.github/workflows/ci-pr.yml` (`pull_request` → `main`) e `.github/workflows/release.yml` (`push` → `main`) | Separa gate (BR-001–002) de publish (BR-003); evita publish acidental em PR |
| ENG-002 | Secret dedicado `E2E_GITHUB_TOKEN` (PAT com escopos mínimos de leitura para discovery/API deste repo); nunca logar; `GITHUB_TOKEN` do Actions **não** substitui o token de integração e2e do produto | REQ-009; BR-007; evita ambiguidade com token de workflow |
| ENG-003 | Release: calcula bump → atualiza `version` em `pyproject.toml` → commit bot na `main` + tag git `vX.Y.Z` → build/push GHCR com tags `latest` e `X.Y.Z` | Mantém `pyproject.toml` como SoT (BR-004); tag-only deixaria SoT desatualizado |
| ENG-004 | Bump: `fix:*` → patch; `feat:*` → minor; `BREAKING CHANGE` / `type!:` → major; sem prefixo aplicável no intervalo desde a última tag → **patch** | REQ-016; BDD-008 |
| ENG-005 | Suíte Robot em `e2e/robot/`, suítes por superfície (`health`, `catalog_indexing`, `ui`, `mcp`), resources compartilhados (URLs, auth via env) | Evita monolito; alinha a BDD-001–024 observáveis |
| ENG-006 | BDD-015 (narrativa Discovery no Cursor) **fora** do Robot; Robot cobre capacidade das tools MCP / fluxos observáveis | Premissa dos requisitos; reduz flakiness |
| ENG-007 | Job e2e no PR **só** roda se os **testes unitários do projeto** e os testes BDD passaram (pré-condição obrigatória + short-circuit); unitários e BDD são required checks do gate (REQ-012); falha em qualquer job required bloqueia merge | Feedback humano (clarificação v0.1.1): deixar inequívoco na pipeline que unitários precedem e2e; economiza minutos de runner |
| ENG-008 | Runner `ubuntu-latest` + Podman (pacote do runner / instalação no job); compose via `podman compose` ou `podman-compose` compatível com os YAML T19 | DEC-005; BR-006 |
| ENG-009 | Imagem GHCR: `ghcr.io/<owner>/<repo>` (owner/repo do GitHub deste projeto); `docker-compose.yml` (T19) já deve referenciar essa imagem pública — release só garante tags publicadas | REQ-015; BDD-006 |
| ENG-010 | Timeout e2e configurável (default sugerido 45–60 min job); retry limitado (ex.: 1 retry) só em erros classificados como rate-limit GitHub | Mitiga flakiness sem mascarar regressão |
| ENG-011 | Nomes estáveis de checks para branch protection: `unit`, `bdd`, `e2e` (ou nomes de job equivalentes documentados em T05) | BDD-001 operacional |
| ENG-012 | Docs: README = usuário final; setup de dev/testes/e2e → `docs/contributing.md` (e índice em `docs/`); produto em `docs/` | REQ-018–021; BDD-007 |
| ENG-013 | Nenhuma alteração em `src/github_rag/**` de domínio; deps de Robot/CI apenas em tooling (`pyproject` optional-deps / requirements e2e / Actions) | BR-008; DEC-008 |

### 1.4 Fronteiras

| Módulo / área | Responsabilidade | Não faz |
|---|---|---|
| `.github/workflows/ci-pr.yml` | Gate PR: unit, BDD, e2e | Publish GHCR; bump versão |
| `.github/workflows/release.yml` | Bump + tag + GHCR pós-merge | Rodar em PR; alterar domínio |
| `e2e/robot/` | Automação e2e observável do MVP | Mock de API GitHub; validação narrativa BDD-015 |
| `docs/` + README/CHANGELOG EN | Onboarding usuário/contribuidor | Spec interna; ownership dos composes |
| Consumo T19 | Subir stack / build imagem | Reescrever Dockerfile/composes |

## 2. Contratos de esteira (interfaces lógicas)

Detalhamento de steps fica no pipeline por task. Contratos estáveis:

| Contrato | Responsabilidade | Separação |
|---|---|---|
| `PrQualityGate` | Orquestrar **unitários do projeto** → BDD → e2e **somente se** unit e BDD verdes; falhar o check sem side-effects de release | Isola validação de publicação; e2e nunca roda sem unitários |
| `E2eStackLauncher` | Subir/derrubar stack via Podman + `docker-compose.e2e.yml`; expor base URLs | Runtime ≠ suíte Robot |
| `RobotE2eSuite` | Validar fluxos MVP observáveis com GitHub real (`E2E_GITHUB_TOKEN`, repo = este) | Não conhece bump/GHCR |
| `SemverBumper` | Ler commits desde última tag; aplicar ENG-004; escrever `pyproject.toml` | SoT de versão fora do Docker |
| `GhcrPublisher` | Build (Dockerfile T19) + push `latest` + versão; falha observável sem “sucesso parcial” enganoso | Publish ≠ gate de PR |
| `DocsSurface` | README usuário; `docs/` produto + contributing | Não é dona dos YAML T19 |

Variáveis/secrets mínimos:

| Nome | Onde | Uso |
|---|---|---|
| `E2E_GITHUB_TOKEN` | secret Actions | Token produto para e2e |
| `GITHUB_TOKEN` / `packages: write` | permissões workflow release | Push GHCR + commit bump |
| Env da stack e2e | compose T19 + job | `CONFIG_PATH`, DB, etc. (sem commit de segredos) |

## 3. Ordem e dependências

### Pré-gate externo

```text
github-etl-mcp-rag/T19-container-delivery  (DONE com 3 composes + imagem + testes)
        │
        ▼
   ondas W1+ desta feature
```

W0 (docs + CI unit/BDD) **pode** iniciar em paralelo ao fechamento de T19; W1+ **bloqueia** em T19.

### DAG (task → depende de)

```text
T01-ci-pr-unit-bdd
T02-docs-readme-changelog-en
T03-docs-product-features-en
T04-robot-e2e-suite              → T19 (externa)
T05-ci-pr-e2e-podman             → T01, T04, T19
T06-release-semver-ghcr          → T19
T07-docs-contributing-en         → T01, T04   (alinha comandos CI/e2e; soft T05 para nomes de jobs)
```

## 4. Ondas paralelas

| Onda | Tasks paralelas | Gate |
|---|---|---|
| W0 | `T01`, `T02`, `T03` | CI unit/BDD + docs usuário/produto (sem e2e/release) |
| W1 | `T04`, `T06` | **após T19**; Robot + release (paralelos) |
| W2 | `T05`, `T07` | Gate e2e no PR + docs contribuidores |

**Critical path:**  
`T19 (externa) → T04 → T05`  
(com `T01` alimentando T05; `T06` paralelo após T19; docs W0/W2 fora do path crítico de merge-gate).

## 5. Estratégia anti-retrabalho

1. **Contratos de workflow e secrets antes da suíte** — nomes de jobs/checks e `E2E_GITHUB_TOKEN` fixados em T01/ENG; Robot e branch protection não renomeiam depois.
2. **Não tocar ownership T19** — só consumir paths/contratos; ajustes mínimos nos composes só se inevitáveis e justificados na task.
3. **Robot por superfície** — evita reescrever monolito quando um fluxo MVP mudar.
4. **Release separado do PR** — zero chance de publish em PR por share de job.
5. **Docs em camadas** — README/produto em W0; contributing após comandos e2e reais (T04).
6. **BDD-015 fora do Robot** — evita automação impossível/frágil.
7. **Bump com commit na SoT** — evita divergência pyproject ↔ GHCR ↔ tags.
8. **Short-circuit unit/BDD** — e2e **exige** unitários + BDD verdes; não sobe stack cara se qualidade básica já falhou (pré-condição obrigatória do gate, não otimização opcional).

## 6. Rastreabilidade requisito → task

| Task | REQs / BRs / DECs | BDDs desta feature |
|---|---|---|
| T01 | REQ-002,012(parcial),014; BR-001–002; ENG-001,007,011 | BDD-001 (parcial), BDD-002 |
| T02 | REQ-004,018–019,021; BR-010; ENG-012 | BDD-007 (README/CHANGELOG) |
| T03 | REQ-004,020; BR-010; ENG-012 | BDD-007 (`docs/` produto) |
| T04 | REQ-001,008–011; BR-006–007,009; ENG-005,006,010 | BDD-003, BDD-004 |
| T05 | REQ-002,007,012–014,017; BR-001–002,006; ENG-001,007,008,011 | BDD-001, BDD-002, BDD-003 |
| T06 | REQ-003,015–017; BR-003–005; ENG-001,003,004,009 | BDD-005, BDD-006, BDD-008 |
| T07 | REQ-011,020–021; BR-006,010; ENG-008,012 | BDD-007 (contributing) |

## 7. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| T19 sem os 3 composes | Gate explícito W1; bloquear T04–T06 até REQ-006 satisfeito |
| Flakiness GitHub real / rate limit | ENG-010; falha explícita se secret ausente; sem mock |
| CI longo (stack + indexação) | Short-circuit; timeouts; escopo Robot só observável |
| GHCR permissions / package visibility | `packages: write` + doc de visibilidade pública no handoff T06 |
| Conflito “não mexer código principal” | ENG-013; só tooling/CI/docs/e2e |
| BDD-015 | ENG-006 — fora do Robot |
| Commit bot do bump vs proteção de branch | Documentar exceção para bot / token com contents:write no release |

## 8. Migração / rollback

- Greenfield de CI/CD/docs: sem migração de dados.
- Rollback de workflow: reverter YAML da task/PR.
- Rollback de release: não retagear `latest` manualmente sem processo; falha de push não marca sucesso; revert do commit de bump se necessário.
- Robot: desabilitar job e2e só como emergência (quebra BR-001) — preferir fix da suíte.

## 9. Critérios de aceite do plano (gate de PR)

- A esteira de PR documenta e implementa a ordem REQ-012: unitários → BDD → e2e.
- Antes do e2e, a esteira **deve** executar os **testes unitários do projeto** (e BDD); ambos verdes são pré-condição do job e2e (ENG-007; T01 + T05).
- Required checks incluem `unit`, `bdd` e `e2e`; falha em unitários bloqueia merge e impede e2e.

## 10. Handoff

Plano **v0.1.1** — `PENDING_HUMAN_PLAN_APPROVAL` (PO_PLAN_REVIEW v0.1.1 aprovado).

- Tasks `T01`–`T07` em `tasks/`; T01/T05 atualizadas para pré-condição unit→e2e.
- Próximo gate: **HUMAN_PLAN_APPROVAL**.
- Implementação: uma task por pipeline; W0 pode iniciar sem T19; W1+ exige T19 DONE com 3 composes.
