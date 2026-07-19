# Design — T05-open-failure-tasks-parent

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T05-open-failure-tasks-parent` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Branch | `feature/mvp-e2e-audit-hardening-T05-open-failure-tasks-parent` |
| Base | `origin/feature/mvp-e2e-audit-hardening-T04-run-e2e-robot` + merge T03 |
| Rastreabilidade | REQ-005, REQ-016–017; BR-005–007; DEC-006–008; ENG-006–007, ENG-009–010; BDD-005, BDD-007 (parcial); contrato `ParentFailureBacklog` |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` (auto-draft) | `0.1.0` | Superfície documental: índice + tasks T22+; pytest zero; T04 tooling-e2e; sem fix; lacunas → T06. |
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` → corrigido | `0.1.0` | M-01: T23 health sem falha independente; M-02: `produto` uniforme em F-T04-001. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Só T22 `tooling-e2e`; classificação combinada REQ-017; índice declara health/catalog/ui/mcp/negative sem falha observável. |

## 1. Contexto

A feature filha `mvp-e2e-audit-hardening` audita o MVP sem corrigir domínio. T05 é a onda W3:

- **Dura:** T03 (`ParentPytestRun`) + T04 (`RobotGreenPathRun`) — evidências em `runs/`.
- Converter falhas run-first em tasks de **correção** no pai `github-etl-mcp-rag` (IDs após T21).
- Agrupar por superfície ENG-006; classificar ENG-007 / REQ-017.
- **Não** implementar fixes (ENG-010); **não** abrir tasks só de lacuna (T06).

### Evidência consumida (fonte da verdade)

| Run | Artefato | Resultado | Falhas acionáveis |
|---|---|---|---|
| T03 | `runs/pytest-all-tasks.md` | exit `0`; failed=`0` | **nenhuma** (lista vazia; D-T03-002) |
| T04 | `runs/e2e-robot-green-path.md` | exit `3`; robot **não** rodou | F-T04-001, F-T04-002, F-T04-003 — todas superfície candidata `tooling-e2e` |

## 2. Problema

1. Falhas T04 devem virar backlog acionável no pai (BDD-005 / BR-005).
2. Pytest verde **não** inventa falhas (D-T05-001).
3. Suítes Robot `unknown` (não executadas) **não** são falhas de produto nas superfícies catalog/ui/mcp/negative/health — lacunas vão para T06; skip de `/healthz` por stack tooling **não** abre task `health` separada.
4. IDs livres após T21 (ENG-009); uma task por superfície dominante afetada (não 1:1 BDD).

## 3. Solução proposta

### 3.1 Decisão de abordagem

| Opção | Avaliação |
|---|---|
| A — Índice + arquivo `T22+` Markdown no pai + BDD de contrato | Satisfaz BDD-005 / REQ-016–017; zero código de produto; alinhado ENG-010 |
| B — Implementar fixes zoekt/compose nesta feature | Viola ENG-010 / fora de escopo T05 |
| C — Tasks 1:1 por F-T04-* sem agrupamento | Viola BR-006 / ENG-006 |
| D — Abrir tasks para catalog/ui/mcp/negative/health “unknown”/skip | Inventa falha; viola D-T05-001; mistura com T06 / over-split |
| E — T22 tooling-e2e + T23 health com F-T04-003 duplicado | Over-split; F-T04-003 é consequência de F-T04-002 (`tooling-e2e` no run T04) |

**Escolha: opção A** — uma task pai na superfície dominante `tooling-e2e`.

### 3.2 Contrato lógico `ParentFailureBacklog`

| Responsabilidade | Motivo da separação |
|---|---|
| Ler T03+T04 e materializar tasks de falha no pai | Isola W3 de runs (T03/T04) e de gap-fill (T06) |
| Agrupar por superfície; classificar achados | REQ-016–017; ENG-006–007 |
| Registrar zero falhas pytest quando aplicável | Evita backlog fantasma |
| Não implementar correção | ENG-010 |

Forma: artefatos Markdown (sem Protocol/ABC em `src/`).

### 3.3 Mapeamento evidência → tasks no pai

| Task ID (pai) | Superfície | Falhas / evidência | Classificação (REQ-017) | Notas |
|---|---|---|---|---|
| `T22-fix-tooling-e2e-compose-zoekt` | `tooling-e2e` | F-T04-001, F-T04-002, F-T04-003 | combinação documentada: F-T04-001 → `flakiness` (pré-req host compose provider); F-T04-002 → `produto` (entrypoint/zoekt/`tini`); F-T04-003 → consequência de F-T04-002 (mesmo handoff; sem task extra) | Superfície candidata do run T04; stack/hang/`healthy`+`robot` skip |

**Não criar** task `T23` nem tasks de falha para `health`, `catalog_indexing`, `ui`, `mcp`, `negative` neste run-first:

- Robot não executou cenários; fase `healthy` ficou `skip` (não falha observável de `/healthz`).
- F-T04-003 é consequência de F-T04-002, já classificada `tooling-e2e` no run T04.
- REQ-016 “health/boot/compose” aplica-se quando a falha dominante for dessa superfície; aqui T04 fixou dominante = `tooling-e2e` (compose provider + entrypoint).

**Pytest:** registrar explicitamente “zero falhas runtime pytest” no índice — sem task de correção pytest.

### 3.4 Artefatos obrigatórios

1. `spec/features/mvp-e2e-audit-hardening/audit/failure-backlog-index.md` — índice local (SoT desta feature); listar superfícies afetadas e não afetadas.
2. `spec/features/github-etl-mcp-rag/tasks/T22-fix-tooling-e2e-compose-zoekt.md`
3. Testes BDD de contrato em `tests/bdd/test_mvp_e2e_audit_failure_backlog.py`

### 3.5 Conteúdo mínimo da task do pai

| Campo | Obrigatório |
|---|---|
| Task ID, Feature pai, Estado `READY_FOR_IMPLEMENTATION` (candidata) | sim |
| Superfície ENG-006 | sim |
| Classificação REQ-017 (incl. combinação por F-T04-* quando necessário) | sim |
| Objetivo (correção / handoff) | sim |
| Evidência (link/IDs F-T04-* / runs) | sim |
| Critérios de aceite | sim |
| Arquivos prováveis | sim |
| Dependências | sim |
| Handoff | sim |
| **Sem** implementação / patch de código nesta feature | sim (ENG-010) |

Aceite de T22 deve distinguir: (a) pré-req/documentação de compose provider (F-T04-001); (b) correção de compose/imagem zoekt entrypoint (F-T04-002) desbloqueando fases `healthy`/`robot`.

### 3.6 Decisões

| ID | Decisão | Motivo |
|---|---|---|
| D-T05-001 | Não inventar falhas pytest nem falhas Robot “unknown”/skip como superfície de produto | Evidência T03/T04 |
| D-T05-002 | Agrupar F-T04-001..003 em **uma** task T22 (`tooling-e2e`); sem T23 `health` | ENG-006; superfície candidata do run; F-T04-003 consequência |
| D-T05-003 | Classificação combinada REQ-017 em T22 | F-T04-001 ≠ defeito de produto; F-T04-002 = `produto` |
| D-T05-004 | ID T22 após T21 | ENG-009 |
| D-T05-005 | Sem mudança `src/github_rag/**`, `e2e/robot/**`, composes nesta feature | ENG-010 |
| D-T05-006 | Lacunas inventário → T06 apenas | BR-007 / plano W4 |

## 4. Fluxo

```text
runs/pytest-all-tasks.md ──┐
                           ├──► ParentFailureBacklog
runs/e2e-robot-green-path.md┘         │
                                      ▼
                    audit/failure-backlog-index.md
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            T22 tooling-e2e   (sem T23)      índice: health/catalog/
                                               ui/mcp/negative =
                                               sem falha observável
                                      │
                                      ▼
                              handoff T06 (gaps only)
```

## 5. Dados

- Entrada: Markdown T03/T04 (já versionados).
- Saída: índice + 1 task pai + asserts BDD.
- Sem secrets; sem logs brutos.

## 6. Erros e bordas

| Caso | Tratamento |
|---|---|
| Pytest 0 falhas | Índice declara zero; sem T2x pytest |
| Robot skip total por tooling | Uma task `tooling-e2e`; não abrir `health`/suítes unknown |
| Falha só de contrato filha | Fora do backlog (D-T03-002 / D-T04-002) |
| Lacuna BDD sem falha runtime | T06, não T05 |

## 7. Segurança

- Não copiar PAT/`.env`/Authorization dos runs.
- Tasks do pai referenciam IDs F-T04-* e paths de resumo, não dumps.

## 8. Compatibilidade

- Não altera runtime T19/T21.
- Tasks abertas no pai entram no pipeline **do pai** após gates humanos/plano do pai.
- PR empilhado: base T04; merge order T03→T04→T05 (ou T04→T03→T05 desde que ambos antes de T05).

## 9. Observabilidade

- Índice lista superfícies afetadas / não afetadas e contagens.
- BDD valida presença de T22, superfícies, classificação combinada, ausência de T23/fix-health fantasma e proibição de fix nesta feature.

## 10. Riscos e rollback

| Risco | Mitigação |
|---|---|
| T06 misturado com falhas | D-T05-006; índice separa |
| Over-split de tasks | D-T05-002 (1 task) |
| Merge sem T03/T04 | PR base T04; merge notes |

Rollback: remover T22 + índice + testes BDD desta task.

## 11. Fora de escopo

- Fixes em compose/zoekt/keywords.
- Gap-fill browser / asserts integrais (T06).
- Declarar MVP entregue (T07).
- Alterar suíte Robot nesta feature.
- Task pai `health` sem falha `/healthz` observável independente.
