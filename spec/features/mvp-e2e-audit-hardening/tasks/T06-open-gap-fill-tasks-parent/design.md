# Design — T06-open-gap-fill-tasks-parent

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T06-open-gap-fill-tasks-parent` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/mvp-e2e-audit-hardening-T06-open-gap-fill-tasks-parent` |
| Base | `origin/feature/mvp-e2e-audit-hardening-T05-open-failure-tasks-parent` |
| Rastreabilidade | REQ-005–007, REQ-018–019; BR-007–008; DEC-003, DEC-008; ENG-008–010; BDD-006, BDD-007, BDD-008; contrato `ParentGapFillBacklog` |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Gap-fill após T05; SoT T01; IDs T23–T27; UI obriga browser; sem duplicar T22; sem keywords nesta feature. |

## 1. Contexto

A feature filha `mvp-e2e-audit-hardening` audita o MVP sem corrigir domínio. T06 é a onda W4:

- **Dura:** T01 (`CoverageInventory`) + T05 (`ParentFailureBacklog` / T22).
- Converter linhas `status=lacuna` do inventário em tasks de **lacuna** (`gap-teste` / `assert-fraco`) no pai `github-etl-mcp-rag`.
- Agrupar por superfície (ENG-006 + superfície `sdk` do inventário T01 para BDD-024).
- Gap-fill UI **obriga** browser (ENG-008 / BDD-006 desta feature); API HTTP sozinha não fecha.
- Ordem: falhas (T05/T22) **antes** de lacunas (BDD-007 / REQ-019 / BR-007).
- **Não** implementar keywords/browser/produto (ENG-010); ownership Robot permanece no pai/T21 (BR-002).

### Evidência consumida (fonte da verdade)

| Fonte | Artefato | Uso |
|---|---|---|
| T01 | `audit/coverage-inventory.md` | Toda linha `status=lacuna` (exc. BDD-015) |
| T05 | `audit/failure-backlog-index.md` + `T22-fix-tooling-e2e-compose-zoekt.md` | Evitar duplicar falha tooling como “só gap”; referência cruzada |

## 2. Problema

1. Lacunas integrais existem mesmo com green path parcial T21 (BDD-008).
2. UI está coberta só via RequestsLibrary — critério integral exige browser (BDD-006 / REQ-007).
3. Denylist parcial T21 (003, 006, 013, 024) e demais lacunas devem virar backlog acionável no pai.
4. IDs livres após T22 (ENG-009); agrupamento por superfície, não 1:1 BDD.
5. Não misturar com T22 (falha runtime tooling).

## 3. Solução proposta

### 3.1 Decisão de abordagem

| Opção | Avaliação |
|---|---|
| A — Índice + tasks `T23+` Markdown no pai + BDD de contrato | Satisfaz BDD-006/008 / REQ-018–019; zero código de produto |
| B — Implementar browser/keywords nesta feature | Viola ENG-010 / BR-002 / fora de escopo T06 |
| C — Tasks 1:1 por BDD lacuna | Viola BR-006 / ENG-006 |
| D — Ignorar lacunas porque Robot não rodou (T04) | Viola BDD-008 / inventário SoT |
| E — Reabrir T22 como gap | Duplica falha; viola handoff T05 |

**Escolha: opção A** — cinco tasks pai por superfície afetada por lacuna.

### 3.2 Contrato lógico `ParentGapFillBacklog`

| Responsabilidade | Motivo da separação |
|---|---|
| Ler inventário T01 + índice T05 e materializar tasks de lacuna no pai | Isola W4 de falhas (T05) e de consolidação (T07) |
| Agrupar por superfície; classificar `gap-teste` / `assert-fraco` | REQ-017–019; ENG-006–008 |
| Exigir browser em task(s) `ui` | ENG-008; BDD-006 |
| Não implementar keywords/browser | ENG-010; BR-002 |

Forma: artefatos Markdown (sem Protocol/ABC em `src/`).

### 3.3 Mapeamento lacunas → tasks no pai

Lacunas do inventário (17 BDDs; BDD-015 excluído):

| Task ID (pai) | Superfície | BDD lacunas | Classificação (REQ-017) | Notas |
|---|---|---|---|---|
| `T23-gap-ui-browser` | `ui` | 001, 002, 007, 009, 010, 016, 019, 023 | `gap-teste` (primária); `assert-fraco` onde T21 só API-smoke | **Obrigatório browser** (Browser Library / Playwright / equiv.); API HTTP sozinha **não** encerra |
| `T24-gap-catalog-indexing-integral` | `catalog_indexing` | 003, 005, 006, 017 | `assert-fraco` (003, 006 denylist); `gap-teste` (005, 017) | Fortalecer asserts integrais na suíte T21 (scheduler 24h, commit, exclusões, só main) |
| `T25-gap-negative-integral` | `negative` | 008, 018, 022 | `gap-teste` / `assert-fraco` | Falha parcial+histórico UI; volume ausente; CONFIG_PATH |
| `T26-gap-mcp-parallel-slo` | `mcp` | 013 | `assert-fraco` | Paralelismo + fila/SLO até limite (denylist T21) |
| `T27-gap-sdk-dec015-conformity` | `sdk` | 024 | `assert-fraco` / `gap-teste` | Smoke ≠ conformidade integral DEC-015/BR-024 |

