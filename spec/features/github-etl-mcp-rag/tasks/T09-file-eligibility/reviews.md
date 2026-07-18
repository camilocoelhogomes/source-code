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

---

## Review — Unit tests (v0.1.0) — QA delivery

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Artefato | `unit-test-plan.md` + `tests/unit/eligibility/test_file_eligibility.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (Architect revisa depois; sem gate humano intermediário) |
| Resultado | `TESTS_READY_FOR_REVIEW` |

### Casos entregues

U-01..U-24 — paths inválidos (`EligibilityError`), sem gitignore, aninhado + `!`,
CSV/imagens case-insensitive, sem extensão, duplicatas, normalização `\`,
loader (root inexistente / skip `.git/` / nested / vazio / não-UTF-8),
sem size caps, idempotência/ordem, Protocol e denylists.

### Evidência red (pré-implementação)

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/eligibility/test_file_eligibility.py -q --tb=line --no-cov
```

Resultado observado (2026-07-18): **21 failed, 3 passed**.

| Resultado | Casos | Motivo |
|---|---|---|
| FAIL | U-01..U-18, U-20, U-21, U-24 | `NotImplementedError` nos stubs `PathspecFileEligibilityFilter.filter` / `load_gitignore_sources` |
| PASS | U-19, U-22, U-23 | assinatura sem size params; Protocol runtime; constantes `rules.py` já materializadas |

Exemplo de falha esperada:

```text
NotImplementedError: PathspecFileEligibilityFilter.filter: implementação após unit-test-plan (T09)
NotImplementedError: load_gitignore_sources: implementação após unit-test-plan (T09)
```

Código de produção **não** alterado além dos stubs existentes.

---

## Review — Unit tests (v0.1.0)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` + `tests/unit/eligibility/test_file_eligibility.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (sem gate humano intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Contratos I-T09-001..008 | OK | U-05/12/13/14/19/21/22/23; assinatura sem size; Protocol; denylists |
| Extremos / corners | OK | U-06 aninhado; U-07 `!`; U-11 extensionless gitignored |
| Inválidos → `EligibilityError` | OK | U-01..U-04; mensagem cita path (U-01/U-02) |
| Vazios | OK | U-05 `sources=[]`; U-18 loader sem `.gitignore` |
| Falhas loader | OK | U-15 root inexistente; U-24 não-UTF-8; U-16 skip `.git/` |
| Alinhamento D-T09-001..006 | OK | porta pura, pathspec corners, denylist, sem extensão, sem caps |
| Evidência red (`NotImplementedError`) | OK | 21 failed, 3 passed (U-19/22/23); stubs intactos |
| SUGGESTIONs BDD anteriores | OK | U-12 duplicatas; U-17 estrutura `GitignoreSource` |

### Achados

| Severidade | Achado | Evidência | Correção esperada | Resolução |
|---|---|---|---|---|
| `MAJOR` | U-02 assertava só `".."` na mensagem, não o path ofensivo | `test_u02_parent_escape_raises` (antes); I-T09-007 / design §2.5 | `assertIn("../outside.py", …)` | Corrigido pelo Architect na review |
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — | — |
| `SUGGESTION` | `filter([], []) → []` e path absoluto estilo Windows não cobertos | critérios “vazios” / §2.7 | Opcional na implementação se surgir dúvida de contrato | Aceito no MVP |

### Decisão

`APPROVED_BY_ARCHITECT` — unit-test-plan v0.1.0 e testes unitários suficientes. Prosseguir para implementação (Developer).
