# Design — T01-coverage-inventory

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T01-coverage-inventory` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `PENDING_ARCHITECT_REVIEW` |
| Versão | `0.1.0` |
| Branch | `feature/mvp-e2e-audit-hardening-T01-coverage-inventory` |
| Natureza | **Puramente documental** — sem código de produção, sem alteração de `e2e/`, sem execução de testes |
| Rastreabilidade | REQ-001, REQ-008–010; BR-001–002; DEC-002; ENG-001–002; BDD-001, BDD-008 (parcial) desta feature |

## 1. Contexto

Feature filha operacional: audita cobertura MVP integral do pai `github-etl-mcp-rag` (BDD-001–024, exceto BDD-015) contra a suíte Robot/T21 e contratos pytest existentes.

T21 (DEC-019) já mapeia fatias **observáveis/parciais** (API-smoke, cron sem esperar 24h, paralelismo sem SLO, UI via RequestsLibrary). Esta auditoria usa o **texto integral** dos BDD do pai (BR-001 / DEC-002): fatia parcial ≠ `coberto-integral`.

Inventário é SoT de lacunas para T06 (`ParentGapFillBacklog`). Não bloqueia T02–T04.

## 2. Problema

Não existe matriz versionada BDD × evidência com status `coberto-integral` | `lacuna`. Sem ela, T06 não tem base rastreável para abrir tasks `gap-teste` no pai.

## 3. Solução proposta

### 3.1 Natureza documental (explícita)

| Faz | Não faz |
|---|---|
| Produzir artefato Markdown versionável | Código Python/Robot novo |
| Classificar cada BDD por inspeção estática | Rodar pytest / `python -m github_rag.e2e` |
| Citar evidência (arquivo, caso, tag, teste) | Abrir tasks no pai |
| Marcar parcial/API-smoke/UI-sem-browser como lacuna | Alterar `e2e/robot/**` ou produto |

**Justificativa do mínimo de “interfaces”:** não há superfície de runtime a implementar. O contrato lógico `CoverageInventory` + schema da matriz bastam para QA/Developer materializarem o artefato e para T06 consumi-lo.

### 3.2 Como a matriz será produzida

1. Extrair BDD-001–024 do pai (`spec/features/github-etl-mcp-rag/requirements.md`); **omitir BDD-015** do corpo da matriz (REQ-010), com nota fixa de exclusão.
2. Cruzar com mapeamento T21 (§3.5 do design T21) e inspeção de:
   - `e2e/robot/*.robot` + `resources/` + `libraries/`
   - testes pytest em `tests/**` que exercitam contratos das tasks do pai relevantes ao critério do BDD
3. Para cada BDD, preencher uma linha do schema (§6) com status e evidência.
4. Regra de classificação (ENG-001 / REQ-009):
   - `coberto-integral` — só se evidência Robot **e/ou** pytest cobre o critério **integral** do texto BDD (UI com browser quando o BDD exige fluxo UI; asserts de exclusão/progresso/erro+histórico/paralelismo sob limite quando exigidos).
   - `lacuna` — ausência, assert parcial, API-smoke onde o integral exige mais, ou UI só via RequestsLibrary quando o fluxo é UI.
5. Publicar em path canônico (§3.3). Não executar suítes nesta task.

### 3.3 Onde vive

| Artefato | Path | Dono |
|---|---|---|
| Matriz (SoT) | `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md` | esta feature |
| Design desta task | `…/tasks/T01-coverage-inventory/design.md` | esta feature |
| Fontes somente-leitura | `e2e/robot/**`, design T21, `requirements.md` do pai, `tests/**` | pai / T21 |

Diretório `audit/` criado na implementação documental da matriz (não nesta etapa de design).

## 4. Impacto / arquivos

| Arquivo | Ação na implementação da T01 |
|---|---|
| `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md` | **criar** (matriz completa) |
| `e2e/robot/**`, produto, compose | **não tocar** |
| Tasks em `github-etl-mcp-rag/tasks/` | **não criar** (T05/T06) |

## 5. Interfaces lógicas

Sem Protocol/ABC Python. Contrato documental único:

### `CoverageInventory`

- **Responsabilidade:** matriz BDD-001–024 (exc. 015) × evidência Robot/pytest/browser/ausente, com status `coberto-integral` | `lacuna`, alimentando T06.
- **Motivo da separação:** isola o SoT de auditoria da feature filha; ownership da suíte permanece em T21 (BR-002); evita misturar inventário com runs (T03/T04) ou backlog (T05/T06).

Campos obrigatórios por linha — ver schema §6.

## 6. Schema da matriz

Cabeçalho do artefato deve declarar: feature, data, critério = texto integral do pai, exclusão BDD-015, método = inspeção estática (sem run).

Tabela (uma linha por BDD 001–014 e 016–024):

| Coluna | Tipo / valores | Obrigatório |
|---|---|---|
| `bdd_id` | `BDD-00N` | sim |
| `superficie` | `health` \| `catalog_indexing` \| `ui` \| `mcp` \| `negative` \| `tooling-e2e` \| `sdk` (para BDD-024) | sim |
| `status` | `coberto-integral` \| `lacuna` | sim |
| `evidencia_robot` | path + nome do caso/tag (`bdd00N`) ou `ausente` | sim |
| `evidencia_pytest` | path do teste/contrato ou `ausente` / `n/a` | sim |
| `evidencia_browser` | `sim` (keyword Browser) \| `nao` \| `n/a` | sim |
| `nota_parcial_t21` | citação da fatia T21/DEC-019 quando status=`lacuna` por parcialidade; senão `—` | sim se lacuna por parcial |
| `motivo_lacuna` | texto curto (ex.: “UI só RequestsLibrary”; “cron sem ciclo diário”; “sem assert exclusão CSV”) ou `—` | sim se `lacuna` |

Nota fixa (fora da tabela):

> BDD-015 — Apoiar Discovery no Cursor: **fora do inventário automatizado** (REQ-010 / DEC-019). Validação humana; não gera linha de status nesta matriz.

Heurísticas mínimas (aplicação na escrita da matriz, não no design):

- UI atual = RequestsLibrary em `ui.robot` / `catalog_indexing.robot` → qualquer BDD cujo critério integral exige interação UI (checkbox, listagem visual, busca na UI) → `lacuna` com `evidencia_browser=nao`, superfície `ui` quando aplicável (REQ-007 / BR-008 desta feature).
- Tags T21 marcadas `manual_or_partial` / design “Sim (parcial)” / “smoke” → presumir `lacuna` até evidência provar integral.
- BDD-024: cobertura tipicamente unitária/revisão SDK; Robot smoke ≠ integral se o critério DEC-015/BR-024 não estiver coberto por testes de conformidade.

## 7. Fluxo

```text
requirements pai (BDD-001–024) ──┐
T21 design mapeamento            ├──► CoverageInventory (audit/coverage-inventory.md)
e2e/robot/** + tests/** (leitura)┘         │
                                           ▼
                                    T06 ParentGapFillBacklog
```

## 8. Dados

Somente texto Markdown versionável. Sem segredos, sem logs de run, sem `e2e/results/`.

## 9. Erros / ambiguidade

| Situação | Tratamento |
|---|---|
| Evidência Robot parcial vs texto integral | `lacuna` + `nota_parcial_t21` |
| Pytest cobre contrato unitário mas Robot não observa runtime | documentar ambas evidências; status pelo **critério integral** (runtime UI/browser conta quando o BDD é de UI) |
| Dúvida se é integral | classificar `lacuna` (conservador); T06 decide task |
| BDD-015 | exclusão explícita; sem linha de status |

## 10. Segurança

Sem tokens, `.env` ou artefatos Robot. Não citar valores de secrets em evidências.

## 11. Compatibilidade

- Não altera contratos T19/T21 nem ownership.
- Consome layout atual: `health.robot`, `catalog_indexing.robot`, `ui.robot`, `mcp.robot`, `negative.robot` + resources RequestsLibrary / `McpKeywords.py`.
- Critério desta feature é mais estrito que o green path T21 parcial — esperado muitas `lacuna`; isso é input de T06, não regressão de T21.

## 12. Observabilidade

Matriz versionada em `audit/`; legível em PR. Sem métricas runtime nesta task.

## 13. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Subcontar lacunas (aceitar parcial T21 como integral) | BR-001 + heurísticas §6; review Architect na matriz |
| Explosão 1:1 BDD→task | T01 só inventaria; agrupamento por superfície fica em T06 (ENG-006) |
| Inventário desatualizado se T21 mudar depois | T01 congela snapshot na data do artefato; reauditoria = nova task/delta |
| Confundir “pytest verde” com cobertura e2e integral | colunas separadas Robot / pytest / browser |

## 14. Rollback

Remover ou reverter `audit/coverage-inventory.md` (+ este design se necessário). Sem impacto em runtime.

## 15. O que NÃO fazer

- Não rodar pytest nem `python -m github_rag.e2e` (T03/T04).
- Não abrir tasks em `github-etl-mcp-rag/tasks/` (T05/T06).
- Não alterar `e2e/robot/**`, fixtures, compose, nem código de produto.
- Não automatizar BDD-015.
- Não implementar Browser Library / novos asserts nesta feature/task.
- Não declarar MVP entregue nem “auditoria encerrada” só com inventário.

## 16. Decisões de design

| ID | Decisão |
|---|---|
| D-T01-001 | Task 100% documental; zero código de produção |
| D-T01-002 | SoT = `audit/coverage-inventory.md` |
| D-T01-003 | Status binário `coberto-integral` \| `lacuna` (sem “parcial” como status — parcial vira `lacuna` + nota) |
| D-T01-004 | BDD-015 fora da tabela; nota de exclusão obrigatória |
| D-T01-005 | UI sem browser = lacuna quando o BDD exige fluxo UI |
| D-T01-006 | Interface lógica única: artefato `CoverageInventory` + schema §6 |
| D-T01-007 | Produção por inspeção estática; runs ficam em T03/T04 |

## 17. Critério de pronto (DoD desta task, pós-implementação documental)

- Matriz com todas as linhas BDD-001–014 e 016–024, schema completo.
- Nota BDD-015 presente.
- Nenhuma alteração em `e2e/` ou produto.
- Handoff claro para T06.