**Não criar** task gap para:

- BDD cobertos integrais: 004, 011, 012, 014, 020, 021
- BDD-015 (fora do inventário)
- Superfície `tooling-e2e` / duplicata de T22 (falha já aberta em T05)
- Superfície `health` sem linha lacuna no inventário

### 3.4 Artefatos obrigatórios

1. `spec/features/mvp-e2e-audit-hardening/audit/gap-fill-backlog-index.md` — índice local (SoT desta feature)
2. Tasks pai T23–T27 sob `spec/features/github-etl-mcp-rag/tasks/`
3. Testes BDD de contrato em `tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py`

### 3.5 Conteúdo mínimo de cada task do pai

| Campo | Obrigatório |
|---|---|
| Task ID, Feature pai, Estado `READY_FOR_IMPLEMENTATION` (candidata) | sim |
| Superfície | sim |
| Classificação REQ-017 (`gap-teste` / `assert-fraco` / combinação) | sim |
| BDD lacunas cobertos (lista) | sim |
| Objetivo (fortalecer suíte T21 / browser UI) | sim |
| Evidência (link inventário T01 + motivo) | sim |
| Critérios de aceite | sim |
| Para `ui`: menção explícita a automação **browser** | sim (T23) |
| Arquivos prováveis (`e2e/robot/**`, etc.) | sim |
| Dependências (T21; T22 tooling antes de re-run; auditoria filha) | sim |
| Handoff: implementação no pipeline do pai; filha não implementa keywords | sim |

### 3.6 Decisões

| ID | Decisão | Motivo |
|---|---|---|
| D-T06-001 | Toda lacuna T01 vira backlog mesmo sem falha runtime | BDD-008 |
| D-T06-002 | Agrupar por superfície → 5 tasks T23–T27 | ENG-006; BR-006 |
| D-T06-003 | T23 UI exige browser; API sozinha insuficiente | ENG-008; BDD-006 |
| D-T06-004 | IDs após T22 (T23+) | ENG-009; handoff T05 |
| D-T06-005 | Não duplicar T22; referenciar no índice | BR-007; T05 |
| D-T06-006 | Sem mudança `src/github_rag/**`, `e2e/robot/**`, composes nesta feature | ENG-010 |
| D-T06-007 | Superfície `sdk` (BDD-024) preservada do inventário T01 | SoT T01; não forçar merge em mcp/catalog |
| D-T06-008 | BDD-015 nunca gera task | REQ-010 / DEC-019 |
| D-T06-009 | Fase gap-fill só após falhas (T05 já na base) | REQ-019; BDD-007 |

## 4. Fluxo

```text
audit/coverage-inventory.md ──┐
                              ├──► ParentGapFillBacklog
audit/failure-backlog-index.md┘         │
   (+ T22 no pai)                       ▼
                         audit/gap-fill-backlog-index.md
                                        │
              ┌───────────┬─────────────┼──────────────┬──────────┐
              ▼           ▼             ▼              ▼          ▼
           T23 ui     T24 catalog   T25 negative   T26 mcp   T27 sdk
           browser    indexing      integral       parallel  dec015
                                        │
                                        ▼
                                 handoff T07
```

## 5. Dados

- Entrada: Markdown T01 + T05 (já versionados).
- Saída: índice + 5 tasks pai + asserts BDD.
- Sem secrets; sem logs brutos.

## 6. Erros e bordas

| Caso | Tratamento |
|---|---|
| Lacuna sem falha runtime | Ainda assim task gap (D-T06-001) |
| UI só API no T21 | Task T23 exige browser (D-T06-003) |
| T22 já cobre tooling | Índice declara “não duplicar”; sem T2x-gap-tooling |
| BDD-015 | Excluído |
| Cobertos integrais | Sem task |

## 7. Segurança

- Não copiar PAT/`.env`/Authorization.
- Tasks referenciam paths de inventário e BDD IDs, não dumps.

## 8. Compatibilidade

- Não altera runtime T19/T21.
- Tasks abertas no pai entram no pipeline **do pai**.
- PR empilhado: base T05; merge order … → T05 → T06.

## 9. Observabilidade

- Índice lista lacunas cobertas, tasks, superfícies, cross-ref T22, contagens.
- BDD valida presença T23–T27, browser em T23, cobertura de todas as lacunas, ausência de BDD-015/T22-duplicata, ENG-010.

## 10. Riscos e rollback

| Risco | Mitigação |
|---|---|
| Misturar com falhas T22 | D-T06-005 |
| Fechar UI só com API | D-T06-003 + aceite T23 |
| Over-split 1:1 BDD | D-T06-002 |
| Merge sem T05 | PR base T05; merge notes |

Rollback: remover T23–T27 + índice + testes BDD desta task.

## 11. Fora de escopo

- Implementar browser/keywords/produto.
- Re-executar green path para “passar” após expandir suíte.
- BDD-015.
- Tasks de falha runtime (T05/T22).
- Declarar MVP entregue (T07).
