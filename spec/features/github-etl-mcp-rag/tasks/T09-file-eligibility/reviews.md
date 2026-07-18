# Reviews — T09-file-eligibility

## Review — Design (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Escopo estrito (sem remota/index/UI) | OK | `design.md` §1, §5 |
| Porta `FileEligibilityFilter` alinhada ao plano | OK | D-T09-001; plano §2 |
| Matching `.gitignore` via pathspec (BR-023/DEC-015/BDD-024) | OK | D-T09-002; dep `pyproject.toml` |
| Inclusão textuais / MD / Java (REQ-014) | OK | D-T09-004 denylist (não allowlist) |
| Exclusão CSV, imagens, gitignore (REQ-015) | OK | D-T09-003, D-T09-004 |
| Sem caps de tamanho (REQ-019) | OK | D-T09-006 |
| Corner: sem `.gitignore` | OK | D-T09-003 item 5 |
| Corner: gitignore aninhado | OK | D-T09-003 + `load_gitignore_sources` |
| Corner: extensões mistas | OK | §3 mapeamento; regras por path |
| Corner: sem extensão documentado | OK | D-T09-005 include-by-default |
| API da porta fechada (puro vs root+I/O) | OK | D-T09-001 porta pura; loader separado |
| Segurança path traversal | OK | §2.6; rejeição absoluto/`..` |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |
| `SUGGESTION` | Semântica “last match wins” entre múltiplos `.gitignore` é aproximação do Git; edge cases de negação entre níveis podem divergir | D-T09-003 | Na etapa BDD/unit: cobrir negação `!` na mesma fonte e un-ignore em filho; se divergência real aparecer, documentar gap MVP sem expandir para exclude global |
| `SUGGESTION` | Lista de extensões de imagem pode crescer (ex.: `.psd`, `.raw`) | D-T09-004 | Aceitável no MVP; estender `rules.py` só se produto pedir |

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.1.0. Prosseguir para BDD (QA) / interfaces sem alteração de escopo.

---

## Review — BDD (v0.1.0) — QA delivery

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Artefato | `bdd.md` + `tests/bdd/test_file_eligibility.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (Architect aprova depois; sem gate humano intermediário) |
| Resultado | `TESTS_READY_FOR_REVIEW` |

### Cenários entregues

ELIG-01..07 — BDD-006, corners (sem gitignore, aninhado, extensões mistas, sem extensão), pathspec/BDD-024, sem caps de tamanho.

### Evidência red (pré-implementação)

```bash
python -m pytest tests/bdd/test_file_eligibility.py -q
```

Esperado: falha por `ImportError` dos módulos `github_rag.eligibility.filter` / `gitignore` (ainda não implementados).

---

## Review — BDD (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `tests/bdd/test_file_eligibility.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| BDD-006 textuais/MD/Java in; CSV/imagens/gitignore out | OK | ELIG-01; `TestELIG01Bdd006EligibleFilter` |
| Corner: sem `.gitignore` | OK | ELIG-02; `gitignore_sources=[]` → só tipo |
| Corner: gitignore aninhado + loader | OK | ELIG-03; fontes in-memory + `load_gitignore_sources` |
| Corner: extensões mistas + case-insensitive | OK | ELIG-04; inclui `.svg`/`.JPEG`/`report.CSV` |
| Corner: sem extensão (D-T09-005) | OK | ELIG-05; Makefile/Dockerfile/LICENSE in; `node_modules/pkg` out |
| pathspec / BDD-024 (D-T09-002) | OK | ELIG-06; comentário/`!`/glob + inspeção de import |
| Sem caps de tamanho (D-T09-006) | OK | ELIG-07; paths elegíveis + assinatura sem params de size |
| Aderência D-T09-001 (porta pura) | OK | Cenários usam `filter(paths, sources)`; loader separado em ELIG-03 |
| Aderência D-T09-003/004/005 | OK | ELIG-02..05 mapeados na tabela de rastreabilidade |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |
| `SUGGESTION` | ELIG-03 loader valida resultado do filtro, não asserta estrutura explícita de `GitignoreSource` | `test_load_gitignore_sources_nested_tree` | Cobrir equivalência de fontes nos unitários de contrato do loader |
| `SUGGESTION` | Colapso de duplicatas (D-T09-001) não está nos BDD | design §2.2 | Cobrir em testes unitários pós-interfaces |

### Decisão

`APPROVED_BY_ARCHITECT` — BDD v0.1.0. Prosseguir para interfaces.

---

## Review — Interfaces (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` + stubs `eligibility/{filter,rules,gitignore}.py` + `pyproject.toml` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Porta pura `filter(paths, gitignore_sources)` | OK | I-T09-001; `FileEligibilityFilter` Protocol |
| Separação loader × porta | OK | I-T09-003; `GitignoreSource` + `load_gitignore_sources` |
| pathspec GitWildMatch + dep `>=0.12` | OK | I-T09-002; import em `filter.py`; `pyproject.toml` |
| Denylist CSV/imagens + sem allowlist | OK | I-T09-004; `rules.py` constantes + `EligibilityRules` |
| Sem extensão include-by-default | OK | I-T09-005; `include_extensionless=True` |
| Sem params de tamanho | OK | I-T09-006; assinatura `filter` |
| Comentários responsabilidade/separação | OK | docstrings padrão T04 em cada contrato |
| Stubs sem comportamento completo | OK | `NotImplementedError` em `filter` / `load_gitignore_sources` |

### Achados

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` | — | — |
| `SUGGESTION` | Colapso de duplicatas e validação de path absoluto/`..` ficam para unit-test-plan | I-T09-007 | Cobrir nos unitários pós-interfaces |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces v0.1.0. Prosseguir para unit-test-plan (QA).
