# Refactoring Blue — T27-gap-sdk-dec015-conformity

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T27-gap-sdk-dec015-conformity` |
| Autor | Developer |
| Data | 2026-07-19 |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Branch | `feature/github-etl-mcp-rag-T27-gap-sdk-dec015-conformity` |
| Superfície | docs (`interfaces.md`, `bdd.md`) + docstring de teste (`tests/bdd/test_dec015_conformity.py`) |
| Orientação | `reviews.md` §5 (B-1/B-2/B-3), a partir dos achados `SUGGESTION` R-4/R-6 |

## 1. Baseline (pré-Blue)

| Métrica | Valor | Evidência |
|---|---|---|
| Suíte completa | **1258 passed**, 2 skipped | `reviews.md` — review `IMPLEMENTATION` `APPROVED_BY_ARCHITECT` 0.1.0 (commits `6e5ebf2`/`fdf29b0`) |
| Cobertura TOTAL | **96.53%** | idem; gate ≥95% |
| Subset T27 (`test_dec015_conformity.py` + 2 suítes de auditoria + `test_coverage_inventory_schema.py`) isolado | 1 failed (corner case pré-existente R-5) / 83 passed / 7 subtests | reproduzido nesta etapa, idêntico ao relatado nas rodadas QA/Architect anteriores |
| Complexidade de produção | Nenhuma (`src/github_rag/**` inalterado desde o início da task) | `git diff da47ed4~1..HEAD -- src/` vazio |
| Achados pendentes (não bloqueantes) | R-4 (`interfaces.md` §5 diverge da implementação real de `TestDEC10Br024Postgres`), R-6 (`bdd.md` DEC015-14 usa `nota_parcial_t21=n/a`, artefato real usa `—`), R-5 (import circular pré-existente, fora de escopo) | `reviews.md` §1/§4 |

### Comando baseline (subset, reproduzido nesta etapa antes das mudanças Blue)

```bash
python -m pytest tests/bdd/test_dec015_conformity.py \
  tests/bdd/test_mvp_e2e_audit_coverage_inventory.py \
  tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py \
  tests/unit/audit/test_coverage_inventory_schema.py -q --no-cov
# → 1 failed (TestDEC03GitPythonReference — R-5, pré-existente/isolado), 83 passed, 7 subtests passed
```

## 2. Metas Blue

| Meta | Critério | Resultado |
|---|---|---|
| Resolver R-4 sem aumentar complexidade | Docs/docstring alinhados à implementação real; **não** migrar `TestDEC10Br024Postgres` para `SourceConformityRule` se isso aumentar complexidade | **OK** — só documentação (B-1) |
| Resolver R-6 | `bdd.md` §DEC015-14 `nota_parcial_t21=n/a` → `—` | **OK** (B-2) |
| Não tocar produção/import circular | `src/github_rag/**` inalterado; R-5 não endereçado | **OK** (B-3) |
| Zero regressão comportamental | Suíte completa com os mesmos números do baseline | **OK** — ver §4 |

## 3. Mudanças Blue aplicadas

| # | Alvo | Mudança | Motivo |
|---|---|---|---|
| B-1 | `tests/bdd/test_dec015_conformity.py::TestDEC10Br024Postgres` (docstring) | Adiciona parágrafo explicando a exceção deliberada a `SourceConformityRule`/`assert_source_conforms` (BR-024 toca 4 arquivos com regras heterogêneas; 2 delas fora do contrato 1-arquivo-1-regra do helper). Nenhuma linha de teste/asserção alterada. | Resolve R-4 documentando a implementação real em vez de forçar a abstração — caminho de menor risco indicado em `reviews.md` §5 B-1. |
| B-1 | `interfaces.md` §5 (tabela classe↔mecanismo) | Linha de `TestDEC10Br024Postgres` corrigida de `SourceConformityRule`/`assert_source_conforms` + regex de URL` para `Path.read_text` + `assertRegex`/`assertNotRegex` direto (exceção deliberada — ver nota)`; nota explicativa adicionada após a tabela de classes (§5). | Mesma justificativa — fecha a divergência doc↔código sem tocar em código de produção/teste executável. |
| B-2 | `bdd.md` §DEC015-14 | `nota_parcial_t21=n/a` → `nota_parcial_t21=—`; header (`Estado`/`Versão`) e histórico (§0) atualizados para `0.1.1`/`BLUE_READY_FOR_REVIEW`, registrando a correção. | Resolve R-6 — alinha à convenção real de `coverage-inventory.md` (toda linha `coberto-integral` usa `—`, nunca `n/a`). |
| B-3 | (decisão, não mudança) | Nenhum arquivo em `src/github_rag/**` tocado; import circular pré-existente (R-5) **não** corrigido nesta task. | Fora de escopo — `reviews.md` §5 B-3; candidato a task de hardening separada. |

Nenhuma regex/constraint de teste foi relaxada; nenhum arquivo em `src/github_rag/**`, `e2e/robot/**` ou composes foi tocado.

## 4. Baseline pós-Blue

```bash
python -m pytest tests/bdd/test_dec015_conformity.py \
  tests/bdd/test_mvp_e2e_audit_coverage_inventory.py \
  tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py \
  tests/unit/audit/test_coverage_inventory_schema.py -q --no-cov
# → 1 failed (TestDEC03GitPythonReference — R-5, pré-existente/isolado, idêntico ao baseline), 83 passed, 7 subtests passed

python -m pytest -q
# → 1258 passed, 2 skipped, cobertura global 96.53% (gate ≥95%)
```

| Métrica | Pré-Blue | Pós-Blue | Delta |
|---|---|---|---|
| Suíte completa | 1258 passed, 2 skipped | 1258 passed, 2 skipped | 0 |
| Cobertura TOTAL | 96.53% | 96.53% | 0 |
| Subset T27 isolado | 1 failed (R-5) / 83 passed / 7 subtests | 1 failed (R-5) / 83 passed / 7 subtests | 0 |

Comparação de performance before/after: **N/A** — Blue é documental/docstring, sem hot path e sem meta de latência.

## 5. Decisão

`BLUE_READY_FOR_REVIEW` — mudanças limitadas a documentação (`interfaces.md`, `bdd.md`) e docstring de teste; zero alteração de comportamento/contratos/cobertura; suíte completa estável em **1258 passed / 2 skipped / 96.53%**. Pendente `BLUE_APPROVED_BY_ARCHITECT`.

## 6. Review Architect

Reproduzido de forma independente (venv efêmera, removida ao final), não só aceito por relato: diff `git show 2702ae4` confirma que só `bdd.md`, `interfaces.md` e a docstring de `TestDEC10Br024Postgres` (comentário, sem tocar em nenhuma linha de asserção/lógica de teste) foram alterados — B-1/B-2 aplicados exatamente como orientado em `reviews.md` §5 (menor risco, sem migrar `TestDEC10Br024Postgres` para `SourceConformityRule`, sem tocar código executável). B-3 confirmado por `git diff fdf29b0..HEAD --stat -- src/ e2e/robot/ docker-compose*.yml Dockerfile` vazio — nenhum arquivo de produção/robot/compose tocado nos commits `2702ae4`/`6b1cde4`. `python -m pytest -q` → **1258 passed, 2 skipped**, cobertura **96.53%** — idêntico byte a byte ao baseline pré-Blue registrado em §1/§4; zero regressão comportamental. `CHANGELOG.md` registra a entrada T27 em `[Unreleased]` com escopo e gap fechado corretos.

**Decisão:** `BLUE_APPROVED_BY_ARCHITECT`
**Data:** 2026-07-19
**Autor:** tech-lead-architect
**Versão:** v0.1.0
