# Interfaces — T03-run-pytest-all-tasks

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T03-run-pytest-all-tasks` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `PENDING_ARCHITECT_REVIEW` |
| Versão | `0.1.0` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/mvp-e2e-audit-hardening-T03-run-pytest-all-tasks` |
| Natureza | **100% documental / operacional** (D-T03-001) |
| Escopo desta etapa | Contrato lógico `ParentPytestRun` — resumo do run pytest; **sem** Protocol/ABC Python, **sem** código de produção |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `PENDING_ARCHITECT_REVIEW` | `0.1.0` | Draft: interface lógica única alinhada design §3 e BDD PYTEST-01..09. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Forma | Papel |
|---|---|---|
| `ParentPytestRun` | Artefato Markdown canônico + execução `pytest` | Executar suíte `tests/` e registrar resultado sanitizado |

Path canônico (design §3.3):

```text
spec/features/mvp-e2e-audit-hardening/runs/pytest-all-tasks.md
```

### Explicitamente fora de escopo — sem interfaces Python de runtime

| Item | Motivo |
|---|---|
| `typing.Protocol` / ABC / classes Python em `src/` | D-T03-001: resumo only; pytest já é o entrypoint |
| Alteração de compose / Robot / domínio | Fora do escopo T03 |
| Abrir tasks no pai | T05 |
| Robot / `python -m github_rag.e2e` | T04 |

**Não serão criados** arquivos `.py` de interface de produção nesta task.

## 2. Interface lógica: `ParentPytestRun`

```text
# ParentPytestRun — interface lógica (documental / operacional)
#
# Responsabilidade:
#   Executar o pytest canônico sobre tests/ (unitários + BDD de contrato de
#   todas as tasks do pai github-etl-mcp-rag) e registrar de forma observável
#   e versionável o resultado (exit code, contagens, falhas do pai com
#   superfície candidata, cobertura/coverage_gate, metadados de ambiente),
#   sem secrets e sem corrigir produto.
#
# Motivo da separação:
#   - Isola a evidência run-first pytest (W1) da prova Robot (T04) e da
#     abertura de backlog no pai (T05).
#   - Congela um resumo auditável (BDD-004 / ENG-002–003 / REQ-015) sem
#     introduzir runner em src/ onde D-T03-001 escolheu superfície zero
#     de produto.
#   - Impõe D-T03-002: falhas listadas para T05 excluem nodeids da feature
#     filha (mvp_e2e_audit_*); coverage_gate não vira falha de produto.
#
# Forma:
#   1) Comando: python -m pytest tests/ -q --tb=line
#   2) Artefato Markdown único no path canônico acima.
#   Sem métodos Python de domínio, sem Protocol/ABC.
```

### Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T03-001 | Única interface lógica: `ParentPytestRun` | Contrato da task | design §3.2 |
| I-T03-002 | Materialização = Markdown em `runs/pytest-all-tasks.md` | SoT versionável | PYTEST-01 |
| I-T03-003 | Sem Protocol/ABC/classes em `src/` | D-T03-001 | design §3.1 |
| I-T03-004 | Comando canônico único §3.4 | ENG-003 | PYTEST-02 |
| I-T03-005 | Lista T05 só falhas do pai | D-T03-002 | PYTEST-05/08 |
| I-T03-006 | `coverage_gate` sempre presente (true/false) | Distinguir fail_under | PYTEST-04 |
| I-T03-007 | Superfícies ENG-006 | Handoff T05 | PYTEST-05 |
| I-T03-008 | Soft-dep T01 documentada | Não bloquear | PYTEST-06 |
| I-T03-009 | Sem secrets no artefato | BR-004 | PYTEST-07 |
| I-T03-010 | Consumidor canônico das falhas = T05 | Handoff | design §5 |

## 3. Estrutura obrigatória do resumo

### 3.1 Metadados (PYTEST-02)

| Campo | Obrigatório |
|---|---|
| Data/hora ISO | sim |
| Branch e/ou commit SHA | sim |
| Comando canônico exato `python -m pytest tests/ -q --tb=line` | sim |
| Python version | sim |
| OS resumido | sim |

### 3.2 Resultado agregado (PYTEST-03)

| Campo | Domínio |
|---|---|
| exit code | inteiro |
| passed | inteiro (quando disponível) |
| failed | inteiro |
| skipped | inteiro |
| errors | inteiro |
| total | inteiro (quando disponível) |

### 3.3 Cobertura (PYTEST-04)

| Campo | Domínio |
|---|---|
| coverage % ou `N/A` + motivo | texto |
| `coverage_gate` | `true` \| `false` (sempre presente) |

### 3.4 Lista de falhas do pai (PYTEST-05 / PYTEST-08)

Por falha (se houver):

| Campo | Domínio |
|---|---|
| nodeid | string pytest |
| tipo | `failed` \| `error` |
| mensagem sanitizada | texto sem secrets |
| superfície candidata | `health` \| `catalog_indexing` \| `ui` \| `mcp` \| `negative` \| `tooling-e2e` |

Regras:

- Se zero falhas do pai: seção presente com indicação explícita de lista vazia.
- Nodeids contendo `mvp_e2e_audit_` **proibidos** nesta lista (D-T03-002).

### 3.5 Soft-dep T01 (PYTEST-06)

| Campo | Domínio |
|---|---|
| Nota T01 | inventário disponível ou run sem depender do artefato T01 |

### 3.6 Declaração de escopo (PYTEST-09)

| Campo | Obrigatório |
|---|---|
| Sem alteração de produto / `e2e/robot/**` nesta task | sim (declaração no artefato) |

## 4. Proibições de secrets

| Regra | Severidade |
|---|---|
| Sem prefixos `ghp_` / `gho_` / `ghu_` / `ghs_` / `ghr_` | obrigatório (PYTEST-07) |
| Sem atribuição com valor longo a `GITHUB_TOKEN` / `E2E_GITHUB_TOKEN` | obrigatório |
| Sem dumps de `os.environ` / Authorization | obrigatório |

## 5. Contrato de consumo por T05

| Aspecto | Contrato |
|---|---|
| Input | Lista de falhas do pai + superfícies + exit code / coverage_gate |
| Não faz | Abrir tasks; classificar `produto`/`flakiness`/… (T05) |
| Ownership | T03 só evidencia |

```text
ParentPytestRun (runs/pytest-all-tasks.md)
        │  falhas do pai + superfícies
        ▼
T05  open-failure-tasks-parent
```

## 6. DoD do contrato (esta etapa)

- [x] Interface lógica `ParentPytestRun` com responsabilidade e motivo da separação.
- [x] Estrutura do resumo (§3) congelada.
- [x] Proibições de secrets (§4) explícitas.
- [x] Explicitado: **nenhuma** interface Python de runtime (D-T03-001).
- [ ] Materialização do Markdown (`runs/pytest-all-tasks.md` — implementação).
