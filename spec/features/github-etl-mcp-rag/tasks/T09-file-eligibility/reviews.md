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
