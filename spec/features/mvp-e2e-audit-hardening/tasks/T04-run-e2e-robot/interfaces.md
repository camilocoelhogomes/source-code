# Interfaces — T04-run-e2e-robot

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T04-run-e2e-robot` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/mvp-e2e-audit-hardening-T04-run-e2e-robot` |
| Natureza | **100% documental / operacional** (D-T04-001) |
| Escopo desta etapa | Contrato lógico `RobotGreenPathRun` — execução + resumo; **sem** Protocol/ABC Python novo, **sem** código de produção |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Interface lógica única alinhada design §3 e BDD E2E-01..10; consome T21 runtime sem reimplementar. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Forma | Papel |
|---|---|---|
| `RobotGreenPathRun` | Execução `python -m github_rag.e2e` + artefato Markdown | Exercitar green path T21 e registrar resultado sanitizado |

Path canônico (design §3.3):

```text
spec/features/mvp-e2e-audit-hardening/runs/e2e-robot-green-path.md
```

### Explicitamente fora de escopo — sem interfaces Python novas de runtime

| Item | Motivo |
|---|---|
| `typing.Protocol` / ABC / classes novas em `src/` | D-T04-001; entrypoint T21 já existe |
| Alteração de `E2eStackLauncher` / `RobotMvpSuite` / compose / `.robot` | Fora do escopo T04; ownership pai T19/T21 |
| Abrir tasks no pai | T05 |
| Expandir cobertura integral / browser | T06 / BR-007 |
| Pytest all-tasks | T03 |

**Não serão criados** arquivos `.py` de interface de produção nesta task.

## 2. Interface lógica: `RobotGreenPathRun`

```text
# RobotGreenPathRun — interface lógica (documental / operacional)
#
# Responsabilidade:
#   Executar o green path e2e canônico (python -m github_rag.e2e com Podman +
#   docker-compose.e2e.yml + credencial HITL para camilocoelhogomes/source-code)
#   e registrar de forma observável e versionável o resultado (exit code,
#   fases, suítes/cenários, timeouts/rate-limit, presença de e2e/results/,
#   falhas com superfície candidata), sem secrets e sem expandir/corrigir
#   a suíte ou o produto.
#
# Motivo da separação:
#   - Isola a evidência run-first Robot (W2) da prep HITL (T02), do pytest
#     (T03) e da abertura de backlog no pai (T05).
#   - Congela um resumo auditável (BDD-003 / ENG-002/004 / REQ-015) sem
#     duplicar o runtime T21 em src/ (D-T04-001).
#   - Impõe BR-007: green path atual apenas; falhas alimentam T05, não
#     justificam keywords novas nesta feature filha.
#
# Forma:
#   1) Comando: python -m github_rag.e2e
#   2) Artefato Markdown único no path canônico acima.
#   Sem Protocol/ABC novos; consome DefaultRobotMvpSuite / PodmanE2eStackLauncher
#   já entregues em T21.
```

### Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T04-001 | Única interface lógica: `RobotGreenPathRun` | Contrato da task | design §3.2 |
| I-T04-002 | Materialização = Markdown em `runs/e2e-robot-green-path.md` | SoT versionável | E2E-01 |
| I-T04-003 | Sem Protocol/ABC/classes novas em `src/` | D-T04-001 | design §3.1 |
| I-T04-004 | Comando canônico `python -m github_rag.e2e` | ENG-004 | E2E-02 |
| I-T04-005 | Consome runtime T21 sem alterar | Ownership pai | design §8 |
| I-T04-006 | Token só `present=true/false` | BR-004 | E2E-03/09 |
| I-T04-007 | Suítes T21 + exclude bdd015 | Green path atual | E2E-06 |
| I-T04-008 | Falhas → superfícies ENG-006 | Handoff T05 | E2E-07 |
| I-T04-009 | Soft-dep T03 independente | REQ-014 soft | E2E-08 |
| I-T04-010 | Sem expansão Robot/browser | BR-007 | E2E-10 |
| I-T04-011 | Consumidor canônico das falhas = T05 | Handoff | design §5 |

## 3. Estrutura obrigatória do resumo

### 3.1 Metadados (E2E-02)

| Campo | Obrigatório |
|---|---|
| Data/hora ISO | sim |
| Branch | sim |
| Commit SHA | sim |
| Comando canônico exato `python -m github_rag.e2e` | sim |
| Python version | sim |
| OS resumido | sim |
| Podman version | sim |

### 3.2 Pré-condições (E2E-03)

| Campo | Domínio |
|---|---|
| Gate T02 | `READY` (esperado) / `BLOCKED` |
| Token | `present=true` \| `present=false` |
| Podman | ok/fail |
| Repo ref | `camilocoelhogomes/source-code` |

### 3.3 Resultado e fases (E2E-04/05)

| Campo | Domínio |
|---|---|
| exit code | inteiro (0 / 2 / 3 / outros ≠0) |
| Fases | credential, compose, healthy, robot, down — status ok/fail/skip |

### 3.4 Suítes (E2E-06)

| Suíte | Resultado |
|---|---|
| health / catalog_indexing / ui / mcp / negative | pass \| fail \| unknown |
| exclude | `bdd015` |

### 3.5 Falhas T05 (E2E-07)

| Campo por entrada | Obrigatório se houver falha |
|---|---|
| Identificação (suíte/cenário/fase) | sim |
| Tipo/motivo sanitizado | sim |
| Superfície candidata ENG-006 | sim |

Lista vazia válida se exit 0 sem falhas.

### 3.6 Soft-dep T03 + escopo (E2E-08/10)

| Campo | Obrigatório |
|---|---|
| Estado T03 + “evidência independente / sem rebase” | sim |
| Declaração sem expansão Robot/browser e sem mudança `src/`/`e2e/robot/**` | sim |

### 3.7 Artefatos locais

| Campo | Domínio |
|---|---|
| `e2e/results/` presente | boolean |
| Conteúdo de logs/XML/HTML | **não versionar** |

## 4. Proibições de secrets

| Regra | Severidade |
|---|---|
| Sem prefixos `ghp_` / `gho_` / `ghu_` / `ghs_` / `ghr_` | obrigatório (E2E-09) |
| Sem assign longo de `GITHUB_TOKEN` / `E2E_GITHUB_TOKEN` | obrigatório |
| `.env` e `e2e/results/` fora do git | obrigatório |
| Redaction de stdout/stderr capturado antes do resumo | obrigatório |

## 5. Consumo de contratos T21 (não são interfaces desta task)

| Contrato T21 | Uso em T04 |
|---|---|
| `E2eCredentialResolver` | Runtime de credencial |
| `E2eStackLauncher` / `PodmanE2eStackLauncher` | Compose up/healthy/down |
| `RobotMvpSuite` / `DefaultRobotMvpSuite` | Orquestração green path |
| `e2e/robot/*.robot` | Suítes consumidas sem alteração |

## 6. Contrato de consumo por T05

| Aspecto | Contrato |
|---|---|
| Input | Lista de falhas + superfícies no resumo |
| Exit ≠ 0 | Achado válido (produto / flakiness / tooling) |
| Exit 0 | Lista vazia; lacunas ainda vêm de T01→T06 |
| Ownership | T04 só evidencia; T05 abre tasks no pai |

## 7. DoD do contrato

- [x] Interface lógica `RobotGreenPathRun` com responsabilidade e motivo da separação.
- [x] Estrutura do resumo (§3) congelada.
- [x] Proibições de secrets (§4) explícitas.
- [x] Explicitado: **nenhuma** interface Python nova de runtime (D-T04-001).
- [x] `APPROVED_BY_ARCHITECT`.
