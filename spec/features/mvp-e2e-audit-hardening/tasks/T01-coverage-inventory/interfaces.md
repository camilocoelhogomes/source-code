# Interfaces — T01-coverage-inventory

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T01-coverage-inventory` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`HUMAN_DESIGN_APPROVED`) |
| BDD base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/mvp-e2e-audit-hardening-T01-coverage-inventory` |
| Natureza | **100% documental** (D-T01-001 / D-T01-006) |
| Escopo desta etapa | Contrato lógico `CoverageInventory` + schema §6 — **sem** Protocol/ABC Python, **sem** código de produção |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Interface lógica única alinhada design §5–§6 e BDD INV-01..08; zero runtime Python. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Forma | Papel |
|---|---|---|
| `CoverageInventory` | Artefato Markdown canônico | Matriz BDD × evidência × status; SoT de lacunas para T06 |

Path canônico (D-T01-002):

```text
spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md
```

### Explicitamente fora de escopo — sem interfaces Python de runtime

| Item | Motivo |
|---|---|
| `typing.Protocol` / ABC / classes Python | D-T01-006: não há superfície de runtime a implementar |
| Módulos em `src/` | Task documental; zero código de produção (D-T01-001) |
| Alteração de `e2e/robot/**`, compose, produto | Fora do escopo T01 |
| Execução pytest/Robot como parte do contrato | Runs = T03/T04 (D-T01-007) |
| Abertura de tasks no pai | T05/T06 |
| Automatização BDD-015 | REQ-010 / D-T01-004 |

**Não serão criados** arquivos `.py` de interface nesta task. O único “contrato” é o schema documental abaixo, validado pelos testes BDD INV-01..08 sobre o Markdown.

## 2. Interface lógica: `CoverageInventory`

```text
# CoverageInventory — interface lógica (documental)
#
# Responsabilidade:
#   Representar a matriz versionável BDD-001–024 (exceto BDD-015) do pai
#   github-etl-mcp-rag cruzada com evidência Robot/pytest/browser/ausente,
#   classificando cada linha como `coberto-integral` ou `lacuna`, e servir
#   como Source of Truth (SoT) de lacunas para T06 (ParentGapFillBacklog).
#
# Motivo da separação:
#   - Isola o inventário de auditoria da feature filha do ownership da suíte
#     Robot (permanece em T21 / BR-002).
#   - Evita misturar inventário estático com runs (T03/T04) ou abertura de
#     backlog no pai (T05/T06).
#   - Congela um schema consumível por humanos e por testes BDD de artefato,
#     sem introduzir Protocol/ABC Python onde não há runtime.
#
# Forma:
#   Artefato Markdown único no path canônico acima.
#   Sem métodos, sem tipos Python, sem serialização além de Markdown/tabela.
```

### Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T01-001 | Única interface lógica: `CoverageInventory` | D-T01-006 | design §5 |
| I-T01-002 | Materialização = Markdown em `audit/coverage-inventory.md` | SoT versionável em PR | D-T01-002; INV-01 |
| I-T01-003 | Sem Protocol/ABC/classes Python | Natureza documental | D-T01-001/006 |
| I-T01-004 | Status binário `coberto-integral` \| `lacuna` | Parcial T21 vira lacuna + nota | D-T01-003; INV-06/07 |
| I-T01-005 | BDD-015 fora da tabela; nota de exclusão obrigatória | REQ-010 | D-T01-004; INV-03/04 |
| I-T01-006 | Produção por inspeção estática (sem run) | Separação de runs | D-T01-007; INV-02 |
| I-T01-007 | Consumidor canônico = T06 | Handoff ParentGapFillBacklog | INV-08; plano §1.4 |

## 3. Schema da matriz (design §6)

### 3.1 Cabeçalho do artefato (obrigatório)

Texto **antes** da tabela da matriz deve declarar:

| Campo | Conteúdo mínimo |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Data | data do inventário |
| Critério | texto integral do pai (BDD-001–024) |
| Exclusão BDD-015 | id `BDD-015` + palavra de exclusão (`exclu` / `fora`) no cabeçalho |
| Método | inspeção estática (sem run) |

Alinhado a INV-02.

### 3.2 Nota fixa BDD-015 (fora da tabela)

> BDD-015 — Apoiar Discovery no Cursor: **fora do inventário automatizado** (REQ-010 / DEC-019). Validação humana; não gera linha de status nesta matriz.

- Obrigatória no corpo (INV-03).
- **Proibido** linha com `bdd_id` = `BDD-015` (INV-04).

### 3.3 Colunas da tabela

Uma linha por BDD em `{001..014} ∪ {016..024}` — exatamente **23** linhas.

| Coluna | Tipo / domínio | Obrigatório | Regras |
|---|---|---|---|
| `bdd_id` | `BDD-00N` | sim | Conjunto fechado acima; sem 015 |
| `superficie` | `health` \| `catalog_indexing` \| `ui` \| `mcp` \| `negative` \| `tooling-e2e` \| `sdk` | sim | `sdk` tipicamente BDD-024 |
| `status` | `coberto-integral` \| `lacuna` | sim | Sem status “parcial” |
| `evidencia_robot` | path + caso/tag (`bdd00N`) ou `ausente` | sim | Não vazio |
| `evidencia_pytest` | path do teste/contrato ou `ausente` / `n/a` | sim | Não vazio |
| `evidencia_browser` | `sim` \| `nao` \| `n/a` | sim | `sim` = keyword Browser presente |
| `nota_parcial_t21` | citação fatia T21/DEC-019 ou `—` | sim | Obrigatório ≠ `—` se lacuna por parcialidade T21 |
| `motivo_lacuna` | texto curto ou `—` | sim | Se `status=lacuna` ⇒ ≠ `—` e não vazio |

Cabeçalho da tabela deve conter exatamente esses nomes de coluna (INV-05).

### 3.4 Regras de classificação: `coberto-integral` vs `lacuna`

| Status | Condição |
|---|---|
| `coberto-integral` | Evidência Robot **e/ou** pytest cobre o critério **integral** do texto BDD do pai. Exige ao menos uma evidência real: `evidencia_robot` ou `evidencia_pytest` ≠ `ausente`/`n/a` (REQ-009 / INV-06). |
| `lacuna` | Ausência de evidência; assert parcial; API-smoke onde o integral exige mais; UI só via RequestsLibrary quando o BDD exige fluxo UI; ou dúvida conservadora (design §9). |

Regras compostas obrigatórias:

1. **Anti-parcial T21 (denylist mínima):** BDD-003, BDD-006, BDD-013, BDD-024 → `status=lacuna` **e** `nota_parcial_t21` ≠ `—` (INV-07 / BR-001).
2. **UI sem browser (D-T01-005):** se `superficie=ui` e `evidencia_browser=nao` → **não** pode ser `coberto-integral`.
3. **Parcialidade documentada:** fatia T21 `manual_or_partial` / “Sim (parcial)” / smoke → presumir `lacuna` até prova integral.
4. **Campos de lacuna:** toda linha `lacuna` tem `motivo_lacuna` preenchido (≠ `—`).

### 3.5 Heurísticas de preenchimento (aplicação na matriz)

- UI atual = RequestsLibrary (`ui.robot` / `catalog_indexing.robot`) → BDDs de interação UI (checkbox, listagem visual, busca na UI) → `lacuna`, `evidencia_browser=nao`, superfície `ui` quando aplicável.
- BDD-024: Robot smoke ≠ integral se conformidade DEC-015/BR-024 não estiver coberta por testes SDK.
- Em dúvida se é integral → `lacuna` (conservador); T06 decide task.

## 4. Contrato de consumo por T06 (`ParentGapFillBacklog`)

| Aspecto | Contrato |
|---|---|
| Input | `CoverageInventory` no path canônico, schema §6 completo |
| Seleção | Toda linha com `status=lacuna` |
| Chave de rastreio | `bdd_id` + `superficie` + `motivo_lacuna` (INV-08) |
| Uso de notas | `nota_parcial_t21` informa agrupamento `gap-teste` / `assert-fraco` |
| UI | Lacunas `superficie=ui` (ou motivo UI sem browser) exigem task(s) com automação browser no pai — API HTTP sozinha não fecha (REQ-007 / BDD-006 da feature) |
| Exclusões | BDD-015 nunca gera task a partir desta matriz |
| Não-contrato | Green path T21 verde **não** encerra lacunas; inventário não declara “auditoria encerrada” só por green path (INV-08) |
| Ownership | T06 abre tasks no pai; **não** altera o inventário T01 nem a suíte nesta feature |

Fluxo (design §7):

```text
CoverageInventory (audit/coverage-inventory.md)
        │
        ▼
T06 ParentGapFillBacklog  →  tasks gap-* no pai (após T05)
```

## 5. Fontes somente-leitura (não são interfaces desta task)

| Fonte | Uso |
|---|---|
| `spec/features/github-etl-mcp-rag/requirements.md` (BDD-001–024) | Critério integral |
| Design T21 §3.5 / DEC-019 | Fatias parciais/smoke |
| `e2e/robot/**`, `resources/`, `libraries/` | Evidência Robot |
| `tests/**` relevantes | Evidência pytest |

## 6. Segurança e compatibilidade

- Sem tokens, `.env`, logs de run ou `e2e/results/` no artefato.
- Não altera contratos T19/T21 nem ownership Robot.
- Critério desta feature é mais estrito que o green path T21 parcial — muitas `lacuna` são esperadas e são input de T06.

## 7. DoD do contrato (esta etapa)

- [x] Interface lógica `CoverageInventory` documentada com responsabilidade e motivo da separação.
- [x] Schema §6 (colunas, domínios, regras integral/lacuna, exclusão 015) congelado.
- [x] Contrato de consumo T06 explícito.
- [x] Explicitado: **nenhuma** interface Python de runtime.
- [ ] Materialização do Markdown (implementação documental — etapa posterior do Developer).
